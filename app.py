import base64
import datetime
import glob
import os
import folium
from geopy.geocoders import Nominatim
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# 1. Конфигурация на страницата
st.set_page_config(
    page_title="PixelApp - Travel Manager",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 2. Модерен Glassmorphism CSS UI Стилов модул (само визия, без да засяга логиката)
MODERN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #0f172a !important;
        color: #f8fafc !important;
    }

    #MainMenu, footer, header {visibility: hidden;}

    /* Модернизационен слой за въвеждащи полета */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* Бутони - Премиум неонов градиент */
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"],
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39) !important;
        transition: all 0.25s ease !important;
        width: 100% !important;
    }

    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(37, 99, 235, 0.55) !important;
    }

    /* Стилизиране на диалози и подпрозорци */
    div[role="dialog"] {
        background: #0f172a !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
    }

    /* Таблици */
    div[data-testid="stDataFrame"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
</style>
"""
st.markdown(MODERN_CSS, unsafe_allow_html=True)

# 3. Константи и файлова система
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


# 4. Вспомагателни функции
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


def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame(
            [
                {
                    "trip_id": t_id,
                    "car_trip": str(c_t),
                    "track_fuel": str(t_f),
                    "start_km": float(s_k),
                    "end_km": float(e_k),
                    "manual_fuel": float(m_f),
                    "start_date": str(s_d),
                    "end_date": str(e_d),
                }
            ]
        )
        pd.concat([df, new_row], ignore_index=True).to_csv(
            SETTINGS_FILE, index=False, encoding="utf-8"
        )
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


def delete_expense(t_id, idx):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        df_trip = df[df["trip_id"] == t_id]
        if idx in df_trip.index:
            df = df.drop(idx)
            df.to_csv(DATA_FILE, index=False, encoding="utf-8")
            return True
    except Exception:
        pass
    return False


def get_map_points(t_id):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        return df[df["trip_id"] == t_id].copy()
    except Exception:
        return pd.DataFrame(
            columns=["trip_id", "lat", "lon", "title", "color"]
        )


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


def delete_map_point(t_id, idx):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        df_trip = df[df["trip_id"] == t_id]
        if idx in df_trip.index:
            df = df.drop(idx)
            df.to_csv(MAP_FILE, index=False, encoding="utf-8")
            return True
    except Exception:
        pass
    return False


# Инициализация на Session State
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = None
if "form_version" not in st.session_state:
    st.session_state["form_version"] = 0
if "view_photos" not in st.session_state:
    st.session_state["view_photos"] = False

# ==================== ЧАСТ 1: НАЧАЛЕН ЕКРАН ====================
if st.session_state["current_trip"] is None:
    st.markdown(
        "<h1 style='text-align: center;'>🐾 PixelApp</h1>",
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
        choice = st.selectbox("Изберете вашето пътуване:", opts)
        if st.button("📂 ОТВОРИ ПЪТУВАНЕТО", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.rerun()

    st.markdown("---")

    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:").strip()
        d_range = st.date_input(
            "Дати на престоя:",
            value=[datetime.date.today(), datetime.date.today()],
        )
        st.write("---")
        viber_car = st.radio(
            "Транспорт:",
            ["Не, с друг транспорт", "Да, със собствен автомобил"],
            index=0,
        )
        new_skm = 0.0
        if viber_car == "Да, със собствен автомобил":
            new_skm = st.number_input(
                "Начални километри (км):",
                value=None,
                placeholder="км на тръгване...",
                step=1.0,
            )

        if (
            st.button(
                "🚀 СЪЗДАЙ И ОТВОРИ",
                use_container_width=True,
                type="primary",
            )
            and txt
        ):
            if isinstance(d_range, (list, tuple)):
                s_d_str = (
                    d_range[0].strftime("%d.%m.%Y")
                    if len(d_range) > 0
                    else ""
                )
                e_d_str = (
                    d_range[-1].strftime("%d.%m.%Y")
                    if len(d_range) > 1
                    else s_d_str
                )
            else:
                s_d_str = e_d_str = (
                    d_range.strftime("%d.%m.%Y")
                    if hasattr(d_range, "strftime")
                    else ""
                )

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
                geolocator = Nominatim(
                    user_agent="pixelapp_travel_manager_2026"
                )
                location = geolocator.geocode(
                    f"{txt}, Europe", language="bg,en"
                )
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

# ==================== ЧАСТ 2: УПРАВЛЕНИЕ НА ПЪТУВАНЕТО ====================
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

    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(
        df_trip[df_trip["type"] == "deposit"]["amount"].sum()
    )
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

    st.markdown(
        f"<h2 style='text-align: center;'>🌴 {trip_id.replace('_', ' ')}</h2>",
        unsafe_allow_html=True,
    )
    if st_date and st_date != "nan":
        st.markdown(
            f"<p style='text-align: center; color: #38bdf8;'>📅 {st_date} - {en_date}</p>",
            unsafe_allow_html=True,
        )

    if st.button("⬅️ Назад към избор на почивка", use_container_width=True):
        st.session_state["current_trip"] = None
        st.rerun()

    st.write("---")

    # Форма за добавяне
    v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1:
        s_input = st.number_input(
            "СУМА (EUR)",
            value=None,
            placeholder="0.00",
            format="%.2f",
            key=f"su_{v_id}",
        )
    with col2:
        o_input = st.text_input(
            "Описание", placeholder="За какво беше...", key=f"op_{v_id}"
        )

    is_trip_finished = e_km > 0.0

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description, is_dep):
        if is_trip_finished:
            st.error("🔒 Пътуването е приключено!")
            return
        liters = st.number_input(
            "Литри:", value=None, placeholder="0.0", step=0.1
        )
        fuel_type = st.radio(
            "Тип зареждане:",
            ["Да, до горе (Пълен резервоар)", "Не, частично"],
            index=0,
        )
        df_f = get_trip_data(trip_id)[
            lambda d: (d["category"] == "Транспорт") & (d["current_km"] > 0)
        ]
        last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
        km_input = st.number_input(
            "Километри на таблото:",
            value=None,
            placeholder="км...",
            step=1.0,
        )

        if (
            liters
            and km_input
            and km_input > last_km
            and "до горе" in fuel_type.lower()
        ):
            st.info(
                f"📊 Етапен разход: **{(liters / (km_input - last_km) * 100):.1f} л / 100 км**"
            )

        if st.button(
            "💾 Запиши зареждането", use_container_width=True, type="primary"
        ):
            lit, ckm = (float(liters) if liters else 0.0), (
                float(km_input) if km_input else 0.0
            )
            is_full = (
                "ПЪЛЕН" if "до горе" in fuel_type.lower() else "ЧАСТИЧЕН"
            )
            full_desc = f"[{is_full} ГОРИВО] {description}"
            if ckm > last_km and lit > 0 and is_full == "ПЪЛЕН":
                full_desc += f" (Етап: {(ckm - last_km):.0f}км, Разход: {(lit / (ckm - last_km) * 100):.1f}л/100км)"
            if add_expense(
                trip_id, amount, category, full_desc, is_dep, lit, ckm
            ):
                st.session_state["form_version"] += 1
                st.rerun()

    # Бутони по категории
    grid = st.columns(3)
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            is_disabled = is_trip_finished and (kat == "Транспорт")
            label = f"{get_emoji(kat)} {kat}"
            if st.button(
                label,
                use_container_width=True,
                key=f"bt_{i}",
                disabled=is_disabled,
            ):
                if s_input and s_input > 0:
                    desc, is_d = (
                        o_input.strip() if o_input else "Без описание"
                    ), (kat == "Депозит/Резервация")
                    if kat == "Транспорт" and any(
                        k in desc.lower()
                        for k in ["гориво", "зареждане", "бензин", "дизел"]
                    ):
                        fuel_modal(s_input, kat, desc, is_d)
                    else:
                        if add_expense(trip_id, s_input, kat, desc, is_d):
                            st.session_state["form_version"] += 1
                            st.rerun()

    st.write("---")

    # Показване на статистики
    st.subheader("📊 Общ преглед")
    st.write(f"🏨 **Депозит / Хотел:** {depozit_hotel:.2f} EUR")
    st.write(f"💰 **Разходи на място:** {total_on_site:.2f} EUR")

    st.write("---")
    st.subheader("📋 Разходи по категории")
    for kat, s_value in categories_totals.items():
        st.write(f"{get_emoji(kat)} **{kat}:** {s_value:.2f} EUR")

    if car_trip == "Да":
        st.write("---")
        st.subheader("🚗 Автомобил и Гориво")
        st.write(f"📏 Начални км: **{s_km:.0f} км**")
        st.write(f"🛣 Изминати км: **{dist:.0f} км**")

    # Секция "История на разходите"
    st.write("---")
    st.subheader("📜 История на разходите")
    if not df_trip.empty:
        for idx, row in df_trip.iterrows():
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.write(
                    f"**{get_emoji(row['category'])} {row['category']}** ({row['date']})"
                )
                st.caption(f"{row['description']}")
            with c2:
                st.write(f"**{row['amount']:.2f} EUR**")
            with c3:
                if st.button("🗑️", key=f"del_{idx}"):
                    delete_expense(trip_id, idx)
                    st.rerun()

    # Секция "Интерактивна карта"
    st.write("---")
    st.subheader("🗺️ Карта на забележителностите")

    @st.dialog("📍 Добави точка на картата")
    def add_point_modal():
        p_name = st.text_input("Име на мястото:")
        p_color = st.selectbox(
            "Цвят на маркера:", ["blue", "red", "green", "purple", "orange"]
        )
        p_lat = st.number_input("Географска ширина (Lat):", format="%.6f")
        p_lon = st.number_input("Географска дължина (Lon):", format="%.6f")

        if st.button("💾 Запиши точката", type="primary") and p_name:
            if add_map_point(trip_id, p_lat, p_lon, p_name, p_color):
                st.rerun()

    if st.button("📍 Добави място на картата"):
        add_point_modal()

    pts = get_map_points(trip_id)
    if not pts.empty:
        m = folium.Map(
            location=[pts.iloc[0]["lat"], pts.iloc[0]["lon"]], zoom_start=11
        )
        for idx, p in pts.iterrows():
            folium.Marker(
                [p["lat"], p["lon"]],
                popup=p["title"],
                icon=folium.Icon(color=p["color"]),
            ).add_to(m)
        st_folium(m, width=700, height=400)

        # Списък и триене на точки
        for idx, p in pts.iterrows():
            col_p1, col_p2 = st.columns([4, 1])
            with col_p1:
                st.write(f"📍 **{p['title']}** ({p['lat']:.4f}, {p['lon']:.4f})")
            with col_p2:
                if st.button("🗑️", key=f"del_map_{idx}"):
                    delete_map_point(trip_id, idx)
                    st.rerun()

    # Секция "Галерия със снимки"
    st.write("---")
    st.subheader("🖼️ Снимки и спомени")
    if not os.path.exists(papka_snimki):
        os.makedirs(papka_snimki)

    uploaded_files = st.file_uploader(
        "Прикачи снимки от пътуването:",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        for u_f in uploaded_files:
            f_path = os.path.join(papka_snimki, u_f.name)
            with open(f_path, "wb") as f:
                f.write(u_f.getbuffer())
        st.success("Снимките са качени успешно!")
        st.rerun()

    photos = glob.glob(f"{papka_snimki}/*")
    if photos:
        p_cols = st.columns(3)
        for i, photo_path in enumerate(photos):
            with p_cols[i % 3]:
                st.image(photo_path, use_container_width=True)
                if st.button("🗑️ Премахни", key=f"del_img_{i}"):
                    os.remove(photo_path)
                    st.rerun()
