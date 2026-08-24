import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- НАСТРОЙКА НА СТРАНИЦАТА ---
st.set_page_config(
    page_title="Travel Manager", 
    page_icon="🚗", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- БАЗА ДАННИ (SQLite) ---
DB_NAME = "travel_manager.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Таблица за всички разходи (общи и гориво)
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            amount REAL,
            description TEXT,
            is_fuel INTEGER,
            odometer REAL,
            liters REAL,
            is_full_tank INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_expense(date, amount, description, is_fuel, odometer, liters, is_full_tank):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO expenses (date, amount, description, is_fuel, odometer, liters, is_full_tank)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date.strftime("%Y-%m-%d"), amount, description, 1 if is_fuel else 0, odometer, liters, 1 if is_full_tank else 0))
    conn.commit()
    conn.close()

def get_expenses():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()

# --- СТИЛИЗАЦИЯ И ДИЗАЙН ---
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0px;
    }
    .logo-sub {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    .quick-btn-container {
        display: flex;
        justify-content: center;
        margin-bottom: 30px;
    }
    .stButton>button {
        border-radius: 25px;
    }
    </style>
""", unsafe_unsafe_html=True)

# Инициализация на състоянието за активния изглед
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Начало"

# --- ЦЕНТРАЛНО ЛОГО И ЗАГЛАВИЕ ---
st.markdown("<div class='main-title'>🚗 TRAVEL MANAGER</div>", unsafe_allow_html=True)
st.markdown("<div class='logo-sub'>Следене на разходи, километри и зареждания</div>", unsafe_allow_html=True)

# --- ГЛАВНА НАВИГАЦИЯ ---
col_nav1, col_nav2, col_nav3 = st.columns([1, 1.2, 1])

with col_nav1:
    if st.button("🏠 Начало", use_container_width=True, type="primary" if st.session_state.active_tab == "Начало" else "secondary"):
        st.session_state.active_tab = "Начало"
        st.rerun()

with col_nav2:
    if st.button("➕ БЪРЗ РАЗХОД", use_container_width=True, type="primary" if st.session_state.active_tab == "Бърз разход" else "secondary"):
        st.session_state.active_tab = "Бърз разход"
        st.rerun()

with col_nav3:
    if st.button("🗺️ Пътувания & История", use_container_width=True, type="primary" if st.session_state.active_tab == "Пътувания" else "secondary"):
        st.session_state.active_tab = "Пътувания"
        st.rerun()

st.divider()

# ==========================================
# 1. ЕКРАН: БЪРЗ РАЗХОД (УМНА ФОРМА)
# ==========================================
if st.session_state.active_tab == "Бърз разход":
    st.subheader("⚡ Бързо въвеждане на разход")
    
    with st.container(border=True):
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            amount = st.number_input("Сума (лв.) *", min_value=0.01, step=1.0, value=20.0)
            date_val = st.date_input("Дата", datetime.today())
            
        with col_b:
            description = st.text_input("Описание *", placeholder="напр. Бензин OMV / Автомивка / Топ кафе...")
        
        # Детекция на ключови думи за гориво
        FUEL_KEYWORDS = ["газ", "гориво", "зареждане", "бензин", "дизел"]
        desc_lower = description.lower().strip()
        is_fuel_detected = any(keyword in desc_lower for keyword in FUEL_KEYWORDS)
        
        # Полета за гориво (показват се динамично при засичане на дума)
        odometer = 0.0
        liters = 0.0
        is_full_tank = False
        
        if is_fuel_detected:
            st.info("⛽ **Открито е зареждане с гориво!** Моля, попълнете данните за разхода:")
            
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                odometer = st.number_input("Текущ километраж (km)", min_value=0.0, step=10.0, help="Километражът на таблото")
            with f_col2:
                liters = st.number_input("Количество литри (L)", min_value=0.0, step=1.0, help="Заредени литри")
            with f_col3:
                st.write("")
                st.write("")
                is_full_tank = st.checkbox("Зареждане до горе", value=True)
                
        save_btn = st.button("💾 Запази разхода", type="primary", use_container_width=True)
        
        if save_btn:
            if not description:
                st.error("Моля, въведете описание!")
            else:
                save_expense(date_val, amount, description, is_fuel_detected, odometer, liters, is_full_tank)
                st.success("Разходът бе записан успешно!")
                st.balloons()

# ==========================================
# 2. ЕКРАН: НАЧАЛО (ТАБЛО)
# ==========================================
elif st.session_state.active_tab == "Начало":
    st.subheader("📊 Преглед и статистика")
    
    df = get_expenses()
    
    if df.empty:
        st.info("Все още нямате записани разходи. Натиснете бутона '**➕ БЪРЗ РАЗХОД**' по-горе, за да добавите първия!")
    else:
        # Метрики
        total_spent = df['amount'].sum()
        fuel_df = df[df['is_fuel'] == 1]
        total_fuel_spent = fuel_df['amount'].sum() if not fuel_df.empty else 0.0
        total_liters = fuel_df['liters'].sum() if not fuel_df.empty else 0.0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Общо изхарчени суми", f"{total_spent:.2f} лв.")
        m2.metric("Разход за гориво", f"{total_fuel_spent:.2f} лв.")
        m3.metric("Общо заредени литри", f"{total_liters:.1f} L")
        
        st.write("### 🕒 Последни 5 записа")
        st.dataframe(
            df[['date', 'description', 'amount', 'is_fuel', 'liters', 'odometer']].head(5), 
            use_container_width=True
        )

# ==========================================
# 3. ЕКРАН: ПЪТУВАНИЯ И ИСТОРИЯ
# ==========================================
elif st.session_state.active_tab == "Пътувания":
    st.subheader("🗺️ Пълна история на записите")
    
    df = get_expenses()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Няма налични данни.")
