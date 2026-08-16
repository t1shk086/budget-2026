import streamlit as st
import pandas as pd
import datetime
import os
import glob
import io
import base64

# 1. НАСТРОЙКА НА СТРАНИЦАТА И 3Д CSS ДИЗАЙН
st.set_page_config(page_title="Бюджет 2026", page_icon="💰", layout="centered")

st.markdown("""
<style>
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader, .stExpander {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4), 
                    -2px -2px 8px rgba(255, 255, 255, 0.02) !important;
        margin-bottom: 15px !important;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #2e2e2e, #1c1c1c) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5), 
                    -1px -1px 4px rgba(255, 255, 255, 0.05) !important;
        transition: all 0.2s ease !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #3d3d3d, #252525) !important;
        transform: translateY(-2px) !important;
        box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.6) !important;
    }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"

def get_emoji(category):
    mapping = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return mapping.get(category, "💳")

if not os.path.exists(DATA_FILE):
    try: pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"]).to_csv(DATA_FILE, index=False, encoding="utf-8")
    except: pass
else:
    try:
        df_check = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "liters" not in df_check.columns:
            df_check["liters"] = 0.0
            df_check.to_csv(DATA_FILE, index=False, encoding="utf-8")
    except: pass

if not os.path.exists(SETTINGS_FILE):
    try: pd.DataFrame(columns=["trip_id", "car_trip", "track_fuel", "start_km", "end_km", "manual_fuel"]).to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def get_trip_data(trip_id):
    if not os.path.exists(DATA_FILE): return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"])
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        df_trip = df[df["trip_id"] == trip_id].copy()
        if "liters" not in df_trip.columns: df_trip["liters"] = 0.0
        return df_trip
    except: return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"])
def get_trip_settings(trip_id):
    default = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0}
    if not os.path.exists(SETTINGS_FILE): return default
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df_trip = df[df["trip_id"] == trip_id]
        if not df_trip.empty:
            res = df_trip.iloc[0].to_dict()
            return {"car_trip": str(res.get("car_trip", "Не")), "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), "start_km": float(res.get("start_km", 0.0)), "end_km": float(res.get("end_km", 0.0)), "manual_fuel": float(res.get("manual_fuel", 0.0))}
    except: pass
    return default

def save_trip_settings(trip_id, car_trip, track_fuel, start_km, end_km, manual_fuel=0.0):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != trip_id]
        new_row = {"trip_id": trip_id, "car_trip": car_trip, "track_fuel": track_fuel, "start_km": float(start_km), "end_km": float(end_km), "manual_fuel": float(manual_fuel)}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def add_expense(trip_id, amount, category, description, is_deposit=False, liters=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8") if os.path.exists(DATA_FILE) else pd.DataFrame()
        new_row = {"trip_id": trip_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amount), "category": category, "description": description if description else "Без описание", "type": "deposit" if is_deposit else "expense", "liters": float(liters)}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False

def generate_html_pdf(trip_name, total_site, deposit, categories_totals, rows_data, fuel_info=None):
    html_content = f"<html><body><h1>Отчет: {trip_name}</h1></body></html>"
    return html_content.encode('utf-8')

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0

if st.session_state["current_trip"] is None:
    st.markdown("<h1 style='text-align: center;'>💰 Бюджет 2026</h1>", unsafe_allow_html=True)
    existing_trips = []
    if os.path.exists(DATA_FILE):
        try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            existing_trips = list(df_all["trip_id"].unique())
        except: pass
    menu_options = ["-- Изберете почивка --"] + [t.replace("_", " ") for t in existing_trips] + ["➕ СЪЗДАЙ НОВО ПЪТУВАНЕ"]
    user_choice = st.selectbox("Вашите дестинации:", menu_options)
    if user_choice == "➕ СЪЗДАЙ НОВО ПЪТУВАНЕ":
        input_text = st.text_input("Въведете име на новата дестинация:").strip()
        if st.button("🚀 НАЧАЛО", use_container_width=True):
            if input_text:
                st.session_state["current_trip"] = input_text.replace(" ", "_")
                st.rerun()
    elif user_choice != "-- Изберете почивка --":
        if st.button("📂 ОТВОРИ ПОЧИВКАТА", use_container_width=True):
            st.session_state["current_trip"] = user_choice.replace(" ", "_")
            st.rerun()
else:
    trip_id = st.session_state["current_trip"]
    if st.button("⬅️ НАЗАД КЪМ НАЧАЛОТО", use_container_width=True):
        st.session_state["current_trip"] = None
        st.rerun()
    st.markdown(f"<h2 style='text-align: center; color: #00f2fe;'>🌴 {trip_id.upper().replace('_', ' ')}</h2>", unsafe_allow_html=True)
    
    current_settings = get_trip_settings(trip_id)
    car_index = 0 if current_settings["car_trip"] == "Не" else 1
    car_choice = st.selectbox("Пътувате ли със собствен автомобил?", ["Не", "Да"], index=car_index)
    track_fuel_choice = "Не"
    start_km_val, end_km_val, manual_fuel_val = 0.0, 0.0, 0.0
    if car_choice == "Да":
        track_index = 0 if current_settings["track_fuel"] == "Да" else 1
        track_fuel_choice = st.selectbox("Искате ли изчисляване на разход на гориво?", ["Да", "Добави впоследствие"], index=track_index)
        if track_fuel_choice == "Да":
            start_km_val = st.number_input("Начални км", value=float(current_settings["start_km"]))
            end_km_val = st.number_input("Крайни км", value=float(current_settings["end_km"]))
    save_trip_settings(trip_id, car_choice, track_fuel_choice, start_km_val, end_km_val, manual_fuel_val)

    v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1: s_input = st.number_input("СУМА (EUR)", min_value=0.0, step=1.0, key=f"s_{v_id}")
    with col2: o_input = st.text_input("Описание", key=f"o_{v_id}")

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description):
        liters = st.number_input("Литри", min_value=0.0, step=0.1)
        if st.button("💾 Запиши гориво", use_container_width=True, type="primary"):
            if add_expense(trip_id, amount, category, f"[ГОРИВО] {description}", liters=liters):
                st.session_state["form_version"] += 1
                st.rerun()

    grid = st.columns(3)
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"b_{i}"):
                if s_input and s_input > 0:
                    desc = o_input.strip() if o_input else "Без описание"
                    if kat == "Транспорт" and car_choice == "Да" and track_fuel_choice == "Да" and any(k in desc.lower() for k in ["гориво", "зареждане", "бензин", "дизел"]):
                        fuel_modal(s_input, kat, desc)
                    else:
                        if add_expense(trip_id, s_input, kat, desc):
                            st.session_state["form_version"] += 1
                            st.rerun()

    df_trip = get_trip_data(trip_id)
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    total_liters_sum = 0.0
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
        if row["category"] == "Транспорт": total_liters_sum += float(row.get("liters", 0.0))

    st.subheader("📊 Анализ")
    for kat, s_value in categories_totals.items():
        st.write(f"{get_emoji(kat)} {kat}: **{s_value:.2f} EUR**")

    if car_choice == "Да" and track_fuel_choice == "Да":
        dist = end_km_val - start_km_val
        if dist > 0:
            st.info(f"⛽ Среден разход: **{(total_liters_sum / dist * 100):.1f} л / 100 км** (Изминати: {dist:.1f} км)")

    if not df_trip.empty:
        st.subheader("📋 Хронология")
        for _, r in df_expenses.iterrows():
            st.text(f"{r['date']} - {r['category']}: {r['amount']} EUR ({r['description']})")
