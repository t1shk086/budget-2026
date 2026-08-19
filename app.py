import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim


st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

st.markdown("""
<style>
    /* Луксозен, дълбок уеб градиент, който прелива плавно по целия екран */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #090b0e 0%, #11151c 50%, #0d1117 100%) !important;
        background-attachment: fixed !important;
    }
    
    /* Фин предпазен слой за перфектен контраст на белия текст */
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.15) !important;
        z-index: -1;
        pointer-events: none;
    }

    /* Модерни полупрозрачни полета (Glassmorphism ефект) */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important; 
        padding: 10px 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        backdrop-filter: blur(4px) !important;
        -webkit-backdrop-filter: blur(4px) !important;
        margin-bottom: 15px !important;
    }

    /* Професионални тъмни бутони с дълбока сянка */
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"],
    [data-testid="stFileUploaderDropzone"] button {
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

    /* Елегантен светлинен ефект при посочване на бутоните */
    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFileUploaderDropzone"] button:hover {
        background: linear-gradient(135deg, #2e343f, #1c2028) !important;
        transform: translateY(-1px) !important; 
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.15) !important;
        border-color: rgba(0, 242, 254, 0.2) !important;
    }

    small { color: #7e8494 !important; }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"

if not os.path.exists(MAP_FILE):
    pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(MAP_FILE, index=False, encoding="utf-8")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), 
                (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])]:
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

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        f = df[df["trip_id"] == t_id]
        if not f.empty:
            res = f.iloc[0].to_dict()
            return {
                "trip_id": t_id, 
                "car_trip": str(res.get("car_trip", "Не")), 
                "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), 
                "start_km": float(res.get("start_km", 0.0)), 
                "end_km": float(res.get("end_km", 0.0)), 
                "manual_fuel": float(res.get("manual_fuel", 0.0)), 
                "start_date": str(res.get("start_date", "")), 
                "end_date": str(res.get("end_date", ""))
            }
    except: 
        pass
    return d

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: 
        pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "current_km" not in df.columns: df["current_km"] = 0.0
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: 
        return False

def get_map_points(t_id):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        return df[df["trip_id"] == t_id].copy()
    except: 
        return pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        df = pd.read_csv(MAP_FILE, encoding="utf-8")
        row = {"trip_id": t_id, "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(MAP_FILE, index=False, encoding="utf-8")
        return True
    except: 
        return False
if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0
if "view_photos" not in st.session_state: st.session_state["view_photos"] = False

if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center; margin-bottom: 5px;'><h1 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 10px rgba(0, 242, 254, 0.2); margin-bottom: 0px;'>🐾 PixelApp</h1><p style='font-family: \"Segoe UI\", Roboto, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; margin-top: 4px; margin-bottom: 30px;'>Travel Manager</p></div>", unsafe_allow_html=True)
    
    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("✔️ Зареди", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_"); st.rerun()
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-bottom:15px;'>Все още нямате записани почивки. Създайте първото си приключение по-долу!</div>", unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>", unsafe_allow_html=True)
    
    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:").strip()
        d_range = st.date_input("Изберете дати за почивката:", value=[datetime.date.today(), datetime.date.today()])
        st.write("---"); st.write("🚗 Пътувате ли със собствен автомобил?")
        viber_car = st.radio("Изберете variant:", ["Не, с друг транспорт", "Да, със собствен автомобил"], index=0)
        new_skm = 0.0
        if viber_car == "Да, със собствен автомобил":
            new_skm = st.number_input("Начални километри (км):", value=None, placeholder="Въведете км на тръгване...", step=1.0)
        if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True, type="primary") and txt:
            if isinstance(d_range, (list, tuple)):
                s_d_str = d_range[0].strftime("%d.%m.%Y") if len(d_range) > 0 else ""
                e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 else s_d_str
            elif hasattr(d_range, "strftime"): s_d_str = d_range.strftime("%d.%m.%Y"); e_d_str = s_d_str
            else: s_d_str, e_d_str = "", ""
            sk = float(new_skm) if new_skm is not None else 0.0
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, "Да" if viber_car == "Да, със собствен автомобил" else "Не", "Да" if viber_car == "Да, със собствен автомобил" else "Добави впоследствие", sk, 0.0, 0.0, s_d_str, e_d_str)
            try:
                geolocator = Nominatim(user_agent="pixelapp_travel_manager_2026")
                location = geolocator.geocode(f"{txt}, Europe", language="bg,en")
                if location: add_map_point(target_id, location.latitude, location.longitude, f"🏁 Център: {txt}", "red")
            except: pass
            st.session_state["current_trip"] = target_id; st.rerun()

    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
else:
    trip_id = st.session_state["current_trip"]
    papka_snimki = f"snimki_{trip_id}_2026"
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    @st.dialog("🗑️ Потвърждение за изтриване")
    def confirm_delete_dialog():
        if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
            st.write("Сигурни ли сте, че искате да изтриете този разход?")
            idx = st.session_state["delete_idx"]
            try:
                df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                r = df_all.loc[idx]
                st.markdown(f"**{get_emoji(r['category'])} {r['category']}** — <span style='color:#ff4b4b; font-weight:bold;'>{r['amount']:.2f} EUR</span><br><small>{r['description']}</small>", unsafe_allow_html=True)
            except: pass
            c_del1, c_del2 = st.columns(2)
            with c_del1:
                if st.button("✔️ ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                    try:
                        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                        df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8")
                    except: pass
                    st.session_state["delete_idx"] = None; st.rerun()
            with c_del2:
                if st.button("✖️ ОТКАЗ", use_container_width=True): st.session_state["delete_idx"] = None; st.rerun()

    @st.dialog("🚨 Изтриване на цялото пътуване")
    def confirm_delete_trip_dialog():
        st.error(f"ВНИМАНИЕ! Изтриване на пътуването до {trip_id.replace('_', ' ')}?")
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            if st.button("✔️ ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
                try:
                    pd.read_csv(DATA_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
                    pd.read_csv(SETTINGS_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
                    if os.path.exists(papka_snimki):
                        for p in glob.glob(os.path.join(papka_snimki, "*")): os.remove(p)
                        os.rmdir(papka_snimki)
                except: pass
                st.session_state["current_trip"] = None; st.rerun()
        with c_tr2:
            if st.button("✖️ ОТКАЗ", use_container_width=True): st.rerun()

    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    total_liters_sum, auto_fuel_money = 0.0, 0.0
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
        if row["category"] == "Транспорт":
            if float(row.get("liters", 0)) > 0: total_liters_sum += float(row["liters"]); auto_fuel_money += float(row["amount"])
            elif any(k in str(row["description"]).lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): auto_fuel_money += float(row["amount"])
    
    total_liters_calculated = total_liters_sum + m_fuel
    max_current_km = float(df_expenses["current_km"].max()) if not df_expenses.empty and "current_km" in df_expenses.columns else 0.0
    eff_end_km = e_km if e_km > 0 else max_current_km
    dist = eff_end_km - s_km if eff_end_km > s_km else 0.0

    # 🌟 КОПИРАЙ И ЗАМЕНИ С ТОВА ЗА ПРАВИЛЕН КРАЕН РАЗХОД:
    progressive_avg_con, has_progressive_data = 0.0, False
    try:
        df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
        # Търсим само записите, при които резервоарът е напълнен "ДО ГОРЕ" (ПЪЛНО или ПЪЛЕН)
        df_full_points = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
        
        if not df_full_points.empty:
            # Смятаме разхода до последната сигурна точка, в която резервоарът е бил пълен
            last_full_km = float(df_full_points.iloc[-1]["current_km"])
            total_dist = last_full_km - s_km
            
            # Взимаме абсолютно всички литри (начални + частични + пълни) до тази последна точка
            total_liters = float(df_trans_fuel[df_trans_fuel["current_km"] <= last_full_km]["liters"].sum()) + m_fuel
            
            if total_dist > 0 and total_liters > 0:
                progressive_avg_con = (total_liters / total_dist * 100)
                has_progressive_data = True
    except: 
        pass








        
 

        # Ред 2: Перфектно центрираното заглавие и датите отдолу
        date_html = f"<p style='font-size: 14px; color: #888; font-weight: 500; margin-top: 5px; margin-bottom: 0;'>{st_date} - {en_date}</p>" if st_date and st_date != "nan" else ""
        st.markdown(f"<div style='text-align: center; margin-top: -10px; margin-bottom: 10px; width: 100%;'><h2 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 500; font-size: 26px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; padding: 0;'>🌴 Дестинация: {trip_id.replace('_', ' ')}</h2>{date_html}</div>", unsafe_allow_html=True)
        
        st.markdown("---")




        # 🌟 КОПИРАЙ И СЛОЖИ ТОЗИ РЕД ТУК (за да знае браузърът къде е "най-горе"):
        st.markdown("<div id='trip_top_anchor' style='scroll-margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        ekran_za_kategorii = st.empty()


        if st.button("🔙 НАЗАД КЪМ ИЗБОР НА ПОЧИВКА", use_container_width=True): 
            st.session_state["current_trip"] = None
            st.rerun()

        v_id = st.session_state["form_version"]
        
        # Премахваме опасния марджин, който застъпваше бутона, и правим чиста котва
        st.markdown('<div id="target_sum_box" style="position: relative; scroll-margin-top: 30px;"></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1: s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Напишете сума...", format="%.2f", key=f"su_{v_id}")
        with col2: o_input = st.text_input("Описание", placeholder="Напишете описание...", key=f"op_{v_id}")

        
        is_trip_finished = (e_km > 0.0)

        
        is_trip_finished = (e_km > 0.0)



        @st.dialog("⛽ Зареждане на гориво")
        def fuel_modal(amount, category, description, is_dep):
            if is_trip_finished: st.error("🔒 Пътуването е приключено!"); return
            liters = st.number_input("Литри:", value=None, placeholder="Напишете литри...", step=0.1)
            fuel_type = st.radio("Тип на зареждането:", ["Да, до горе (Пълен резервоар)", "Не, частично (за конкретна сума)"], index=0)
            
            # Взимаме всички транспортни записи с въведени километри
            df_f = get_trip_data(trip_id)[lambda d: (d["category"] == "Транспорт") & (d["current_km"] > 0)].sort_index()
            last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
            km_input = st.number_input("Текущи километри на таблото (км):", value=None, placeholder="Въведете км...", step=1.0)
            
            total_segment_liters = 0.0
            segment_dist = 0.0
            
            # Изчисляване на етапен разход на екрана ПРЕДИ запис (само при ПЪЛНО зареждане)
            if liters and km_input and km_input > last_km and "до горе" in fuel_type.lower():
                # Търсим кога за последно резервоарът е бил зареден ДО ГОРЕ (ПЪЛЕН или ПЪЛНО)
                df_since_full = df_f[df_f["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
                if not df_since_full.empty:
                    last_full_km = float(df_since_full.iloc[-1]["current_km"])
                    # Взимаме всички частични литри, заредени СЛЕД последното пълно зареждане
                    partial_liters = float(df_f[df_f["current_km"] > last_full_km]["liters"].sum())
                    total_segment_liters = partial_liters + liters
                    segment_dist = km_input - last_full_km
                else:
                    # Ако няма предишно пълно зареждане, смятаме от началото на пътуването
                    total_segment_liters = float(df_f["liters"].sum()) + liters + m_fuel
                    segment_dist = km_input - s_km
                
                if segment_dist > 0 and total_segment_liters > 0:
                    st.success(f"📊 Реален разход за етапа: **{(total_segment_liters / segment_dist * 100):.1f} л / 100 км**")
            
            if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
                lit, ckm = (float(liters) if liters is not None else 0.0), (float(km_input) if km_input is not None else 0.0)
                is_full = "ПЪЛНО" if "до горе" in fuel_type.lower() else "ЧАСТИЧНО"
                full_desc = f"[{is_full} ЗАРЕЖДАНЕ] {description}"
                
                # Ако записваме ПЪЛНО зареждане, пресмятаме реалните данни за описанието в историята
                if ckm > last_km and lit > 0 and is_full == "ПЪЛНО":
                    df_since_full = df_f[df_f["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
                    if not df_since_full.empty:
                        last_full_km = float(df_since_full.iloc[-1]["current_km"])
                        partial_liters = float(df_f[df_f["current_km"] > last_full_km]["liters"].sum())
                        t_liters = partial_liters + lit
                        t_dist = ckm - last_full_km
                    else:
                        t_liters = float(df_f["liters"].sum()) + lit + m_fuel
                        t_dist = ckm - s_km
                    
                    if t_dist > 0 and t_liters > 0:
                        full_desc += f" (Етап: {t_dist:.0f}км, Реален разход: {(t_liters / t_dist * 100):.1f}л/100км)"
                
                if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm): 
                    st.session_state["form_version"] += 1
                    st.rerun()


       
        # Проверка дали потребителят е въвел описание и е натиснал Enter
        if o_input.strip() and s_input and s_input > 0:
            header_text = f"Записване на: <b>{s_input:.2f} EUR</b> за <i>\"{o_input.strip()}\"</i>"
            
            # Използваме контейнера най-горе на екрана, за да "застъпим" всичко останало
            with ekran_za_kategorii.container():
                st.markdown(f"""
                <div style='text-align: center; margin: 10px 0 20px 0; animation: fadeIn 0.4s ease-in-out;'>
                    <h3 style='color: #00f2fe; font-family: "Segoe UI", sans-serif; font-weight: 700; margin-bottom: 5px;'>🎯 ИЗБЕРЕТЕ КАТЕГОРИЯ</h3>
                    <p style='color: #aaa; font-size: 14px; margin-bottom: 15px;'>{header_text}</p>
                </div>
                <style>
                    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
                </style>
                """, unsafe_allow_html=True)
                
                grid = st.columns(3)
                for i, kat in enumerate(KATEGORII):
                    with grid[i % 3]:
                        is_disabled = is_trip_finished and (kat == "Транспорт")
                        if st.button(f"🔒 {kat}" if is_disabled else kat, use_container_width=True, key=f"bt_{i}", disabled=is_disabled):
                            desc, is_d = o_input.strip(), (kat == "Депозит/Резервация")
                            if kat == "Транспорт" and any(k in desc.lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): 
                                fuel_modal(s_input, kat, desc, is_d)
                            else:
                                if add_expense(trip_id, s_input, kat, desc, is_d): 
                                    st.session_state["form_version"] += 1
                                    st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("❌ ОКОНЧАТЕЛЕН ОТКАЗ / НАЗАД", use_container_width=True):
                    st.session_state["form_version"] += 1
                    st.rerun()
                
                st.markdown("---")
                # Спираме кода тук, така че старите полета за въвеждане и хронологията изобщо да не се рендерират отдолу!
                st.stop()


        if car_trip == "Да":
            val_to_show, is_final_status = 0.0, False
            try:
                df_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] >= s_km)].sort_values(by="current_km")
                total_valid_liters, total_valid_dist, prev_km, temp_liters = 0.0, 0.0, s_km, 0.0
                for _, row in df_fuel.iterrows():
                    current_entry_km = float(row["current_km"])
                    if current_entry_km == s_km: continue
                    stage_dist = current_entry_km - prev_km
                    if stage_dist > 0:
                        temp_liters += float(row.get("liters", 0.0))
                        if "ПЪЛЕН" in str(row["description"]).upper():
                            total_valid_dist += stage_dist; total_valid_liters += temp_liters
                            temp_liters, prev_km = 0.0, current_entry_km
                total_valid_liters += m_fuel
                if total_valid_dist > 0 and total_valid_liters > 0: val_to_show = (total_valid_liters / total_valid_dist) * 100
                if e_km > s_km:
                    is_final_status = True
                    if val_to_show == 0.0 and total_liters_calculated > 0: val_to_show = (total_liters_calculated / dist) * 100
            except: pass

            km_progress_pct = 100 if is_final_status else min(100, max(0, (dist / 1000 * 100))) if dist > 0 else 0
            finish_icon_html = f"<div style='position: absolute; right: 0; top: -8px; background: #1c1c1c; border: 2px solid #ff4b4b; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>F</div>" if is_trip_finished else f"<div style='position: absolute; left: calc({km_progress_pct}% - 10px); top: -12px; font-size: 16px;'>🚗</div>"

            val_to_show = 0.0
            label_to_show = "последен затворен етап"
            
            if is_trip_finished:
                val_to_show = progressive_avg_con if 'progressive_avg_con' in locals() else 0.0
                label_to_show = "финален среден разход"
            else:
                try:
                    df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
                    df_only_full = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
                    
                    if not df_only_full.empty:
                        last_full_row = df_only_full.iloc[-1]["description"]
                        import re
                        match = re.search(r"(?:Реален разход:|Разход:)\s*([0-9.]+)", last_full_row)
                        if match:
                            val_to_show = float(match.group(1))
                        else:
                            val_to_show = progressive_avg_con if 'progressive_avg_con' in locals() else 0.0
                    else:
                        if not df_trans_fuel.empty:
                            current_dist = float(df_trans_fuel.iloc[-1]["current_km"]) - s_km
                            current_liters = float(df_trans_fuel["liters"].sum()) + m_fuel
                            if current_dist > 0 and current_liters > 0:
                                val_to_show = (current_liters / current_dist * 100)
                                label_to_show = "среден разход до момента"
                            else:
                                val_to_show = 0.0
                        else:
                            val_to_show = 0.0
                except:
                    val_to_show = 0.0

            color_gauge = "#00f2fe" if val_to_show < 6.0 else ("#ffa500" if val_to_show < 8.5 else "#ff4b4b")
            transport_liters = float(df_expenses[df_expenses['category'] == 'Транспорт']['liters'].sum()) + m_fuel

            # Изчертаване на Данните за Пробега най-отгоре
            st.markdown(f"### 🚗 Данни за километраж и пробег")
            st.markdown(f"<div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center;'><div style='display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 5px; position: relative;'><span style='font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;'>📍 СЛЕДЕНЕ НА ПРОБЕГА</span>{f'<span style=\"background:rgba(255,75,75,0.15); color:#ff4b4b; font-size:10px; padding:2px 8px; border-radius:10px; font-weight:bold;\">🔒 ЗАКЛЮЧЕН</span>' if is_trip_finished else ''}</div><div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 25px 15px 15px 15px;'><div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div><div style='position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>S</div>{finish_icon_html}</div><div style='display: flex; justify-content: space-between; font-size: 13px; padding: 0 10px; gap: 10px;'><div style='text-align: left;'><span style='color: #666; display: block; font-size: 11px;'>Старт</span><b style='color: white; font-size: 14px;'>{s_km:.0f} км</b></div><div style='text-align: center;'><span style='color: #666; display: block; font-size: 11px;'>Изминати</span><b style='color: #00f2fe; font-size: 14px;'>{dist:.0f} км</b></div><div style='text-align: right;'><span style='color: #666; display: block; font-size: 11px;'>Краен</span><b style='color: white; font-size: 14px;'>{f'{eff_end_km:.0f} км' if eff_end_km > 0 else '—'}</b></div></div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 15px; width: 100%;'><div style='flex: 1; min-width: 280px; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center;'><div style='color: #888; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 15px;'>ТЕКУЩ РАЗХОД</div><div style='width: 110px; height: 110px; border-radius: 50%; border: 4px dashed {color_gauge}; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: inset 0 0 15px rgba(0,0,0,0.6); margin-bottom: 15px;'><div style='color: white; font-size: 28px; font-weight: 900; line-height: 1.1;'>{val_to_show:.1f}</div><div style='color: #666; font-size: 10px; font-weight: bold; margin-top: 2px;'>л/100км</div></div><div style='color: #666; font-size: 11px;'>{label_to_show}</div></div><div style='flex: 1; min-width: 280px; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 25px 20px; border-radius: 16px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center; box-shadow: 4px 4px 12px rgba(0,0,0,0.3);'><div style='margin-bottom: 25px; width: 100%; text-align: center;'><div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 8px;'>💧 ОБЩО ЗАРЕДЕНО ГОРИВО</div><div style='color: white; font-size: 28px; font-weight: 800;'>{transport_liters:.1f} <span style='font-size: 14px; color: #666; font-weight: normal;'>литра</span></div></div><div style='padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.06); width: 100%; text-align: center;'><div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 8px;'>💰 ОБЩА СТОЙНОСТ ТРАНСПОРТ</div><div style='color: white; font-size: 28px; font-weight: 800;'>{auto_fuel_money:.2f} <span style='font-size: 14px; color: #666; font-weight: normal;'>EUR</span></div></div></div></div><br>", unsafe_allow_html=True)
        # Сега изграждаме Анализа на разходите отдолу
        # =========================================================
        # ⚙️ БУТОНИ ЗА УПРАВЛЕНИЕ НА КОЛАТА (СЕГА СА НАД АНАЛИЗА)
        # =========================================================
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        @st.dialog("⚙️ Настройки за автомобил и период")
        def edit_car_modal():
            v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=0 if car_trip == "Не" else 1, disabled=is_trip_finished)
            new_sk = st.number_input("Начални км:", value=None if s_km == 0.0 else s_km, disabled=is_trip_finished)
            new_mf = st.number_input("Добави пропуснато гориво (л):", value=None if m_fuel == 0.0 else m_fuel, disabled=is_trip_finished)
            has_cash_expense = st.checkbox("💵 Има ли финансов разход за добавеното гориво?") if (new_mf and new_mf > 0 and not is_trip_finished) else False
            manual_cash_amt = st.number_input("Въведете платена сума (EUR):", value=None, format="%.2f") if has_cash_expense else 0.0
            try:
                current_start = datetime.datetime.strptime(st_date, "%d.%m.%Y").date() if st_date and st_date != "nan" else datetime.date.today()
                current_end = datetime.datetime.strptime(en_date, "%d.%m.%Y").date() if en_date and en_date != "nan" else datetime.date.today() + datetime.timedelta(days=5)
            except: current_start, current_end = datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)
            edit_range = st.date_input("Изберете нови дати:", value=[current_start, current_end], key="edit_dates_cal")
            if st.button("💾 Обнови", use_container_width=True, type="primary", disabled=is_trip_finished):
                sk_val, mf_val = (float(new_sk) if new_sk is not None else 0.0), (float(new_mf) if new_mf is not None else 0.0)
                s_d_str = edit_range[0].strftime("%d.%m.%Y") if (isinstance(edit_range, (list, tuple)) and len(edit_range) > 0) else st_date
                e_d_str = edit_range[-1].strftime("%d.%m.%Y") if (isinstance(edit_range, (list, tuple)) and len(edit_range) > 1) else s_d_str
                if has_cash_expense and manual_cash_amt and manual_cash_amt > 0: add_expense(trip_id, manual_cash_amt, "Транспорт", f"[ПРОПУСНАТО ГОРИВО] Добавени {mf_val:.1f} литра", False, 0.0, 0.0)
                save_trip_settings(trip_id, str(v_car), "Да", sk_val, e_km, mf_val, s_d_str, e_d_str); st.session_state["form_version"] += 1; st.rerun()

        @st.dialog("🏁 Край на пътуването")
        def finish_trip_modal():
            end_km_input = st.number_input("Финални километри от таблото (км):", value=None if e_km == 0.0 else e_km, step=1.0)
            if st.button("🔒 ЗАКЛЮЧИ И ПРИКЛЮЧИ", use_container_width=True, type="primary"):
                if end_km_input and end_km_input > s_km: save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date); st.session_state["form_version"] += 1; st.rerun()
                else: st.error(f"Трябва да са над {s_km:.0f} км!")

        if car_trip == "Да":
            col_manage1, col_manage2 = st.columns(2)
            with col_manage1: st.button("🔒 Заключени настройки" if is_trip_finished else "⚙️ Настройки кола", use_container_width=True, disabled=is_trip_finished, on_click=edit_car_modal)
            with col_manage2: st.button("🏁 Пътуването е приключено 🔒" if is_trip_finished else "🏁 Край на пътуването", use_container_width=True, disabled=is_trip_finished, on_click=finish_trip_modal)
        else:
            if st.button("🚗 Добави автомобил към пътуването", use_container_width=True): edit_car_modal()

        st.markdown("<br>", unsafe_allow_html=True)

        # =========================================================
        # 📊 АНАЛИЗ НА РАЗХОДИТЕ (СЕГА Е ПОД БУТОНИТЕ)
        # =========================================================
        st.markdown("### 📊 Анализ на разходите")
        stat_grid = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            with stat_grid[idx % 2]:
                pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
                
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 14px; border-radius: 14px; margin-bottom: 12px; box-shadow: 4px 4px 10px rgba(0,0,0,0.3); display: flex; flex-direction: column; justify-content: space-between;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 500; font-size: 15px;">{get_emoji(kat)} {kat}</span>
                        <span style="font-weight: bold; color: #ff4b4b; font-size: 15px;">{s_value:.2f} EUR</span>
                    </div>
                    <div style="background: rgba(0, 0, 0, 0.4); height: 16px; border-radius: 20px; padding: 2px; box-shadow: inset 2px 2px 5px rgba(0,0,0,0.5), inset -1px -1px 2px rgba(255,255,255,0.05); position: relative; display: flex; align-items: center; overflow: hidden; margin-top: 4px;">
                        <div style="width: {pct}%; height: 100%; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); border-radius: 20px; box-shadow: 2px 2px 5px rgba(0, 242, 254, 0.4), inset 0 2px 2px rgba(255,255,255,0.3); transition: width 0.5s ease-in-out;"></div>
                        <span style="position: absolute; right: 8px; font-size: 10px; font-weight: 900; color: rgba(255,255,255,0.85); text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">{pct:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center; margin-bottom: 12px;'><small style='color:#aaa; font-weight:bold;'>🏨 ДЕПОЗИТ</small><h2 style='color:#ff4b4b; margin:5px 0;'>{depozit_hotel:.2f} <span style='font-size: 14px; font-weight: 500; color: #7e8494;'>EUR</span></h2></div>", unsafe_allow_html=True)
        with col_st2:
            st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center;'><small style='color:#aaa; font-weight:bold;'>💰 НА МЯСТО</small><h2 style='color:#00f2fe; margin:5px 0;'>{total_on_site:.2f} <span style='font-size: 14px; font-weight: 500; color: #7e8494;'>EUR</span></h2></div>", unsafe_allow_html=True)

        if not df_trip.empty:
            st.markdown("---")

            # =========================================================
            # 📜 ДЕФИНИЦИЯ НА ИЗСКАЧАЩИЯ ПРОЗОРЕЦ ЗА ХРОНОЛОГИЯ
            # =========================================================
            @st.dialog("📜 Хронология на плащанията", width="large")
            def hronologia_popup_dialog():
                st.markdown("<p style='color: #888; margin-bottom: 20px;'>Всички записани разходи за текущото пътуване по категории и дати:</p>", unsafe_allow_html=True)
                
                st.markdown("""
                    <style>
                        .premium-expense-card {
                            background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%) !important;
                            padding: 14px 18px !important;
                            border-radius: 12px !important;
                            border: 1px solid rgba(250, 250, 250, 0.2) !important;
                            box-shadow: 0px 4px 12px rgba(0,0,0,0.2) !important;
                            margin-bottom: 2px !important;
                            min-height: 52px !important;
                            display: flex !important;
                            flex-direction: column !important;
                            justify-content: center !important;
                        }
                        .expense-delete-wrapper {
                            display: flex !important;
                            align-items: center !important;
                            justify-content: center !important;
                            height: 100% !important;
                            margin-top: 10px !important;
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                try:
                    df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                    valid_expenses = df_all[df_all["trip_id"] == trip_id].index.tolist()
                    
                    if not valid_expenses:
                        st.info("Няма регистрирани разходи за това пътуване.")
                    else:
                        for idx in reversed(valid_expenses):
                            # Сигурна проверка: Ако индексът случайно е изтрит в рамките на текущия цикъл, го прескачаме без грешка
                            if idx not in df_all.index:
                                continue
                                
                            r = df_all.loc[idx]
                            l_txt = f" | ⛽ {r['liters']:.1f} л" if float(r.get("liters", 0)) > 0 else ""
                            
                            col_rec, col_del = st.columns([0.88, 0.12])
                            
                            with col_rec:
                                st.markdown(f'''
                                    <div class="premium-expense-card">
                                        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                                            <div style="font-size: 16px; font-weight: 600; color: #fafafa;">
                                                <span>{get_emoji(r["category"])}</span> {r["category"]}
                                            </div>
                                            <div style="font-size: 16px; font-weight: 700; color: #ff4b4b; letter-spacing: 0.5px;">
                                                -{r["amount"]:.2f} EUR
                                            </div>
                                        </div>
                                        <div style="margin-top: 6px; font-size: 12.5px; color: rgba(250,250,250,0.5); font-family: sans-serif;">
                                            📅 {r["date"]} — <span style="color: rgba(250,250,250,0.75);">{r["description"]}</span>{l_txt}
                                        </div>
                                    </div>
                                ''', unsafe_allow_html=True)
                                
                            with col_del:
                                st.markdown('<div class="expense-delete-wrapper">', unsafe_allow_html=True)
                                if st.button("🗑️", key=f"quick_del_{idx}", use_container_width=True, help="Изтрий веднага"):
                                    # Първо прочитаме наново за абсолютна сигурност, трием и записваме
                                    df_fresh = pd.read_csv(DATA_FILE, encoding="utf-8")
                                    df_fresh.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8")
                                    st.session_state["form_version"] += 1
                                    # Моментално прекратяваме изпълнението, за да не се счупи цикъла отдолу!
                                    st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error("Грешка при зареждане на хронологията.")
                
                st.markdown("---")
                if st.button("❌ Изход", use_container_width=True, key="close_hronologia_popup_btn"):
                    st.rerun()



            # =========================================================
            # 📊 ПОДГОТОВКА НА ДАННИТЕ ЗА КРАЙНИЯ ОТЧЕТ
            # =========================================================
            avg_con_txt = f"{(total_liters_calculated / dist * 100):.1f} л / 100 км" if dist > 0 else (f"{progressive_avg_con:.1f} л / 100 км" if has_progressive_data else "Няма данни")
            grand_total = depozit_hotel + total_on_site
            period_html = f" | <b>Период:</b> {st_date} - {en_date}" if st_date and st_date != "nan" else ""
            dist_html = f" | <b>Общо изминати км. :</b> {dist:.0f} км" if dist > 0 else ""
            
            pdf_html = f"<html><head><meta charset='utf-8'><style>body{{font-family:sans-serif;padding:30px;color:#333;}}h2{{color:#222;border-bottom:2px solid #00f2fe;padding-bottom:8px;margin-bottom:15px;}}h3{{color:#4facfe;margin-top:20px;border-bottom:1px solid #eee;padding-bottom:5px;}}table{{width:100%;border-collapse:collapse;margin-top:15px;}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd;}}th{{background:#f5f5f5;}}.fuel-highlight{{color:#ff1493;font-weight:bold;}}.badge-km{{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:12px;color:#555;font-weight:bold;}}</style></head><body><h2>ОТЧЕТ: {trip_id.upper().replace('_', ' ')}</h2><p style='font-size:15px;'><b>Депозит:</b> {depozit_hotel:.2f} EUR | <b>На място:</b> {total_on_site:.2f} EUR{period_html}{dist_html}</p><p style='font-size:18px; color:#ff4b4b; background:#fff5f5; padding:10px; border-left:4px solid #ff4b4b; margin-top:10px;'><b>💰 ОБЩА СУМА: {grand_total:.2f} EUR</b></p><h3>🚗 Кола:</h3><ul><li><b>Начални:</b> {s_km:.0f} км | <b>Крайна:</b> {eff_end_km:.0f} км</li><li><b>Гориво:</b> {total_liters_calculated:.1f} л | <b>Стойност:</b> {auto_fuel_money:.2f} EUR</li><li><b>Среден разход:</b> {avg_con_txt}</li></ul><h3>📋 Разходи:</h3><table><tr><th>Дата и час</th><th>Описание</th><th>Километраж</th><th>Сума</th><th>Категория</th></tr>"
            
            for _, row in df_trip.iterrows():
                desc_val = str(row['description'])
                if "Моментен разход:" in desc_val:
                    desc_val = desc_val.replace("Моментен разход:", "<span class='fuel-highlight'>Моментен разход:</span>")
                cur_km_val = float(row.get('current_km', 0.0))
                km_td_html = f"<span class='badge-km'>{cur_km_val:.0f} км</span>" if cur_km_val > 0 else "<span style='color:#ccc;'>—</span>"
                pdf_html += f"<tr><td>{row['date']}</td><td>{desc_val}</td><td>{km_td_html}</td><td>{row['amount']:.2f} EUR</td><td>{row['category']}</td></tr>"
                
            pdf_html += f"<tr><td colspan='3' style='text-align:right; font-weight:bold;'>Общо:</td><td colspan='2' style='font-weight:bold; color:#ff4b4b;'>{grand_total:.2f} EUR</td></tr></table></body></html>"
            # =========================================================
            # 👑 ОБЕДИНЕН ЧИСТ STREAMLIT БЛОК С БУТОНИ
            # =========================================================
            
            
            # Изместваме скрития HTML маркер извън блока с бутоните, за да не отваря празно място
            st.markdown("<a id='click_scroll_trigger' href='#top_of_page' style='display:none;'></a>", unsafe_allow_html=True)
            
            # 1. Оригинален бутон за Хронология
            if st.button("♾️ Хронология на Разходите", use_container_width=True, key="open_hronologia_popup_trigger"):
                hronologia_popup_dialog()

            # 2. Фабричен бутон за изтегляне (Download Button) на Streamlit
            st.download_button(
                label="Отчет в PDF",
                data=pdf_html,
                file_name=f"Otchet_{trip_id}_2026.html",
                mime="text/html",
                use_container_width=True,
                key="st_premium_report_download_btn"
            )


            st.markdown("---") # Крайна обща линия след пакета с бутони






        # 7. Карта на спирките и дестинациите (Folium) - Финална версия с динамичен ключ
        st.subheader("🗺️ Карта на спирките и дестинациите")
        df_points = get_map_points(trip_id)
        
        # Рестартиране на центъра и зуума единствено при пълна смяна на пътуването
        if "map_current_trip_id" not in st.session_state or st.session_state["map_current_trip_id"] != trip_id:
            st.session_state["map_current_trip_id"] = trip_id
            if not df_points.empty:
                st.session_state["stable_lat"] = float(df_points["lat"].mean())
                st.session_state["stable_lon"] = float(df_points["lon"].mean())
                st.session_state["stable_zoom"] = 8
            else:
                st.session_state["stable_lat"] = 42.7339
                st.session_state["stable_lon"] = 25.4858
                st.session_state["stable_zoom"] = 6

        # Създаваме картата с последно запазените в сесията параметри
        m = folium.Map(
            location=[st.session_state["stable_lat"], st.session_state["stable_lon"]], 
            zoom_start=st.session_state["stable_zoom"]
        )
        m.get_root().html.add_child(folium.Element("<script>document.documentElement.lang = 'bg';</script>"))
        folium.LatLngPopup().add_to(m)
        
        for _, pt in df_points.iterrows(): 
            folium.Marker(
                location=[pt["lat"], pt["lon"]], 
                popup=pt["title"], 
                icon=folium.Icon(color=pt["color"], icon="info-sign")
            ).add_to(m)
        
        # ДИНАМИЧЕН КЛЮЧ: Променя се спрямо броя точки и състоянието на клика.
        # Това принуждава браузъра да приложи новия stable_zoom веднага, без да го нулира!
        points_count = len(df_points)
        click_state = "active" if "active_click" in st.session_state and st.session_state["active_click"] is not None else "idle"
        dynamic_map_key = f"folium_map_{trip_id}_{points_count}_{click_state}"

        map_data = st_folium(
            m, 
            width=700, 
            height=400, 
            key=dynamic_map_key, 
            returned_objects=["last_clicked", "zoom"]
        )

        # Обработка на клик за нова точка
        if map_data and map_data.get("last_clicked"):
            new_click = map_data["last_clicked"]
            if st.session_state.get("active_click") != new_click: 
                st.session_state["stable_lat"] = new_click["lat"]
                st.session_state["stable_lon"] = new_click["lng"]
                
                # Хващаме точния зуум, на който е бил потребителят в момента на клика
                if map_data.get("zoom") is not None:
                    st.session_state["stable_zoom"] = map_data["zoom"]
                
                st.session_state["active_click"] = new_click
                st.rerun()
                
        if "active_click" in st.session_state and st.session_state["active_click"] is not None and not is_trip_finished:
            click_coords = st.session_state["active_click"]
            st.markdown(f"📌 **Избрано място:** Ширина: `{click_coords['lat']:.4f}`, Дължина: `{click_coords['lng']:.4f}`")
            c_m1, c_m2 = st.columns([0.7, 0.3])
            with c_m1: title_in = st.text_input("Име на новата спирка:", placeholder="напр. Хотел...", key="map_title_click")
            with c_m2: color_in = st.selectbox("Цвят:", ["blue", "green", "red", "purple", "orange"], key="map_color_click")
            cb1, cb2 = st.columns([0.7, 0.3])
            with cb1:
                if st.button("💾 Запис", use_container_width=True, type="primary") and title_in:
                    if add_map_point(trip_id, click_coords["lat"], click_coords["lng"], title_in, color_in): 
                        # При успешен запис държим същия зуум, който хванахме при клика!
                        st.session_state["active_click"] = None
                        st.rerun()
            with cb2:
                if st.button("❌ Отказ", use_container_width=True): 
                    st.session_state["active_click"] = None
                    st.rerun()





        if not df_points.empty:
            st.markdown("#### 📍 Любими места от пътуването")
            st.markdown("---")
            try:
                df_all_map = pd.read_csv(MAP_FILE, encoding="utf-8")
                color_emojis = {"blue": "🔵", "green": "🟢", "red": "🔴", "purple": "🟣", "orange": "🟠"}
                for idx in df_all_map[df_all_map["trip_id"] == trip_id].index.tolist():
                    pt_row = df_all_map.loc[idx]
                    col_p_txt, col_p_del = st.columns([0.85, 0.15])
                    with col_p_txt:
                        st.markdown(f"{color_emojis.get(pt_row['color'], '🔵')} **{pt_row['title']}** <small>({pt_row['lat']:.4f}, {pt_row['lon']:.4f})</small>", unsafe_allow_html=True)
                    with col_p_del:
                        if st.button("❌", key=f"del_pin_{idx}", use_container_width=True, disabled=is_trip_finished):
                            df_all_map.drop(idx).to_csv(MAP_FILE, index=False, encoding="utf-8")
                            st.rerun()
            except:
                pass

     

            
        st.markdown("---")
        if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True, key="delete_whole_trip_final_btn"):
            confirm_delete_trip_dialog()
        # 🌟 КОПИРАЙ И ЗАМЕНИ НА САМИЯ КРАЙ НА ФАЙЛА СИ:
        # 🌟 КРАЙ НА ФАЙЛА: АБСОЛЮТНО ОГЛЕДАЛНИ 3Д БЛИЗНАЦИ С ЕДНАКВИ ЕФЕКТИ
        st.markdown("""
            <style>
                /* Глобално правило за плавно и нежно приплъзване на екрана */
                html {
                    scroll-behavior: smooth !important;
                }
                
                /* 👑 ЕДИНЕН ЛУКСОЗЕН 3Д ДИЗАЙН ЗА ДВАТА БУТОНА */
                .twin-premium-3d-btn {
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    width: 100% !important; 
                    height: 38.4px !important; /* Точната фабрична височина */
                    background: linear-gradient(to bottom, #262730 0%, #1a1c23 100%) !important; /* Тъмен графитен металик */
                    color: #ffffff !important; 
                    border: 1px solid rgba(255, 255, 255, 0.12) !important; /* Деликатен светъл ръб */
                    padding: 0.25rem 0.75rem !important;
                    font-weight: 600 !important;
                    font-size: 14px !important;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                    border-radius: 0.5rem !important;
                    cursor: pointer !important;
                    user-select: none !important;
                    /* 3D Обем: Твърдо сиво дъно отдолу + външна мека сянка */
                    box-shadow: 0px 3px 0px #0e1117, 0px 5px 10px rgba(0,0,0,0.35) !important;
                    transition: all 0.15s ease-in-out !important; /* Плавно преливане на ховъра */
                }
                
                /* 🌟 УЕДНАКВЕН ХОУВЪР: И двата бутона светват абсолютно еднакво нежно */
                .twin-premium-3d-btn:hover {
                    background: linear-gradient(to bottom, #31333e 0%, #22242d 100%) !important;
                    border-color: rgba(255, 255, 255, 0.3) !important;
                    box-shadow: 0px 3px 0px #0e1117, 0px 7px 14px rgba(0,0,0,0.45) !important;
                }
                
                /* 🌟 УЕДНАКВЕНО 3Д ПОТЪВАНЕ: И двата бутона хлътват по абсолютно един и същ начин при клик */
                .twin-premium-3d-btn:active {
                    transform: translateY(2px) !important; /* Бутоните потъват физически */
                    box-shadow: 0px 1px 0px #0e1117, 0px 2px 4px rgba(0,0,0,0.2) !important; /* Дъното се свива */
                    transition: all 0.05s ease !important;
                }
                
                /* Скриваме стандартните очертания на линковете в решетката */
                .twin-grid-wrapper a {
                    text-decoration: none !important;
                    width: 100% !important;
                    display: block !important;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Създаваме чистата решетка от 2 колони
        bottom_cols = st.columns(2)
        
        with bottom_cols[0]: # 🏠 Първи близнак: Главно Меню
            # Използваме уеб линк, който нулира пътуването и презарежда приложението чисто
            if st.button("🏠 ГЛАВНО МЕНЮ", use_container_width=True, key="fallback_home_trigger_btn"):
                st.session_state["current_trip"] = None
                st.rerun()
                
        with bottom_cols[1]: # 🎚️ Втори близнак: Към Разходите
            st.markdown("""
                <div class="twin-grid-wrapper">
                    <a href="#trip_top_anchor" target="_self">
                        <button class="twin-premium-3d-btn">
                            🔝 КЪМ РАЗХОДИТЕ
                        </button>
                    </a>
                </div>
            """, unsafe_allow_html=True)

        # =========================================================
        # 🛠️ СКРИТИ АДМИНИСТРАТИВНИ ИНСТРУМЕНТИ (БЕКАП И ВЪЗСТАНОВЯВАНЕ)
        # =========================================================
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        
        if "show_admin_panel" not in st.session_state:
            st.session_state["show_admin_panel"] = False

        if st.button("🛠️ Административни Инструменти", use_container_width=True, key="toggle_admin_panel_btn"):
            st.session_state["show_admin_panel"] = not st.session_state["show_admin_panel"]
            st.rerun()

        if st.session_state["show_admin_panel"]:
            st.markdown("""
                <div style="background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,255,255,0.15); padding: 15px; border-radius: 12px; margin-top: 10px;">
                    <h4 style="margin-top:0; color:#00f2fe;">📦 Архивиране и Възстановяване на данни</h4>
                    <p style="color: #aaa; font-size: 13px; margin-bottom: 15px;">Използвайте тази секция, за да свалите вашите данни локално или да ги качите обратно, ако сървърът се рестартира.</p>
                </div>
            """, unsafe_allow_html=True)
            
            col_backup1, col_backup2 = st.columns(2)
            
            with col_backup1:
                st.markdown("##### 📥 Сваляне на архив")
                try:
                    import zipfile
                    import io
                    
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for file_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE]:
                            if os.path.exists(file_name):
                                zip_file.write(file_name, arcname=file_name)
                    
                    # Фиксирано име на файла и маркер за презаписване от браузъра
                    st.download_button(
                        label="📥 Свали всички CSV логове (.ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="PixelApp_Data_Backup.zip",
                        mime="application/octet-stream",
                        use_container_width=True,
                        key="download_all_csv_backup_btn"
                    )
                except:
                    st.error("Грешка при генериране на архива.")
                    
            with col_backup2:
                st.markdown("##### 📤 Качване на архив")
                uploaded_zip = st.file_uploader(
                    "Качете сваления по-горе .ZIP файл тук:", 
                    type=["zip"], 
                    key="restore_all_csv_backup_uploader",
                    label_visibility="collapsed"
                )
                
                if uploaded_zip is not None:
                    if st.button("🔄 ВЪЗСТАНОВИ ДАННИТЕ СЕГА", use_container_width=True, type="primary", key="trigger_restore_data_btn"):
                        success_extract = False
                        try:
                            import zipfile
                            with zipfile.ZipFile(uploaded_zip) as zip_file:
                                namelist = zip_file.namelist()
                                restored_count = 0
                                for f_name in [DATA_FILE, SETTINGS_FILE, MAP_FILE]:
                                    if f_name in namelist:
                                        with open(f_name, "wb") as f_out:
                                            f_out.write(zip_file.read(f_name))
                                        restored_count += 1
                                if restored_count > 0:
                                    success_extract = True
                                else:
                                    st.error("В ZIP архива не бяха открити валидни бази данни на PixelApp.")
                        except:
                            st.error("Конфликт при разархивирането. Уверете се, че качвате правилния файл.")
                        
                        if success_extract:
                            st.success("🎉 Данните са възстановени успешно!")
                            st.session_state["show_admin_panel"] = False
                            st.session_state["current_trip"] = None
                            st.rerun()



