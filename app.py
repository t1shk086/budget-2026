import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import io
import html
import streamlit.components.v1 as components

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

# =========================================================
# PIXELAPP MOBILE UI & DARK NEON STYLING
# =========================================================

st.markdown("""
<style>
    /* Главен заден фон и типография */
    .stAppViewContainer, .stApp {
        background: #0D0F17 !important;
        color: #E2E8F0 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Скриване на излишните Streamlit елементи */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Главни карти (Card Design) */
    .pixel-card {
        background: rgba(22, 27, 38, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Заглавна карта с градиент (Header Card) */
    .hero-card {
        background: linear-gradient(135deg, #6C5CE7 0%, #3B82F6 50%, #00CEC9 100%);
        border-radius: 20px;
        padding: 20px;
        color: #FFFFFF;
        box-shadow: 0 10px 25px rgba(108, 92, 231, 0.3);
        margin-bottom: 20px;
    }
    
    .hero-title {
        font-size: 24px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        font-size: 13px;
        opacity: 0.9;
        margin-top: 4px;
    }

    /* Индикаторни блокове (KPI Grid Cards) */
    .metric-box {
        background: #161B26;
        border-radius: 14px;
        padding: 14px;
        border-left: 4px solid #6C5CE7;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        margin-bottom: 10px;
    }
    .metric-box.green { border-left-color: #00B894; }
    .metric-box.orange { border-left-color: #FDCB6E; }
    .metric-box.red { border-left-color: #FF7675; }
    
    .metric-title {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #A0AEC0;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 20px;
        font-weight: 700;
        color: #FFFFFF;
    }

    /* Модернизация на бутоните */
    .stButton > button {
        border-radius: 12px !important;
        background: linear-gradient(135deg, #6C5CE7 0%, #5A49E0 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 12px 20px !important;
        box-shadow: 0 4px 14px rgba(108, 92, 231, 0.4) !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(108, 92, 231, 0.6) !important;
    }

    /* Форми и списъци */
    div[data-baseweb="select"] > div, input {
        background-color: #1E2330 !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #FFFFFF !important;
    }
    
    /* Табове (Tabs Styling) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161B26;
        padding: 6px;
        border-radius: 14px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #A0AEC0;
        font-weight: 600;
        padding: 8px 16px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #6C5CE7 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# Fullscreen бутон
components.html(
    """
    <style>
        #fullscreenBtn {
            position: fixed;
            top: 12px;
            right: 16px;
            z-index: 999999;
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: #FFFFFF;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            backdrop-filter: blur(5px);
        }
    </style>
    <button id="fullscreenBtn" onclick="toggleFS()">⛶</button>
    <script>
        function toggleFS() {
            var doc = window.parent.document;
            if (!doc.fullscreenElement) {
                doc.documentElement.requestFullscreen();
            } else {
                doc.exitFullscreen();
            }
        }
    </script>
    """,
    height=45,
)

# =========================================================
# ФАЙЛОВЕ И НАСТРОЙКИ (ПЪЛНА ЛОГИКА)
# =========================================================

DATA_FILE = "expenses.csv"
SETTINGS_FILE = "settings.csv"
MAP_FILE = "map_locations.csv"
TRIP_PLAN_FILE = "trip_plans.csv"
CATEGORY_BUDGETS_FILE = "category_budgets.csv"
UI_LABELS_FILE = "ui_labels.csv"

# Логика за зареждане/записване на данни
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "id" not in df.columns:
            df["id"] = [hashlib.md5(f"{r['date']}_{r['amount']}_{i}".encode()).hexdigest()[:8] for i, r in df.iterrows()]
            df.to_csv(DATA_FILE, index=False)
        return df
    return pd.DataFrame(columns=["id", "trip_id", "amount", "description", "is_fuel", "odometer", "liters", "full_tank", "date"])

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        return pd.read_csv(SETTINGS_FILE)
    return pd.DataFrame([{"trip_id": "Общ", "budget": 1000.0, "start_date": str(datetime.date.today()), "end_date": str(datetime.date.today() + datetime.timedelta(days=7)), "is_finished": False}])

def load_ui_labels():
    if os.path.exists(UI_LABELS_FILE):
        df = pd.read_csv(UI_LABELS_FILE)
        return dict(zip(df['key'], df['value']))
    return {"pet_label": "Домашен любимец", "accommodation_label": "Хотелски такси", "fuel_red_threshold": 1.80}

def get_active_trip_id():
    settings = load_settings()
    active = settings[settings["is_finished"] == False]
    if not active.empty:
        return active.iloc[0]["trip_id"]
    return "Общ"

# =========================================================
# МОБИЛЕН ХЕДЪР И КАРТИ ЗА ПРЕГЛЕД (UI VISUALS)
# =========================================================

active_trip = get_active_trip_id()
df_expenses = load_data()
trip_expenses = df_expenses[df_expenses["trip_id"] == active_trip]
total_spent = trip_expenses["amount"].sum() if not trip_expenses.empty else 0.0

settings_df = load_settings()
current_trip_row = settings_df[settings_df["trip_id"] == active_trip]
current_budget = float(current_trip_row.iloc[0]["budget"]) if not current_trip_row.empty else 1000.0
remaining = current_budget - total_spent

# Мобилен Герой-Карта (Hero Card)
st.markdown(f"""
<div class="hero-card">
    <div class="hero-subtitle">АКТИВНО ПЪТУВАНЕ</div>
    <div class="hero-title">📍 {active_trip}</div>
    <hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 12px 0;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 11px; opacity: 0.8;">ОСТАВАЩ БЮДЖЕТ</div>
            <div style="font-size: 22px; font-weight: 800;">{remaining:.2f} €</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 11px; opacity: 0.8;">ОБЩО РАЗХОДИ</div>
            <div style="font-size: 22px; font-weight: 800;">{total_spent:.2f} €</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Бързи KPI Индикатори
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="metric-box green">
        <div class="metric-title">💡 Бюджет</div>
        <div class="metric-value">{current_budget:.0f} €</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-box orange">
        <div class="metric-title">📊 Разход / ден</div>
        <div class="metric-value">{(total_spent/7):.1f} €</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# ТАБОВЕ НА НАВИГАЦИЯТА
# =========================================================

tab_expenses, tab_map, tab_admin = st.tabs(["💳 Разходи", "🗺️ Карта & План", "⚙️ Настройки"])

with tab_expenses:
    st.markdown('<div class="pixel-card">', unsafe_allow_html=True)
    st.subheader("Добави нов разход")
    
    with st.form("add_expense_form", clear_on_submit=True):
        amount = st.number_input("Сума (€)", min_value=0.01, step=1.0)
        description = st.text_input("Описание / Категория", placeholder="напр. Гориво, Вечеря, Хотел")
        is_fuel = st.checkbox("Е гориво ⛽")
        
        submitted = st.form_submit_button("➕ Запази разхода")
        if submitted:
            new_id = hashlib.md5(f"{datetime.datetime.now()}_{amount}".encode()).hexdigest()[:8]
            new_row = pd.DataFrame([{
                "id": new_id,
                "trip_id": active_trip,
                "amount": amount,
                "description": description,
                "is_fuel": is_fuel,
                "odometer": 0,
                "liters": 0.0,
                "full_tank": False,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }])
            df_updated = pd.concat([df_expenses, new_row], ignore_index=True)
            df_updated.to_csv(DATA_FILE, index=False)
            st.success("Разходът бе добавен успешно!")
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

    # Таблица с разходи
    st.subheader("Последни разходи")
    if not trip_expenses.empty:
        st.dataframe(
            trip_expenses[["date", "description", "amount"]].sort_values(by="date", ascending=False),
            use_container_width=True
        )
    else:
        st.info("Няма регистрирани разходи за това пътуване.")

with tab_map:
    st.markdown('<div class="pixel-card">', unsafe_allow_html=True)
    st.subheader("Маршрут и локации")
    # Карта Folium
    m = folium.Map(location=[42.6977, 23.3219], zoom_start=6)
    st_folium(m, width="100%", height=300)
    st.markdown('</div>', unsafe_allow_html=True)

with tab_admin:
    st.markdown('<div class="pixel-card">', unsafe_allow_html=True)
    st.subheader("Управление на пътуването")
    new_budget = st.number_input("Актуализирай бюджет (€)", value=current_budget)
    if st.button("💾 Запази бюджета"):
        settings_df.loc[settings_df["trip_id"] == active_trip, "budget"] = new_budget
        settings_df.to_csv(SETTINGS_FILE, index=False)
        st.success("Бюджетът бе обновен!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
