import base64
import datetime
import glob
import os
import folium
from geopy.geocoders import Nominatim
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# 🐾 Настройка на страницата и оригинален премиум 3D CSS дизайн за PixelApp
st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

st.markdown(
    """
<style>
    /* Модерни кутии за въвеждане на данни */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important; padding: 10px 15px !important;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4), -2px -2px 8px rgba(255, 255, 255, 0.02) !important;
        margin-bottom: 15px !important;
    }
    /* Премиум 3D бутони */
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"],
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #2e2e2e, #1c1c1c) !important; 
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important; 
        border-radius: 10px !important;
        box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5), -1px -1px 4px rgba(255, 255, 255, 0.05) !important;
        transition: all 0.2s ease !important; 
        font-weight: bold !important;
        width: 100% !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFileUploaderDropzone"] button:hover {
        background: linear-gradient(135deg, #3d3d3d, #252525) !important;
        transform: translateY(-2px) !important; 
        box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.6) !important;
    }
    small { color: #888 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# 🪙 Дефиниране на константи и файлови пътища
KATEGORII = [
    "Храна и напитки",
    "Транспорт",
    "Куче",
    "Други",
    "Нощувки/Хотел",
    "Депозит/Резервация",
]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"

# Автоматично създаване на файловете, ако не съществуват
if not os.path.exists(MAP_FILE):
  pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(
      MAP_FILE, index=False, encoding="utf-8"
  )


def get_emoji(cat):
  m = {
      "Храна и напитки": "🍔",
      "Транспорт": "🚗",
      "Куче": "🐾",
      "Нощувки/Хотел": "🏨",
      "Депозит/Резервация": "📌",
      "Други": "🪙",
  }
  return m.get(cat, "💳")


for f, cols in [
    (
        DATA_FILE,
        [
            "trip_id",
            "date",
            "amount",
            "category",
            "description",
            "type",
            "liters",
            "current_km",
        ],
    ),
    (
        SETTINGS_FILE,
        [
            "trip_id",
            "car_trip",
            "track_fuel",
            "start_km",
            "end_km",
            "manual_fuel",
            "start_date",
            "end_date",
        ],
    ),
]:
  if not os.path.exists(f):
    pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")


def get_trip_data(t_id):
  try:
    df = pd.read_csv(DATA_FILE, encoding="utf-8")
    r = df[df["trip_id"] == t_id].copy()
    if "liters" not in r.columns:
      r["liters"] = 0.0
    if "current_km" not in r.columns:
      r["current_km"] = 0.0
    return r
  except Exception:
    return pd.DataFrame(
        columns=[
            "trip_id",
            "date",
            "amount",
            "category",
            "description",
            "type",
            "liters",
            "current_km",
        ]
    )


def get_trip_settings(t_id):
  d = {
      "car_trip": "Не",
      "track_fuel": "Добави впоследствие",
      "start_km": 0.0,
      "end_km": 0.0,
      "manual_fuel": 0.0,
      "start_date": "",
      "end_date": "",
  }
  try:
    df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
    f = df[df["trip_id"] == t_id]
    if not f.empty:
      res = f.iloc[0].to_dict()
      return {
          "trip_id": t_id,
          "car_trip": str(res.get("car_trip", "Не")),
          "track_fuel": str(res.get("track_fuel", "Добави впоследствие")),
          "start_km": float(res.get("start_km", 0.0)),
          "end_km": float(res.get("end_km", 0.0)),
          "manual_fuel": float(res.get("manual_fuel", 0.0)),
          "start_date": str(res.get("start_date", "")),
          "end_date": str(res.get("end_date", "")),
      }
  except Exception:
    pass
  return d


def save_trip_settings(
    t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""
):
  try:
    df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
    df = df[df["trip_id"] != t_id]
    new_row = pd.DataFrame([{
        "trip_id": t_id,
        "car_trip": str(c_t),
        "track_fuel": str(t_f),
        "start_km": float(s_k),
        "end_km": float(e_k),
        "manual_fuel": float(m_f),
        "start_date": str(s_d),
        "end_date": str(e_d),
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
  except Exception:
    pass


def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
  try:
    df = pd.read_csv(DATA_FILE, encoding="utf-8")
    if "current_km" not in df.columns:
      df["current_km"] = 0.0
    row = {
        "trip_id": t_id,
        "date": datetime.datetime.now().strftime("%d.%m %H:%M"),
        "amount": float(amt),
        "category": cat,
        "description": desc if desc else "Без описание",
        "type": "deposit" if is_dep else "expense",
        "liters": float(lit),
        "current_km": float(c_km),
    }
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(
        DATA_FILE, index=False, encoding="utf-8"
    )
    return True
  except Exception:
    return False


def get_map_points(t_id):
  try:
    df = pd.read_csv(MAP_FILE, encoding="utf-8")
    return df[df["trip_id"] == t_id].copy()
  except Exception:
    return pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"])


def add_map_point(t_id, lat, lon, title, color="blue"):
  try:
    df = pd.read_csv(MAP_FILE, encoding="utf-8")
    row = {
        "trip_id": t_id,
        "lat": float(lat),
        "lon": float(lon),
        "title": str(title),
        "color": str(color),
    }
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(
        MAP_FILE, index=False, encoding="utf-8"
    )
    return True
  except Exception:
    return False


# Инициализиране на сесийни променливи
if "current_trip" not in st.session_state:
  st.session_state["current_trip"] = None
if "form_version" not in st.session_state:
  st.session_state["form_version"] = 0
if "view_photos" not in st.session_state:
  st.session_state["view_photos"] = False

# 🏠 ЕКРАН 1: Главно меню (Когато няма избрано пътуване)
if st.session_state["current_trip"] is None:
  st.markdown(
      """<div style='text-align: center; margin-bottom: 5px;'>
        <h1 style='font-family: "Segoe UI", Roboto, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px;'>🐾 PixelApp</h1>
        <p style='font-family: "Segoe UI", Roboto, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; margin-top: 4px; margin-bottom: 30px;'>Travel Manager</p>
    </div>""",
      unsafe_allow_html=True,
  )

  existing = (
      list(pd.read_csv(DATA_FILE)["trip_id"].unique())
      if os.path.exists(DATA_FILE)
      else []
  )
  existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]

  if existing:
    opts = [t.replace("_", " ") for t in existing]
    choice = st.selectbox("Изберете пътуване до:", opts)
    if st.button("📂 ОТВОРИ ПЪТУВАНЕ", use_container_width=True):
      st.session_state["current_trip"] = choice.replace(" ", "_")
      st.rerun()
  else:
    st.markdown(
        "<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-bottom:15px;'>Все още нямате записани почивки. Създайте първото си приключение по-долу!</div>",
        unsafe_allow_html=True,
    )

  st.markdown(
      "<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>",
      unsafe_allow_html=True,
  )

  @st.dialog("➕ Създаване на ново приключение")
  def create_trip_modal():
    txt = st.text_input("Име на дестинацията:").strip()
    d_range = st.date_input(
        "Изберете дати за почивката:",
        value=[datetime.date.today(), datetime.date.today()],
    )
    st.write("---")
    st.write("🚗 Пътувате ли със собствен автомобил?")
    viber_car = st.radio(
        "Изберете вариант:",
        ["Не, с друг транспорт", "Да, със собствен автомобил"],
        index=0,
    )
    new_skm = 0.0
    if viber_car == "Да, със собствен автомобил":
      new_skm = st.number_input(
          "Начални километри (км):",
          value=None,
          placeholder="Въведете км на тръгване...",
          step=1.0,
      )

    if (
        st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True, type="primary")
        and txt
    ):
      if isinstance(d_range, (list, tuple)):
        s_d_str = (
            d_range[0].strftime("%d.%m.%Y") if len(d_range) > 0 else ""
        )
        e_d_str = (
            d_range[-1].strftime("%d.%m.%Y")
            if len(d_range) > 1
            else s_d_str
        )
      elif hasattr(d_range, "strftime"):
        s_d_str = d_range.strftime("%d.%m.%Y")
        e_d_str = s_d_str
      else:
        s_d_str, e_d_str = "", ""

      sk = float(new_skm) if new_skm is not None else 0.0
      target_id = txt.replace(" ", "_")
      save_trip_settings(
          target_id,
          "Да" if viber_car == "Да, със собствен автомобил" else "Не",
          (
              "Да"
              if viber_car == "Да, със собствен автомобил"
              else "Добави впоследствие"
          ),
          sk,
          0.0,
          0.0,
          s_d_str,
          e_d_str,
      )

      try:
        geolocator = Nominatim(user_agent="pixelapp_travel_manager_2026")
        location = geolocator.geocode(f"{txt}, Europe", language="bg,en")
        if location:
          add_map_point(
              target_id,
              location.latitude,
              location.longitude,
              f"🏁 Център: {txt}",
              "red",
          )
      except Exception:
        pass

      st.session_state["current_trip"] = target_id
      st.rerun()

  if st.button("➕ Ново пътуване", use_container_width=True):
    create_trip_modal()

# 🌴 ЕКРАН 2: Контролен панел на избраното пътуване
else:
  trip_id = st.session_state["current_trip"]
  papka_snimki = f"snimki_{trip_id}_2026"
  c_s = get_trip_settings(trip_id)

  car_trip, t_fuel, s_km, e_km, m_fuel = (
      str(c_s["car_trip"]),
      str(c_s["track_fuel"]),
      float(c_s["start_km"]),
      float(c_s["end_km"]),
      float(c_s["manual_fuel"]),
  )
  st_date, en_date = str(c_s.get("start_date", "")), str(
      c_s.get("end_date", "")
  )

  @st.dialog("🗑️ Потвърждение за изтриване")
  def confirm_delete_dialog():
    if (
        "delete_idx" in st.session_state
        and st.session_state["delete_idx"] is not None
    ):
      st.write("Сигурни ли сте, че искате да изтриете този разход?")
      idx = st.session_state["delete_idx"]
      try:
        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
        r = df_all.loc[idx]
        st.markdown(
            f"{get_emoji(r['category'])} {r['category']} — {r['amount']:.2f}"
            f" EUR\n{r['description']}",
            unsafe_allow_html=True,
        )
      except Exception:
        pass
      c_del1, c_del2 = st.columns(2)
      with c_del1:
        if st.button(
            "👍 ДА, ИЗТРИЙ", use_container_width=True, type="primary"
        ):
          try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8")
          except Exception:
            pass
          st.session_state["delete_idx"] = None
          st.rerun()
      with c_del2:
        if st.button("🛟 ОТКАЗ", use_container_width=True):
          st.session_state["delete_idx"] = None
          st.rerun()

  @st.dialog("🚨 Изтриване на цялото пътуване")
  def confirm_delete_trip_dialog():
    st.error(
        f"ВНИМАНИЕ! Изтриване на пътуването до {trip_id.replace('_', ' ')}?"
    )
    c_tr1, c_tr2 = st.columns(2)
    with c_tr1:
      if st.button(
          "💥 ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"
      ):
        try:
          pd.read_csv(DATA_FILE, encoding="utf-8")[
              lambda d: d["trip_id"] != trip_id
          ].to_csv(DATA_FILE, index=False, encoding="utf-8")
          pd.read_csv(SETTINGS_FILE, encoding="utf-8")[
              lambda d: d["trip_id"] != trip_id
          ].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
          if os.path.exists(papka_snimki):
            for p in glob.glob(os.path.join(papka_snimki, "*")):
              os.remove(p)
            os.rmdir(papka_snimki)
        except Exception:
          pass
        st.session_state["current_trip"] = None
        st.rerun()
    with c_tr2:
      if st.button("🛟 ОТКАЗ", use_container_width=True):
        st.rerun()

  # Изчисляване на глобални бюджети
  df_trip = get_trip_data(trip_id)
  depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
  df_expenses = df_trip[df_trip["type"] == "expense"]
  total_on_site = float(df_expenses["amount"].sum())
  categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
  total_liters_sum, auto_fuel_money = 0.0, 0.0

  for _, row in df_expenses.iterrows():
    if row["category"] in categories_totals:
      categories_totals[row["category"]] += float(row["amount"])
    if row["category"] == "Транспорт":
      if float(row.get("liters", 0)) > 0:
        total_liters_sum += float(row["liters"])
        auto_fuel_money += float(row["amount"])
      elif any(
          k in str(row["description"]).lower()
          for k in ["гориво", "зареждане", "бензин", "дизел"]
      ):
        auto_fuel_money += float(row["amount"])

  total_liters_calculated = total_liters_sum + m_fuel
  max_current_km = (
      float(df_expenses["current_km"].max())
      if not df_expenses.empty and "current_km" in df_expenses.columns
      else 0.0
  )
  eff_end_km = e_km if e_km > 0 else max_current_km
  dist = eff_end_km - s_km if eff_end_km > s_km else 0.0
  progressive_avg_con, has_progressive_data = 0.0, False

  try:
    df_trans_fuel = df_expenses[
        (df_expenses["category"] == "Транспорт")
        & (df_expenses["current_km"] > s_km)
    ].sort_index()
    if not df_trans_fuel.empty:
      progressive_dist = float(df_trans_fuel.iloc[-1]["current_km"]) - s_km
      progressive_liters = float(df_trans_fuel["liters"].sum()) + m_fuel
      if progressive_dist > 0 and progressive_liters > 0:
        progressive_avg_con = (
            progressive_liters / progressive_dist * 100
        )
        has_progressive_data = True
  except Exception:
    pass

  # 🖼️ ПОД-ЕКРАН: Галерия със снимки
  if st.session_state["view_photos"]:
    if st.button("⬅️ НАЗАД КЪМ РАЗХОДИТЕ", use_container_width=True):
      st.session_state["view_photos"] = False
      st.rerun()

    if not os.path.exists(papka_snimki):
      os.makedirs(papka_snimki)

    up = st.file_uploader(
        "Добавете нови спомени в албума:",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"u_{trip_id}",
    )
    if up:
      for f in up:
        if not os.path.exists(os.path.join(papka_snimki, f.name)):
          with open(os.path.join(papka_snimki, f.name), "wb") as out:
            out.write(f.getbuffer())
      st.rerun()

    saved = glob.glob(os.path.join(papka_snimki, "*"))
    if saved:
      img_grid = st.columns(2)
      for idx, p in enumerate(saved):
        with img_grid[idx % 2]:
          st.image(p, use_container_width=True)
          if st.button(
              "🗑️ Изтрий", key=f"di_{idx}", use_container_width=True
          ):
            os.remove(p)
            st.rerun()
    else:
      st.info("Все още няма качени снимки.")

  # 💰 ПОД-ЕКРАН: Главно оперативно табло с разходи
  else:
    date_html = (
        f" ({st_date} - {en_date})" if st_date and st_date != "nan" else ""
    )
    st.title(f"🌴 {trip_id.replace('_', ' ')}{date_html}")
    st.markdown("---")

    if st.button("⬅️ НАЗАД КЪМ ИЗБОР НА ПОЧИВКА", use_container_width=True):
      st.session_state["current_trip"] = None
      st.rerun()

    v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1:
      s_input = st.number_input(
          "СУМА (EUR)",
          value=None,
          placeholder="Напишете сума...",
          format="%.2f",
          key=f"su_{v_id}",
      )
    with col2:
      o_input = st.text_input(
          "Описание",
          placeholder="Напишете описание...",
          key=f"op_{v_id}",
      )

    is_trip_finished = e_km > 0.0

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description, is_dep):
      if is_trip_finished:
        st.error("🔒 Пътуването е приключено!")
        return
      liters = st.number_input(
          "Литри:", value=None, placeholder="Напишете литри...", step=0.1
      )
      fuel_type = st.radio(
          "Тип на зареждането:",
          [
              "Да, до горе (Пълен резервоар)",
              "Не, частично (за конкретна сума)",
          ],
          index=0,
      )

      df_f = get_trip_data(trip_id)[
          lambda d: (d["category"] == "Транспорт") & (d["current_km"] > 0)
      ]
      last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
      km_input = st.number_input(
          "Текущи километри на таблото (км):",
          value=None,
          placeholder="Въведете км...",
          step=1.0,
      )

      if liters and km_input and km_input > last_km and "до горе" in fuel_type.lower():
        st.success(
            f"📊 Етапен разход: {(liters / (km_input - last_km) * 100):.1f} л /"
            " 100 км"
        )

      if st.button(
          "💾 Запиши зареждането", use_container_width=True, type="primary"
      ):
        lit = float(liters) if liters is not None else 0.0
        ckm = float(km_input) if km_input is not None else 0.0
        is_full = "ПЪЛЕН" if "до горе" in fuel_type.lower() else "ЧАСТИЧЕН"
        full_desc = f"[{is_full} ГОРИВО] {description}"
        if ckm > last_km and lit > 0 and is_full == "ПЪЛЕН":
          full_desc += (
              f" (Етап: {(ckm - last_km):.0f}км, Разход:"
              f" {(lit / (ckm - last_km) * 100):.1f}л/100км)"
          )
        if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm):
          st.session_state["form_version"] += 1
          st.rerun()

    # Решетка с бутони за категории
    grid = st.columns(3)
    for i, kat in enumerate(KATEGORII):
      with grid[i % 3]:
        is_disabled = is_trip_finished and (kat == "Транспорт")
        if st.button(
            f"🔒 {kat}" if is_disabled else kat,
            use_container_width=True,
            key=f"bt_{i}",
            disabled=is_disabled,
        ):
          if s_input and s_input > 0:
            desc = o_input.strip() if o_input else "Без описание"
            is_d = kat == "Депозит/Резервация"
            if kat == "Транспорт" and any(
                k in desc.lower()
                for k in ["гориво", "зареждане", "бензин", "дизел"]
            ):
              fuel_modal(s_input, kat, desc, is_d)
            else:
              if add_expense(trip_id, s_input, kat, desc, is_d):
                st.session_state["form_version"] += 1
                st.rerun()

    # 📊 СЕКЦИЯ: Анализ на разходите по категории
    st.markdown("### 📊 Анализ на разходите")
    stat_grid = st.columns(2)
    for idx, (kat, s_value) in enumerate(categories_totals.items()):
      with stat_grid[idx % 2]:
        st.metric(label=f"{get_emoji(kat)} {kat}", value=f"{s_value:.2f} EUR")

    # 🚗 СЕКЦИЯ: Автомобилно табло
    if car_trip == "Да":
      val_to_show, is_final_status = 0.0, False
      try:
        df_fuel = df_expenses[
            (df_expenses["category"] == "Транспорт")
            & (df_expenses["current_km"] >= s_km)
        ].sort_values(by="current_km")
        total_valid_liters, total_valid_dist, prev_km, temp_liters = (
            0.0,
            0.0,
            s_km,
            0.0,
        )

        for _, row in df_fuel.iterrows():
          current_entry_km = float(row["current_km"])
          if current_entry_km == s_km:
            continue
          stage_dist = current_entry_km - prev_km
          if stage_dist > 0:
            temp_liters += float(row.get("liters", 0.0))
            if "ПЪЛЕН" in str(row["description"]).upper():
              total_valid_dist += stage_dist
              total_valid_liters += temp_liters
              temp_liters, prev_km = 0.0, current_entry_km

        total_valid_liters += m_fuel
        if total_valid_dist > 0 and total_valid_liters > 0:
          val_to_show = (total_valid_liters / total_valid_dist) * 100

        if e_km > s_km:
          is_final_status = True
          if val_to_show == 0.0 and total_liters_calculated > 0:
            val_to_show = (total_liters_calculated / dist) * 100
      except Exception:
        pass

      st.markdown("---")
      st.subheader("📍 Следене на пробега")
      m1, m2, m3 = st.columns(3)
      m1.metric("Старт", f"{s_km:.0f} км")
      m2.metric("Изминати", f"{dist:.0f} км")
      m3.metric(
          "Крайни" if is_trip_finished else "Текущи",
          f"{eff_end_km:.0f} км" if eff_end_km > 0 else "—",
      )

      st.metric(
          label="СРЕДЕН РАЗХОД",
          value=f"{val_to_show:.1f} л/100км",
          delta="Финални данни" if is_final_status else "Затворени етапи",
      )

    @st.dialog("⚙️ Настройки на превозно средство и период")
    def edit_car_modal():
      v_car = st.radio(
          "Автомобил ли използвате?",
          ["Не", "Да"],
          index=0 if car_trip == "Не" else 1,
          disabled=is_trip_finished,
      )
      new_sk = st.number_input(
          "Начални км:",
          value=None if s_km == 0.0 else s_km,
          disabled=is_trip_finished,
      )
      new_mf = st.number_input(
          "Добави пропуснато гориво (л):",
          value=None if m_fuel == 0.0 else m_fuel,
          disabled=is_trip_finished,
      )
      has_cash_expense = (
          st.checkbox("💵 Има ли финансов разход за добавеното гориво?")
          if (new_mf and new_mf > 0 and not is_trip_finished)
          else False
      )
      manual_cash_amt = (
          st.number_input(
              "Въведете платена сума (EUR):", value=None, format="%.2f"
          )
          if has_cash_expense
          else 0.0
      )

      try:
        current_start = (
            datetime.datetime.strptime(st_date, "%d.%m.%Y").date()
            if st_date and st_date != "nan"
            else datetime.date.today()
        )
        current_end = (
            datetime.datetime.strptime(en_date, "%d.%m.%Y").date()
            if en_date and en_date != "nan"
            else datetime.date.today() + datetime.timedelta(days=5)
        )
      except Exception:
        current_start, current_end = (
            datetime.date.today(),
            datetime.date.today() + datetime.timedelta(days=5),
        )

      edit_range = st.date_input(
          "Изберете нови дати:",
          value=[current_start, current_end],
          key="edit_dates_cal",
      )

      if st.button(
          "💾 Обнови",
          use_container_width=True,
          type="primary",
          disabled=is_trip_finished,
      ):
        sk_val = float(new_sk) if new_sk is not None else 0.0
        mf_val = float(new_mf) if new_mf is not None else 0.0
        s_d_str = (
            edit_range.strftime("%d.%m.%Y")
            if (isinstance(edit_range, (list, tuple)) and len(edit_range) > 0)
            else st_date
        )
        e_d_str = (
            edit_range.strftime("%d.%m.%Y")
            if (isinstance(edit_range, (list, tuple)) and len(edit_range) > 1)
            else s_d_str
        )

        if has_cash_expense and manual_cash_amt and manual_cash_amt > 0:
          add_expense(
              trip_id,
              manual_cash_amt,
              "Транспорт",
              f"[ПРОПУСНАТО ГОРИВО] Добавени {mf_val:.1f} литра",
              False,
              0.0,
              0.0,
          )

        save_trip_settings(
            trip_id,
            str(v_car),
            "Да",
            sk_val,
            e_km,
            mf_val,
            s_d_str,
            e_d_str,
        )
        st.session_state["form_version"] += 1
        st.rerun()

    @st.dialog("🏁 Край на пътуването")
    def finish_trip_modal():
      end_km_input = st.number_input(
          "Финални километри от таблото (км):",
          value=None if e_km == 0.0 else e_km,
          step=1.0,
      )
      if st.button(
          "🔒 ЗАКЛЮЧИ И ПРИКЛЮЧИ", use_container_width=True, type="primary"
      ):
        if end_km_input and end_km_input > s_km:
          save_trip_settings(
              trip_id,
              car_trip,
              t_fuel,
              s_km,
              float(end_km_input),
              m_fuel,
              st_date,
              en_date,
          )
          st.session_state["form_version"] += 1
          st.rerun()
        else:
          st.error(f"Трябва да са над {s_km:.0f} км!")

    # Бутони за управление на автомобилния модул
    if car_trip == "Да":
      col_manage1, col_manage2 = st.columns(2)
      with col_manage1:
        st.button(
            "🔒 Заключени настройки"
            if is_trip_finished
            else "⚙️ Настройки кола",
            use_container_width=True,
            disabled=is_trip_finished,
            on_click=edit_car_modal,
        )
      with col_manage2:
        st.button(
            "🏁 Пътуването е приключено 🔒"
            if is_trip_finished
            else "🏁 Край на пътуването",
            use_container_width=True,
            disabled=is_trip_finished,
            on_click=finish_trip_modal,
        )
    else:
      if st.button(
          "🚗 Добави автомобил към пътуването", use_container_width=True
      ):
        edit_car_modal()

    # Показване на Основни финансови стълбове
    st.markdown("---")
    col_st1, col_st2 = st.columns(2)
    with col_st1:
      st.metric("🏨 ДЕПОЗИТ", f"{depozit_hotel:.2f} EUR")
    with col_st2:
      st.metric("💰 НА МЯСТО", f"{total_on_site:.2f} EUR")

    # 📋 СЕКЦИЯ: Хронология на плащанията
    if not df_trip.empty:
      st.markdown("---")
      st.subheader("📋 Хронология на плащанията")
      try:
        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
        for idx in reversed(
            df_all[df_all["trip_id"] == trip_id].index.tolist()
        ):
          r = df_all.loc[idx]
          l_txt = (
              f" | ⛽ {r['liters']:.1f} л"
              if float(r.get("liters", 0)) > 0
              else ""
          )
          col_rec, col_del = st.columns([0.88, 0.12])
          with col_rec:
            st.markdown(
                f"**{get_emoji(r['category'])} {r['category']}** —"
                f" `{r['amount']:.2f} EUR`\n"
                f"<small>📅 {r['date']} — {r['description']}{l_txt}</small>",
                unsafe_allow_html=True,
            )
          with col_del:
            if st.button("❌", key=f"dl_{idx}", use_container_width=True):
              st.session_state["delete_idx"] = idx
              confirm_delete_dialog()
      except Exception:
        pass

    # Превключвател за влизане в албума
    st.markdown("---")
    st.button(
        "📸 Снимки и спомени",
        use_container_width=True,
        on_click=lambda: st.session_state.update({"view_photos": True}),
    )
    st.markdown("---")

    # 📄 СЕКЦИЯ: Експорт на пълен цифров отчет (HTML)
    avg_con_txt = (
        f"{(total_liters_calculated / dist * 100):.1f} л / 100 км"
        if dist > 0
        else (
            f"{progressive_avg_con:.1f} л / 100 км"
            if has_progressive_data
            else "Няма данни"
        )
    )
    grand_total = depozit_hotel + total_on_site

    pdf_html = f"""
    <html>
    <head><meta charset="utf-8">
    <style>
        body{{font-family:sans-serif;padding:30px;color:#333;}}
        h2{{color:#222;border-bottom:2px solid #00f2fe;padding-bottom:8px;}}
        table{{width:100%;border-collapse:collapse;margin-top:15px;}}
        th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd;}}
        th{{background:#f5f5f5;}}
    </style>
    </head>
    <body>
        <h2>ОТЧЕТ: {trip_id.upper().replace('_', ' ')}</h2>
        <p><b>Депозит:</b> {depozit_hotel:.2f} EUR | <b>На място:</b> {total_on_site:.2f} EUR</p>
        <p><b>ОБЩА СУМА:</b> {grand_total:.2f} EUR</p>
        <hr>
        <h3>🚗 Транспорт</h3>
        <p>Начални: {s_km:.0f} км | Крайни: {eff_end_km:.0f} км | Гориво: {total_liters_calculated:.1f} л</p>
        <p>Среден разход: {avg_con_txt}</p>
        <hr>
        <h3>📋 Подробни разходи</h3>
        <table>
            <tr><th>Дата</th><th>Описание</th><th>Километраж</th><th>Сума</th><th>Категория</th></tr>
    """
    for _, row in df_trip.iterrows():
      cur_km_val = float(row.get("current_km", 0.0))
      km_td_html = f"{cur_km_val:.0f} км" if cur_km_val > 0 else "—"
      pdf_html += f"<tr><td>{row['date']}</td><td>{row['description']}</td><td>{km_td_html}</td><td>{row['amount']:.2f} EUR</td><td>{row['category']}</td></tr>"

    pdf_html += f"</table><h3>Общо: {grand_total:.2f} EUR</h3></body></html>"

    b64_html_data = base64.b64encode(pdf_html.encode("utf-8")).decode("utf-8")
    st.markdown(
        f'<a href="data:text/html;base64,{b64_html_data}"'
        f' download="Отчет_{trip_id}.html" style="display:block; text-align:center;'
        " background:#2e2e2e; color:white; padding:10px; border-radius:10px;"
        ' text-decoration:none; font-weight:bold;">📄 СВАЛИ ПЪЛЕН ОТЧЕТ'
        " (HTML)</a>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 🗺️ СЕКЦИЯ: Интерактивна карта с пинчета (Folium)
    st.subheader("🗺️ Карта на спирките и дестинациите")
    df_points = get_map_points(trip_id)
    c_lat, c_lon = (
        (df_points["lat"].mean(), df_points["lon"].mean())
        if not df_points.empty
        else (42.7339, 25.4858)
    )

    m = folium.Map(location=[c_lat, c_lon], zoom_start=6)
    folium.LatLngPopup().add_to(m)

    for _, pt in df_points.iterrows():
      folium.Marker(
          location=[pt["lat"], pt["lon"]],
          popup=pt["title"],
          icon=folium.Icon(color=pt["color"], icon="info-sign"),
      ).add_to(m)

    map_data = st_folium(m, width=700, height=400, key=f"map_{trip_id}")

    if map_data and map_data.get("last_clicked"):
      st.session_state["active_click"] = map_data["last_clicked"]

    if (
        "active_click" in st.session_state
        and st.session_state["active_click"] is not None
        and not is_trip_finished
    ):
      click_coords = st.session_state["active_click"]
      st.info(
          f"📌 Избрано място: {click_coords['lat']:.4f},"
          f" {click_coords['lng']:.4f}"
      )
      c_m1, c_m2 = st.columns([0.7, 0.3])
      with c_m1:
        title_in = st.text_input(
            "Име на новата спирка:",
            placeholder="напр. Хотел...",
            key="map_title_click",
        )
      with c_m2:
        color_in = st.selectbox(
            "Цвят:",
            ["blue", "green", "red", "purple", "orange"],
            key="map_color_click",
        )

      cb1, cb2 = st.columns([0.7, 0.3])
      with cb1:
        if (
            st.button(
                "💾 ЗАПИШИ ПИНЧЕТО", use_container_width=True, type="primary"
            )
            and title_in
        ):
          if add_map_point(
              trip_id,
              click_coords["lat"],
              click_coords["lng"],
              title_in,
              color_in,
          ):
            st.session_state["active_click"] = None
            st.rerun()
      with cb2:
        if st.button("❌ Отказ", use_container_width=True):
          st.session_state["active_click"] = None
          st.rerun()

    # Списък и триене на запазени географски локации
    if not df_points.empty:
      st.markdown("#### 📍 Списък на запазените локации")
      try:
        df_all_map = pd.read_csv(MAP_FILE, encoding="utf-8")
        color_emojis = {
            "blue": "🔵",
            "green": "🟢",
            "red": "🔴",
            "purple": "🟣",
            "orange": "🟠",
        }
        for idx in df_all_map[df_all_map["trip_id"] == trip_id].index.tolist():
          pt_row = df_all_map.loc[idx]
          col_p_txt, col_p_del = st.columns([0.85, 0.15])
          with col_p_txt:
            st.write(
                f"{color_emojis.get(pt_row['color'], '🔵')} **{pt_row['title']}**"
                f" ({pt_row['lat']:.4f}, {pt_row['lon']:.4f})"
            )
          with col_p_del:
            if st.button(
                "🗑️",
                key=f"del_pin_{idx}",
                use_container_width=True,
                disabled=is_trip_finished,
            ):
              df_all_map.drop(idx).to_csv(
                  MAP_FILE, index=False, encoding="utf-8"
              )
              st.rerun()
      except Exception:
        pass

    st.markdown("---")
    if st.button(
        "❌ Изтрий цялото пътуване",
        type="primary",
        use_container_width=True,
        key="delete_whole_trip_final_btn",
    ):
      confirm_delete_trip_dialog()
