import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
import uuid
from datetime import datetime
from geopy.geocoders import Nominatim

# ---------------------------------------------------------
# 1. КОНФИГУРАЦИЯ И СТИЛОВЕ
# ---------------------------------------------------------
st.set_page_config(page_title="Pixelapp Travel Manager", layout="wide", page_icon="✈️")

# Файлове за данни
TRIPS_FILE = "trips_2026.csv"
EXPENSES_FILE = "expenses_2026.csv"
FUEL_FILE = "fuel_2026.csv"
NOTES_FILE = "notes_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"

# Инициализация на файловете
for file in [TRIPS_FILE, EXPENSES_FILE, FUEL_FILE, NOTES_FILE, MAP_FILE]:
    if not os.path.exists(file):
        pd.DataFrame().to_csv(file, index=False)

# Инициализация на Session State
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = None
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Обглед"

# CSS Стилизация
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .tm-header { display: flex; align-items: center; justify-content: space-between; padding: 15px 25px; background: #151c2c; border-radius: 12px; margin-bottom: 25px; border: 1px solid #1e293b; }
    .tm-title { font-size: 24px; font-weight: bold; color: #f8fafc; }
    .tm-trip-card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; height: 100%; transition: transform 0.2s; }
    .tm-trip-card:hover { transform: translateY(-3px); border-color: #3b82f6; }
    .tm-card-title { font-size: 20px; font-weight: bold; color: #f8fafc; margin-bottom: 5px; }
    .tm-card-dates { font-size: 14px; color: #94a3b8; margin-bottom: 12px; }
    .tm-card-budget { font-size: 16px; color: #38bdf8; font-weight: 600; margin-bottom: 15px; }
    .tm-badge-planned { background: #1e3a5f; color: #60a5fa; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .tm-badge-completed { background: #064e3b; color: #34d399; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .tm-stat-box { background: #151c2c; border-radius: 10px; padding: 15px; border: 1px solid #1e293b; text-align: center; }
    .tm-stat-val { font-size: 22px; font-weight: bold; color: #38bdf8; }
    .tm-stat-lbl { font-size: 12px; color: #94a3b8; margin-top: 4px; }
    .tm-home-trips-title { font-size: 20px; font-weight: bold; color: #f8fafc; margin: 25px 0 15px 0; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. ПОМОЩНИ ФУНКЦИИ ЗА ДАННИ
# ---------------------------------------------------------
def load_data(file_path):
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return pd.read_csv(file_path, encoding="utf-8")
    except Exception:
        pass
    return pd.DataFrame()

def save_data(df, file_path):
    df.to_csv(file_path, index=False, encoding="utf-8")

def geocode_location(place_name):
    try:
        geolocator = Nominatim(user_agent="pixelapp_travel_manager")
        location = geolocator.geocode(place_name, timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

# ---------------------------------------------------------
# 3. МОДАЛНИ ПРОЗОРЦИ И ДЕЙСТВИЯ
# ---------------------------------------------------------
@st.dialog("➕ Ново Пътуване")
def create_trip_modal():
    with st.form("new_trip_form", clear_on_submit=True):
        title = st.text_input("Име на пътуването*", placeholder="напр. Ски в Алпите")
        destination = st.text_input("Дестинация*", placeholder="напр. Банско, България")
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Начална дата")
        end_date = col2.date_input("Крайна дата")
        budget = st.number_input("Бюджет (лв.)", min_value=0.0, step=50.0)
        color = st.selectbox("Цвят на маркер", ["blue", "red", "green", "purple", "orange"])
        
        submitted = st.form_submit_button("Запази пътуването", use_container_width=True)
        if submitted:
            if not title or not destination:
                st.error("Моля, попълнете задължителните полета (*)!")
            else:
                trip_id = str(uuid.uuid4())[:8]
                new_trip = {
                    "id": trip_id,
                    "title": title,
                    "destination": destination,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "budget": budget,
                    "color": color,
                    "status": "Планирано"
                }
                
                df_trips = load_data(TRIPS_FILE)
                df_trips = pd.concat([df_trips, pd.DataFrame([new_trip])], ignore_index=True)
                save_data(df_trips, TRIPS_FILE)
                
                # Геокодиране и запазване на точката за общата карта
                lat, lon = geocode_location(destination)
                if lat and lon:
                    df_map = load_data(MAP_FILE)
                    new_point = {
                        "trip_id": trip_id,
                        "title": title,
                        "lat": lat,
                        "lon": lon,
                        "color": color
                    }
                    df_map = pd.concat([df_map, pd.DataFrame([new_point])], ignore_index=True)
                    save_data(df_map, MAP_FILE)
                
                st.success("Пътуването е добавено успешно!")
                st.rerun()

# ---------------------------------------------------------
# 4. НАЧАЛЕН ЕКРАН (HOME)
# ---------------------------------------------------------
if st.session_state["current_trip"] is None:
    # Хедър
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("<div class='tm-title'>✈️ Pixelapp Travel Manager</div>", unsafe_allow_html=True)
    with col_h2:
        if st.button("➕ Ново Пътуване", use_container_width=True, type="primary"):
            create_trip_modal()

    df_trips = load_data(TRIPS_FILE)
    
    if df_trips.empty:
        st.info("Нямате добавени пътувания. Натиснете 'Ново Пътуване', за да започнете!")
    else:
        st.markdown("<div class='tm-home-trips-title'>Моите Пътувания</div>", unsafe_allow_html=True)
        
        # Грид с карти за пътуванията
        cols = st.columns(3)
        for idx, row in df_trips.iterrows():
            with cols[idx % 3]:
                badge_class = "tm-badge-planned" if row.get("status") == "Планирано" else "tm-badge-completed"
                st.markdown(f"""
                <div class='tm-trip-card'>
                    <div style='display:flex; justify-space-between; align-items:center;'>
                        <span class='tm-card-title'>{row['title']}</span>
                        <span class='{badge_class}'>{row.get('status', 'Планирано')}</span>
                    </div>
                    <div style='color:#38bdf8; font-size:14px;'>📍 {row['destination']}</div>
                    <div class='tm-card-dates'>📅 {row['start_date']} — {row['end_date']}</div>
                    <div class='tm-card-budget'>💰 Бюджет: {row['budget']:.2f} лв.</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Отвори #{row['id']}", key=f"open_{row['id']}", use_container_width=True):
                    st.session_state["current_trip"] = row['id']
                    st.rerun()

    # ---------------------------------------------------------
    # ОБЩА КАРТА С ВСИЧКИ ПОСЕТЕНИ МЕСТА (ДОЛУ НА НАЧАЛНИЯ ЕКРАН)
    # ---------------------------------------------------------
    st.markdown("<div class='tm-home-trips-title'>🗺️ Карта на всички посетени места</div>", unsafe_allow_html=True)
    
    try:
        if os.path.exists(MAP_FILE):
            df_all_maps = load_data(MAP_FILE)
            if not df_all_maps.empty and {"lat", "lon"}.issubset(df_all_maps.columns):
                avg_lat = df_all_maps["lat"].mean()
                avg_lon = df_all_maps["lon"].mean()
                
                m_home = folium.Map(location=[avg_lat, avg_lon], zoom_start=5, tiles="CartoDB dark_matter")
                
                for _, map_row in df_all_maps.iterrows():
                    trip_title = str(map_row.get("title", "Посетено място"))
                    color_marker = str(map_row.get("color", "blue"))
                    folium.Marker(
                        [map_row["lat"], map_row["lon"]],
                        popup=trip_title,
                        tooltip=trip_title,
                        icon=folium.Icon(color=color_marker, icon="info-sign")
                    ).add_to(m_home)
                
                st_folium(m_home, width="100%", height=400, key="global_home_map")
            else:
                st.info("Все още няма добавени географски точки за показване на картата.")
        else:
            st.info("Все още няма добавени географски точки.")
    except Exception:
        st.info("Картата временно не може да бъде заредена.")

# ---------------------------------------------------------
# 5. ДЕТАЙЛЕН ЕКРАН НА ПЪТУВАНЕ (TRIP DETAILS)
# ---------------------------------------------------------
else:
    trip_id = st.session_state["current_trip"]
    df_trips = load_data(TRIPS_FILE)
    trip_data = df_trips[df_trips["id"] == trip_id]
    
    if trip_data.empty:
        st.error("Пътуването не е намерено!")
        if st.button("⬅️ Обратно към началния екран"):
            st.session_state["current_trip"] = None
            st.rerun()
    else:
        trip = trip_data.iloc[0]
        
        # Хедър на пътуването
        col_back, col_t_title, col_actions = st.columns([1, 4, 2])
        with col_back:
            if st.button("⬅️ Назад", use_container_width=True):
                st.session_state["current_trip"] = None
                st.rerun()
        with col_t_title:
            st.markdown(f"<h2 style='margin:0;'>{trip['title']} ({trip['destination']})</h2>", unsafe_allow_html=True)
        with col_actions:
            if st.button("🗑️ Изтрий пътуването", use_container_width=True):
                df_trips = df_trips[df_trips["id"] != trip_id]
                save_data(df_trips, TRIPS_FILE)
                
                # Почистване на свързаните данни
                for f in [EXPENSES_FILE, FUEL_FILE, NOTES_FILE, MAP_FILE]:
                    df_sub = load_data(f)
                    if not df_sub.empty and "trip_id" in df_sub.columns:
                        df_sub = df_sub[df_sub["trip_id"] != trip_id]
                        save_data(df_sub, f)
                
                st.session_state["current_trip"] = None
                st.rerun()

        st.divider()

        # Табове
        tab_overview, tab_expenses, tab_fuel, tab_notes = st.tabs(["📊 Обглед", "💳 Разходи", "⛽ Гориво", "📝 Бележки"])

        # TAB 1: ОБГЛЕД (Без карта)
        with tab_overview:
            df_exp = load_data(EXPENSES_FILE)
            trip_exp = df_exp[df_exp["trip_id"] == trip_id] if not df_exp.empty and "trip_id" in df_exp.columns else pd.DataFrame()
            
            df_fuel = load_data(FUEL_FILE)
            trip_fuel = df_fuel[df_fuel["trip_id"] == trip_id] if not df_fuel.empty and "trip_id" in df_fuel.columns else pd.DataFrame()
            
            total_exp = trip_exp["amount"].sum() if not trip_exp.empty else 0.0
            total_fuel = trip_fuel["total_price"].sum() if not trip_fuel.empty else 0.0
            grand_total = total_exp + total_fuel
            budget = float(trip["budget"])
            rem_budget = budget - grand_total
            
            st_col1, st_col2, st_col3, st_col4 = st.columns(4)
            with st_col1:
                st.markdown(f"<div class='tm-stat-box'><div class='tm-stat-val'>{budget:.2f} лв.</div><div class='tm-stat-lbl'>Заложен Бюджет</div></div>", unsafe_allow_html=True)
            with st_col2:
                st.markdown(f"<div class='tm-stat-box'><div class='tm-stat-val'>{grand_total:.2f} лв.</div><div class='tm-stat-lbl'>Общо Изразходвани</div></div>", unsafe_allow_html=True)
            with st_col3:
                color_rem = "#34d399" if rem_budget >= 0 else "#f87171"
                st.markdown(f"<div class='tm-stat-box'><div class='tm-stat-val' style='color:{color_rem};'>{rem_budget:.2f} лв.</div><div class='tm-stat-lbl'>Оставащ Бюджет</div></div>", unsafe_allow_html=True)
            with st_col4:
                st.markdown(f"<div class='tm-stat-box'><div class='tm-stat-val'>{trip['start_date']}</div><div class='tm-stat-lbl'>Начална Дата</div></div>", unsafe_allow_html=True)

        # TAB 2: РАЗХОДИ
        with tab_expenses:
            col_e1, col_e2 = st.columns([1, 2])
            with col_e1:
                st.subheader("Добави разход")
                with st.form("add_exp_form", clear_on_submit=True):
                    exp_cat = st.selectbox("Категория", ["Храна", "Нощувки", "Забавления", "Транспорт", "Пазаруване", "Други"])
                    exp_amt = st.number_input("Сума (лв.)", min_value=0.0, step=5.0)
                    exp_note = st.text_input("Описание/Бележка")
                    if st.form_submit_button("Запази разхода", use_container_width=True):
                        df_exp_all = load_data(EXPENSES_FILE)
                        new_exp = {
                            "trip_id": trip_id,
                            "category": exp_cat,
                            "amount": exp_amt,
                            "note": exp_note,
                            "date": str(datetime.now().date())
                        }
                        df_exp_all = pd.concat([df_exp_all, pd.DataFrame([new_exp])], ignore_index=True)
                        save_data(df_exp_all, EXPENSES_FILE)
                        st.success("Разходът е добавен!")
                        st.rerun()
            with col_e2:
                st.subheader("Списък с разходи")
                df_exp_all = load_data(EXPENSES_FILE)
                if not df_exp_all.empty and "trip_id" in df_exp_all.columns:
                    t_exp = df_exp_all[df_exp_all["trip_id"] == trip_id]
                    if not t_exp.empty:
                        st.dataframe(t_exp[["date", "category", "amount", "note"]], use_container_width=True)
                    else:
                        st.info("Няма записани разходи за това пътуване.")

        # TAB 3: ГОРИВО
        with tab_fuel:
            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                st.subheader("Зареждане на гориво")
                with st.form("add_fuel_form", clear_on_submit=True):
                    liters = st.number_input("Литри", min_value=0.0, step=1.0)
                    price_per_l = st.number_input("Цена за литър (лв.)", min_value=0.0, step=0.05)
                    full_tank = st.checkbox("Пълен резервоар", value=True)
                    if st.form_submit_button("Запази зареждането", use_container_width=True):
                        df_fuel_all = load_data(FUEL_FILE)
                        new_fuel = {
                            "trip_id": trip_id,
                            "liters": liters,
                            "price_per_l": price_per_l,
                            "total_price": liters * price_per_l,
                            "full_tank": full_tank,
                            "date": str(datetime.now().date())
                        }
                        df_fuel_all = pd.concat([df_fuel_all, pd.DataFrame([new_fuel])], ignore_index=True)
                        save_data(df_fuel_all, FUEL_FILE)
                        st.success("Зареждането е записано!")
                        st.rerun()
            with col_f2:
                st.subheader("История на зарежданията")
                df_fuel_all = load_data(FUEL_FILE)
                if not df_fuel_all.empty and "trip_id" in df_fuel_all.columns:
                    t_fuel = df_fuel_all[df_fuel_all["trip_id"] == trip_id]
                    if not t_fuel.empty:
                        st.dataframe(t_fuel[["date", "liters", "price_per_l", "total_price", "full_tank"]], use_container_width=True)
                    else:
                        st.info("Няма записани зареждания.")

        # TAB 4: БЕЛЕЖКИ
        with tab_notes:
            st.subheader("Бележки кaм пътуването")
            df_notes_all = load_data(NOTES_FILE)
            existing_note = ""
            if not df_notes_all.empty and "trip_id" in df_notes_all.columns:
                t_note = df_notes_all[df_notes_all["trip_id"] == trip_id]
                if not t_note.empty:
                    existing_note = t_note.iloc[0].get("content", "")
            
            with st.form("notes_form"):
                note_content = st.text_area("Вашите бележки", value=existing_note, height=200)
                if st.form_submit_button("Запази бележките"):
                    if not df_notes_all.empty and "trip_id" in df_notes_all.columns:
                        df_notes_all = df_notes_all[df_notes_all["trip_id"] != trip_id]
                    new_note = {"trip_id": trip_id, "content": note_content}
                    df_notes_all = pd.concat([df_notes_all, pd.DataFrame([new_note])], ignore_index=True)
                    save_data(df_notes_all, NOTES_FILE)
                    st.success("Бележките бяха обновени!")
