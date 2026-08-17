import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

# Връщане на оригиналния луксозен графитен дизайн с неонови акценти
st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important; padding: 10px 15px !important;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 15px !important;
    }
    button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #2e2e2e, #1c1c1c) !important; color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 10px !important;
        box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5) !important; font-weight: bold !important; width: 100% !important;
    }
    h1, h2, h3, h4, h5, h6, label, p { color: #ffffff !important; }
    small { color: #888 !important; }
</style>
""", unsafe_allow_html=True)
KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE, MAP_FILE = "budget_data_2026.csv", "trip_settings_2026.csv", "trip_map_points_2026.csv"

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), 
                (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"]),
                (MAP_FILE, ["trip_id", "lat", "lon", "title", "color"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")
def get_trip_data(t_id):
    try: 
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        return df[df["trip_id"] == t_id].copy()
    except: 
        return pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"])

def get_trip_settings(t_id):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        f = df[df["trip_id"] == t_id]
        if not f.empty:
            res = f.iloc[0].to_dict()
            return {"trip_id": t_id, "car_trip": str(res.get("car_trip", "Не")), "track_fuel": str(res.get("track_fuel", "Да")), "start_km": float(res.get("start_km", 0.0)), "end_km": float(res.get("end_km", 0.0)), "manual_fuel": float(res.get("manual_fuel", 0.0)), "start_date": str(res.get("start_date", "")), "end_date": str(res.get("end_date", ""))}
    except: pass
    return {"car_trip": "Не", "track_fuel": "Да", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        pd.concat([df, new_row], ignore_index=True).to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False

def get_map_points(t_id):
    try: return pd.read_csv(MAP_FILE, encoding="utf-8")[lambda d: d["trip_id"] == t_id].copy()
    except: return pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        row = {"trip_id": t_id, "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(MAP_FILE, index=False, encoding="utf-8")
        return True
    except: return False
if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0
if "view_photos" not in st.session_state: st.session_state["view_photos"] = False
if "delete_idx" not in st.session_state: st.session_state["delete_idx"] = None

if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center;'><h1>🐾 PixelApp</h1><p style='color: #ffd700;'>Premium Travel Manager</p></div>", unsafe_allow_html=True)
    try:
        existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique())
        existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    except: existing = []
    
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("📂 ОТВОРИ ПЪТУВАНЕ", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_"); st.rerun()
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa;'>Няма открити активни почивки.</div>", unsafe_allow_html=True)
    
    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:").strip()
        d_range = st.date_input("Изберете дати:", value=[datetime.date.today(), datetime.date.today()])
        viber_car = st.radio("Автомобил?", ["Не", "Да"])
        new_skm = st.number_input("Начални километри (км):", value=0.0)
        if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True, type="primary") and txt:
            s_d_str = d_range.strftime("%d.%m.%Y") if isinstance(d_range, (list, tuple)) and len(d_range) > 0 else ""
            e_d_str = d_range[-1].strftime("%d.%m.%Y") if isinstance(d_range, (list, tuple)) and len(d_range) > 1 else s_d_str
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, viber_car, "Да", new_skm, 0.0, 0.0, s_d_str, e_d_str)
            st.session_state["current_trip"] = target_id; st.rerun()

    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
else:
    trip_id = st.session_state["current_trip"]
    papka_snimki = f"snimki_{trip_id}_2026"
    if not os.path.exists(papka_snimki): os.makedirs(papka_snimki)
    
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    @st.dialog("🗑️ Потвърждение за изтриване")
    def confirm_delete_dialog():
        if st.session_state["delete_idx"] is not None:
            if st.button("👍 ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                try:
                    df = pd.read_csv(DATA_FILE, encoding="utf-8")
                    df = df.drop(st.session_state["delete_idx"])
                    df.to_csv(DATA_FILE, index=False, encoding="utf-8")
                except: pass
                st.session_state["delete_idx"] = None; st.rerun()

    st.markdown(f"<div style='text-align: center;'><h2>🌴 Дестинация: {trip_id.replace('_', ' ')}</h2><p>{st_date} - {en_date}</p></div>", unsafe_allow_html=True)
    
    if st.button("📸 ГАЛЕРИЯ СЪС СНИМКИ" if not st.session_state["view_photos"] else "⬅️ ОБРАТНО КЪМ РАЗХОДИТЕ", use_container_width=True):
        st.session_state["view_photos"] = not st.session_state["view_photos"]; st.rerun()

    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())

    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
    if st.session_state["view_photos"]:
        st.subheader("🖼️ Галерия на приключението")
        kacheni = st.file_uploader("Качете снимка:", type=["jpg","png","jpeg"], accept_multiple_files=True)
        if kacheni:
            for sn in kacheni:
                with open(os.path.exists(os.path.join(papka_snimki, sn.name)), "wb") as f: f.write(sn.getbuffer())
            st.success("Снимките са запазени!"); st.rerun()
        f_snimki = glob.glob(os.path.join(papka_snimki, "*"))
        if f_snimki:
            for s_path in f_snimki: st.image(s_path, use_container_width=True)
        else: st.info("Все още няма качени снимки.")
    else:
        if st.button("⬅️ НАЗАД КЪМ ИЗБОР", use_container_width=True): st.session_state["current_trip"] = None; st.rerun()
        
        v_id = st.session_state["form_version"]
        col1, col2 = st.columns(2)
        with col1: s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Сума...", key=f"su_{v_id}")
        with col2: o_input = st.text_input("Описание", placeholder="Описание...", key=f"op_{v_id}")

        @st.dialog("⛽ Зареждане на гориво")
        def fuel_modal(amount, category, description):
            liters = st.number_input("Литри:", value=0.0)
            fuel_type = st.radio("Тип:", ["Да, до горе (Пълен резервоар)", "Не, частично"])
            km_input = st.number_input("Текущи километри:", value=s_km)
            if st.button("💾 Запиши", use_container_width=True, type="primary"):
                is_full = "ПЪЛЕН" if "до горе" in fuel_type.lower() else "ЧАСТИЧЕН"
                if add_expense(trip_id, amount, category, f"[{is_full} ГОРИВО] {description}", False, liters, km_input):
                    if is_full == "ПЪЛЕН": save_trip_settings(trip_id, car_trip, t_fuel, s_km, km_input, m_fuel, st_date, en_date)
                    st.session_state["form_version"] += 1; st.rerun()

        grid = st.columns(3)
        for i, kat in enumerate(KATEGORII):
            with grid[i % 3]:
                if st.button(kat, use_container_width=True, key=f"bt_{i}"):
                    if s_input and s_input > 0:
                        desc = o_input.strip() if o_input else "Без описание"
                        if kat == "Транспорт" and any(k in desc.lower() for k in ["гориво", "зареждане"]): fuel_modal(s_input, kat, desc)
                        else:
                            if add_expense(trip_id, s_input, kat, desc, (kat == "Депозит/Резервация")):
                                st.session_state["form_version"] += 1; st.rerun()

        st.markdown("### 📊 Анализ на разходите")
        stat_grid = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            with stat_grid[idx % 2]:
                st.markdown(f'<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 12px; border-radius: 14px; margin-bottom: 12px; height: 110px; display: flex; flex-direction: column; justify-content: space-between;"><div>{get_emoji(kat)} {kat}</div><h3 style="margin:0;">{s_value:.2f} EUR</h3></div>', unsafe_allow_html=True)

        if car_trip == "Да":
            st.markdown("#### ⛽ Автомобилно табло")
            razhod_km = 0.0
            try:
                df_fuel = df_expenses[df_expenses["category"] == "Транспорт"].sort_values(by="current_km")
                t_liters, t_dist, last_k = 0.0, 0.0, s_km
                for _, r in df_fuel.iterrows():
                    if "ПЪЛЕН" in str(r["description"]).upper() and float(r["current_km"]) > last_k:
                        t_dist += (float(r["current_km"]) - last_k)
                        t_liters += float(r.get("liters", 0.0))
                        last_k = float(r["current_km"])
                if t_dist > 0: razhod_km = (t_liters / t_dist) * 100
            except: pass
            
            color_g = "#666" if razhod_km == 0.0 else "#00f2fe"
            lbl_g = "⚠️ Изчислява се при зареждане до горе" if razhod_km == 0.0 else f"Среден разход: {razhod_km:.1f} л / 100 км"
            st.markdown(f"<div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; text-align: center; margin-bottom:15px;'>📍 Километри по табло: <b>{(e_km - s_km) if e_km > s_km else 0:.0f} км</b><br><small style='color:{color_g}; font-weight:bold;'>{lbl_g}</small></div>", unsafe_allow_html=True)

        st.markdown("---")
        col_st1, col_st2 = st.columns(2)
        with col_st1: st.markdown(f"<div style='background:rgba(255,255,255,0.03); padding:15px; border-radius:12px; text-align:center;'>🏨 ДЕПОЗИТ<br><h2>{depozit_hotel:.2f} EUR</h2></div>", unsafe_allow_html=True)
        with col_st2: st.markdown(f"<div style='background:rgba(255,255,255,0.03); padding:15px; border-radius:12px; text-align:center;'>💰 НА МЯСТО<br><h2>{total_on_site:.2f} EUR</h2></div>", unsafe_allow_html=True)

        if not df_trip.empty:
            st.markdown("---"); st.subheader("📋 Хронология на плащанията")
            for idx in reversed(df_trip.index.tolist()):
                r = df_trip.loc[idx]
                col_rec, col_del = st.columns([0.85, 0.15])
                with col_rec: 
                    st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); padding: 15px 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); display: flex; flex-direction: column; justify-content: center;"><span style="font-size:15px; font-weight: bold;">{get_emoji(r["category"])} {r["category"]} — <span style="color:#ff4b4b;">{r["amount"]:.2f} EUR</span></span><small style="color:#aaa; margin-top: 6px;">📅 {r["date"]} — {r["description"]}</small></div>', unsafe_allow_html=True)
                with col_del:
                    if st.button("❌", key=f"dl_{idx}", use_container_width=True):
                        st.session_state["delete_idx"] = idx; confirm_delete_dialog()

        st.markdown("---")
        df_points = get_map_points(trip_id)
        c_lat, c_lon = (df_points["lat"].mean(), df_points["lon"].mean()) if not df_points.empty else (42.7339, 25.4858)
        m = folium.Map(location=[c_lat, c_lon], zoom_start=6)
        for _, pt in df_points.iterrows(): folium.Marker(location=[pt["lat"], pt["lon"]], popup=pt["title"]).add_to(m)
        map_data = st_folium(m, width=700, height=300, key=f"map_{trip_id}")
        if map_data and map_data.get("last_clicked"):
            click_coords = map_data["last_clicked"]
            if add_map_point(trip_id, click_coords["lat"], click_coords["lng"], "Нова спирка"): st.rerun()

        grand_total = depozit_hotel + total_on_site
        pdf_html = f"<html><body><h2>ОТЧЕТ: {trip_id.upper()}</h2><p><b>💰 ОБЩО: {grand_total:.2f} EUR</b></p></body></html>"
        b64_pdf = base64.b64encode(pdf_html.encode('utf-8')).decode('utf-8')
        st.markdown(f'<a href="data:text/html;base64,{b64_pdf}" download="Otchet_{trip_id}.html"><button style="width:100%; background:linear-gradient(135deg, #00f2fe, #4facfe); color:white; border:none; padding:12px; font-weight:bold; border-radius:10px;">📄 СВАЛИ ПЪЛЕН ОТЧЕТ</button></a>', unsafe_allow_html=True)
