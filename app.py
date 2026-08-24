import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. Настройка на страницата
st.set_page_config(page_title="Pixelapp Travel Manager", page_icon="🚗", layout="centered")

# 2. Инициализация и авто-миграция на базата данни
def init_db():
    conn = sqlite3.connect("travel_manager.db")
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT,
            start_km REAL,
            status TEXT DEFAULT 'Активно'
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            amount REAL,
            description TEXT,
            is_fuel INTEGER,
            odometer REAL,
            liters REAL,
            full_tank INTEGER,
            date TEXT
        )
    """)
    
    # Автоматична проверка и добавяне на липсващи колони
    c.execute("PRAGMA table_info(expenses)")
    existing_columns = [column[1] for column in c.fetchall()]
    required_columns = {
        "trip_id": "INTEGER", "amount": "REAL", "description": "TEXT",
        "is_fuel": "INTEGER", "odometer": "REAL", "liters": "REAL",
        "full_tank": "INTEGER", "date": "TEXT"
    }
    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            c.execute(f"ALTER TABLE expenses ADD COLUMN {col_name} {col_type}")
            
    conn.commit()
    conn.close()

init_db()

# 3. Помощни функции за данни
def get_active_trips():
    conn = sqlite3.connect("travel_manager.db")
    df = pd.read_sql_query("SELECT id, name FROM trips WHERE status = 'Активно'", conn)
    conn.close()
    return df

def save_trip(name, start_date, start_km):
    conn = sqlite3.connect("travel_manager.db")
    c = conn.cursor()
    c.execute("INSERT INTO trips (name, start_date, start_km) VALUES (?, ?, ?)",
              (name, str(start_date), start_km))
    conn.commit()
    conn.close()

def save_expense(trip_id, amount, description, is_fuel, odometer, liters, full_tank):
    conn = sqlite3.connect("travel_manager.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO expenses (trip_id, amount, description, is_fuel, odometer, liters, full_tank, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (trip_id, amount, description, int(is_fuel), odometer, liters, int(full_tank), datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

# 4. Стилизиране
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: bold;
        margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5rem;
        font-size: 1.1rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 5. ИЗСКАЧАЩИ ПРОЗОРЦИ (MODALS)

@st.dialog("✈️ Започване на ново пътуване")
def open_trip_dialog():
    with st.form("dialog_trip_form", clear_on_submit=True):
        trip_name = st.text_input("Име на пътуването / Дестинация", placeholder="напр. София - Бургас")
        col1, col2 = st.columns(2)
        with col1:
            trip_date = st.date_input("Дата на тръгване", datetime.today())
        with col2:
            start_km = st.number_input("Начален километраж", min_value=0.0, step=1.0)
            
        submit = st.form_submit_button("Запази пътуването", type="primary")
        if submit:
            if not trip_name.strip():
                st.error("Моля, въведете име на пътуването.")
            else:
                save_trip(trip_name, trip_date, start_km)
                st.success(f"Пътуването '{trip_name}' е започнато!")
                st.rerun()

@st.dialog("➕ Бързо въвеждане на разход")
def open_expense_dialog():
    trips_df = get_active_trips()
    trip_options = {"Общ разход (без пътуване)": None}
    for _, row in trips_df.iterrows():
        trip_options[row["name"]] = row["id"]
        
    selected_trip_name = st.selectbox("Към кое пътуване е разходът?", list(trip_options.keys()))
    selected_trip_id = trip_options[selected_trip_name]
    
    description = st.text_input("Описание", placeholder="напр. Бензин Shell, Сандвичи, Тол такса")
    amount = st.number_input("Сума (лв.)", min_value=0.0, step=0.1, format="%.2f")
    
    fuel_keywords = ["газ", "гориво", "зареждане", "бензин", "дизел", "shell", "omv", "lukoil", "rompetrol"]
    is_fuel = any(keyword in description.lower() for keyword in fuel_keywords)
    
    odometer = 0.0
    liters = 0.0
    full_tank = False
    
    if is_fuel:
        st.info("⛽ Автоматично засечено зареждане на гориво:")
        col1, col2 = st.columns(2)
        with col1:
            odometer = st.number_input("Текущ километраж", min_value=0.0, step=1.0)
            liters = st.number_input("Заредени литри", min_value=0.0, step=0.1)
        with col2:
            full_tank = st.checkbox("Зареждане до горе?")

    if st.button("Запази разхода", type="primary"):
        if amount <= 0:
            st.error("Моля, въведете сума.")
        else:
            save_expense(selected_trip_id, amount, description, is_fuel, odometer, liters, full_tank)
            st.success("Разходът е записан!")
            st.rerun()

# 6. НАЧАЛЕН ЕКРАН (ОЛИТЕКСТИРАН И ИЗЧИСТЕН)
st.markdown("<div class='main-title'>🚗 Pixelapp Travel Manager</div>", unsafe_allow_html=True)

col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("➕ Бърз разход", type="primary"):
        open_expense_dialog()

with col_b2:
    if st.button("✈️ Ново пътуване"):
        open_trip_dialog()

st.divider()

# 7. ТАБЛО С ДАННИ
st.subheader("📊 Преглед")
tab1, tab2 = st.tabs(["✈️ Активни пътувания", "💸 Всички разходи"])

conn = sqlite3.connect("travel_manager.db")

with tab1:
    trips_data = pd.read_sql_query("SELECT id AS ID, name AS Име, start_date AS Дата, start_km AS 'Нач. KM' FROM trips WHERE status='Активно'", conn)
    if not trips_data.empty:
        st.dataframe(trips_data, use_container_width=True)
    else:
        st.info("Няма активни пътувания в момента.")

with tab2:
    expenses_data = pd.read_sql_query("""
        SELECT e.date AS Дата, COALESCE(t.name, 'Общ разход') AS Пътуване, e.description AS Описание, 
               e.amount AS Сума, e.liters AS Литри, e.odometer AS Километраж
        FROM expenses e
        LEFT JOIN trips t ON e.trip_id = t.id
        ORDER BY e.id DESC
    """, conn)
    if not expenses_data.empty:
        st.dataframe(expenses_data, use_container_width=True)
    else:
        st.info("Все още няма записани разходи.")

conn.close()
