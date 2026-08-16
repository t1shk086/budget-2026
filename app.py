import streamlit as st
import pandas as pd
import datetime
import os
import glob
import io
import base64

# 1. НАСТРОЙКА НА СТРАНИЦАТА И ПЪЛЕН ОРИГИНАЛЕН 3Д CSS ДИЗАЙН
st.set_page_config(page_title="Бюджет 2026", page_icon="💰", layout="centered")

st.markdown("""
<style>
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader, .stExpander {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4), 
                    -2px -2px 8px rgba(255, 255, 255, 0.02) !important;
        margin-bottom: 15px !important;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #2e2e2e, #1c1c1c) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5), 
                    -1px -1px 4px rgba(255, 255, 255, 0.05) !important;
        transition: all 0.2s ease !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #3d3d3d, #252525) !important;
        transform: translateY(-2px) !important;
        box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.6) !important;
    }
    div.stButton > button:active {
        transform: translateY(1px) !important;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"
def get_emoji(category):
    mapping = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return mapping.get(category, "💳")

if not os.path.exists(DATA_FILE):
    try: pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"]).to_csv(DATA_FILE, index=False, encoding="utf-8")
    except: pass
else:
    try:
        df_check = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "liters" not in df_check.columns:
            df_check["liters"] = 0.0
            df_check.to_csv(DATA_FILE, index=False, encoding="utf-8")
    except: pass

if not os.path.exists(SETTINGS_FILE):
    try: pd.DataFrame(columns=["trip_id", "car_trip", "track_fuel", "start_km", "end_km", "manual_fuel"]).to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def get_trip_data(trip_id):
    if not os.path.exists(DATA_FILE): return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"])
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        df_trip = df[df["trip_id"] == trip_id].copy()
        if "liters" not in df_trip.columns: df_trip["liters"] = 0.0
        return df_trip
    except: return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"])
def get_trip_settings(trip_id):
    default_settings = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0}
    if not os.path.exists(SETTINGS_FILE): return default_settings
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df_trip = df[df["trip_id"] == trip_id]
        if not df_trip.empty:
            res = df_trip.iloc.to_dict()
            return {"car_trip": str(res.get("car_trip", "Не")), "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), "start_km": float(res.get("start_km", 0.0)), "end_km": float(res.get("end_km", 0.0)), "manual_fuel": float(res.get("manual_fuel", 0.0))}
    except: pass
    return default_settings

def save_trip_settings(trip_id, car_trip, track_fuel, start_km, end_km, manual_fuel=0.0):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != trip_id]
        new_row = {"trip_id": trip_id, "car_trip": car_trip, "track_fuel": track_fuel, "start_km": float(start_km), "end_km": float(end_km), "manual_fuel": float(manual_fuel)}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def add_expense(trip_id, amount, category, description, is_deposit=False, liters=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8") if os.path.exists(DATA_FILE) else pd.DataFrame()
        new_row = {"trip_id": trip_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amount), "category": category, "description": description if description else "Без описание", "type": "deposit" if is_deposit else "expense", "liters": float(liters)}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False

def generate_html_pdf(trip_name, total_site, deposit, categories_totals, rows_data, fuel_info=None):
    html_content = f"<html><body><h1>Финансов отчет: {trip_name.upper()}</h1><p><b>ОБЩО:</b> {deposit + total_site:.2f} EUR</p></body></html>"
    return html_content.encode('utf-8')

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0

if st.session_state["current_trip"] is None:
    st.markdown("<h1 style='text-shadow: 2px 2px 4px rgba(0,0,0,0.6); text-align: center;'>💰 Бюджет 2026</h1>", unsafe_allow_html=True)
    existing_trips = []
    if os.path.exists(DATA_FILE):
        try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            existing_trips = list(df_all["trip_id"].unique())
        except: pass
    menu_options = ["-- Изберете почивка --"] + [t.replace("_", " ") for t in existing_trips] + ["➕ СЪЗДАЙ НОВО ПЪТУВАНЕ"]
    user_choice = st.selectbox("Изберете или създайте почивка:", menu_options)
    if user_choice == "➕ СЪЗДАЙ НОВО ПЪТУВАНЕ":
        input_text = st.text_input("Въведете име на новата дестинация:").strip()
        if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True) and input_text:
            st.session_state["current_trip"] = input_text.replace(" ", "_"); st.rerun()
    elif user_choice != "-- Изберете почивка --":
        if st.button("📂 ОТВОРИ ПОЧИВКАТА", use_container_width=True):
            st.session_state["current_trip"] = user_choice.replace(" ", "_"); st.rerun()
else:
    trip_id = st.session_state["current_trip"]
    if st.button("⬅️ НАЗАД КЪМ ВСИЧКИ ПОЧИВКИ", use_container_width=True):
        st.session_state["current_trip"] = None; st.rerun()
        
    st.markdown(f"<h2 style='text-align: center; color: #00f2fe;'>🌴 Дестинация: {trip_id.upper().replace('_', ' ')}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    current_settings = get_trip_settings(trip_id)
    car_index = 0 if current_settings["car_trip"] == "Не" else 1
    car_choice = st.selectbox("Пътувате ли със собствен автомобил?", ["Не", "Да"], index=car_index)
    track_fuel_choice, start_km_val, end_km_val, manual_fuel_val = "Добави впоследствие", float(current_settings["start_km"]), float(current_settings["end_km"]), float(current_settings["manual_fuel"])
    
    if car_choice == "Да":
        track_index = 0 if current_settings["track_fuel"] == "Да" else 1
        track_fuel_choice = st.selectbox("Искате ли изчисляване на разход на гориво?", ["Да", "Добави впоследствие"], index=track_index)
        if track_fuel_choice == "Да":
            col_km1, col_km2 = st.columns(2)
            with col_km1: start_km_val = st.number_input("Начални километри (км)", min_value=0.0, value=start_km_val)
            with col_km2: end_km_val = st.number_input("Крайни километри (км)", min_value=0.0, value=end_km_val)
            manual_fuel_val = st.number_input("Допълнително / Ръчно гориво (EUR)", min_value=0.0, value=manual_fuel_val)

    save_trip_settings(trip_id, car_choice, track_fuel_choice, start_km_val, end_km_val, manual_fuel_val)
    st.markdown("---")
    papka_snimki = f"snimki_{trip_id}_2026"; df_trip = get_trip_data(trip_id); depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum()); v_id = st.session_state["form_version"]
    
    col1, col2 = st.columns(2)
    with col1: s_input = st.number_input("СУМА (EUR)", min_value=0.0, step=1.0, format="%.2f", value=None, placeholder="Сума...", key=f"suma_{v_id}")
    with col2: o_input = st.text_input("Описание", placeholder="Описание...", key=f"opis_{v_id}")

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description, is_dep):
        st.write(f"Зареждане на гориво за **{amount:.2f} EUR**.")
        liters = st.number_input("Колко литра?", min_value=0.0, step=0.1, format="%.1f")
        if st.button("💾 Запиши разхода", use_container_width=True, type="primary"):
            if add_expense(trip_id, amount, category, f"[ГОРИВО] {description}", is_deposit=is_dep, liters=liters):
                st.session_state["form_version"] += 1; st.rerun()

    grid = st.columns(3)
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"btn_{i}"):
                if s_input and s_input > 0:
                    clean_desc = o_input.strip() if o_input else "Без описание"
                    is_dep = (kat == "Депозит/Резервация")
                    if kat == "Транспорт" and car_choice == "Да" and track_fuel_choice == "Да" and any(kw in clean_desc.lower() for kw in ["гориво", "зареждане", "бензин", "дизел"]):
                        fuel_modal(s_input, kat, clean_desc, is_dep)
                    else:
                        if add_expense(trip_id, s_input, kat, clean_desc, is_deposit=is_dep):
                            st.session_state["form_version"] += 1; st.rerun()
    df_expenses = df_trip[df_trip["type"] == "expense"]; total_on_site = float(df_expenses["amount"].sum()); categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}; rows_data = []; total_liters_sum, auto_fuel_money = 0.0, 0.0
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
        rows_data.append([row["date"], float(row["amount"]), row["category"], row["description"]])
        if row["category"] == "Транспорт":
            r_lit = float(row.get("liters", 0.0))
            if r_lit > 0: total_liters_sum += r_lit; auto_fuel_money += float(row["amount"])
            elif any(kw in str(row["description"]).lower() for kw in ["гориво", "зареждане", "бензин", "дизел"]): auto_fuel_money += float(row["amount"])
    total_fuel_calculated = auto_fuel_money + manual_fuel_val

    st.markdown("### 📊 Анализ на разходите")
    stat_grid = st.columns(2)
    for idx, (kat, s_value) in enumerate(categories_totals.items()):
        pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
        icon = get_emoji(kat)
        b_color = "rgba(255,75,75,0.4)" if pct > 40 else "rgba(255,165,0,0.4)" if pct > 20 else "rgba(0,242,254,0.3)" if pct > 0 else "rgba(255,255,255,0.08)"
        b_bg = "rgba(255,75,75,0.2)" if pct > 40 else "rgba(255,165,0,0.2)" if pct > 20 else "rgba(0,242,254,0.15)" if pct > 0 else "rgba(255,255,255,0.1)"
        b_txt = "#ff4b4b" if pct > 40 else "#ffa500" if pct > 20 else "#00f2fe" if pct > 0 else "#aaa"
        with stat_grid[idx % 2]:
            st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); border: 1px solid {b_color}; padding: 12px 15px; border-radius: 14px; box-shadow: 3px 3px 10px rgba(0,0,0,0.3); margin-bottom: 12px; height: 120px; display: flex; flex-direction: column; justify-content: space-between;"><div style="display: flex; justify-content: space-between; align-items: center;"><span style="font-size: 14px; font-weight: bold; color: #eee;">{icon} {kat}</span><span style="background: {b_bg}; color: {b_txt}; font-size: 11px; padding: 2px 7px; border-radius: 20px; font-weight: bold;">{pct:.1f}%</span></div><h3 style="margin: 0; color: white; font-size: 20px; font-weight: 800;">{s_value:.2f} <span style="font-size: 11px; color: #aaa;">EUR</span></h3><div style="background: rgba(255,255,255,0.05); width: 100%; height: 6px; border-radius: 10px; overflow: hidden;"><div style="background: {b_txt}; width: {pct}%; height: 100%; border-radius: 10px;"></div></div></div>', unsafe_allow_html=True)

    if car_choice == "Да" and track_fuel_choice == "Да":
        st.markdown("#### ⛽ Справка за разхода и горивото")
        distance = end_km_val - start_km_val
        col_fuel1, col_fuel2 = st.columns(2)
        with col_fuel1: st.markdown(f'<div style="background: rgba(255, 165, 0, 0.05); border: 1px solid rgba(255, 165, 0, 0.2); padding: 15px; border-radius: 12px; text-align: center;"><small style="color: #ffa500; font-weight: bold;">⛽ ОБЩО ЗА ГОРИВО</small><h3 style="color: white; margin: 5px 0;">{total_fuel_calculated:.2f} EUR</h3><small style="color: #aaa;">Общо: {total_liters_sum:.1f} л</small></div>', unsafe_allow_html=True)
        with col_fuel2:
            if distance > 0:
                avg_con = (total_liters_sum / distance * 100) if total_liters_sum > 0 else 0.0
                st.markdown(f'<div style="background: rgba(0, 242, 254, 0.05); border: 1px solid rgba(0, 242, 254, 0.2); padding: 15px; border-radius: 12px; text-align: center;"><small style="color: #00f2fe; font-weight: bold;">📊 СРЕДЕН РАЗХОД</small><h3 style="color: white; margin: 5px 0;">{avg_con:.1f} л / 100 км</h3><small style="color: #aaa;">Дистанция: {distance:.1f} км</small></div>', unsafe_allow_html=True)
            else: st.markdown('<div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; text-align: center; height: 90px; display: flex; align-items: center; justify-content: center;"><small style="color: #aaa;">Въведете километри горе за среден разход.</small></div>', unsafe_allow_html=True)

    st.markdown("---"); col_stat1, col_stat2 = st.columns(2)
    with col_stat1: st.markdown(f"<div style='background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; text-align: center;'><small style='color: #aaa; font-weight: bold;'>🏨 ДЕПОЗИТ</small><h2 style='color: #ff4b4b; margin: 5px 0;'>{depozit_hotel:.2f} EUR</h2></div>", unsafe_allow_html=True)
    with col_stat2: st.markdown(f"<div style='background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; text-align: center;'><small style='color: #aaa; font-weight: bold;'>💰 НА МЯСТО</small><h2 style='color: #00f2fe; margin: 5px 0;'>{total_on_site:.2f} EUR</h2></div>", unsafe_allow_html=True)

    if not df_trip.empty:
        st.markdown("---"); st.subheader("📋 Хронология на плащанията")
        try:
            df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8"); trip_indices = df_all_data[df_all_data["trip_id"] == trip_id].index.tolist()
            for idx in reversed(trip_indices):
                r_row = df_all_data.loc[idx]; icon = get_emoji(r_row["category"]); l_text = f" | ⛽ {r_row['liters']:.1f} л" if float(r_row.get("liters", 0.0)) > 0 else ""
                st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); padding: 12px; border-radius: 10px; margin-bottom: 2px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 3px 3px 8px rgba(0,0,0,0.3);"><span style="font-size: 18px;">{icon}</span> <b>{r_row["category"]}</b> — <span style="color:#ff4b4b; font-weight:bold;">{r_row["amount"]:.2f} EUR</span><br><small style="color:#aaa;">📅 {r_row["date"]} | 📝 {r_row["description"]}{l_text}</small></div>', unsafe_allow_html=True)
                if st.button("❌ Изтрий разход", key=f"del_{idx}", use_container_width=True):
                    df_all_data.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8"); st.rerun()
        except: pass

    st.markdown("---"); fuel_info_pdf = {"total_fuel": total_fuel_calculated, "distance": end_km_val - start_km_val} if car_choice == "Да" else None; html_buffer = generate_html_pdf(trip_id, total_on_site, depozit_hotel, categories_totals, rows_data, fuel_info_pdf); b64_html = base64.b64encode(html_buffer).decode()
    st.markdown(f'<a href="data:text/html;base64,{b64_html}" download="otchet_{trip_id}_2026.html" style="text-decoration: none;"><button style="width: 100%; background: linear-gradient(135deg, #ff4b4b, #b31010); color: white; padding: 12px 20px; border: none; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 4px 4px 10px rgba(0,0,0,0.4); text-transform: uppercase;">📥 ПРИКЛЮЧИ ПОЧИВКАТА И СВАЛИ PDF</button></a>', unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("📸 Снимки и спомени от почивката"):
        if not os.path.exists(papka_snimki):
            try: os.makedirs(papka_snimki)
            except: pass
        uploaded_files = st.file_uploader("Качете снимки:", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"uploader_{trip_id}")
        if uploaded_files:
            for file in uploaded_files:
                if not os.path.exists(os.path.join(papka_snimki, file.name)):
                    with open(os.path.join(papka_snimki, file.name), "wb") as f: f.write(file.getbuffer())
            st.rerun()
        saved_photos = glob.glob(os.path.join(papka_snimki, "*"))
        if saved_photos:
            img_grid = st.columns(3)
            for idx, img_path in enumerate(saved_photos):
                with img_grid[idx % 3]:
                    st.image(img_path, use_container_width=True)
                    if st.button("🗑️ Трий", key=f"del_img_{idx}", use_container_width=True):
                        os.remove(img_path); st.rerun()

    st.markdown("---"); potvurditel = st.checkbox("Потвърждавам изтриването на цялото пътуване")
    if st.button("🗑️ ИЗТРИЙ ЦЯЛОТО ПЪТУВАНЕ", type="primary", use_container_width=True, disabled=not potvurditel):
        try:
            df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8"); df_all_data[df_all_data["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
            if os.path.exists(papka_snimki):
                for p in glob.glob(os.path.join(papka_snimki, "*")): os.remove(p)
                os.rmdir(papka_snimki)
            st.session_state["current_trip"] = None; st.rerun()
        except: pass
