import streamlit as st
import pandas as pd
import datetime
import os
import glob
import io
import base64

# 1. НАСТРОЙКА НА СТРАНИЦАТА И 3Д CSS ДИЗАЙН
st.set_page_config(page_title="Бюджет 2026", page_icon="💰", layout="centered")

st.markdown("""
<style>
    /* Стил за белите контейнери / инфо кутии */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader, .stExpander {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4), 
                    -2px -2px 8px rgba(255, 255, 255, 0.02) !important;
        margin-bottom: 15px !important;
    }
    
    /* 3D Ефект за бутоните за категории и триене */
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
FUEL_KEYWORDS = ["гориво", "зареждане", "бензин", "дизел", "нафта", "газ", "заредих"]

def get_emoji(category):
    mapping = {
        "Храна и напитки": "🍔",
        "Транспорт": "🚗",
        "Куче": "🐾",
        "Нощувки/Хотел": "🏨",
        "Депозит/Резервация": "📌",
        "Други": "🪙"
    }
    return mapping.get(category, "💳")

# Инициализация и миграция на файловете
if not os.path.exists(DATA_FILE):
    try:
        pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"]).to_csv(DATA_FILE, index=False, encoding="utf-8")
    except: pass
else:
    try:
        df_check = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "liters" not in df_check.columns:
            df_check["liters"] = 0.0
            df_check.to_csv(DATA_FILE, index=False, encoding="utf-8")
    except: pass

if not os.path.exists(SETTINGS_FILE):
    try:
        pd.DataFrame(columns=["trip_id", "car_trip", "track_fuel", "start_km", "end_km", "manual_fuel"]).to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def get_trip_data(trip_id):
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"])
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        return df[df["trip_id"] == trip_id]
    except:
        return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"])

def get_trip_settings(trip_id):
    if not os.path.exists(SETTINGS_FILE):
        return {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0}
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df_trip = df[df["trip_id"] == trip_id]
        if not df_trip.empty:
            res = df_trip.iloc[0].to_dict()
            return res
    except: pass
    return {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0}

def save_trip_settings(trip_id, car_trip, track_fuel, start_km, end_km, manual_fuel=0.0):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != trip_id]
        new_row = {
            "trip_id": trip_id, "car_trip": car_trip, "track_fuel": track_fuel,
            "start_km": float(start_km), "end_km": float(end_km), "manual_fuel": float(manual_fuel)
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def add_expense(trip_id, amount, category, description, is_deposit=False, liters=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8") if os.path.exists(DATA_FILE) else pd.DataFrame()
        new_row = {
            "trip_id": trip_id,
            "date": datetime.datetime.now().strftime("%d.%m %H:%M"),
            "amount": float(amount),
            "category": category,
            "description": description if description else "Без описание",
            "type": "deposit" if is_deposit else "expense",
            "liters": float(liters)
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False

def generate_html_pdf(trip_name, total_site, deposit, categories_totals, rows_data, fuel_info=None):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Отчет_{trip_name}</title>
        <style>
            body {{ font-family: 'Arial', sans-serif; color: #2c3e50; padding: 30px; }}
            h1 {{ color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 10px; margin-bottom: 5px; }}
            h2 {{ color: #2c3e50; margin-top: 25px; font-size: 18px; border-left: 4px solid #1f77b4; padding-left: 10px; }}
            .stats {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin-top: 15px; border: 1px solid #e2e8f0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; }}
            th {{ background-color: #f1f5f9; color: #334155; font-weight: bold; }}
            .chrono-th {{ background-color: #e2e8f0; color: #1e293b; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
        </style>
    </head>
    <body>
        <h1>Финансов отчет: {trip_name.upper().replace('_', ' ')}</h1>
        <p style="color: #64748b; font-size: 13px;"><b>Дата на генериране:</b> {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        <div class="stats">
            <p style="margin: 5px 0;"><b>Платен депозит за хотел:</b> {deposit:.2f} EUR</p>
            <p style="margin: 5px 0;"><b>Общо похарчени на място:</b> {total_site:.2f} EUR</p>
            {f"<p style='margin: 5px 0; color: #d97706;'><b>Общо за гориво:</b> {fuel_info['total_fuel']:.2f} EUR ({fuel_info['distance']:.1f} км)</p>" if fuel_info and fuel_info['distance'] > 0 else ""}
            {f"<p style='margin: 5px 0; color: #059669;'><b>Среден разход:</b> {fuel_info['avg_consumption']:.2f} л / 100 км</p>" if fuel_info and fuel_info['avg_consumption'] > 0 else ""}
            <p style="margin: 5px 0; font-size: 16px; color: #1e3a8a;"><b>ОБЩО РАЗХОДИ ЗА ПОЧИВКАТА:</b> {deposit + total_site:.2f} EUR</p>
        </div>
        <h2>Разходи по категории</h2>
        <table>
            <tr><th>Категория</th><th>Сума (EUR)</th><th>Процент</th></tr>
    """
    for kat, s_value in categories_totals.items():
        percentage = (s_value / total_site * 100) if total_site > 0 else 0.0
        html_content += f"<tr><td><b>{kat}</b></td><td>{s_value:.2f} EUR</td><td>{percentage:.1f}%</td></tr>"
    html_content += """
        </table>
        <h2>Пълна хронология на плащанията</h2>
        <table>
            <tr>
                <th class="chrono-th">Дата/Час</th>
                <th class="chrono-th">Сума</th>
                <th class="chrono-th">Категория</th>
                <th class="chrono-th">Описание</th>
            </tr>
    """
    for row in reversed(rows_data):
        pdf_date, pdf_amount, pdf_cat, pdf_desc = row[:4]
        html_content += f"<tr><td>{pdf_date}</td><td><b>{pdf_amount:.2f} EUR</b></td><td>{pdf_cat}</td><td>{pdf_desc}</td></tr>"
    html_content += "</table><script>window.onload = function() { window.print(); }</script></body></html>"
    return html_content.encode('utf-8')

# 2. СТАРТОВ ЕКРАН И ВЪВЕЖДАНЕ НА ДАННИ
if "form_version" not in st.session_state:
    st.session_state["form_version"] = 0

st.markdown("<h1 style='text-shadow: 2px 2px 4px rgba(0,0,0,0.6);'>💰 Бюджет 2026</h1>", unsafe_allow_html=True)

existing_trips = []
if os.path.exists(DATA_FILE):
    try:
        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
        existing_trips = list(df_all["trip_id"].unique())
    except: pass

menu_options = [t.replace("_", " ") for t in existing_trips] + ["➕ СЪЗДАЙ НОВО ПЪТУВАНЕ"]
user_choice = st.selectbox("Изберете или създайте почивка:", menu_options)

trip_id = ""
is_new_trip = user_choice == "➕ СЪЗДАЙ НОВО ПЪТУВАНЕ"

if is_new_trip:
    input_text = st.text_input("Въведете име на новата дестинация:").strip()
    if input_text:
        trip_id = input_text.replace(" ", "_")
else:
    trip_id = user_choice.replace(" ", "_")

if trip_id:
    st.markdown("---")
    st.subheader(f"🌴 Дестинация: {trip_id.upper().replace('_', ' ')}")
    
    current_settings = get_trip_settings(trip_id)
    
    # 🚗 ЛОГИКА ЗА АВТОМОБИЛ И ГОРИВО
    st.markdown("### 🚗 Настройки за транспорт")
    
    car_choice = st.selectbox("Пътувате ли със собствен автомобил?", ["Не", "Да"], 
                              index=0 if current_settings.get("car_trip") == "Не" else 1)
    
    track_fuel_choice = "Добави впоследствие"
    start_km_val = float(current_settings.get("start_km", 0.0))
    end_km_val = float(current_settings.get("end_km", 0.0))
    manual_fuel_val = float(current_settings.get("manual_fuel", 0.0))
    
    if car_choice == "Да":
        track_fuel_choice = st.selectbox("Искате ли изчисляване на разход на гориво?", ["Да", "Добави впоследствие"],
                                         index=0 if current_settings.get("track_fuel") == "Да" else 1)
        
        if track_fuel_choice == "Да":
            col_km1, col_km2 = st.columns(2)
            with col_km1:
                start_km_val = st.number_input("Начални километри (км)", min_value=0.0, value=start_km_val, step=1.0)
            with col_km2:
                end_km_val = st.number_input("Крайни километри (км)", min_value=0.0, value=end_km_val, step=1.0)
            
            manual_fuel_val = st.number_input("Допълнително / Ръчно въведено гориво (EUR)", min_value=0.0, value=manual_fuel_val, step=1.0, help="Въведете сума, ако не сте я описали в хронологията")

    save_trip_settings(trip_id, car_choice, track_fuel_choice, start_km_val, end_km_val, manual_fuel_val)
    
    st.markdown("---")
    papka_snimki = f"snimki_{trip_id}_2026"
    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    
    v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1:
        s_input = st.number_input("СУМА (EUR)", min_value=0.0, step=1.0, format="%.2f", value=None, placeholder="Въведете сума...", key=f"suma_{v_id}")
    with col2:
        o_input = st.text_input("Описание", placeholder="Напр. за бензин, вечеря, такса...", key=f"opis_{v_id}")

    # ДИНАМИЧНО ПОКАЗВАНЕ НА ПОЛЕТО ЗА ЛИТРИ В РЕАЛНО ВРЕМЕ ДОКАТО ПИШЕ
    liters_input = 0.0
    is_fuel_detected = False
    if o_input:
        desc_lower_check = o_input.lower()
        if any(kw in desc_lower_check for kw in FUEL_KEYWORDS):
            is_fuel_detected = True
            liters_input = st.number_input("⛽ Въведете литри (л):", min_value=0.0, step=0.1, format="%.1f", key=f"liters_{v_id}")

    st.write("Изберете категория за запис:")
    grid = st.columns(3)
    
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"btn_{i}"):
                if s_input is not None and s_input > 0:
                    clean_desc = o_input.replace("|", "-").strip() if o_input else "Без описание"
                    is_dep = (kat == "Депозит/Резервация")
                    
                    # Записваме литри само ако сме в категория Транспорт и сме открили ключова дума
                    final_liters = liters_input if (kat == "Транспорт" and is_fuel_detected) else 0.0
                    
                    if add_expense(trip_id, s_input, kat, clean_desc, is_deposit=is_dep, liters=final_liters):
                        st.session_state["form_version"] += 1
                        st.success("Записано успешно!")
                        st.rerun()
                else:
                    st.warning("⚠️ Моля, въведете сума!")

    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    rows_data = []
    
    auto_fuel_sum = 0.0
    total_liters_sum = 0.0
    
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals:
            categories_totals[row["category"]] += float(row["amount"])
        
        row_liters = float(row["liters"]) if "liters" in row and not pd.isna(row["liters"]) else 0.0
        rows_data.append([row["date"], float(row["amount"]), row["category"], row["description"], row_liters])
        
        if row["category"] == "Транспорт":
            desc_lower = str(row["description"]).lower()
            if any(kw in desc_lower for kw in FUEL_KEYWORDS) or row_liters > 0:
                auto_fuel_sum += float(row["amount"])
                total_liters_sum += row_liters

    total_fuel_calculated = auto_fuel_sum + manual_fuel_val

    # 📊 МОДЕРНО ТАБЛО С ВГРАДЕНИ ЛЕНТИ
    st.markdown("---")
    st.subheader("📊 Анализ на разходите")
    
    stat_grid = st.columns(2)
    for idx, (kat, s_value) in enumerate(categories_totals.items()):
        percentage_text = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
        icon = get_emoji(kat)
        
        if percentage_text == 0:
            border_color = "rgba(255,255,255,0.08)"
            badge_bg = "rgba(255,255,255,0.1)"
            badge_color = "#aaa"
            bar_color = "rgba(255,255,255,0.15)"
        elif percentage_text > 40:
            border_color = "rgba(255, 75, 75, 0.4)"
            badge_bg = "rgba(255, 75, 75, 0.2)"
            badge_color = "#ff4b4b"
            bar_color = "#ff4b4b"
        elif percentage_text > 20:
            border_color = "rgba(255, 165, 0, 0.4)"
            badge_bg = "rgba(255, 165, 0, 0.2)"
            badge_color = "#ffa500"
            bar_color = "#ffa500"
        else:
            border_color = "rgba(0, 242, 254, 0.3)"
            badge_bg = "rgba(0, 242, 254, 0.15)"
            badge_color = "#00f2fe"
            bar_color = "#00f2fe"

        with stat_grid[idx % 2]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); 
                        border: 1px solid {border_color}; padding: 12px 15px; border-radius: 14px; 
                        box-shadow: 3px 3px 10px rgba(0,0,0,0.3); margin-bottom: 12px; height: 120px;
                        display: flex; flex-direction: column; justify-content: space-between;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; font-weight: bold; color: #eee; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{icon} {kat}</span>
                    <span style="background: {badge_bg}; color: {badge_color}; font-size: 11px; padding: 2px 7px; border-radius: 20px; font-weight: bold;">{percentage_text:.1f}%</span>
                </div>
                <div style="margin-top: 2px; margin-bottom: 2px;">
                    <h3 style="margin: 0; color: white; font-size: 20px; font-weight: 800;">{s_value:.2f} <span style="font-size: 11px; color: #aaa;">EUR</span></h3>
                </div>
                <div style="background: rgba(255,255,255,0.05); width: 100%; height: 6px; border-radius: 10px; overflow: hidden;">
                    <div style="background: {bar_color}; width: {percentage_text}%; height: 100%; border-radius: 10px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 🚗 СПЕЦИАЛНО ТАБЛО ЗА АВТОМОБИЛ И СРЕДЕН РАЗХОД
    distance = end_km_val - start_km_val
    avg_consumption = (total_liters_sum / distance * 100) if (distance > 0 and total_liters_sum > 0) else 0.0

    if car_choice == "Да" and track_fuel_choice == "Да":
        st.markdown("#### ⛽ Справка за горивото и среден разход")
        
        col_fuel1, col_fuel2 = st.columns(2)
        with col_fuel1:
            st.markdown(f"""
            <div style="background: rgba(255, 165, 0, 0.05); border: 1px solid rgba(255, 165, 0, 0.2); padding: 15px; border-radius: 12px; text-align: center;">
                <small style="color: #ffa500; font-weight: bold;">⛽ ОБЩО ЗА ГОРИВО</small>
                <h3 style="color: white; margin: 5px 0;">{total_fuel_calculated:.2f} EUR</h3>
                <small style="color: #aaa;">Заредени литри: {total_liters_sum:.1f} л</small>
            </div>
            """, unsafe_allow_html=True)
        with col_fuel2:
            if distance > 0:
                cost_per_km = total_fuel_calculated / distance
                consumption_text = f"{avg_consumption:.2f} л / 100 км" if avg_consumption > 0 else "Няма въведени литри"
                st.markdown(f"""
                <div style="background: rgba(0, 242, 254, 0.05); border: 1px solid rgba(0, 242, 254, 0.2); padding: 15px; border-radius: 12px; text-align: center;">
                    <small style="color: #00f2fe; font-weight: bold;">🛣️ СРЕДЕН РАЗХОД И КИЛОМЕТРИ</small>
                    <h3 style="color: white; margin: 5px 0;">{consumption_text}</h3>
                    <small style="color: #aaa;">Дистанция: {distance:.1f} км | Цена/км: {cost_per_km:.2f} EUR</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; text-align: center; height: 100px; display: flex; align-items: center; justify-content: center;">
                    <small style="color: #aaa;">Въведете крайна дистанция по-голяма от началната горе, за да сметнем средния разход.</small>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; box-shadow: 4px 4px 10px rgba(0,0,0,0.4); text-align: center;">
            <small style="color: #aaa; font-weight: bold;">🏨 ПЛАТЕН ДЕПОЗИТ</small>
            <h2 style="color: #ff4b4b; margin: 5px 0;">{depozit_hotel:.2f} EUR</h2>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; box-shadow: 4px 4px 10px rgba(0,0,0,0.4); text-align: center;">
            <small style="color: #aaa; font-weight: bold;">💰 ОБЩО НА МЯСТО</small>
            <h2 style="color: #00f2fe; margin: 5px 0;">{total_on_site:.2f} EUR</h2>
        </div>
        """, unsafe_allow_html=True)

    if not df_trip.empty:
        st.markdown("---")
        st.subheader("📋 Хронология на плащанията")
        
        try:
            df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8")
            trip_indices = df_all_data[df_all_data["trip_id"] == trip_id].index.tolist()
            
            for idx in reversed(trip_indices):
                r_row = df_all_data.loc[idx]
                icon = get_emoji(r_row["category"])
                
                liters_badge = ""
                if "liters" in r_row and float(r_row["liters"]) > 0:
                    liters_badge = f" <span style='background:rgba(255,165,0,0.2); color:#ffa500; font-size:11px; padding:1px 5px; border-radius:5px;'>⛽ {r_row['liters']:.1f} л</span>"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); padding: 12px; border-radius: 10px; margin-bottom: 2px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 3px 3px 8px rgba(0,0,0,0.3);">
                    <span style="font-size: 18px;">{icon}</span> <b>{r_row["category"]}</b> — 
                    <span style="color:#ff4b4b; font-weight:bold;">{r_row["amount"]:.2f} EUR</span>{liters_badge}<br>
                    <small style="color:#aaa;">📅 {r_row["date"]} | 📝 {r_row["description"]}</small>
                </div>
                """, unsafe_allow_html=True)
                
                confirm_key = f"confirm_delete_{idx}"
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False
                
                if not st.session_state[confirm_key]:
                    if st.button("❌ Изтрий", key=f"del_{idx}", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Наистина ли искате да изтриете този разход?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Да, изтрий го", key=f"yes_{idx}", use_container_width=True):
                            df_all_data = df_all_data.drop(idx)
                            df_all_data.to_csv(DATA_FILE, index=False, encoding="utf-8")
                            st.session_state[confirm_key] = False
                            st.success("Разходът е премахнат!")
                            st.rerun()
                    with col_no:
                        if st.button("↩️ Отказ", key=f"no_{idx}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()
                            
                st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
        except: pass

    st.markdown("---")
    st.subheader("🏁 Приключване на почивката")
    
    fuel_info_pdf = {
        "total_fuel": total_fuel_calculated, 
        "distance": distance,
        "avg_consumption": avg_consumption
    } if car_choice == "Да" else None
    
    html_buffer = generate_html_pdf(trip_id, total_on_site, depozit_hotel, categories_totals, rows_data, fuel_info_pdf)
    b64_html = base64.b64encode(html_buffer).decode()
    
    custom_css_button = f"""
        <a href="data:text/html;base64,{b64_html}" download="otchet_{trip_id}_2026.html" style="text-decoration: none;">
            <button style="width: 100%; background: linear-gradient(135deg, #ff4b4b, #b31010); color: white; padding: 12px 20px; border: none; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 4px 4px 10px rgba(0,0,0,0.4); text-transform: uppercase;">
                📥 ПРИКЛЮЧИ ПОЧИВКАТА И СВАЛИ PDF
            </button>
        </a>
    """
    st.markdown(custom_css_button, unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("📸 Снимки и спомени от почивката"):
        if not os.path.exists(papka_snimki):
            try: os.makedirs(papka_snimki)
            except: pass
            
        uploaded_files = st.file_uploader("Качете снимки за спомен:", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"uploader_{trip_id}")
        if uploaded_files:
            for file in uploaded_files:
                path_to_save = os.path.join(papka_snimki, file.name)
                if not os.path.exists(path_to_save):
                    with open(path_to_save, "wb") as f:
                        f.write(file.getbuffer())
            st.success("Запазени!")
            st.rerun()
            
        saved_photos = glob.glob(os.path.join(papka_snimki, "*"))
        if saved_photos:
            st.write(f"Запазени спомени: {len(saved_photos)}")
            снимки_имена = [os.path.basename(p) for p in saved_photos]
            избрана_снимка = st.selectbox("👁️ Изберете снимка за преглед в голям размер:", ["-- Изберете снимка --"] + снимки_имена)
            
            if избрана_снимка != "-- Изберете снимка --":
                път_към_голяма = os.path.join(papka_snimki, избрана_снимка)
                st.markdown("<div style='border-radius:12px; overflow:hidden; box-shadow: 5px 5px 15px rgba(0,0,0,0.5); border:1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                st.image(път_към_голяма, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            img_grid = st.columns(3)
            for idx, img_path in enumerate(saved_photos):
                with img_grid[idx % 3]:
                    st.markdown("<div style='border-radius:8px; overflow:hidden; box-shadow: 2px 2px 6px rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.05); margin-bottom:5px;'>", unsafe_allow_html=True)
                    st.image(img_path, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    img_confirm_key = f"confirm_img_{idx}"
                    if img_confirm_key not in st.session_state:
                        st.session_state[img_confirm_key] = False
                        
                    if not st.session_state[img_confirm_key]:
                        if st.button("❌ Изтрий", key=f"del_img_{idx}", use_container_width=True):
                            st.session_state[img_confirm_key] = True
                            st.rerun()
                    else:
                        if st.button("💥 ПОТВЪРДИ?", key=f"yes_img_{idx}", type="primary", use_container_width=True):
                            os.remove(img_path)
                            st.session_state[img_confirm_key] = False
                            st.rerun()
                        if st.button("↩️ Не", key=f"no_img_{idx}", use_container_width=True):
                            st.session_state[img_confirm_key] = False
                            st.rerun()
        else:
            st.info("Все още няма качени снимки.")

    st.markdown("---")
    st.subheader("🚨 Изтриване на цялото пътуване")
    име_за_показване = trip_id.upper().replace('_', ' ')
    potvurditel = st.checkbox(f"Потвърждавам изтриването на '{име_за_показване}'.")
    
    if st.button("🗑️ ИЗТРИЙ ЦЯЛОТО ПЪТУВАНЕ", type="primary", use_container_width=True, disabled=not potvurditel):
        try:
            df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8")
            df_all_data = df_all_data[df_all_data["trip_id"] != trip_id]
            df_all_data.to_csv(DATA_FILE, index=False, encoding="utf-8")
            if os.path.exists(papka_snimki):
                for img_path in glob.glob(os.path.join(papka_snimki, "*")):
                    os.remove(img_path)
                os.rmdir(papka_snimki)
            st.success(f"Изтрито!")
            st.rerun()
        except: pass
else:
    st.info("👋 Добре дошли! Моля, изберете съществуващо пътуване от менюто горе или натиснете '➕ СЪЗДАЙ НОВО ПЪТУВАНЕ', за да започнете.")
