import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

# 1. Конфигурация за широк десктоп изглед
st.set_page_config(
    page_title="PIXEL APP - Travel Manager",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ИНИЦИАЛИЗАЦИЯ НА ФАЙЛОВЕ И СЕСИЯ (ПЪЛНА ЛОГИКА)
# =========================================================

DATA_FILE = "expenses.csv"
SETTINGS_FILE = "settings.csv"
TRIP_PLAN_FILE = "trip_plans.csv"
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

# Управление на състоянието на навигацията
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Начална страница"

# =========================================================
# CSS СТИЛИЗИРАНЕ
# =========================================================

st.markdown("""
<style>
    .stAppViewContainer, .stApp { background-color: #0B0E14 !important; color: #E2E8F0 !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    section[data-testid="stSidebar"] { background-color: #121620 !important; border-right: 1px solid rgba(255, 255, 255, 0.05) !important; }
    
    .dark-card {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .kpi-card {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 14px 16px;
    }
    .kpi-val { font-size: 18px; font-weight: 700; color: #FFFFFF; }
    .kpi-lbl { font-size: 10px; color: #718096; text-transform: uppercase; font-weight: 600; }
    .status-tag { background: rgba(16, 185, 129, 0.15); color: #10B981; font-size: 11px; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    
    .stButton > button {
        border-radius: 10px !important;
        background-color: #1E2538 !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        width: 100%;
    }
    .stButton > button:hover { background-color: #2D3748 !important; color: #FFFFFF !important; }
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
# ДИАЛОЗИ ЗА БЪРЗИ ДЕЙСТВИЯ (РАБОТЕЩИ МOДАЛНИ ПРОЗОРЦИ)
# =========================================================

@st.dialog("➕ Добави нов разход")
def modal_add_expense(active_trip):
    with st.form("modal_exp_form"):
        amount = st.number_input("Сума (€)", min_value=0.01, step=1.0)
        category = st.selectbox("Категория", ["Храна и напитки", "Транспорт", "Настаняване", "Забавления", "Покупки", "Други"])
        description = st.text_input("Описание", placeholder="напр. Вечеря в ресторант")
        is_fuel = st.checkbox("Гориво ⛽")
        
        if st.form_submit_button("Запази разхода"):
            df_exp = load_data(DATA_FILE)
            new_id = hashlib.md5(f"{datetime.datetime.now()}_{amount}".encode()).hexdigest()[:8]
            new_row = pd.DataFrame([{
                "id": new_id, "trip_id": active_trip, "amount": amount,
                "category": category, "description": description, "is_fuel": is_fuel,
                "odometer": 0, "liters": 0.0, "full_tank": False,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }])
            save_data(pd.concat([df_exp, new_row], ignore_index=True), DATA_FILE)
            st.success("Разходът е добавен!")
            st.rerun()

@st.dialog("📝 Добави нова бележка")
def modal_add_note(active_trip):
    with st.form("modal_note_form"):
        note_text = st.text_area("Бележка")
        if st.form_submit_button("Запази бележката"):
            df_notes = load_data(NOTES_FILE)
            new_id = hashlib.md5(f"{datetime.datetime.now()}".encode()).hexdigest()[:8]
            new_row = pd.DataFrame([{
                "id": new_id, "trip_id": active_trip, "note": note_text,
                "date": datetime.datetime.now().strftime("%d %b")
            }])
            save_data(pd.concat([df_notes, new_row], ignore_index=True), NOTES_FILE)
            st.success("Бележката е запазена!")
            st.rerun()

# =========================================================
# SIDEBAR МЕНЮ С ФУНКЦИОНАЛНИ БУТОНИ
# =========================================================

settings_df = load_data(SETTINGS_FILE)
active_trips = settings_df[settings_df["is_finished"] == False]
active_trip_id = active_trips.iloc[0]["trip_id"] if not active_trips.empty else "Бургас"
current_budget = float(active_trips.iloc[0]["budget"]) if not active_trips.empty else 1200.0

with st.sidebar:
    st.markdown("### 🟨 **PIXEL APP**")
    st.caption("Travel Manager")
    st.write("")
    
    st.markdown("**Навигация**")
    pages = ["🏠 Начална страница", "🌴 Пътувания", "🗺️ Карта на пътуванията", "📊 Анализи", "⚙️ Настройки"]
    for page in pages:
        if st.button(page, key=f"nav_{page}"):
            st.session_state["current_page"] = page
            st.rerun()
            
    st.divider()
    
    st.markdown('<div class="kpi-lbl">АКТИВНО ПЪТУВАНЕ</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background: #181F2E; padding: 12px; border-radius: 10px; margin-top: 6px; border: 1px solid rgba(255,255,255,0.05);">
        <div style="font-weight: 700; font-size: 15px;">{active_trip_id}</div>
        <div style="font-size: 11px; color: #A0AEC0;">20 – 24 Авг 2025</div>
        <div style="margin-top: 6px;"><span class="status-tag">В ПРОЦЕС</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown('**Бързи действия**')
    if st.button("➕ Нов разход", key="btn_quick_add"):
        modal_add_expense(active_trip_id)
    if st.button("📝 Нова бележка", key="btn_quick_note"):
        modal_add_note(active_trip_id)

# =========================================================
# ДАННИ И ИЗЧИСЛЕНИЯ
# =========================================================

df_expenses = load_data(DATA_FILE)
trip_expenses = df_expenses[df_expenses["trip_id"] == active_trip_id]
total_spent = trip_expenses["amount"].sum() if not trip_expenses.empty else 0.0
remaining_budget = current_budget - total_spent

# =========================================================
# ОСНОВЕН ДАШБОРД (СПРЯМО ИЗБРАНАТА СТРАНИЦА)
# =========================================================

if st.session_state["current_page"] in ["🏠 Начална страница", "🌴 Пътувания"]:
    
    # Хедър с бутони за управление
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown(f"## 🌴 Дестинация: {active_trip_id}")
        st.markdown("<span style='color: #A0AEC0; font-size: 13px;'>🗓️ 20 – 24 Авг 2025 (4 дни) &nbsp;&nbsp;</span> <span class='status-tag'>В ПРОЦЕС</span>", unsafe_allow_html=True)

    with head_col2:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("➕ Разход", key="head_exp"): modal_add_expense(active_trip_id)
        with b2:
            if st.button("📝 Бележка", key="head_note"): modal_add_note(active_trip_id)

    st.write("")

    # KPI Показатели
    kpi_cols = st.columns(5)
    metrics = [
        ("ОБЩ БЮДЖЕТ", f"€{current_budget:.2f}"),
        ("ПОХАРЧЕНО ДО СЕГА", f"€{total_spent:.2f}"),
        ("ОСТАВАЩ БЮДЖЕТ", f"€{remaining_budget:.2f}"),
        ("ОСТАВАЩИ ДНИ", "2 дни"),
        ("СРЕДНО НА ДЕН", f"€{(total_spent/4 if total_spent>0 else 0):.2f}")
    ]

    for col, (title, val) in zip(kpi_cols, metrics):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-lbl">{title}</div>
                <div class="kpi-val">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # Грид с динамична информация
    col_left, col_mid, col_right = st.columns([1.1, 1.1, 1.3])

    with col_left:
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**РАЗПРЕДЕЛЕНИЕ ПО КАТЕГОРИИ**")
        if not trip_expenses.empty and "category" in trip_expenses.columns:
            cat_df = trip_expenses.groupby("category")["amount"].sum().reset_index()
            st.dataframe(cat_df, use_container_width=True, hide_index=True)
        else:
            st.info("Няма данни за категории все още.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**ПОСЛЕДНИ РАЗХОДИ**")
        if not trip_expenses.empty:
            for _, row in trip_expenses.tail(4).iterrows():
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <div><b>{row['description']}</b><br><small style="color:#718096">{row['date']}</small></div>
                    <div style="font-weight:700;">€{row['amount']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Няма последни разходи.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_mid:
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**ДНЕВЕН ПРОГРЕС**")
        if not trip_expenses.empty:
            st.bar_chart(trip_expenses.set_index("date")["amount"])
        else:
            st.caption("Графиката ще се покаже при въведени разходи.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**БЕЛЕЖКИ**")
        df_notes = load_data(NOTES_FILE)
        trip_notes = df_notes[df_notes["trip_id"] == active_trip_id] if not df_notes.empty else pd.DataFrame()
        if not trip_notes.empty:
            for _, n_row in trip_notes.iterrows():
                st.markdown(f"• **{n_row['date']}**: {n_row['note']}")
        else:
            st.caption("Няма добавени бележки.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="dark-card">', unsafe_allow_html=True)
        st.markdown("**КАРТА НА ПЪТУВАНЕТО**")
        m = folium.Map(location=[42.5042, 27.4626], zoom_start=11)
        st_folium(m, width="100%", height=380)
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state["current_page"] == "⚙️ Настройки":
    st.title("⚙️ Настройки")
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    new_b = st.number_input("Промени бюджет за активното пътуване (€)", value=current_budget)
    if st.button("💾 Запази промените"):
        settings_df.loc[settings_df["trip_id"] == active_trip_id, "budget"] = new_b
        save_data(settings_df, SETTINGS_FILE)
        st.success("Настройките са обновени!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.title(st.session_state["current_page"])
    st.info("Разделът е готов за въвеждане на допълнителни модули.")
