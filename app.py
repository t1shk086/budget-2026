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
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important; padding: 10px 15px !important;
        margin-bottom: 15px !important;
    }
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #2e2e2e, #1c1c1c) !important; 
        color: white !important;
        border-radius: 10px !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)
KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"

if not os.path.exists(MAP_FILE):
    pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(MAP_FILE, index=False, encoding="utf-8")

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])]:
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")
def get_trip_data(t_id):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        r = df[df["trip_id"] == t_id].copy()
        if "liters" not in r.columns: r["liters"] = 0.0
        if "current_km" not in r.columns: r["current_km"] = 0.0
        return r
    except: return pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"])

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        f = df[df["trip_id"] == t_id]
        if not f.empty:
            res = f.iloc[0].to_dict()
            return {"trip_id": t_id, "car_trip": str(res.get("car_trip", "Не")), "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), "start_km": float(res.get("start_km", 0.0)), "end_km": float(res.get("end_km", 0.0)), "manual_fuel": float(res.get("manual_fuel", 0.0)), "start_date": str(res.get("start_date", "")), "end_date": str(res.get("end_date", ""))}
    except: pass
    return d
def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "current_km" not in df.columns: df["current_km"] = 0.0
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False
def get_map_points(t_id):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        return df[df["trip_id"] == t_id].copy()
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
if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center;'><h1>🐾 PixelApp</h1></div>", unsafe_allow_html=True)
    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("📂 ОТВОРИ ПЪТУВАНЕ", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_"); st.rerun()
    
    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:").strip()
        d_range = st.date_input("Изберете дати:", value=[datetime.date.today(), datetime.date.today()])
        st.write("🚗 Собствен автомобил?")
        viber_car = st.radio("Избор:", ["Не", "Да"])
        new_skm = st.number_input("Начални км:", value=0.0)
        if st.button("🚀 СЪЗДАЙ", use_container_width=True, type="primary") and txt:
            s_d_str = d_range[0].strftime("%d.%m.%Y") if isinstance(d_range, list) else ""
            e_d_str = d_range[-1].strftime("%d.%m.%Y") if isinstance(d_range, list) else ""
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, str(viber_car), "Да", float(new_skm), 0.0, 0.0, s_d_str, e_d_str)
            st.session_state["current_trip"] = target_id; st.rerun()

    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
else:
    trip_id = st.session_state["current_trip"]
    papka_snimki = f"snimki_{trip_id}_2026"
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    @st.dialog("🗑️ Потвърждение")
    def confirm_delete_dialog():
        if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
            idx = st.session_state["delete_idx"]
            if st.button("👍 ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                try:
                    df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                    df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8")
                except: pass
                st.session_state["delete_idx"] = None; st.rerun()

    @st.dialog("🚨 Изтриване на цялото пътуване")
    def confirm_delete_trip_dialog():
        if st.button("💥 ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
            try:
                pd.read_csv(DATA_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
                pd.read_csv(SETTINGS_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
            except: pass
            st.session_state["current_trip"] = None; st.rerun()

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
    
    total_liters_calculated = total_liters_sum + m_fuel
    max_current_km = float(df_expenses["current_km"].max()) if not df_expenses.empty else 0.0
    eff_end_km = e_km if e_km > 0 else max_current_km
    dist = eff_end_km - s_km if eff_end_km > s_km else 0.0
    progressive_avg_con, has_progressive_data = 0.0, False

    if st.session_state["view_photos"]:
        if st.button("⬅️ НАЗАД", use_container_width=True): st.session_state["view_photos"] = False; st.rerun()
    else:
        st.markdown(f"<div style='text-align: center;'><h2>🌴 {trip_id.replace('_', ' ')}</h2></div>", unsafe_allow_html=True)
        if st.button("⬅️ НАЗАД КЪМ МЕНЮТО", use_container_width=True): st.session_state["current_trip"] = None; st.rerun()
        
        v_id = st.session_state["form_version"]
        col1, col2 = st.columns(2)
        with col1: s_input = st.number_input("СУМА (EUR)", value=None, format="%.2f", key=f"su_{v_id}")
        with col2: o_input = st.text_input("Описание", key=f"op_{v_id}")
        is_trip_finished = (e_km > 0.0)
        @st.dialog("⛽ Зареждане")
        def fuel_modal(amount, category, description, is_dep):
            liters = st.number_input("Литри:", value=0.0)
            km_input = st.number_input("Текущи км:", value=0.0)
            if st.button("💾 Запиши", use_container_width=True, type="primary"):
                if add_expense(trip_id, amount, category, f"[ГОРИВО] {description}", is_dep, float(liters), float(km_input)):
                    st.session_state["form_version"] += 1; st.rerun()

        grid = st.columns(3)
        for i, kat in enumerate(KATEGORII):
            with grid[i % 3]:
                if st.button(kat, use_container_width=True, key=f"bt_{i}"):
                    if s_input and s_input > 0:
                        desc, is_d = (o_input.strip() if o_input else "Без описание"), (kat == "Депозит/Резервация")
                        if kat == "Транспорт": fuel_modal(s_input, kat, desc, is_d)
                        else:
                            if add_expense(trip_id, s_input, kat, desc, is_d): st.session_state["form_version"] += 1; st.rerun()

        @st.dialog("⚙️ Настройки")
        def edit_car_modal():
            v_car = st.radio("Кола?", ["Не", "Да"])
            new_sk = st.number_input("Начални км:", value=0.0)
            new_mf = st.number_input("Гориво (л):", value=0.0)
            if st.button("💾 Обнови", use_container_width=True, type="primary"):
                save_trip_settings(trip_id, str(v_car), "Да", float(new_sk), e_km, float(new_mf), st_date, en_date)
                st.session_state["form_version"] += 1; st.rerun()

        @st.dialog("🏁 Край")
        def finish_trip_modal():
            end_km_input = st.number_input("Финални км:", value=0.0)
            if st.button("🔒 ЗАКЛЮЧИ", use_container_width=True, type="primary"):
                save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date)
                st.session_state["form_version"] += 1; st.rerun()
        if car_trip == "Да":
            c_m1, c_m2 = st.columns(2)
            with c_m1: st.button("⚙️ Настройки кола", use_container_width=True, on_click=edit_car_modal)
            with c_m2: st.button("🏁 Край на пътуването", use_container_width=True, on_click=finish_trip_modal)
        
        st.markdown("---")
        col_st1, col_st2 = st.columns(2)
        with col_st1: st.metric("🏨 ДЕПОЗИТ", f"{depozit_hotel:.2f} EUR")
        with col_st2: st.metric("💰 НА МЯСТО", f"{total_on_site:.2f} EUR")

        if not df_trip.empty:
            st.markdown("---")
            for idx, r in df_expenses.iterrows():
                st.markdown(f"**{get_emoji(r['category'])} {r['category']}** — {r['amount']:.2f} EUR<br><small>{r['date']} — {r['description']}</small>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🗺️ Карта")
        df_points = get_map_points(trip_id)
        c_lat, c_lon = (df_points["lat"].mean(), df_points["lon"].mean()) if not df_points.empty else (42.7339, 25.4858)
        m = folium.Map(location=[c_lat, c_lon], zoom_start=6)
        for _, pt in df_points.iterrows(): folium.Marker(location=[pt["lat"], pt["lon"]], popup=pt["title"]).add_to(m)
        st_folium(m, width=700, height=400, key=f"map_{trip_id}")
            
        st.markdown("---")
        if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True): confirm_delete_trip_dialog()
