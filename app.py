import streamlit as st
import pandas as pd
import datetime
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import io
import html
import streamlit.components.v1 as components

# Настройка на страницата
st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

# CSS стилове за персонализиран тъмен интерфейс и компоненти
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #090b0e 0%, #11151c 50%, #0d1117 100%) !important;
        background-attachment: fixed !important;
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.15) !important;
        z-index: -1;
        pointer-events: none;
    }
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader, div.stDateInput {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important; 
        padding: 10px 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        backdrop-filter: blur(4px) !important;
        margin-bottom: 15px !important;
    }
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #252932, #16191f) !important; 
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; 
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
        transition: all 0.25s ease !important; 
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        width: 100% !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #2e343f, #1c2028) !important;
        transform: translateY(-1px) !important; 
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.15) !important;
        border-color: rgba(0, 242, 254, 0.2) !important;
    }
    small { color: #7e8494 !important; }

    /* Единен шрифт за целия интерфейс */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: "Segoe UI", Roboto, sans-serif !important;
    }

    /* Финална визия на картите: една карта = един бутон, текстът вляво. */
    div[class*="st-key-trip_card_"] { position:relative; margin-bottom:8px; }
    div[class*="st-key-trip_card_"] .tm-trip-card-visual {
        box-sizing:border-box; min-height:108px; padding:13px 16px 13px;
        border-radius:16px; border:1px solid rgba(255,255,255,.08);
        background:linear-gradient(135deg,rgba(255,255,255,.035),rgba(255,255,255,.012));
        box-shadow:4px 4px 12px rgba(0,0,0,.24); color:#fff; text-align:left;
    }
    div[class*="st-key-trip_card_"] .tm-trip-card-title {
        display:flex; align-items:center; justify-content:space-between; width:100%;
        font-size:14px; line-height:1.35; font-weight:800; text-align:left;
    }
    div[class*="st-key-trip_card_"] .tm-trip-arrow { margin-left:auto; padding-left:10px; opacity:.85; }
    div[class*="st-key-trip_card_"] .tm-trip-card-status {
        margin-top:3px; font-size:12px; line-height:1.3; font-weight:700; text-align:left;
    }
    div[class*="st-key-trip_card_"] .tm-trip-card-budget { margin-top:7px; }
    div[class*="st-key-trip_card_"] .tm-trip-card-budget-text {
        margin-bottom:4px; font-size:11px; line-height:1.25; font-weight:800;
        color:rgba(255,255,255,.88); text-align:left;
    }
    div[class*="st-key-trip_card_"] .tm-trip-card-budget-track {
        width:100%; height:12px; padding:2px; box-sizing:border-box; overflow:hidden;
        border-radius:20px; background:rgba(0,0,0,.42);
        box-shadow:inset 2px 2px 5px rgba(0,0,0,.45);
    }
    div[class*="st-key-trip_card_"] .tm-trip-card-budget-fill {
        height:100%; border-radius:20px;
        background:linear-gradient(90deg,#4facfe 0%,#00f2fe 100%);
        box-shadow:inset 0 2px 2px rgba(255,255,255,.25);
    }
    @media(max-width:640px){
        div[class*="st-key-trip_card_"] .tm-trip-card-visual { min-height:102px; padding:12px 14px; }
        div[class*="st-key-trip_card_"] div[data-testid="stButton"] button { min-height:102px !important; }
    }

    /* No-budget card */
    div[class*="st-key-trip_card_"] .tm-trip-card-budget-text {
        text-align:left !important;
    }
</style>
""", unsafe_allow_html=True)

# Глобални константи и файлове
KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"
LABELS_FILE = "pixelapp_labels_2026.csv"
TRIP_PLAN_FILE = "trip_plan_2026.csv"

DEFAULT_UI_LABELS = {
    "pet": "Куче",
    "hotel": "Нощувки/Хотел",
    "deposit": "Депозит/Резервация",
    "fuel_red_threshold": 1.80
}

def get_ui_labels():
    labels = DEFAULT_UI_LABELS.copy()
    try:
        if os.path.exists(LABELS_FILE):
            df = pd.read_csv(LABELS_FILE, encoding="utf-8")
            if not df.empty:
                row = df.iloc[0]
                for key in labels:
                    value = str(row.get(key, labels[key]))
                    if value and value != "nan":
                        if key == "fuel_red_threshold":
                            labels[key] = float(value)
                        else:
                            labels[key] = value
    except:
        pass
    return labels

def save_ui_labels(pet_label, hotel_label, deposit_label, fuel_red_threshold=1.80):
    try:
        try:
            fuel_red_threshold = float(fuel_red_threshold)
        except (TypeError, ValueError):
            fuel_red_threshold = 1.80
        fuel_red_threshold = max(0.01, fuel_red_threshold)
        pd.DataFrame([{
            "pet": pet_label,
            "hotel": hotel_label,
            "deposit": deposit_label,
            "fuel_red_threshold": fuel_red_threshold
        }]).to_csv(LABELS_FILE, index=False, encoding="utf-8")
        return True
    except:
        return False

UI_LABELS = get_ui_labels()

def get_display_category(category):
    category_text = str(category)
    replacements = {
        "Куче": UI_LABELS.get("pet", "Куче"),
        "Нощувки/Хотел": UI_LABELS.get("hotel", "Нощувки/Хотел"),
        "Депозит/Резервация": UI_LABELS.get("deposit", "Депозит/Резервация")
    }
    for canonical, label in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        category_text = category_text.replace(canonical, label)
    return category_text

# Инициализация на локални CSV файлове
if not os.path.exists(MAP_FILE):
    pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(MAP_FILE, index=False, encoding="utf-8")

if not os.path.exists(TRIP_PLAN_FILE):
    pd.DataFrame(columns=["trip_id", "item_id", "title", "done", "created"]).to_csv(TRIP_PLAN_FILE, index=False, encoding="utf-8")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), 
                (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date","budget","status"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")

def get_trip_data(t_id):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        r = df[df["trip_id"] == t_id].copy()
        if "liters" not in r.columns: r["liters"] = 0.0
        if "current_km" not in r.columns: r["current_km"] = 0.0
        return r
    except:
        return pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"])

# Функция за безопасно рендериране на картичките и прогрес баровете
def render_trip_cards():
    try:
        settings_df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
    except:
        settings_df = pd.DataFrame()

    if settings_df.empty:
        st.info("Няма намерени активни пътувания в настройките.")
        return

    # Зареждане на всички разходи за изчисления
    try:
        data_df = pd.read_csv(DATA_FILE, encoding="utf-8")
    except:
        data_df = pd.DataFrame()

    for idx, row in settings_df.iterrows():
        t_id = row.get("trip_id", f"trip_{idx}")
        status = row.get("status", "Активно")
        
        # Защита при парсване на бюджета
        try:
            budget = float(row.get("budget", 0))
        except:
            budget = 0.0

        # Изчисляване на похарчената сума
        if not data_df.empty and "trip_id" in data_df.columns and "amount" in data_df.columns:
            total_spent = data_df[data_df["trip_id"] == t_id]["amount"].sum()
        else:
            total_spent = 0.0

        # Коректно и безопасно изчисляване на процента
        if budget > 0:
            percentage_val = (total_spent / budget) * 100
            # Ограничаваме прогрес бара до 100% за визуализацията в CSS, за да не експлодира извън контейнера
            bar_width = min(100.0, percentage_val)
            percentage_text = f"{int(percentage_val)}%"
        else:
            bar_width = 0.0
            percentage_text = "--%"

        # Генериране на HTML структура с уникален ключ и коригиран стил за прогреса
        card_html = f"""
        <div class="st-key-trip_card_{idx}">
            <div class="tm-trip-card-visual">
                <div class="tm-trip-card-title">
                    <span>✈️ {html.escape(str(t_id))}</span>
                    <span class="tm-trip-arrow">➔</span>
                </div>
                <div class="tm-trip-card-status">
                    🟢 {html.escape(str(status))}
                </div>
                <div class="tm-trip-card-budget">
                    <div class="tm-trip-card-budget-text">
                        €{total_spent:,.2f} / €{budget:,.2f} • {percentage_text}
                    </div>
                    <div class="tm-trip-card-budget-track">
                        <div class="tm-trip-card-budget-fill" style="width: {bar_width}%;"></div>
                    </div>
                </div>
            </div>
        </div>
        """
        # Изчертаване с уникален Streamlit ключ, избягвайки дублиране в DOM дървото
        st.components.v1.html(card_html, height=125, scrolling=False)

# Главен интерфейс
st.title("PixelApp 🐾")
st.subheader("Система за управление на лични пътувания и бюджети")

# Показване на списъка с картички на началния екран
st.write("### Вашите пътувания:")
render_trip_cards()

# Секция за настройки
with st.sidebar:
    st.header("⚙️ Настройки на приложението")
    nov_куче_етикет = st.text_input("Етикет за 'Куче':", UI_LABELS.get("pet", "Куче"))
    nov_хотел_етикет = st.text_input("Етикет за 'Нощувки/Хотел':", UI_LABELS.get("hotel", "Нощувки/Хотел"))
    nov_депозит_етикет = st.text_input("Етикет за 'Депозит/Резервация':", UI_LABELS.get("deposit", "Депозит/Резервация"))
    праг_гориво = st.number_input("Критичен праг на гориво:", value=float(UI_LABELS.get("fuel_red_threshold", 1.80)))
    
    if st.button("Запази настройките"):
        if save_ui_labels(нов_куче_етикет, нов_хотел_етикет, нов_депозит_етикет, праг_гориво):
            st.success("Настройките са запазени!")
            st.rerun()
