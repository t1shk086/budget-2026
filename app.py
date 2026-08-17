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
    /* Луксозен, дълбок уеб градиент */
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
        -webkit-backdrop-filter: blur(4px) !important;
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
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, 
         "manual_fuel": 0.0, "start_date": "", "end_date": ""}
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

if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center; margin-bottom: 5px;'><h1 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 10px rgba(0, 242, 254, 0.2); margin-bottom: 0px;'>🐾 PixelApp</h1><p style='font-family: \"Segoe UI\", Roboto, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; margin-top: 4px; margin-bottom: 30px;'>Travel Manager</p></div>", unsafe_allow_html=True)
    
    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("📂 ОТВОРИ ПЪТУВАНЕ", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.rerun()
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-bottom:15px;'>Все още нямате записани почивки. Създайте първото си приключение по-долу!</div>", unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>", unsafe_allow_html=True)
    
    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:").strip()
        d_range = st.date_input("Изберете дати за почивката:", value=[datetime.date.today(), datetime.date.today()])
        st.write("---")
        st.write("🚗 Пътувате ли със собствен автомобил?")
        viber_car = st.radio("Изберете вариант:", ["Не, с друг транспорт", "Да, със собствен автомобил"], index=0)
        new_skm = 0.0
        if viber_car == "Да, със собствен автомобил":
            new_skm = st.number_input("Начални километри (км):", value=None, placeholder="Въведете км на тръгване...", step=1.0)
        if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True, type="primary") and txt:
            if isinstance(d_range, (list, tuple)):
                s_d_str = d_range[0].strftime("%d.%m.%Y") if len(d_range) > 0 else ""
                e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 else s_d_str
            elif hasattr(d_range, "strftime"):
                s_d_str = d_range.strftime("%d.%m.%Y")
                e_d_str = s_d_str
            else:
                s_d_str, e_d_str = "", ""
            sk = float(new_skm) if new_skm is not None else 0.0
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, "Да" if viber_car == "Да, със собствен автомобил" else "Не", "Да" if viber_car == "Да, със собствен автомобил" else "Добави впоследствие", sk, 0.0, 0.0, s_d_str, e_d_str)
            try:
                geolocator = Nominatim(user_agent="pixelapp_travel_manager_2026")
                location = geolocator.geocode(f"{txt}, Europe", language="bg,en")
                if location:
                    add_map_point(target_id, location.latitude, location.longitude, f"🏁 Център: {txt}", "red")
            except:
                pass
            st.session_state["current_trip"] = target_id
            st.rerun()

    if st.button("➕ Ново пътуване", use_container_width=True):
        create_trip_modal()

else:
    trip_id = st.session_state["current_trip"]
    papka_snimki = f"snimki_{trip_id}_2026"
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    date_html = f"<p style='font-size: 14px; color: #888; font-weight: 500; margin-top: 5px;'>{st_date} - {en_date}</p>" if st_date and st_date != "nan" else ""
    st.markdown(f"<div style='text-align: center; margin-top: 5px; margin-bottom: 15px;'><h2 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 500; font-size: 28px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🌴 Дестинация: {trip_id.replace('_', ' ')}</h2>{date_html}</div>", unsafe_allow_html=True)

    if st.button("⬅️ НАЗАД КЪМ ИЗБОР НА ПОЧИВКА", use_container_width=True):
        st.session_state["current_trip"] = None
        st.rerun()

    # --- ТАБОВЕ ЗА НАВИГАЦИЯ ---
    tab_exp, tab_map, tab_gallery = st.tabs(["💸 Разходи & Анализ", "🗺️ Карта", "📸 Галерия"])

    # === ТАБ 1: РАЗХОДИ И АНАЛИЗ ===
    with tab_exp:
        df_trip = get_trip_data(trip_id)
        df_expenses = df_trip[df_trip["type"] == "expense"]
        total_on_site = float(df_expenses["amount"].sum())
        categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
        auto_fuel_money = 0.0
        for _, row in df_expenses.iterrows():
            if row["category"] in categories_totals:
                categories_totals[row["category"]] += float(row["amount"])
            if row["category"] == "Транспорт":
                auto_fuel_money += float(row["amount"])

        v_id = st.session_state["form_version"]
        col1, col2 = st.columns(2)
        with col1: s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Напишете сума...", format="%.2f", key=f"su_{v_id}")
        with col2: o_input = st.text_input("Описание", placeholder="Напишете описание...", key=f"op_{v_id}")
        is_trip_finished = (e_km > 0.0)

        if o_input.strip():
            st.markdown("<small style='color: #4facfe; font-weight: bold;'>🎯 ИЗБЕРЕТЕ КАТЕГОРИЯ ЗА ЗАПИС:</small>", unsafe_allow_html=True)
            grid = st.columns(3)
            for i, kat in enumerate(KATEGORII):
                with grid[i % 3]:
                    is_disabled = is_trip_finished and (kat == "Транспорт")
                    if st.button(f"🔒 {kat}" if is_disabled else kat, use_container_width=True, key=f"bt_{i}", disabled=is_disabled):
                        if s_input and s_input > 0:
                            desc, is_d = o_input.strip(), (kat == "Депозит/Резервация")
                            if add_expense(trip_id, s_input, kat, desc, is_d):
                                st.session_state["form_version"] += 1
                                st.rerun()

        st.markdown("### 📊 Анализ на разходите")
        stat_grid = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            with stat_grid[idx % 2]:
                pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 14px; border-radius: 14px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{get_emoji(kat)} {kat}</span>
                        <span style="font-weight: bold; color: #ff4b4b;">{s_value:.2f} EUR</span>
                    </div>
                    <div style="background: rgba(0,0,0,0.4); height: 10px; border-radius: 10px; margin-top: 6px; overflow: hidden;">
                        <div style="width: {pct}%; height: 100%; background: #00f2fe;"></div>
                    </div>
                    <small style="color:#aaa;">{pct:.1f}%</small>
                </div>
                """, unsafe_allow_html=True)

    # === ТАБ 2: ИНТЕРАКТИВНА КАРТА ===
    with tab_map:
        st.markdown("### 🗺️ Запазени точки на картата")
        df_points = get_map_points(trip_id)
        
        if not df_points.empty:
            m = folium.Map(location=[df_points.iloc[0]["lat"], df_points.iloc[0]["lon"]], zoom_start=12)
            for _, pt in df_points.iterrows():
                folium.Marker([pt["lat"], pt["lon"]], popup=pt["title"], icon=folium.Icon(color=pt["color"])).add_to(m)
            st_folium(m, width=700, height=400)
        else:
            st.info("Все още няма заснети/добавени локации на картата.")

        st.write("---")
        st.markdown("#### ➕ Добавяне на точка")
        c_lat, c_lon = st.columns(2)
        with c_lat: new_lat = st.number_input("Геогр. ширина (Lat):", format="%.6f")
        with c_lon: new_lon = st.number_input("Геогр. дължина (Lon):", format="%.6f")
        pt_title = st.text_input("Заглавие на мястото:")
        if st.button("📍 Запази локацията", type="primary") and pt_title and new_lat and new_lon:
            add_map_point(trip_id, new_lat, new_lon, pt_title, "blue")
            st.rerun()

    # === ТАБ 3: ГАЛЕРИЯ ===
    with tab_gallery:
        st.markdown("### 📸 Снимки и спомени")
        if not os.path.exists(papka_snimki): 
            os.makedirs(papka_snimki)
            
        up = st.file_uploader("Добавете нови спомени в албума:", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"u_{trip_id}")
        if up:
            for f in up:
                if not os.path.exists(os.path.join(papka_snimki, f.name)):
                    with open(os.path.join(papka_snimki, f.name), "wb") as out:
                        out.write(f.getbuffer())
            st.rerun()
            
        saved = glob.glob(os.path.join(papka_snimki, "*"))
        if saved:
            st.markdown("<br>", unsafe_allow_html=True)
            img_grid = st.columns(2)
            for idx, p in enumerate(saved):
                with img_grid[idx % 2]:
                    st.image(p, use_container_width=True)
                    if st.button("🗑️ Изтрий", key=f"di_{idx}", use_container_width=True):
                        os.remove(p)
                        st.rerun()
        else:
            st.markdown("<div style='text-align:center; margin-top:40px; color:#666;'>Все още няма качени снимки.</div>", unsafe_allow_html=True)
