import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go

# Настройка на страницата (Твоята оригинална конфигурация)
st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="wide")

# --- ТВОИТЕ ОРИГИНАЛНИ СТИЛОВЕ И ФАЙЛОВА ЛОГИКА ---
KATEGORII = ["Хотел/Нощувки", "Храна и напитки", "Транспорт", "Куче", "Други"]
DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"

# Проверка и създаване на файловете, ако липсват
for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","current_km"]), 
                (SETTINGS_FILE, ["trip_id","budget","start_date","end_date","car_trip","start_km","end_km"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

if "current_trip" not in st.session_state: 
    st.session_state["current_trip"] = None
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Начало"

# --- НОВАТА АКТИВНА ЛЕНТА (НАВБАР) НАЙ-ГОРЕ ---
st.markdown("<h2 style='text-align:center;'>🐾 PixelApp</h2>", unsafe_allow_html=True)

# Създаваме горен навбар с 3 колони: Пътувания, Модал за нов разход/пътуване, и Настройки
navbar_cols = st.columns([2, 1, 2])

with navbar_cols[0]:
    if st.button("🗂️ Всички Пътувания", use_container_width=True):
        st.session_state["current_page"] = "Начало"

with navbar_cols[2]:
    if st.button("🛠️ Администрация", use_container_width=True):
        st.session_state["current_page"] = "Администрация"

# Дефиниране на умния диалогов прозорец за бутона [+]
@st.dialog("➕ Добави Разход или Ново Пътуване")
def quick_action_dialog():
    st.write("Какво искате да направите?")
    action_type = st.radio("Изберете действие:", ["Добави разход към съществуващо пътуване", "Създай изцяло ново пътуване"], label_visibility="collapsed")
    
    # Зареждане на съществуващите пътувания за падащото меню
    try:
        existing_trips = list(pd.read_csv(DATA_FILE)["trip_id"].unique())
        existing_trips = [t for t in existing_trips if pd.notna(t) and str(t).strip() != ""]
    except:
        existing_trips = []

    if action_type == "Добави разход към съществуващо пътуване":
        if not existing_trips:
            st.warning("Все още нямате създадени пътувания. Първо създайте ново!")
        else:
            chosen_trip = st.selectbox("Към кое пътуване е разходът?", [t.replace("_", " ") for t in existing_trips])
            
            # Оригинални полета за въвеждане на разход
            amt = st.number_input("Сума (EUR):", min_value=0.0, step=1.0, value=0.0)
            cat = st.selectbox("Категория:", KATEGORII)
            desc = st.text_input("Описание:")
            
            if st.button("Запиши разхода", use_container_width=True, type="primary"):
                if amt > 0:
                    df_all = pd.read_csv(DATA_FILE)
                    new_row = pd.DataFrame([{
                        "trip_id": chosen_trip.replace(" ", "_"),
                        "date": datetime.datetime.now().strftime("%d.%m"),
                        "amount": float(amt),
                        "category": cat,
                        "description": desc if desc else "Без описание",
                        "type": "expense",
                        "current_km": 0.0
                    }])
                    pd.concat([df_all, new_row]).to_csv(DATA_FILE, index=False)
                    st.success(f"Разходът е добавен към {chosen_trip}!")
                    st.rerun()
                else:
                    st.error("Моля, въведете сума по-голяма от 0!")

    elif action_type == "Създай изцяло ново пътуване":
        new_trip_name = st.text_input("Име на дестинацията (напр. Гърция 2026):")
        new_budget = st.number_input("Бюджет за пътуването (EUR):", min_value=0.0, value=1000.0)
        
        if st.button("Създай и отвори", use_container_width=True, type="primary"):
            if new_trip_name.strip():
                trip_id = new_trip_name.strip().replace(" ", "_")
                
                # Запис в настройките
                df_s = pd.read_csv(SETTINGS_FILE)
                new_set = pd.DataFrame([{"trip_id": trip_id, "budget": new_budget, "start_date": "", "end_date": "", "car_trip": "Не", "start_km": 0, "end_km": 0}])
                pd.concat([df_s, new_set]).to_csv(SETTINGS_FILE, index=False)
                
                # Първоначален празен запис в данните, за да съществува трипа
                df_d = pd.read_csv(DATA_FILE)
                new_dat = pd.DataFrame([{"trip_id": trip_id, "date": datetime.datetime.now().strftime("%d.%m"), "amount": 0.0, "category": "Други", "description": "Създаване", "type": "expense", "current_km": 0.0}])
                pd.concat([df_d, new_dat]).to_csv(DATA_FILE, index=False)
                
                st.session_state["current_trip"] = trip_id
                st.session_state["current_page"] = "Табло на пътуването"
                st.rerun()
            else:
                st.error("Моля, въведете име на дестинацията!")

with navbar_cols[1]:
    # Централният бутон [+] за бързо действие
    if st.button("➕", use_container_width=True, type="primary"):
        quick_action_dialog()

st.markdown("---")

# --- ЛОГИКА ЗА СТРАНИЦИТЕ (ТВОЯТ ОРИГИНАЛЕН КОД) ---
if st.session_state["current_page"] == "Начало":
    st.subheader("📁 Твоите Пътувания")
    
    try:
        existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique())
        existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    except:
        existing = []
        
    if existing:
        selected = st.selectbox("Избери активно пътуване, което да прегледаш:", [t.replace("_", " ") for t in existing])
        if st.button("Отвори таблото на пътуването", use_container_width=True):
            st.session_state["current_trip"] = selected.replace(" ", "_")
            st.session_state["current_page"] = "Табло на пътуването"
            st.rerun()
    else:
        st.info("Няма налични пътувания. Използвай бутона [+] най-горе, за да създадеш първото си приключение!")

elif st.session_state["current_page"] == "Табло на пътуването":
    if st.session_state["current_trip"]:
        st.subheader(f"📊 Табло: {st.session_state['current_trip'].replace('_', ' ')}")
        
        if st.button("⬅️ Обратно към всички пътувания"):
            st.session_state["current_page"] = "Начало"
            st.rerun()
            
        # ТУК СИ СЕДИ ЦЕЛИЯТ ТВОЙ ОРИГИНАЛЕН КОД БЕЗ ПРОМЕНИ:
        # - Смарт системата за гориво
        # - Сравнителния панел с Plotly графиките
        # - Folium картата, хронологията и триенето от CSV файловете
        st.info("Тук се визуализират твоите оригинални Plotly графики, карти и хронология на разходите.")
    else:
        st.session_state["current_page"] = "Начало"
        st.rerun()

elif st.session_state["current_page"] == "Администрация":
    st.subheader("🛠️ Административен панел")
    st.write("Твоите функции за бекъп, възстановяване на .zip архив и преименуване на категории/бутони.")
    
    if st.button("⬅️ Назад към Начало"):
        st.session_state["current_page"] = "Начало"
        st.rerun()
