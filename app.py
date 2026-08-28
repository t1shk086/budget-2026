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
# DESKTOP DARK THEME & DASHBOARD STYLING
# =========================================================

st.markdown("""
<style>
    /* Главен заден фон */
    .stAppViewContainer, .stApp {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Скриване на стандартния Streamlit хедър */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Настройки за Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #121620 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding-top: 10px;
    }

    /* Главни карти (Card Elements) */
    .dark-card {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 16px;
    }

    /* Hero банер с изображение за дестинацията */
    .hero-banner {
        position: relative;
        background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.7)), 
                    url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80');
        background-size: cover;
        background-position: center;
        border-radius: 16px;
        height: 180px;
        padding: 20px;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        margin-bottom: 20px;
    }

    .hero-overlay-card {
        background: rgba(18, 22, 32, 0.85);
        backdrop-filter: blur(8px);
        border-radius: 12px;
        padding: 12px 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* KPI Иконни карти (Карти за бюджети и километри) */
    .kpi-card {
        background: #121620;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .kpi-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }

    .kpi-val {
        font-size: 18px;
        font-weight: 700;
        color: #FFFFFF;
        margin-top: 2px;
    }

    .kpi-lbl {
        font-size: 10px;
        color: #718096;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* Стил на списъци с последни разходи */
    .expense-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    
    .expense-item:last-child {
        border-bottom: none;
    }

    /* Зелен статус таг */
    .status-tag {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }

    /* Бутони */
    .stButton > button {
        border-radius: 10px !important;
        background-color: #1E2538 !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        font-weight: 500 !important;
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
components.html(
    """
    <style>
        #fullscreenBtn {
            position: fixed;
            top: 14px;
            right: 20px;
            z-index: 999999;
            width: 34px;
            height: 34px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.08);
            color: #E2E8F0;
            font-size: 16px;
            cursor: pointer;
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
    height=40,
)

# =========================================================
# SIDEBAR (СТРАНИЧНО МЕНЮ И АКТИВНО ПЪТУВАНЕ)
# =========================================================

with st.sidebar:
    st.markdown("### 🟨 **PIXEL APP**")
    st.caption("Travel Manager")
    st.write("")
    
    # Главна навигация
    st.markdown("**Навигация**")
    st.button("🏠 Начална страница")
    st.button("🌴 Пътувания")
    st.button("🗺️ Карта на пътуванията")
    st.button("📊 Анализи")
    st.button("⚙️ Настройки")
    
    st.divider()
    
    # Активно пътуване карта
    st.markdown('<div class="kpi-lbl">АКТИВНО ПЪТУВАНЕ</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: #181F2E; padding: 12px; border-radius: 10px; margin-top: 6px; border: 1px solid rgba(255,255,255,0.05);">
        <div style="font-weight: 700; font-size: 15px;">Бургас</div>
        <div style="font-size: 11px; color: #A0AEC0;">20 – 24 Авг 2025</div>
        <div style="margin-top: 6px;"><span class="status-tag">В ПРОЦЕС</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Бързи действия
    st.markdown('**Бързи действия**')
    if st.button("➕ Нов разход"):
        st.toast("Отворен диалог за нов разход")
    st.button("📝 Нова бележка")
    st.button("📤 Качване на файл")
    st.button("📊 Експорт на отчет")

# =========================================================
# MAIN DASHBOARD CONTENT (ГЛАВНА ИНФОРМАЦИОННА ЧАСТ)
# =========================================================

# Горен заглавен ред
head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.markdown("## 🌴 Дестинация: Бургас")
    st.markdown("<span style='color: #A0AEC0; font-size: 13px;'>🗓️ 20 – 24 Авг 2025 (4 дни) &nbsp;&nbsp;</span> <span class='status-tag'>В ПРОЦЕС</span>", unsafe_allow_html=True)

with head_col2:
    b1, b2, b3 = st.columns(3)
    with b1: st.button("⬅️")
    with b2: st.button("✏️")
    with b3: st.button("🗑️")

st.write("")

# 1. HERO BANNER С ОПИСАНИЕ И ПРОГНОЗА ЗА ВРЕМЕТО
st.markdown("""
<div class="hero-banner">
    <div class="hero-overlay-card">
        <div class="kpi-lbl">ОТЧЕТ ЗА ПЪТУВАНЕ</div>
        <div style="font-size: 22px; font-weight: 800; color: #FFF;">€856 / €1,200</div>
        <div style="width: 180px; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; margin-top: 6px;">
            <div style="width: 71%; background: #10B981; height: 100%; border-radius: 3px;"></div>
        </div>
    </div>
    <div class="hero-overlay-card" style="text-align: right;">
        <div style="font-size: 20px; font-weight: 700;">☀️ 28°C</div>
        <div style="font-size: 11px; color: #CBD5E0;">Слънчево</div>
        <div style="font-size: 10px; color: #718096;">📍 Бургас, България</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. KPI ПОЛЕТА В ЕДИН РЕД (5 Колони)
kpi_cols = st.columns(5)
metrics = [
    ("ОБЩ БЮДЖЕТ", "€1,200.00", "👛", "#2B6CB0"),
    ("ПОХАРЧЕНО ДО СЕГА", "€856.00", "💸", "#D69E2E"),
    ("ОСТАВАЩ БЮДЖЕТ", "€344.00", "🟣", "#805AD5"),
    ("ОСТАВАЩИ ДНИ", "2 дни", "📅", "#DD6B20"),
    ("СРЕДНО НА ДЕН", "€214.00", "📈", "#319795")
]

for col, (title, val, icon, color) in zip(kpi_cols, metrics):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background: {color}22; color: {color};">{icon}</div>
            <div>
                <div class="kpi-lbl">{title}</div>
                <div class="kpi-val">{val}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# 3. ОСНОВНА ГРИД СТРУКТУРА (3 Колони)
main_col1, main_col2, main_col3 = st.columns([1.1, 1.1, 1.3])

with main_col1:
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    st.markdown("**РАЗПРЕДЕЛЕНИЕ ПО КАТЕГОРИИ**")
    
    # Симулирана кръгова диаграма/данни
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-size: 24px; font-weight: 800;">€856</div>
        <div style="font-size: 11px; color: #718096;">общо</div>
    </div>
    <div class="expense-item"><span style="color:#10B981;">🟢 Храна и напитки</span> <span>€256 (29.9%)</span></div>
    <div class="expense-item"><span style="color:#3182CE;">🔵 Транспорт</span> <span>€190 (22.2%)</span></div>
    <div class="expense-item"><span style="color:#805AD5;">🟣 Настаняване</span> <span>€180 (21.0%)</span></div>
    <div class="expense-item"><span style="color:#DD6B20;">🟠 Забавления</span> <span>€120 (14.0%)</span></div>
    <div class="expense-item"><span style="color:#D69E2E;">🟡 Покупки</span> <span>€70 (8.2%)</span></div>
    <div class="expense-item"><span style="color:#718096;">⚪ Други</span> <span>€40 (4.7%)</span></div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Последни разходи
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    st.markdown("**ПОСЛЕДНИ РАЗХОДИ**")
    st.markdown("""
    <div class="expense-item">
        <div>🍴 <b>Обяд в ресторант</b><br><small style="color:#718096">22 Авг 2025 14:30</small></div>
        <div style="font-weight:700;">€32.50</div>
    </div>
    <div class="expense-item">
        <div>🚕 <b>Такси до плажа</b><br><small style="color:#718096">22 Авг 2025 11:15</small></div>
        <div style="font-weight:700;">€12.00</div>
    </div>
    <div class="expense-item">
        <div>☕ <b>Кафе и закуска</b><br><small style="color:#718096">22 Авг 2025 09:00</small></div>
        <div style="font-weight:700;">€8.90</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with main_col2:
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    st.markdown("**ДНЕВЕН ПРОГРЕС**")
    st.caption("Реални разходи спрямо план по дни")
    # Място за стълбова графика (Bar chart)
    st.bar_chart({"20 Авг": 120, "21 Авг": 210, "22 Авг": 280, "23 Авг": 160, "24 Авг": 86})
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Бележки
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    st.markdown("**БЕЛЕЖКИ**")
    st.markdown("""
    <div style="border-left: 3px solid #D69E2E; padding-left: 10px; margin-bottom: 10px;">
        <small style="color:#718096">20 Авг</small><br>Резервирах маса за вечеря на 23.08 в 20:00
    </div>
    <div style="border-left: 3px solid #3182CE; padding-left: 10px; margin-bottom: 10px;">
        <small style="color:#718096">21 Авг</small><br>Посещение на остров Св. Анастасия 24.08 сутринта
    </div>
    <div style="border-left: 3px solid #10B981; padding-left: 10px;">
        <small style="color:#718096">21 Авг</small><br>Проверка за концерт на 22.08
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with main_col3:
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    st.markdown("**КАРТА НА ПЪТУВАНЕТО**")
    m = folium.Map(location=[42.5042, 27.4626], zoom_start=11)
    st_folium(m, width="100%", height=440)
    st.button("🗺️ Виж маршрута")
    st.markdown('</div>', unsafe_allow_html=True)
