
import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

# ---------------------------------------------------------
# 1. СТРАНИЧНА КОНФИГУРАЦИЯ ЗА ДЕСКТОП ДАШБОРД
# ---------------------------------------------------------
st.set_page_config(
    page_title="PIXEL APP - Travel Manager",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. ФАЙЛОВА ЛОГИКА И ИНИЦИАЛИЗАЦИЯ (ОТ ТВОЯ КОД)
# ---------------------------------------------------------
DATA_FILE = "expenses.csv"
SETTINGS_FILE = "settings.csv"
NOTES_FILE = "notes.csv"

def init_files():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=["id", "trip_id", "amount", "description", "category", "is_fuel", "odometer", "liters", "full_tank", "date"]).to_csv(DATA_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame([{"trip_id": "Бургас", "budget": 1200.0, "start_date": "2025-08-20", "end_date": "2025-08-24", "is_finished": False}]).to_csv(SETTINGS_FILE, index=False)
    if not os.path.exists(NOTES_FILE):
        pd.DataFrame(columns=["id", "trip_id", "note", "date"]).to_csv(NOTES_FILE, index=False)

init_files()

def load_data(file_path):
    return pd.read_csv(file_path)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Състояние на навигацията
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Пътувания"

# ---------------------------------------------------------
# 3. ТОЧНИ ДАРК СТИЛОВЕ И CSS ДИЗАЙН (1:1 СЪС СНИМКАТА)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Основна тъмна тема */
    .stAppViewContainer, .stApp {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    
    /* Странично меню (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #121620 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Главни карти (Card Design) */
    .dark-card {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 16px;
    }

    /* Hero банер с покритие и прозрачни KPI панели върху него */
    .hero-banner {
        position: relative;
        background: linear-gradient(rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.6)), 
                    url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80');
        background-size: cover;
        background-position: center;
        border-radius: 16px;
        height: 190px;
        padding: 20px;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        margin-bottom: 16px;
    }

    .hero-glass-box {
        background: rgba(18, 22, 32, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 12px 18px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Малки KPI карти под банера */
    .kpi-card {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 12px 14px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .kpi-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }
    .kpi-title { font-size: 10px; color: #718096; text-transform: uppercase; font-weight: 700; }
    .kpi-value { font-size: 17px; font-weight: 700; color: #FFFFFF; }

    /* Зелен таг за статус "В ПРОЦЕС" */
    .status-tag {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }

    /* Модернизация на бутоните в Streamlit */
    .stButton > button {
        border-radius: 8px !important;
        background-color: #1A202C !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #2D3748 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. ДИАЛОЗИ ЗА БЪРЗИ ДЕЙСТВИЯ (МОДАЛНИ ПРОЗОРЦИ)
# ---------------------------------------------------------
@st.dialog("➕ Нов разход")
def modal_add_expense(trip_id):
    with st.form("form_add_exp"):
        amount = st.number_input("Сума (€)", min_value=0.01, step=1.0)
        category = st.selectbox("Категория", ["Храна и напитки", "Транспорт", "Настаняване", "Забавления", "Покупки", "Други"])
        description = st.text_input("Описание", placeholder="напр. Обяд в ресторант")
        is_fuel = st.checkbox("Е гориво ⛽")
        
        # Полета за гориво от твоя код
        odometer = st.number_input("Километраж (км)", min_value=0, value=0) if is_fuel else 0
        liters = st.number_input("Литри", min_value=0.0, value=0.0) if is_fuel else 0.0
        full_tank = st.checkbox("Пълен резервоар") if is_fuel else False

        if st.form_submit_button("Запази разхода"):
            df = load_data(DATA_FILE)
            new_id = hashlib.md5(f"{datetime.datetime.now()}_{amount}".encode()).hexdigest()[:8]
            new_row = pd.DataFrame([{
                "id": new_id, "trip_id": trip_id, "amount": amount,
                "category": category, "description": description, "is_fuel": is_fuel,
                "odometer": odometer, "liters": liters, "full_tank": full_tank,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }])
            save_data(pd.concat([df, new_row], ignore_index=True), DATA_FILE)
            st.success("Успешно добавен разход!")
            st.rerun()

@st.dialog("📝 Нова бележка")
def modal_add_note(trip_id):
    with st.form("form_add_note"):
        note_text = st.text_area("Съдържание на бележката")
        if st.form_submit_button("Запази бележка"):
            df = load_data(NOTES_FILE)
            new_id = hashlib.md5(f"{datetime.datetime.now()}".encode()).hexdigest()[:8]
            new_row = pd.DataFrame([{
                "id": new_id, "trip_id": trip_id, "note": note_text,
                "date": datetime.datetime.now().strftime("%d %b")
            }])
            save_data(pd.concat([df, new_row], ignore_index=True), NOTES_FILE)
            st.success("Бележката е запазена!")
            st.rerun()

# ---------------------------------------------------------
# 5. СТРАНИЧНО МЕНЮ (SIDEBAR) И АКТИВНО ПЪТУВАНЕ
# ---------------------------------------------------------
settings_df = load_data(SETTINGS_FILE)
active_trips = settings_df[settings_df["is_finished"] == False]
active_trip_id = active_trips.iloc[0]["trip_id"] if not active_trips.empty else "Бургас"
current_budget = float(active_trips.iloc[0]["budget"]) if not active_trips.empty else 1200.0

with st.sidebar:
    st.markdown("### 🟨 **PIXEL APP**")
    st.caption("Travel Manager")
    st.write("")
    
    st.markdown("**Навигация**")
    nav_items = [
        ("🏠 Начална страница", "Начална страница"),
        ("🌴 Пътувания", "Пътувания"),
        ("🗺️ Карта на пътуванията", "Карта"),
        ("📊 Анализи", "Анализи"),
        ("⚙️ Настройки", "Настройки")
    ]
    for label, key_val in nav_items:
        if st.button(label, key=f"nav_{key_val}"):
            st.session_state["current_page"] = key_val
            st.rerun()

    st.divider()

    # Карточка за активно пътуване в менюто
    st.markdown('<div class="kpi-title">АКТИВНО ПЪТУВАНЕ</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background: #181F2E; padding: 12px; border-radius: 10px; margin-top: 6px; border: 1px solid rgba(255,255,255,0.05);">
        <div style="font-weight: 700; font-size: 15px;">{active_trip_id}</div>
        <div style="font-size: 11px; color: #A0AEC0;">20 – 24 Авг 2025</div>
        <div style="margin-top: 6px;"><span class="status-tag">В ПРОЦЕС</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Работещи бутони за бързи действия
    st.markdown('**Бързи действия**')
    if st.button("➕ Нов разход", key="sb_quick_exp"): modal_add_expense(active_trip_id)
    if st.button("📝 Нова бележка", key="sb_quick_note"): modal_add_note(active_trip_id)

# ---------------------------------------------------------
# 6. ДАННИ И ИЗЧИСЛЕНИЯ
# ---------------------------------------------------------
df_expenses = load_data(DATA_FILE)
trip_expenses = df_expenses[df_expenses["trip_id"] == active_trip_id]
total_spent = trip_expenses["amount"].sum() if not trip_expenses.empty else 0.0
remaining_budget = current_budget - total_spent
pct_spent = int((total_spent / current_budget) * 100) if current_budget > 0 else 0

# ---------------------------------------------------------
# 7. ОСНОВЕН ДЕКСТОП ДАШБОРД (ИЗГЛЕД ОТ СНИМКАТА)
# ---------------------------------------------------------
if st.session_state["current_page"] in ["Пътувания", "Начална страница"]:

    # Хедер ред с бутони за управление
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown(f"## 🌴 Дестинация: {active_trip_id}")
        st.markdown("<span style='color: #A0AEC0; font-size: 13px;'>🗓️ 20 – 24 Авг 2025 (4 дни) &nbsp;&nbsp;</span> <span class='status-tag'>В ПРОЦЕС</span>", unsafe_allow_html=True)
    with h_col2:
        btn_c1, btn_c2, btn_c3 = st.columns(3)
        with btn_c1:
            if st.button("⬅️"): st.toast("Назад към пътуванията")
        with btn_c2:
            if st.button("✏️"): st.toast("Редакция на пътуването")
        with btn_c3:
            if st.button("🗑️"): st.toast("Изтрий пътуване")

    st.write("")

    # Hero Banner с прикрепени прозрачни елементи
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-glass-box">
            <div class="kpi-title">ОТЧЕТ ЗА ПЪТУВАНЕ</div>
            <div style="font-size: 22px; font-weight: 800; color: #FFF;">€{total_spent:,.0f} / €{current_budget:,.0f}</div>
            <div style="width: 200px; background: rgba(255,255,255,0.15); height: 6px; border-radius: 3px; margin-top: 8px;">
                <div style="width: {min(pct_spent, 100)}%; background: #10B981; height: 100%; border-radius: 3px;"></div>
            </div>
            <div style="font-size: 10px; color: #A0AEC0; text-align: right; margin-top: 2px;">{pct_spent}%</div>
        </div>
        <div class="hero-glass-box" style="text-align: right;">
            <div style="font-size: 20px; font-weight: 700;">☀️ 28°C</div>
            <div style="font-size: 11px; color: #CBD5E0;">Слънчево</div>
            <div style="font-size: 10px; color: #718096;">📍 {active_trip_id}, България</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Ред с 5 KPI карти под банера
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    kpi_data = [
        (kpi1, "ОБЩ БЮДЖЕТ", f"€{current_budget:,.2f}", "👛", "#2B6CB0"),
        (kpi2, "ПОХАРЧЕНО ДО СЕГА", f"€{total_spent:,.2f}", "💸", "#D69E2E"),
        (kpi3, "ОСТАВАЩ БЮДЖЕТ", f"€{remaining_budget:,.2f}", "🟣", "#805AD5"),
        (kpi4, "ОСТАВАЩИ ДНИ", "2 дни", "📅", "#DD6B20"),
        (kpi5, "СРЕДНО НА ДЕН", f"€{(total_spent/4 if total_spent>0 else 0):,.2f}", "📈", "#319795")
    ]

    for col, title, val, icon, color in kpi_data:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon" style="background: {color}22; color: {color};">{icon}</div>
                <div>
                    <div class="kpi-title">{title}</div>
                    <div class="kpi-value">{val}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # Ред от 3 основни колони с карти (Категории, Дневен прогрес, Карта)
    col_a, col_b, col_c = st.columns([1.1, 1.1, 1.3])

    with col_a:
        # Карта: Разпределение по категории
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**РАЗПРЕДЕЛЕНИЕ ПО КАТЕГОРИИ**")
        
        if not trip_expenses.empty and "category" in trip_expenses.columns:
            cat_df = trip_expenses.groupby("category")["amount"].sum().reset_index()
            for _, row in cat_df.iterrows():
                pct = (row['amount'] / total_spent * 100) if total_spent > 0 else 0
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <span style="font-size:13px;">🔹 {row['category']}</span>
                    <span style="font-size:13px; font-weight:600;">€{row['amount']:.2f} <small style="color:#718096">({pct:.1f}%)</small></span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Все още няма записани разходи по категории.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Карта: Последни разходи
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**ПОСЛЕДНИ РАЗХОДИ**")
        if not trip_expenses.empty:
            for _, row in trip_expenses.tail(4).iterrows():
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <div>
                        <div style="font-size:13px; font-weight:600;">{row['description']}</div>
                        <small style="color:#718096;">{row['date']}</small>
                    </div>
                    <div style="font-weight:700; font-size:14px;">€{row['amount']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Няма регистрирани разходи.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        # Карта: Дневен прогрес
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**ДНЕВЕН ПРОГРЕС**")
        if not trip_expenses.empty:
            st.bar_chart(trip_expenses.groupby("date")["amount"].sum())
        else:
            st.caption("Добавете разходи, за да видите дневната графика.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Карта: Бележки
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**БЕЛЕЖКИ**")
        df_notes = load_data(NOTES_FILE)
        trip_notes = df_notes[df_notes["trip_id"] == active_trip_id] if not df_notes.empty else pd.DataFrame()
        
        if not trip_notes.empty:
            for _, n in trip_notes.iterrows():
                st.markdown(f"""
                <div style="border-left: 3px solid #3182CE; padding-left: 10px; margin-bottom: 10px;">
                    <small style="color:#718096;">{n['date']}</small><br>
                    <span style="font-size:13px;">{n['note']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Няма добавени бележки за това пътуване.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_c:
        # Карта: Карта на пътуването
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**КАРТА НА ПЪТУВАНЕТО**")
        m = folium.Map(location=[42.5042, 27.4626], zoom_start=11)
        st_folium(m, width="100%", height=400)
        st.button("🗺️ Виж пълния маршрут")
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state["current_page"] == "Настройки":
    st.title("⚙️ Настройки")
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    new_budget = st.number_input("Бюджет за активно пътуване (€)", value=current_budget)
    if st.button("💾 Запази бюджета"):
        settings_df.loc[settings_df["trip_id"] == active_trip_id, "budget"] = new_budget
        save_data(settings_df, SETTINGS_FILE)
        st.success("Бюджетът е актуализиран успешно!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.title(st.session_state["current_page"])
    st.info("Модулът е активен и готов за работа.")
