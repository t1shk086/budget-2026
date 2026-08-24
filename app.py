import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

# 1. Настройка на страницата
st.set_page_config(page_title="Pixelapp Travel Manager", page_icon="🐾", layout="centered")

# 2. Инициализация и миграция на базата данни
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
            category TEXT DEFAULT 'Други',
            amount REAL,
            description TEXT,
            is_fuel INTEGER,
            odometer REAL,
            liters REAL,
            full_tank INTEGER,
            date TEXT
        )
    """)
    
    # Миграция: Проверка и добавяне на колона 'category', ако липсва
    c.execute("PRAGMA table_info(expenses)")
    columns = [column[1] for column in c.fetchall()]
    if "category" not in columns:
        c.execute("ALTER TABLE expenses ADD COLUMN category TEXT DEFAULT 'Други'")
            
    conn.commit()
    conn.close()

init_db()

CATEGORIES = [
    "⛽ Гориво",
    "🍔 Храна & Напитки",
    "🅿️ Тол такси & Паркинг",
    "🔧 Поддръжка & Части",
    "📦 Други"
]

# 3. Помощни функции
def get_active_trips():
    conn = sqlite3.connect("travel_manager.db")
    df = pd.read_sql_query("SELECT id, name FROM trips WHERE status = 'Активно'", conn)
    conn.close()
    return df

def save_trip(name, start_date, start_km):
    conn = sqlite3.connect("travel_manager.db")
    c = conn.cursor()
    c.execute("INSERT INTO trips (name, start_date, start_km) VALUES (?, ?, ?)", (name, str(start_date), start_km))
    conn.commit()
    conn.close()

def save_expense(trip_id, category, amount, description, is_fuel, odometer, liters, full_tank):
    conn = sqlite3.connect("travel_manager.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO expenses (trip_id, category, amount, description, is_fuel, odometer, liters, full_tank, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (trip_id, category, amount, description, int(is_fuel), odometer, liters, int(full_tank), datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

# 4. CSS Стилизиране
st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    .header-container {
        text-align: center;
        padding: 10px 0 20px 0;
    }
    .app-logo {
        font-size: 3.5rem;
        margin-bottom: 5px;
    }
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 400;
    }

    /* Бутони */
    div.stButton > button {
        border-radius: 14px !important;
        height: 3.6rem !important;
        font-weight: 700 !important;
        font-size: 0.98rem !important;
        transition: all 0.2s ease-in-out !important;
        border: 1px solid #334155 !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    div.stButton > button:hover {
        background-color: #334155 !important;
        transform: translateY(-2px);
    }
    
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
    }

    /* Карти със статистика */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 4px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 5. ИЗСКАЧАЩИ ПРОЗОРЦИ
@st.dialog("✈️ Ново пътуване")
def open_trip_dialog():
    with st.form("dialog_trip_form", clear_on_submit=True):
        trip_name = st.text_input("Дестинация / Име", placeholder="напр. София - Бургас")
        col1, col2 = st.columns(2)
        with col1:
            trip_date = st.date_input("Дата", datetime.today())
        with col2:
            start_km = st.number_input("Начален километраж", min_value=0.0, step=1.0)
            
        submit = st.form_submit_button("Запази", type="primary")
        if submit:
            if not trip_name.strip():
                st.error("Моля, въведете име.")
            else:
                save_trip(trip_name, trip_date, start_km)
                st.success("Пътуването е добавено!")
                st.rerun()

@st.dialog("➕ Добави разход")
def open_expense_dialog():
    trips_df = get_active_trips()
    trip_options = {"Общ разход (без пътуване)": None}
    for _, row in trips_df.iterrows():
        trip_options[row["name"]] = row["id"]
        
    selected_trip_name = st.selectbox("Към кое пътуване?", list(trip_options.keys()))
    selected_trip_id = trip_options[selected_trip_name]
    
    category = st.selectbox("Категория", CATEGORIES)
    description = st.text_input("Описание", placeholder="напр. Shell, Кафе, Винетка")
    amount = st.number_input("Сума (лв.)", min_value=0.0, step=0.1, format="%.2f")
    
    is_fuel = (category == "⛽ Гориво")
    
    odometer = 0.0
    liters = 0.0
    full_tank = False
    
    if is_fuel:
        st.info("⛽ Данни за зареждането:")
        col1, col2 = st.columns(2)
        with col1:
            odometer = st.number_input("Километраж", min_value=0.0, step=1.0)
            liters = st.number_input("Литри", min_value=0.0, step=0.1)
        with col2:
            full_tank = st.checkbox("Зареждане до горе?")

    if st.button("Запази разхода", type="primary"):
        if amount <= 0:
            st.error("Моля, въведете сума.")
        else:
            save_expense(selected_trip_id, category, amount, description, is_fuel, odometer, liters, full_tank)
            st.success("Записано!")
            st.rerun()

# 6. ХЕДЪР
st.markdown("""
    <div class='header-container'>
        <div class='app-logo'>🐶</div>
        <div class='main-title'>Pixelapp Travel</div>
        <div class='sub-title'>Пробег & Разходи за пътуване</div>
    </div>
""", unsafe_allow_html=True)

# 7. НАВИГАЦИЯ С ТРИ БУТОНА
col_nav1, col_nav2, col_nav3 = st.columns([1, 1.2, 1])

with col_nav1:
    if st.button("🏠 Начало"):
        st.rerun()

with col_nav2:
    if st.button("➕ Бърз разход", type="primary"):
        open_expense_dialog()

with col_nav3:
    if st.button("✈️ Пътуване"):
        open_trip_dialog()

st.markdown("<br>", unsafe_allow_html=True)

# 8. БЪРЗА СТАТИСТИКА
conn = sqlite3.connect("travel_manager.db")

expenses_df = pd.read_sql_query("SELECT amount, liters FROM expenses", conn)
total_sum = expenses_df["amount"].sum() if not expenses_df.empty else 0.0
total_liters = expenses_df["liters"].sum() if not expenses_df.empty else 0.0

m1, m2 = st.columns(2)
with m1:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Общо изхарчени</div>
            <div class='metric-value'>{total_sum:.2f} лв.</div>
        </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>Заредено гориво</div>
            <div class='metric-value'>{total_liters:.1f} L</div>
        </div>
    """, unsafe_allow_html=True)

# 9. ТАБЛИЦИ И ДИАГРАМИ
tab1, tab2, tab3 = st.tabs(["📊 Сравнение", "📋 Всички разходи", "✈️ Пътувания"])

with tab1:
    cat_df = pd.read_sql_query("SELECT category AS Категория, SUM(amount) AS Сума FROM expenses GROUP BY category", conn)
    if not cat_df.empty and cat_df["Сума"].sum() > 0:
        fig = px.pie(
            cat_df, 
            values="Сума", 
            names="Категория", 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Няма данни за показване на диаграма.")

with tab2:
    expenses_data = pd.read_sql_query("""
        SELECT e.date AS Дата, e.category AS Категория, COALESCE(t.name, 'Общ разход') AS Пътуване, 
               e.description AS Описание, e.amount AS 'Сума (лв.)', e.liters AS Литри
        FROM expenses e
        LEFT JOIN trips t ON e.trip_id = t.id
        ORDER BY e.id DESC
    """, conn)
    if not expenses_data.empty:
        st.dataframe(expenses_data, use_container_width=True, hide_index=True)
    else:
        st.info("Все още няма записани разходи.")

with tab3:
    trips_data = pd.read_sql_query("SELECT name AS Име, start_date AS Дата, start_km AS 'Нач. KM' FROM trips WHERE status='Активно'", conn)
    if not trips_data.empty:
        st.dataframe(trips_data, use_container_width=True, hide_index=True)
    else:
        st.info("Няма активни пътувания.")

conn.close()
