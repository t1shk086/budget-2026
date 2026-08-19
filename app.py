import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

# --- СТИЛОВЕ ---
st.markdown("""
<style>
    .stApp { background: #111217; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

from st_supabase_connection import SupabaseConnection

# --- ИНИЦИАЛИЗАЦИЯ НА ОБЛАЧНАТА ВРЪЗКА (ДИРЕКТЕН МЕТОД) ---
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://fnuqpzzorcnjrbtwwoun.supabase.co",
    key="sb_publishable_OuX6KWlKNzCtiFhGkwmfhA_3ibPLwT7"
)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Нощувки/Хотел", "Депозит/Резервация", "Други"]

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")

def get_trip_data(t_id):
    try:
        res = conn.table("budget_data").select("*").eq("trip_id", t_id).execute()
        if res.data: return pd.DataFrame(res.data)
    except: pass
    return pd.DataFrame(columns=["id", "trip_id", "date", "amount", "category", "description", "type", "liters", "current_km"])

def get_trip_settings(t_id):
    default_settings = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
    try:
        res = conn.table("trip_settings").select("*").eq("trip_id", t_id).execute()
        if res.data: return res.data[0]
    except: pass
    return default_settings

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        row_data = {"trip_id": str(t_id), "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}
        conn.table("trip_settings").upsert(row_data).execute()
    except: pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        row_data = {"trip_id": str(t_id), "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": str(cat), "description": str(desc) if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        conn.table("budget_data").insert(row_data).execute()
        return True
    except: return False

def get_map_points(t_id):
    try:
        res = conn.table("map_points").select("*").eq("trip_id", t_id).execute()
        if res.data: return pd.DataFrame(res.data)
    except: pass
    return pd.DataFrame(columns=["id", "trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        row_data = {"trip_id": str(t_id), "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
        conn.table("map_points").insert(row_data).execute()
        return True
    except: return False

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0
if "view_photos" not in st.session_state: st.session_state["view_photos"] = False
if "delete_idx" not in st.session_state: st.session_state["delete_idx"] = None

@st.dialog("➕ Ново приключение")
def create_trip_modal():
    st.write("Въведете дестинация:")
    new_t = st.text_input("Дестинация:").strip()
    c_t = st.selectbox("Пътуване с кола?", ["Да", "Не"])
    t_f = st.selectbox("Следене на гориво?", ["Добави впоследствие", "Не"])
    s_km = st.number_input("Начални километри:", min_value=0.0, value=0.0)
    if st.button("🚀 Създай", use_container_width=True, type="primary"):
        if new_t:
            trip_id = new_t.replace(" ", "_")
            save_trip_settings(trip_id, c_t, t_f, s_km, s_km)
            add_expense(trip_id, 0.0, "Други", "Създаване на пътуване", is_dep=True)
            st.session_state["current_trip"] = trip_id
            st.success("Приключението е създадено успешно! 🎉")
            st.rerun()

@st.dialog("🗑️ Потвърждение за изтриване")
def confirm_delete_dialog():
    if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
        record_id = st.session_state["delete_idx"]
        st.write("Сигурни ли сте, че искате да изтриете този разход?")
        if st.button("✔️ ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
            conn.table("budget_data").delete().eq("id", record_id).execute()
            st.session_state["delete_idx"] = None
            st.rerun()

@st.dialog("🚨 Изтриване на цялото пътуване")
def confirm_delete_trip_dialog(trip_id):
    st.error(f"Изтриване на пътуването до {trip_id}?")
    if st.button("✔️ ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
        conn.table("budget_data").delete().eq("trip_id", trip_id).execute()
        conn.table("trip_settings").delete().eq("trip_id", trip_id).execute()
        conn.table("map_points").delete().eq("trip_id", trip_id).execute()
        st.session_state["current_trip"] = None
        st.rerun()

if st.session_state["current_trip"] is None:
    st.markdown("<h1>🐾 PixelApp</h1>", unsafe_allow_html=True)
    existing = []
    try:
        res_trips = conn.table("trip_settings").select("trip_id").execute()
        if res_trips.data: existing = list(set([r["trip_id"] for r in res_trips.data if r.get("trip_id")]))
    except: pass

    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("✔️ Зареди", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.rerun()
    
    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
else:
    trip_id = st.session_state["current_trip"]
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])

    st.markdown(f"<h2>🌴 Дестинация: {trip_id.replace('_', ' ')}</h2>", unsafe_allow_html=True)
    
    if st.button("🔙 НАЗАД КЪМ ИЗБОР НА ПОЧИВКА", use_container_width=True):
        st.session_state["current_trip"] = None
        st.rerun()

    v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1: s_input = st.number_input("СУМА (EUR)", value=None, format="%.2f", key=f"su_{v_id}")
    with col2: o_input = st.text_input("Описание", key=f"op_{v_id}")

    if o_input.strip() and s_input and s_input > 0:
        grid = st.columns(3)
        for i, kat in enumerate(KATEGORII):
            with grid[i % 3]:
                if st.button(kat, use_container_width=True, key=f"bt_{i}"):
                    if add_expense(trip_id, s_input, kat, o_input.strip()):
                        st.session_state["form_version"] += 1
                        st.rerun()

    st.markdown("### 📊 Анализ на разходите")
    for kat, s_value in categories_totals.items():
        st.markdown(f"**{get_emoji(kat)} {kat}:** {s_value:.2f} EUR")

    if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True):
        confirm_delete_trip_dialog(trip_id)
