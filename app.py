import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Настройки на страницата
st.set_page_config(page_title="Travel Manager", page_icon="🚗", layout="wide")

st.title("🚗 Travel Manager")
st.subheader("Следене на пробег, разход и разходи за пътуване")

# Файл за съхранение на данните
DATA_FILE = "travel_log.csv"

# Зареждане на съществуващи данни или създаване на празен DataFrame
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Дата", "Начална точка", "Крайна точка", 
        "Начален километраж", "Краен километраж", "Пробег (km)", 
        "Заредено гориво (L)", "Цена за литър", "Разход за гориво", 
        "Други разходи", "Общ разход", "Среден разход (L/100km)"
    ])

# Входна форма за нови данни
with st.form(key="travel_form"):
    st.write("### 📝 Въвеждане на ново пътуване")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date = st.date_input("Дата", datetime.today())
        start_loc = st.text_input("Начална точка")
        end_loc = st.text_input("Крайна точка")
        
    with col2:
        start_km = st.number_input("Начален километраж", min_value=0.0, step=1.0)
        end_km = st.number_input("Краен километраж", min_value=0.0, step=1.0)
        
    with col3:
        fuel_liters = st.number_input("Заредено гориво (литри)", min_value=0.0, step=0.1)
        fuel_price_per_l = st.number_input("Цена за литър", min_value=0.0, step=0.01)
        other_expenses = st.number_input("Други разходи (толове, паркинг и др.)", min_value=0.0, step=1.0)

    submit_button = st.form_submit_button(label="Запази запис")

# Логика при изпращане на формата
if submit_button:
    if end_km < start_km:
        st.error("Крайният километраж не може да бъде по-малък от началния!")
    else:
        distance = end_km - start_km
        fuel_cost = fuel_liters * fuel_price_per_l
        total_cost = fuel_cost + other_expenses
        
        # Изчисляване на среден разход (L/100km)
        avg_consumption = (fuel_liters / distance * 100) if distance > 0 else 0.0

        new_entry = {
            "Дата": date,
            "Начална точка": start_loc,
            "Крайна точка": end_loc,
            "Начален километраж": start_km,
            "Краен километраж": end_km,
            "Пробег (km)": distance,
            "Заредено гориво (L)": fuel_liters,
            "Цена за литър": fuel_price_per_l,
            "Разход за гориво": fuel_cost,
            "Други разходи": other_expenses,
            "Общ разход": total_cost,
            "Среден разход (L/100km)": round(avg_consumption, 2)
        }

        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Данните са запазени успешно!")

# Табло със статистика
st.divider()
st.write("### 📊 Обща статистика")

if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Общо изминати km", f"{df['Пробег (km)'].sum():.1f} km")
    m2.metric("Общ разход", f"{df['Общ разход'].sum():.2f} лв.")
    
    total_liters = df['Заредено гориво (L)'].sum()
    total_dist = df['Пробег (km)'].sum()
    overall_avg = (total_liters / total_dist * 100) if total_dist > 0 else 0.0
    
    m3.metric("Среден разход", f"{overall_avg:.2f} L/100km")
    m4.metric("Цена на километър", f"{(df['Общ разход'].sum() / total_dist):.2f} лв./km" if total_dist > 0 else "0 лв.")

    st.write("### 📋 История на пътуванията")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Все още няма записани пътувания.")
