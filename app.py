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

# =========================================================
# 1. СТРАНИЧНА КОНФИГУРАЦИЯ ЗА ДЕСКТОП ДАШБОРД
# =========================================================
st.set_page_config(
    page_title="PIXEL APP - Travel Manager",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. ИНИЦИАЛИЗАЦИЯ И ЛОГИКА ЗА ДАННИ (ТОЧНО ОТ ТВОЯ КОД)
# =========================================================
DATA_FILE = "expenses.csv"
SETTINGS_FILE = "settings.csv"
MAP_FILE = "map_locations.csv"
TRIP_PLAN_FILE = "trip_plans.csv"
CATEGORY_BUDGETS_FILE = "category_budgets.csv"
UI_LABELS_FILE = "ui_labels.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "id" not in df.columns:
            df["id"] = [hashlib.md5(f"{r['date']}_{r['amount']}_{i}".encode()).hexdigest()[:8] for i, r in df.iterrows()]
            df.to_csv(DATA_FILE, index=False)
        return df
    return pd.DataFrame(columns=["id", "trip_id", "amount", "description", "category", "is_fuel", "odometer", "liters", "full_tank", "date"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        return pd.read_csv(SETTINGS_FILE)
    return pd.DataFrame([{"trip_id": "Бургас", "budget": 1200.0, "start_date": str(datetime.date.today()), "end_date": str(datetime.date.today() + datetime.timedelta(days=4)), "is_finished": False}])

def save_settings(df):
    df.to_csv(SETTINGS_FILE, index=False)

def get_active_trip_id():
    settings = load_settings()
    active = settings[settings["is_finished"] == False]
    if not active.empty:
        return active.iloc[0]["trip_id"]
    return "Бургас"

# Твоята специфична логика за изчисление на среден разход на гориво
def calculate_fuel_stats(df, trip_id):
    trip_df = df[(df["trip_id"] == trip_id) & (df["is_fuel"] == True)].sort_values(by="odometer")
    if len(trip_df) < 2:
        return None, 0, 0
    
    total_liters = trip_df["liters"].sum()
    min_odo = trip_df["odometer"].min()
    max_odo = trip_df["odometer"].max()
    total_km = max_odo - min_odo
    
    if total_km > 0:
        avg_consumption = (total_liters / total_km) * 100
        return avg_consumption, total_km, total_liters
    return None, 0, total_liters

# =========================================================
# 3. ТОЧНИ ДАРК СТИЛОВЕ И CSS ДИЗАЙН (1:1 СЪС СНИМКАТА)
# =========================================================
st.markdown("""
<style>
    /* Основен заден фон */
    .stAppViewContainer, .stApp {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    
    /* Sidebar меню */
    section[data-testid="stSidebar"] {
        background-color: #121620 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Картови елементи */
    .dark-card {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 16px;
    }

    /* Hero банер */
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

    /* KPI карти под банера */
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

    .status-tag {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }

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

# Fullscreen бутон
components.html("""
    <button id="fullscreenBtn" onclick="toggleFS()" style="position: fixed; top: 14px; right: 20px; z-index: 999999; width: 34px; height: 34px; border: none; border-radius: 8px; background: rgba(255, 255, 255, 0.08); color: #E2E8F0; cursor: pointer;">⛶</button>
    <script>
        function toggleFS() {
            var doc = window.parent.document;
            if (!doc.fullscreenElement) { doc.documentElement.requestFullscreen(); } 
            else { doc.exitFullscreen(); }
        }
    </script>
""", height=40)

# =========================================================
# 4. ДИАЛОЗИ ЗА ТВОИТЕ ФОРМИ (РАБОТЕЩИ МOДАЛНИ ПРОЗОРЦИ)
# =========================================================
@st.dialog("➕ Нов разход")
def modal_add_expense(active_trip):
    st.write(f"Добавяне на разход към **{active_trip}**")
    with st.form("modal_add_exp_form"):
        amount = st.number_input("Сума (€)", min_value=0.01, step=0.50)
        category = st.selectbox("Категория", ["Храна и напитки", "Транспорт", "Настаняване", "Забавления", "Покупки", "Други"])
        description = st.text_input("Описание", placeholder="напр. Ресторант, Гориво, Хотел")
        is_fuel = st.checkbox("Е гориво ⛽")
        
        # Разширени полета за гориво от твоя оригинал
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            odometer = st.number_input("Километраж (км)", min_value=0, value=0) if is_fuel else 0
        with col_f2:
            liters = st.number_input("Литри", min_value=0.0, value=0.0, step=0.1) if is_fuel else 0.0
        full_tank = st.checkbox("Пълен резервоар") if is_fuel else False

        if st.form_submit_button("Запази разхода"):
            df = load_data()
            new_id = hashlib.md5(f"{datetime.datetime.now()}_{amount}".encode()).hexdigest()[:8]
            new_row = pd.DataFrame([{
                "id": new_id,
                "trip_id": active_trip,
                "amount": amount,
                "category": category,
                "description": description,
                "is_fuel": is_fuel,
                "odometer": odometer,
                "liters": liters,
                "full_tank": full_tank,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }])
            save_data(pd.concat([df, new_row], ignore_index=True))
            st.success("Успешно добавен разход!")
            st.rerun()

# =========================================================
# 5. СТРАНИЧНО МЕНЮ (SIDEBAR) И УПРАВЛЕНИЕ НА СЕСИЯТА
# =========================================================
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Пътувания"

active_trip_id = get_active_trip_id()
settings_df = load_settings()
current_trip_row = settings_df[settings_df["trip_id"] == active_trip_id]
current_budget = float(current_trip_row.iloc[0]["budget"]) if not current_trip_row.empty else 1200.0

with st.sidebar:
    st.markdown("### 🟨 **PIXEL APP**")
    st.caption("Travel Manager")
    st.write("")
    
    st.markdown("**Навигация**")
    pages = [
        ("🏠 Начална страница", "Начална страница"),
        ("🌴 Пътувания", "Пътувания"),
        ("🗺️ Карта на пътуванията", "Карта"),
        ("📊 Анализи", "Анализи"),
        ("⚙️ Настройки", "Настройки")
    ]
    for label, p_key in pages:
        if st.button(label, key=f"sb_{p_key}"):
            st.session_state["nav_page"] = p_key
            st.rerun()

    st.divider()

    st.markdown('<div class="kpi-title">АКТИВНО ПЪТУВАНЕ</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background: #181F2E; padding: 12px; border-radius: 10px; margin-top: 6px; border: 1px solid rgba(255,255,255,0.05);">
        <div style="font-weight: 700; font-size: 15px;">{active_trip_id}</div>
        <div style="font-size: 11px; color: #A0AEC0;">20 – 24 Авг 2025</div>
        <div style="margin-top: 6px;"><span class="status-tag">В ПРОЦЕС</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown('**Бързи действия**')
    if st.button("➕ Нов разход", key="quick_exp_btn"):
        modal_add_expense(active_trip_id)

# =========================================================
# 6. ДАННИ И ТВОИ ИЗЧИСЛЕНИЯ
# =========================================================
df_expenses = load_data()
trip_expenses = df_expenses[df_expenses["trip_id"] == active_trip_id]
total_spent = trip_expenses["amount"].sum() if not trip_expenses.empty else 0.0
remaining_budget = current_budget - total_spent
pct_spent = int((total_spent / current_budget) * 100) if current_budget > 0 else 0

avg_cons, total_km, total_liters = calculate_fuel_stats(df_expenses, active_trip_id)

# =========================================================
# 7. ДЕСКТОП ДАШБОРД (ИЗГЛЕД ОТ СНИМКАТА С ТВОЯТА ЛОГИКА)
# =========================================================
if st.session_state["nav_page"] in ["Пътувания", "Начална страница"]:

    # Хедер с функционални бутони
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown(f"## 🌴 Дестинация: {active_trip_id}")
        st.markdown("<span style='color: #A0AEC0; font-size: 13px;'>🗓️ 20 – 24 Авг 2025 (4 дни) &nbsp;&nbsp;</span> <span class='status-tag'>В ПРОЦЕС</span>", unsafe_allow_html=True)
    with h_col2:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("➕ Разход"): modal_add_expense(active_trip_id)
        with b2:
            if st.button("🔄 Обнови"): st.rerun()

    st.write("")

    # Hero Banner с реалните ти пресметнати суми
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-glass-box">
            <div class="kpi-title">ОТЧЕТ ЗА ПЪТУВАНЕ</div>
            <div style="font-size: 22px; font-weight: 800; color: #FFF;">€{total_spent:,.2f} / €{current_budget:,.2f}</div>
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

    # 5-те KPI показателя под банера
    k1, k2, k3, k4, k5 = st.columns(5)
    
    fuel_label = f"{avg_cons:.1f} л/100км" if avg_cons else "Няма данни"
    
    kpi_items = [
        (k1, "ОБЩ БЮДЖЕТ", f"€{current_budget:,.2f}", "👛", "#2B6CB0"),
        (k2, "ПОХАРЧЕНО ДО СЕГА", f"€{total_spent:,.2f}", "💸", "#D69E2E"),
        (k3, "ОСТАВАЩ БЮДЖЕТ", f"€{remaining_budget:,.2f}", "🟣", "#805AD5"),
        (k4, "СРЕДЕН РАЗХОД ГOРИВО", fuel_label, "⛽", "#DD6B20"),
        (k5, "СРЕДНО НА ДЕН", f"€{(total_spent/4 if total_spent>0 else 0):,.2f}", "📈", "#319795")
    ]

    for col, title, val, icon, color in kpi_items:
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

    # Грид от 3 колони (Разпределения, Дневен прогрес, Карта)
    col_left, col_mid, col_right = st.columns([1.1, 1.1, 1.3])

    with col_left:
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**РАЗПРЕДЕЛЕНИЕ ПО КАТЕГОРИИ**")
        
        if not trip_expenses.empty and "category" in trip_expenses.columns:
            cat_summary = trip_expenses.groupby("category")["amount"].sum().reset_index()
            for _, r in cat_summary.iterrows():
                pct = (r['amount'] / total_spent * 100) if total_spent > 0 else 0
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <span style="font-size:13px;">🔹 {r['category']}</span>
                    <span style="font-size:13px; font-weight:600;">€{r['amount']:.2f} <small style="color:#718096">({pct:.1f}%)</small></span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Няма данни за категории все още.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**ПОСЛЕДНИ РАЗХОДИ (ТВОЯТА ТАБЛИЦА)**")
        if not trip_expenses.empty:
            # Показване с възможност за изтриване от твоя код
            for idx, row in trip_expenses.tail(5).iterrows():
                c_desc, c_del = st.columns([4, 1])
                with c_desc:
                    st.markdown(f"**{row['description']}** — €{row['amount']:.2f}<br><small style='color:#718096;'>{row['date']}</small>", unsafe_allow_html=True)
                with c_del:
                    if st.button("🗑️", key=f"del_{row['id']}"):
                        df_expenses = df_expenses[df_expenses["id"] != row["id"]]
                        save_data(df_expenses)
                        st.rerun()
        else:
            st.caption("Няма регистрирани разходи.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_mid:
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**ДНЕВЕН ПРОГРЕС**")
        if not trip_expenses.empty:
            st.bar_chart(trip_expenses.groupby("date")["amount"].sum())
        else:
            st.caption("Графиката се актуализира при въведени разходи.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**КАРТА НА ПЪТУВАНЕТО (FOLIUM)**")
        m = folium.Map(location=[42.5042, 27.4626], zoom_start=11)
        st_folium(m, width="100%", height=380)
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state["nav_page"] == "Настройки":
    st.title("⚙️ Настройки на пътуването")
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    new_b = st.number_input("Бюджет за активно пътуване (€)", value=current_budget)
    if st.button("💾 Запази бюджета"):
        settings_df.loc[settings_df["trip_id"] == active_trip_id, "budget"] = new_b
        save_settings(settings_df)
        st.success("Бюджетът е запазен!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
