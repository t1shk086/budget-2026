import streamlit as st
import pandas as pd
import datetime
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import io

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #090b0e 0%, #11151c 50%, #0d1117 100%) !important;
        background-attachment: fixed !important;
    }
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
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
    /* Стили за горната навигационна активна лента */
    .nav-bar-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 12px 20px;
        margin-bottom: 25px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
    }
    .nav-brand {
        font-family: "Segoe UI", Roboto, sans-serif;
        font-weight: 800;
        font-size: 20px;
        background: linear-gradient(135deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"
LABELS_FILE = "pixelapp_labels_2026.csv"

DEFAULT_UI_LABELS = {
    "pet": "Куче",
    "hotel": "Нощувки/Хотел",
    "deposit": "Депозит/Резервация"
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
                        labels[key] = value
    except: pass
    return labels

def save_ui_labels(pet_label, hotel_label, deposit_label):
    try:
        pd.DataFrame([{"pet": pet_label, "hotel": hotel_label, "deposit": deposit_label}]).to_csv(LABELS_FILE, index=False, encoding="utf-8")
        return True
    except: return False

UI_LABELS = get_ui_labels()

def get_display_category(category):
    category_text = str(category)
    replacements = {"Куче": UI_LABELS.get("pet", "Куче"), "Нощувки/Хотел": UI_LABELS.get("hotel", "Нощувки/Хотел"), "Депозит/Резервация": UI_LABELS.get("deposit", "Депозит/Резервация")}
    for canonical, label in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        category_text = category_text.replace(canonical, label)
    return category_text

if not os.path.exists(MAP_FILE):
    pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(MAP_FILE, index=False, encoding="utf-8")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), 
                (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])]:
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")

def get_trip_data(t_id):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        r = df[df["trip_id"] == t_id].copy()
        return r
    except: return pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"])

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        f = df[df["trip_id"] == t_id]
        if not f.empty: return f.iloc[0].to_dict()
    except: pass
    return d

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        pd.concat([df, new_row], ignore_index=True).to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False

def get_map_points(t_id):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        return df[df["trip_id"] == t_id].copy()
    except: return pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        row = {"trip_id": t_id, "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(MAP_FILE, index=False, encoding="utf-8")
        return True
    except: return False

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0

existing_trips = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
existing_trips = [t for t in existing_trips if pd.notna(t) and str(t).strip() != ""]

@st.dialog("➕ Създаване на ново приключение")
def create_trip_modal():
    txt = st.text_input("Име на дестинацията:").strip()
    d_range = st.date_input("Изберете дати:", value=[datetime.date.today(), datetime.date.today()])
    viber_car = st.radio("Автомобил ли използвате?:", ["Не, с друг транспорт", "Да, със собствен автомобил"])
    new_skm = st.number_input("Начални километри:", value=0.0)
    if st.button("🚀 СЪЗДАЙ И ОТВОРИ", type="primary") and txt:
        s_d_str = d_range[0].strftime("%d.%m.%Y") if len(d_range) > 0 else ""
        e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 else s_d_str
        target_id = txt.replace(" ", "_")
        save_trip_settings(target_id, "Да" if "собствен" in viber_car else "Не", "Да", float(new_skm), 0.0, 0.0, s_d_str, e_d_str)
        st.session_state["current_trip"] = target_id
        st.rerun()

@st.dialog("➕ Добавяне на нов разход")
def quick_expense_modal():
    st.markdown("##### Към кое пътуване се отнася разходът?")
    options = ["— Изберете съществуващо —"] + [t.replace("_", " ") for t in existing_trips]
    choice = st.selectbox("Пътуване:", options, label_visibility="collapsed")
    if choice and choice != "— Изберете съществуващо —":
        selected_id = choice.replace(" ", "_")
        amt_in = st.number_input("СУМА (EUR)", format="%.2f")
        desc_in = st.text_input("Описание на разхода:")
        st.write("---")
        cat_cols = st.columns(3)
        for i, kat in enumerate(KATEGORII):
            with cat_cols[i % 3]:
                if st.button(get_display_category(kat), key=f"q_cat_{i}"):
                    if amt_in and amt_in > 0 and desc_in:
                        if add_expense(selected_id, amt_in, kat, desc_in, (kat == "Депозит/Резервация")):
                            st.success("✅ Записано!")
                            st.session_state["current_trip"] = selected_id
                            st.rerun()

# === АКТИВНА НАВИГАЦИОННА ЛЕНТА ===
st.markdown('<div class="nav-bar-container"><div class="nav-brand">🐾 PixelApp</div></div>', unsafe_allow_html=True)
nav_cols = st.columns([0.4, 0.4, 0.2])
with nav_cols[0]:
    if st.button("🗂️ Всички Пътувания", use_container_width=True):
        st.session_state["current_trip"] = None
        st.rerun()
with nav_cols[1]:
    if st.button("➕ Бърз Разход", use_container_width=True, type="primary"):
        quick_expense_modal()
with nav_cols[2]:
    if st.button("🛠️ Настройки", use_container_width=True):
        st.session_state["current_trip"] = "__settings_global__"
        st.rerun()

st.markdown("---")

# === ЛОГИКА НА ЕКРАНИТЕ ===
if st.session_state["current_trip"] == "__settings_global__":
    st.markdown("### 🛠️ Настройки и Системен Архив")
    # Backup code structure remains same as user profile implementation...
    st.info("Административният панел е активен тук.")

elif st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center;'><h1 style='font-weight: 900; color: #4facfe;'>Пътувания</h1></div>", unsafe_allow_html=True)
    if existing_trips:
        opts = [t.replace("_", " ") for t in existing_trips]
        choice = st.selectbox("Изберете Ваше приключение:", opts)
        if st.button("✔️ Зареди", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.rerun()
    else:
        st.info("Няма налични пътувания.")
    if st.button("➕ Създай Ново Пътуване", use_container_width=True):
        create_trip_modal()
else:
    # Зареждане на конкретното пътуване...
    st.write(f"Отворено пътуване: {st.session_state['current_trip'].replace('_', ' ')}")
