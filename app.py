import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Настройка на страницата
st.set_page_config(page_title="Pixelapp Travel Manager", page_icon="🚗", layout="centered")

# Инициализация и миграция на SQLite база данни
def init_db():
    conn = sqlite3.connect("travel_manager.db")
    c = conn.cursor()
    
    # 1. Създаване на таблица за пътувания
    c.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT,
            start_km REAL,
            status TEXT DEFAULT 'Активно'
        )
    """)
    
    # 2. Създаване на таблица за разходи
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
    
    # Автоматична миграция: проверка за trip_id, ако базата данни е от стара версия
    c.execute("PRAGMA table_info(expenses)")
    columns = [column[1] for column in c.fetchall()]
    if "trip_id" not in columns:
        c.execute("ALTER TABLE expenses ADD COLUMN trip_id INTEGER")
        
    conn.commit()
    conn.close()

init_db()

# Помощни функции за работа с базата данни
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

# CSS стилове
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.2rem;
        font-size: 1.1rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Заглавие на началната страница
st.markdown("<div class='main-title'>🚗 Pixelapp Travel Manager</div>", unsafe_allow_html=True)

# Бутони за основни действия на началния екран
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    show_expense_dialog = st.button("➕ Бърз разход", type="primary")

with col_btn2:
    show_trip_dialog = st.button("✈️ Ново пътуване")

st.divider()

# --- 1. СЕКЦИЯ: НОВО ПЪТУВАНЕ ---
if show_trip_dialog or st.session_state.get("adding_trip", False):
    st.session_state["adding_trip"] = True
    st.subheader("✈️ Започване на ново пътуване")
    
    with st.form("new_trip_form"):
        trip_name = st.text_input("Име на пътуването / Дестинация", placeholder="напр. София - Бургас")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            trip_date = st.date_input("Дата на тръгване", datetime.today())
        with col_t2:
            start_km = st.number_input("Начален километраж", min_value=0.0, step=1.0)
            
        submit_trip = st.form_submit_button("Запази пътуването")
        
        if submit_trip:
            if not trip_name.strip():
                st.error("Моля, въведете име на пътуването.")
            else:
                save_trip(trip_name, trip_date, start_km)
                st.success(f"Пътуването '{trip_name}' беше създадено успешно!")
                st.session_state["adding_trip"] = False
                st.rerun()

# --- 2. СЕКЦИЯ: БЪРЗ РАЗХОД ---
if show_expense_dialog or st.session_state.get("adding_expense", False):
    st.session_state["adding_expense"] = True
    st.subheader("➕ Бързо въвеждане на разход")
    
    # Зареждаме активните пътувания
    trips_df = get_active_trips()
    trip_options = {"Общ разход (без конкретно пътуване)": None}
    for _, row in trips_df.iterrows():
        trip_options[row["name"]] = row["id"]
        
    selected_trip_name = st.selectbox("Към кое пътуване е разходът?", list(trip_options.keys()))
    selected_trip_id = trip_options[selected_trip_name]
    
    description = st.text_input("Описание на разхода", placeholder="напр. Бензин Shell, Сандвичи, Тол такса")
    amount = st.number_input("Сума (лв.)", min_value=0.0, step=0.1, format="%.2f")
    
    # Проверка за ключови думи за гориво
    fuel_keywords = ["газ", "гориво", "зареждане", "бензин", "дизел", "shell", "omv", "lukoil", "rompetrol"]
    is_fuel = any(keyword in description.lower() for keyword in fuel_keywords)
    
    odometer = 0.0
    liters = 0.0
    full_tank = False
    
    if is_fuel:
        st.info("⛽ Открита е дума за гориво! Попълнете данните за зареждането:")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            odometer = st.number_input("Текущ километраж", min_value=0.0, step=1.0)
            liters = st.number_input("Заредени литри", min_value=0.0, step=0.1)
        with col_f2:
            full_tank = st.checkbox("Зареждане до горе (пълен резервоар)?")

    if st.button("Запази разхода", type="primary"):
        if amount <= 0:
            st.error("Моля, въведете валидна сума.")
        else:
            save_expense(
                trip_id=selected_trip_id,
                amount=amount,
                description=description,
                is_fuel=is_fuel,
                odometer=odometer,
                liters=liters,
                full_tank=full_tank
            )
            st.success("Разходът е записан успешно!")
            st.session_state["adding_expense"] = False
            st.rerun()

# --- 3. ПРЕГЛЕД НА ТАБЛИЦИТЕ С ДАННИ ---
st.subheader("📊 Преглед на данните")
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
