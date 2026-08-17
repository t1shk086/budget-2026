import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #090b0e 0%, #11151c 50%, #0d1117 100%) !important;
        background-attachment: fixed !important;
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.15) !important;
        z-index: -1;
        pointer-events: none;
    }
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important; 
        padding: 10px 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        backdrop-filter: blur(4px) !important;
        margin-bottom: 15px !important;
    }
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"],
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #252932, #16191f) !important; 
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; 
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
        transition: all 0.25s ease !important; 
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        width: 100% !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFileUploaderDropzone"] button:hover {
        background: linear-gradient(135deg, #2e343f, #1c2028) !important;
        transform: translateY(-1px) !important; 
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.15) !important;
        border-color: rgba(0, 242, 254, 0.2) !important;
    }
    small { color: #7e8494 !important; }
</style>
""", unsafe_allow_html=True)
KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"

if not os.path.exists(MAP_FILE):
    pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(MAP_FILE, index=False, encoding="utf-8")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), 
                (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")
def get_trip_data(t_id):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        r = df[df["trip_id"] == t_id].copy()
        if "liters" not in r.columns: r["liters"] = 0.0
        if "current_km" not in r.columns: r["current_km"] = 0.0
        return r
    except: 
        return pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"])

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
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
                "end_date": str(res.get("end_date", ""))
            }
    except: 
        pass
    return d

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: 
        pass
def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "current_km" not in df.columns: df["current_km"] = 0.0
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: 
        return False

def get_map_points(t_id):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        return df[df["trip_id"] == t_id].copy()
    except: 
        return pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        row = {"trip_id": t_id, "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(MAP_FILE, index=False, encoding="utf-8")
        return True
    except: 
        return False
if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0
if "view_photos" not in st.session_state: st.session_state["view_photos"] = False

if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center; margin-bottom: 5px;'><h1 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 10px rgba(0, 242, 254, 0.2); margin-bottom: 0px;'>🐾 PixelApp</h1><p style='font-family: \"Segoe UI\", Roboto, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; margin-top: 4px; margin-bottom: 30px;'>Travel Manager</p></div>", unsafe_allow_html=True)
    
    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете дестинация за отваряне:", opts)
        if st.button("📂 ОТВОРИ ПЪТУВАНЕ", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_"); st.rerun()
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-bottom:15px;'>Все още нямате записани почивки. Създайте първото си приключение по-долу!</div>", unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>", unsafe_allow_html=True)
    
    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:").strip()
        d_range = st.date_input("Изберете дати за почивката:", value=[datetime.date.today(), datetime.date.today()])
        st.write("---"); st.write("🚗 Пътувате ли со собствен автомобил?")
        viber_car = st.radio("Изберете вариант:", ["Не, с друг транспорт", "Да, със собствен автомобил"], index=0)
        new_skm = 0.0
        if viber_car == "Да, със собствен автомобил":
            new_skm = st.number_input("Начални километри (км):", value=None, placeholder="Въведете км на тръгване...", step=1.0)
        if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True, type="primary") and txt:
            if isinstance(d_range, (list, tuple)):
                s_d_str = d_range[0].strftime("%d.%m.%Y") if len(d_range) > 0 else ""
                e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 else s_d_str
            elif hasattr(d_range, "strftime"): s_d_str = d_range.strftime("%d.%m.%Y"); e_d_str = s_d_str
            else: s_d_str, e_d_str = "", ""
            sk = float(new_skm) if new_skm is not None else 0.0
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, "Да" if viber_car == "Да, със собствен автомобил" else "Не", "Да" if viber_car == "Да, със собствен автомобил" else "Добави впоследствие", sk, 0.0, 0.0, s_d_str, e_d_str)
            try:
                geolocator = Nominatim(user_agent="pixelapp_travel_manager_2026")
                location = geolocator.geocode(f"{txt}, Europe", language="bg,en")
                if location: add_map_point(target_id, location.latitude, location.longitude, f"🏁 Център: {txt}", "red")
            except: pass
            st.session_state["current_trip"] = target_id; st.rerun()

    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
else:
    trip_id = st.session_state["current_trip"]
    papka_snimki = f"snimki_{trip_id}_2026"
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    @st.dialog("🗑️ Потвърждение за изтриване")
    def confirm_delete_dialog():
        if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
            idx = st.session_state["delete_idx"]
            try:
                df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                r = df_all.loc[idx]
                st.markdown(f"**{get_emoji(r['category'])} {r['category']}** — <span style='color:#ff4b4b; font-weight:bold;'>{r['amount']:.2f} EUR</span><br><small>{r['description']}</small>", unsafe_allow_html=True)
            except: pass
            c_del1, c_del2 = st.columns(2)
            with c_del1:
                if st.button("👍 ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                    try:
                        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                        df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8")
                    except: pass
                    st.session_state["delete_idx"] = None; st.rerun()
            with c_del2:
                if st.button("🛟 ОТКАЗ", use_container_width=True): st.session_state["delete_idx"] = None; st.rerun()

    @st.dialog("🚨 Изтриване на цялото пътуване")
    def confirm_delete_trip_dialog():
        st.error(f"ВНИМАНИЕ! Изтриване на почивката до {trip_id.replace('_', ' ')}?")
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            if st.button("💥 ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
                try:
                    pd.read_csv(DATA_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
                    pd.read_csv(SETTINGS_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
                    if os.path.exists(papka_snimki):
                        for p in glob.glob(os.path.join(papka_snimki, "*")): os.remove(p)
                        os.rmdir(papka_snimki)
                except: pass
                st.session_state["current_trip"] = None; st.rerun()
        with c_tr2:
            if st.button("🛟 ОТКАЗ", use_container_width=True): st.rerun()

    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    total_liters_sum, auto_fuel_money = 0.0, 0.0
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
        if row["category"] == "Транспорт":
            if float(row.get("liters", 0)) > 0: total_liters_sum += float(row["liters"]); auto_fuel_money += float(row["amount"])
            elif any(k in str(row["description"]).lower() for k in ["гориво", "зареждане", "бензин", "дизел"]): auto_fuel_money += float(row["amount"])
    
    total_liters_calculated = total_liters_sum + m_fuel
    max_current_km = float(df_expenses["current_km"].max()) if not df_expenses.empty and "current_km" in df_expenses.columns else 0.0
    eff_end_km = e_km if e_km > 0 else max_current_km
    dist = eff_end_km - s_km if eff_end_km > s_km else 0.0

    if st.session_state["view_photos"]:
        if st.button("⬅️ НАЗАД КЪМ РАЗХОДИТЕ", use_container_width=True): st.session_state["view_photos"] = False; st.rerun()
        if not os.path.exists(papka_snimki): os.makedirs(papka_snimki)
        up = st.file_uploader("Добавете снимки:", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if up:
            for f in up:
                if not os.path.exists(os.path.join(papka_snimki, f.name)):
                    with open(os.path.join(papka_snimki, f.name), "wb") as out: out.write(f.getbuffer())
            st.rerun()
        saved = glob.glob(os.path.join(papka_snimki, "*"))
        if saved:
            img_grid = st.columns(2)
            for idx, p in enumerate(saved):
                with img_grid[idx % 2]:
                    st.image(p, use_container_width=True)
                    if st.button("🗑️ Изтрий", key=f"di_{idx}", use_container_width=True): os.remove(p); st.rerun()
        else: st.markdown("<div style='text-align:center; color:#666;'>Няма снимки.</div>", unsafe_allow_html=True)
    else:
        date_html = f"<p style='font-size: 14px; color: #888;'>{st_date} - {en_date}</p>" if st_date and st_date != "nan" else ""
        st.markdown(f"<div style='text-align: center;'><h2 style='background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🌴 Дестинация: {trip_id.replace('_', ' ')}</h2>{date_html}</div>", unsafe_allow_html=True)
        st.markdown("---")

        if st.button("⬅️ НАЗАД КЪМ ИЗБОР НА ПОЧИВКА", use_container_width=True): st.session_state["current_trip"] = None; st.rerun()
        
        v_id = st.session_state["form_version"]
        col1, col2 = st.columns(2)
        with col1: s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Сума...", format="%.2f", key=f"su_{v_id}")
        with col2: o_input = st.text_input("Описание", placeholder="Описание...", key=f"op_{v_id}")
        is_trip_finished = (e_km > 0.0)

        @st.dialog("⛽ Зареждане на гориво")
        def fuel_modal(amount, category, description, is_dep):
            if is_trip_finished: st.error("🔒 Заключено!"); return
            liters = st.number_input("Литри:", value=None, step=0.1)
            fuel_type = st.radio("Тип:", ["Да, до горе (Пълен резервоар)", "Не, частично"], index=0)
            df_f = get_trip_data(trip_id)[lambda d: (d["category"] == "Транспорт") & (d["current_km"] > 0)]
            last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
            km_input = st.number_input("Текущи км:", value=None, step=1.0)
            if liters and km_input and km_input > last_km and "до горе" in fuel_type.lower():
                st.success(f"📊 Разход: **{(liters / (km_input - last_km) * 100):.1f} л/100 км**")
            if st.button("💾 Запиши гориво", use_container_width=True, type="primary"):
                lit, ckm = (float(liters) if liters is not None else 0.0), (float(km_input) if km_input is not None else 0.0)
                is_full = "ПЪЛЕН" if "до горе" in fuel_type.lower() else "ЧАСТИЧЕН"
                full_desc = f"[{is_full} ГОРИВО] {description}"
                if ckm > last_km and lit > 0 and is_full == "ПЪЛЕН": full_desc += f" (Етап: {(ckm - last_km):.0f}км, Разход: {(lit / (ckm - last_km) * 100):.1f}л/100км)"
                if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm): st.session_state["form_version"] += 1; st.rerun()

        @st.dialog("🎯 Изберете категория")
        def categories_popup_modal(amount, description):
            st.write("Категория на разхода:")
            grid = st.columns(3)
            for i, kat in enumerate(KATEGORII):
                with grid[i % 3]:
                    is_disabled = is_trip_finished and (kat == "Транспорт")
                    if st.button(f"🔒 {kat}" if is_disabled else kat, use_container_width=True, key=f"popup_bt_{i}", disabled=is_disabled):
                        is_d = (kat == "Депозит/Резервация")
                        if kat == "Транспорт" and any(k in description.lower() for k in ["гориво", "зареждане", "бензин", "дизел"]):
                            fuel_modal(amount, kat, description, is_d)
                        else:
                            if add_expense(trip_id, amount, kat, description, is_d):
                                st.session_state["form_version"] += 1; st.rerun()

        if s_input and s_input > 0 and o_input.strip():
            if st.button("🎯 ИЗБЕРИ КАТЕГОРИЯ И ЗАПИШИ", use_container_width=True, type="primary"):
                categories_popup_modal(s_input, o_input.strip())
        else:
            st.markdown("<div style='text-align:center; padding:12px; color:#555; background:rgba(255,255,255,0.01); border-radius:10px; font-size:13px;'>Въведете сума и описание, за да запишете...</div>", unsafe_allow_html=True)
        st.markdown("### 📊 Анализ на разходите")
        stat_grid = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            with stat_grid[idx % 2]:
                pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 14px; border-radius: 14px; margin-bottom: 12px; display: flex; flex-direction: column;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>{get_emoji(kat)} {kat}</span>
                        <span style="font-weight: bold; color: #ff4b4b;">{s_value:.2f} EUR</span>
                    </div>
                    <div style="background: rgba(0, 0, 0, 0.4); height: 16px; border-radius: 20px; padding: 2px; position: relative; display: flex; align-items: center; overflow: hidden; margin-top: 6px;">
                        <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); border-radius: 20px;"></div>
                        <span style="position: absolute; right: 8px; font-size: 10px; font-weight: 900; color: white;">{pct:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        if car_trip == "Да":
            val_to_show = 0.0
            try:
                df_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] >= s_km)].sort_values(by="current_km")
                total_valid_liters, total_valid_dist, prev_km, temp_liters = 0.0, 0.0, s_km, 0.0
                for _, row in df_fuel.iterrows():
                    current_entry_km = float(row["current_km"])
                    if current_entry_km == s_km: continue
                    stage_dist = current_entry_km - prev_km
                    if stage_dist > 0:
                        temp_liters += float(row.get("liters", 0.0))
                        if "ПЪЛЕН" in str(row["description"]).upper():
                            total_valid_dist += stage_dist; total_valid_liters += temp_liters
                            temp_liters, prev_km = 0.0, current_entry_km
                total_valid_liters += m_fuel
                if total_valid_dist > 0 and total_valid_liters > 0: val_to_show = (total_valid_liters / total_valid_dist) * 100
                if e_km > s_km and val_to_show == 0.0 and total_liters_calculated > 0: val_to_show = (total_liters_calculated / dist) * 100
            except: pass

            color_gauge = "#666" if val_to_show == 0.0 else "#00f2fe" if val_to_show <= 8.0 else "#ff4b4b"
            km_p_pct = 100 if is_trip_finished else min(100, max(0, (dist / 1000 * 100))) if dist > 0 else 0
            f_icon = f"<div style='position: absolute; right: 0; top: -8px; background: #1c1c1c; border: 2px solid #ff4b4b; width: 20px; height: 20px; border-radius: 50%; font-size: 9px; color: white; display:flex; align-items:center; justify-content:center;'>F</div>" if is_trip_finished else f"<div style='position: absolute; left: calc({km_p_pct}% - 10px); top: -12px; font-size: 16px;'>🚗</div>"

            st.markdown(f"<div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center;'><small>📍 ПРОБЕГ</small><div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 25px 15px 15px 15px;'><div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_p_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div>{f_icon}</div><div style='display: flex; justify-content: space-between; font-size: 13px;'><div style='text-align: left;'><small>Старт</small><br><b>{s_km:.0f} км</b></div><div style='text-align: center;'><small>Изминати</small><br><b style='color: #00f2fe;'>{dist:.0f} км</b></div><div style='text-align: right;'><small>Краен</small><br><b>{eff_end_km:.0f} км</b></div></div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 15px;'><div style='flex: 1; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; text-align: center; display: flex; flex-direction: column; align-items: center;'><small>СРЕДЕН РАЗХОД</small><div style='width: 90px; height: 90px; border-radius: 50%; border: 3px dashed {color_gauge}; display: flex; flex-direction: column; justify-content: center; align-items: center; margin: 10px 0;'><b>{val_to_show:.1f}</b><small style='font-size:9px;'>л/100км</small></div></div><div style='flex: 1; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px;'><small>💧 ОБЩО ГОРВO</small><h3>{(total_liters_calculated):.1f} л</h3><hr style='margin:8px 0; border-color:rgba(255,255,255,0.05);'><small>💰 СТОЙНОСТ</small><h3>{auto_fuel_money:.2f} EUR</h3></div></div>", unsafe_allow_html=True)
        @st.dialog("⚙️ Настройки превозно средство")
        def edit_car_modal():
            v_car = st.radio("Кола?", ["Не", "Да"], index=0 if car_trip == "Не" else 1, disabled=is_trip_finished)
            new_sk = st.number_input("Старт км:", value=None if s_km == 0.0 else s_km, disabled=is_trip_finished)
            new_mf = st.number_input("Пропуснато гориво (л):", value=None if m_fuel == 0.0 else m_fuel, disabled=is_trip_finished)
            if st.button("💾 Обнови", use_container_width=True, type="primary"):
                save_trip_settings(trip_id, str(v_car), "Да", float(new_sk) if new_sk else 0.0, e_km, float(new_mf) if new_mf else 0.0, st_date, en_date)
                st.session_state["form_version"] += 1; st.rerun()

        @st.dialog("🏁 Край на почивката")
        def finish_trip_modal():
            end_km_input = st.number_input("Финални км:", value=None if e_km == 0.0 else e_km, step=1.0)
            if st.button("🔒 ЗАКЛЮЧИ", use_container_width=True, type="primary"):
                if end_km_input and end_km_input > s_km: 
                    save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date)
                    st.session_state["form_version"] += 1; st.rerun()

        c_m1, c_m2 = st.columns(2)
        with c_m1: st.button("⚙️ Настройки кола", use_container_width=True, disabled=is_trip_finished, on_click=edit_car_modal)
        with c_m2: st.button("🏁 Край на пътуването", use_container_width=True, disabled=is_trip_finished, on_click=finish_trip_modal)

        st.markdown("---")
        cl_s1, cl_s2 = st.columns(2)
        with cl_s1: st.markdown(f"<div style='background:rgba(255,255,255,0.02); padding:12px; border-radius:12px; text-align:center;'><small>🏨 ДЕПОЗИТ</small><h3>{depozit_hotel:.2f} EUR</h3></div>", unsafe_allow_html=True)
        with cl_s2: st.markdown(f"<div style='background:rgba(255,255,255,0.02); padding:12px; border-radius:12px; text-align:center;'><small>💰 НА МЯСТО</small><h3>{total_on_site:.2f} EUR</h3></div>", unsafe_allow_html=True)

        if not df_trip.empty:
            st.markdown("---")
            try:
                df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                for idx in reversed(df_all[df_all["trip_id"] == trip_id].index.tolist()):
                    r = df_all.loc[idx]
                    col_rec, col_del = st.columns([0.88, 0.12])
                    with col_rec: st.markdown(f'<div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.05); font-size:13px;">{get_emoji(r["category"])} <b>{r["category"]}</b> — <span style="color:#ff4b4b;">{r["amount"]:.2f} EUR</span><br><small>{r["date"]} — {r["description"]}</small></div>', unsafe_allow_html=True)
                    with col_del: 
                        if st.button("❌", key=f"dl_{idx}", use_container_width=True): 
                            st.session_state["delete_idx"] = idx; confirm_delete_dialog()
            except: pass

        st.markdown("---")
        st.button("📸 Снимки и албум", use_container_width=True, on_click=lambda: st.session_state.update({"view_photos": True}))
        
        pdf_html = f"<html><body><h2>ОТЧЕТ: {trip_id.upper()}</h2><p>Общо: {(depozit_hotel+total_on_site):.2f} EUR</p></body></html>"
        b64_data = base64.b64encode(pdf_html.encode("utf-8")).decode("utf-8")
        st.markdown(f'<br><a href="data:text/html;base64,{b64_data}" download="Otchet_{trip_id}.html"><button style="width:100%; background:linear-gradient(135deg, #00f2fe, #4facfe); color:white; padding:12px; border:none; border-radius:10px; font-weight:bold;">📄 СВАЛИ ОТЧЕТ</button></a>', unsafe_allow_html=True)
        
        st.markdown("---")
        df_points = get_map_points(trip_id)
        c_lat, c_lon = (df_points["lat"].mean(), df_points["lon"].mean()) if not df_points.empty else (42.7339, 25.4858)
        m = folium.Map(location=[c_lat, c_lon], zoom_start=6)
        for _, pt in df_points.iterrows(): folium.Marker(location=[pt["lat"], pt["lon"]], popup=pt["title"]).add_to(m)
        map_data = st_folium(m, width=700, height=350, key=f"map_{trip_id}")
        if map_data and map_data.get("last_clicked") and not is_trip_finished:
            cl = map_data["last_clicked"]
            if st.button("📌 Запиши локация тук"): add_map_point(trip_id, cl["lat"], cl["lng"], "Нова спирка"); st.rerun()

        if st.button("🗑️ Изтрий цялото пътуване", type="primary", use_container_width=True): confirm_delete_trip_dialog()
