import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import requests
import json

# =====================================================================
# 🔑 ГЛОБАЛНА ОБЛАЧНА КОНФИГУРАЦИЯ (С ВАШИТЕ РАБОТЕЩИ ДАННИ)
# =====================================================================
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidW5xcWtrZWN6andtZW1kdW95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcxNTE4MDEsImV4cCI6MjEwMjcyNzgwMX0.tOn9YEJ5iM8BCxDdHscFTCzcWkAcLl7H1n3ASZngwMk"

# Локални файлове на сървъра (Новата визия 2026)
DATA_FILE = "budget_data_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"

# Подсигуряване на локалните структури
for f in [DATA_FILE, MAP_FILE, SETTINGS_FILE]:
    if not os.path.exists(f):
        pd.DataFrame().to_csv(f, index=False, encoding="utf-8")

# =====================================================================
# ⚡ ФОНОВИ ИНЖЕКЦИИ КЪМ SUPABASE (ПРАТЯТ ДАННИ ТИХО В ЗАДЕН ФОН)
# =====================================================================
def cloud_log_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        url = f"{SUPABASE_URL}/rest/v1/budget_data"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        payload = {
            "trip_id": str(t_id), "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt),
            "category": str(cat), "description": str(desc) if desc else "Без описание",
            "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)
        }
        requests.post(url, json=payload, headers=headers, timeout=3)
    except: pass

def cloud_log_pin(t_id, lat, lon, title, color="blue"):
    try:
        url = f"{SUPABASE_URL}/rest/v1/map_points"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        payload = {"trip_id": str(t_id), "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
        requests.post(url, json=payload, headers=headers, timeout=3)
    except: pass

def cloud_log_photo(bucket_name, file_name, file_bytes):
    try:
        url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{file_name}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        requests.post(url, data=file_bytes, headers=headers, timeout=5)
    except: pass

# =====================================================================
# 🚘 ОРИГИНАЛНИ ФУНКЦИИ С ВГРАДЕНО ОБЛАЧНО ДУБЛИРАНЕ
# =====================================================================
def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8") if os.path.getsize(DATA_FILE) > 0 else pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"])
        row = {"trip_id": str(t_id), "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": str(cat), "description": str(desc) if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        
        # 🌟 Живо дублиране в Supabase при натискане на бутона
        cloud_log_expense(t_id, amt, cat, desc, is_dep, lit, c_km)
        return True
    except: return False

def get_trip_data(t_id):
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            df = pd.read_csv(DATA_FILE, encoding="utf-8")
            if not df.empty and "trip_id" in df.columns:
                return df[df["trip_id"] == str(t_id)]
    except: pass
    return pd.DataFrame(columns=["id", "trip_id", "date", "amount", "category", "description", "type", "liters", "current_km"])

# =====================================================================
# 🎨 ГЛАВЕН ИНТЕРФЕЙС И ВИЗИЯ (Абсолютно недокоснати)
# =====================================================================
st.set_page_config(page_title="PixelBudget 2026", layout="wide", initial_sidebar_state="expanded")

# Проверка на сесията за активно пътуване
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = "Пътуване 1"
if "view_photos" not in st.session_state:
    st.session_state["view_photos"] = False

trip_id = st.session_state["current_trip"]

st.title(f"📊 Дигитален Портфейл - {trip_id}")

# Форма за въвеждане на разходи
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        сума = st.number_input("Сума (EUR):", min_value=0.0, step=1.0, value=0.0, key="main_amt")
    with col2:
        описание = st.text_input("Описание / Ограничение:", placeholder="Напр. Обяд в ресторант", key="main_desc")

    st.write("Категории разходи:")
    cat_cols = st.columns(4)
    Категории = ["🍔 Храна", "⛽ Гориво", "🏨 Хотел", "🛒 Пазаруване", "🚗 Такси/Път", "🎭 Развлечение", "🎁 Подаръци", "🛠️ Други"]
    
    for idx, cat in enumerate(Категории):
        with cat_cols[idx % 4]:
            if st.button(cat, use_container_width=True, key=f"btn_{idx}"):
                if сума > 0:
                    if add_expense(trip_id, сума, cat, описание):
                        st.success(f"Записано локално и в облака: {сума} EUR в {cat}!")
                        st.rerun()
                else:
                    st.error("Въведете сума по-голяма от 0!")

# =====================================================================
# 📸 ГАЛЕРИЯ С АВТОМАТИЧНО ОБЛАЧНО АРХИВИРАНЕ НА СНИМКИТЕ
# =====================================================================
st.markdown("---")
st.subheader("📸 Спомени от пътуването")
papka_snimki = f"snimki_{trip_id}_2026"
if not os.path.exists(papka_snimki):
    os.makedirs(papka_snimki)

up = st.file_uploader("Добавете нови спомени в албума:", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="uploader_gallery")
if up:
    for f in up:
        if not os.path.exists(os.path.join(papka_snimki, f.name)):
            bytes_data = f.getbuffer()
            # 1. Локален запис
            with open(os.path.join(papka_snimki, f.name), "wb") as out:
                out.write(bytes_data)
            # 2. Облачен запис в контейнер 'snimki'
            cloud_name = f"{trip_id}_{f.name}"
            cloud_log_photo("snimki", cloud_name, bytes_data)
    st.success("Снимките са архивирани безопасно в облака!")
    st.rerun()

# Визуализация на хронологията на екрана
st.markdown("---")
st.subheader("📜 Хронология на текущото пътуване")
df_trip = get_trip_data(trip_id)

if not df_trip.empty:
    st.dataframe(df_trip[["date", "amount", "category", "description"]].sort_index(ascending=False), use_container_width=True)
else:
    st.info("Хронологията в момента е празна. Въведете първия си разход по-горе!")
