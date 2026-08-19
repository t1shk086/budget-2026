import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64
import folium
import requests
import re
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
        content: ""; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.15) !important; z-index: -1; pointer-events: none;
    }
    
    /* Модерни полупрозрачни полета (Glassmorphism ефект) */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important; padding: 10px 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        backdrop-filter: blur(4px) !important; -webkit-backdrop-filter: blur(4px) !important;
        margin-bottom: 15px !important;
    }

    /* Професионални тъмни бутони с дълбока сянка */
    button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-primary"],
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #252932, #16191f) !important; color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important; transition: all 0.25s ease !important;
        font-weight: 600 !important; letter-spacing: 0.5px !important; width: 100% !important;
    }
    /* Елегантен светлинен ефект при посочване на бутоните */
    button[data-testid="stBaseButton-secondary"]:hover, button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFileUploaderDropzone"] button:hover {
        background: linear-gradient(135deg, #2e343f, #1c2028) !important;
        transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(0, 242, 254, 0.15) !important;
        border-color: rgba(0, 242, 254, 0.2) !important;
    }
    small { color: #7e8494 !important; }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]

SUPABASE_URL = "https://supabase.co"
SUPABASE_HEADERS = {
    "apikey": "sb_publishable_OuX6KWlKNzCtiFhGkwmfhA_3ibPLwT7",
    "Authorization": "Bearer sb_publishable_OuX6KWlKNzCtiFhGkwmfhA_3ibPLwT7",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")

def get_trip_data(t_id):
    try:
        url = f"{SUPABASE_URL}/budget_data?trip_id=eq.{t_id}"
        res = requests.get(url, headers=SUPABASE_HEADERS)
        if res.status_code == 200 and res.json():
            r = pd.DataFrame(res.json())
            if "liters" not in r.columns: r["liters"] = 0.0
            if "current_km" not in r.columns: r["current_km"] = 0.0
            return r
    except: pass
    return pd.DataFrame(columns=["id","trip_id","date","amount","category","description","type","liters","current_km"])
def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
    try:
        url = f"{SUPABASE_URL}/trip_settings?trip_id=eq.{t_id}"
        res = requests.get(url, headers=SUPABASE_HEADERS)
        if res.status_code == 200 and res.json() and len(res.json()) > 0:
            return res.json()[0]
    except: pass
    return d

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        url = f"{SUPABASE_URL}/trip_settings"
        payload = {
            "trip_id": str(t_id), "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k),
            "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)
        }
        headers = SUPABASE_HEADERS.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        requests.post(url, json=payload, headers=headers)
    except: pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        url = f"{SUPABASE_URL}/budget_data"
        payload = {
            "trip_id": str(t_id), "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt),
            "category": str(cat), "description": str(desc) if desc else "Без описание", "type": "deposit" if is_dep else "expense",
            "liters": float(lit), "current_km": float(c_km)
        }
        res = requests.post(url, json=payload, headers=SUPABASE_HEADERS)
        return (res.status_code == 200 or res.status_code == 201)
    except: return False

def get_map_points(t_id):
    try:
        url = f"{SUPABASE_URL}/map_points?trip_id=eq.{t_id}"
        res = requests.get(url, headers=SUPABASE_HEADERS)
        if res.status_code == 200 and res.json(): return pd.DataFrame(res.json())
    except: pass
    return pd.DataFrame(columns=["id", "trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        url = f"{SUPABASE_URL}/map_points"
        payload = {"trip_id": str(t_id), "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
        requests.post(url, json=payload, headers=SUPABASE_HEADERS)
        return True
    except: return False

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0
if "view_photos" not in st.session_state: st.session_state["view_photos"] = False
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
        s_d_str, e_d_str = "", ""
        if isinstance(d_range, (list, tuple)) and len(d_range) > 0:
            s_d_str = d_range[0].strftime("%d.%m.%Y")
            e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 else s_d_str
        elif hasattr(d_range, "strftime"):
            s_d_str = d_range.strftime("%d.%m.%Y"); e_d_str = s_d_str
        sk = float(new_skm) if new_skm is not None else 0.0; target_id = txt.replace(" ", "_")
        save_trip_settings(target_id, "Да" if "автомобил" in viber_car.lower() else "Не", "Да" if "автомобил" in viber_car.lower() else "Добави впоследствие", sk, 0.0, 0.0, s_d_str, e_d_str)
        try:
            geolocator = Nominatim(user_agent="pixelapp_travel_manager_2026")
            location = geolocator.geocode(f"{txt}, Europe", language="bg,en")
            if location: add_map_point(target_id, location.latitude, location.longitude, f"🏁 Център: {txt}", "red")
        except: pass
        st.session_state["current_trip"] = target_id; st.rerun()

if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center; margin-bottom: 5px;'><h1 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 10px rgba(0, 242, 254, 0.2); margin-bottom: 0px;'>🐾 PixelApp</h1><p style='font-family: \"Segoe UI\", Roboto, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; margin-top: 4px; margin-bottom: 30px;'>Travel Manager</p></div>", unsafe_allow_html=True)
    existing = []
    try:
        res_trips = requests.get(f"{SUPABASE_URL}/trip_settings?select=trip_id", headers=SUPABASE_HEADERS)
        if res_trips.status_code == 200 and res_trips.json(): existing = list(set([r["trip_id"] for r in res_trips.json() if r.get("trip_id")]))
    except: pass
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("✔️ Зареди", use_container_width=True): st.session_state["current_trip"] = choice.replace(" ", "_"); st.rerun()
    else: st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-bottom:15px;'>Все още нямате записани почивки.</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>", unsafe_allow_html=True)
    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
    st.stop()
else:
    trip_id = st.session_state["current_trip"]; papka_snimki = f"snimki_{trip_id}_2026"; c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s.get("car_trip", "Не")), str(c_s.get("track_fuel", "Не")), float(c_s.get("start_km", 0.0)), float(c_s.get("end_km", 0.0)), float(c_s.get("manual_fuel", 0.0))
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    @st.dialog("🗑️ Потвърждение за изтриване")
    def confirm_delete_dialog():
        if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
            record_id = st.session_state["delete_idx"]
            st.write("Сигурни ли сте, че искате да изтриете този разход?")
            c_del1, c_del2 = st.columns(2)
            with c_del1:
                if st.button("✔️ ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                    requests.delete(f"{SUPABASE_URL}/budget_data?id=eq.{record_id}", headers=SUPABASE_HEADERS)
                    st.session_state["delete_idx"] = None; st.rerun()
            with c_del2:
                if st.button("✖️ ОТКАЗ", use_container_width=True): st.session_state["delete_idx"] = None; st.rerun()

    @st.dialog("🚨 Изтриване на цялото пътуване")
    def confirm_delete_trip_dialog():
        st.error(f"ВНИМАНИЕ! Изтриване на пътуването до {trip_id.replace('_', ' ')}?")
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            if st.button("✔️ ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
                requests.delete(f"{SUPABASE_URL}/budget_data?trip_id=eq.{trip_id}", headers=SUPABASE_HEADERS)
                requests.delete(f"{SUPABASE_URL}/trip_settings?trip_id=eq.{trip_id}", headers=SUPABASE_HEADERS)
                requests.delete(f"{SUPABASE_URL}/map_points?trip_id=eq.{trip_id}", headers=SUPABASE_HEADERS)
                st.session_state["current_trip"] = None; st.rerun()
        with c_tr2:
            if st.button("✖️ ОТКАЗ", use_container_width=True): st.rerun()

    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum()) if not df_trip.empty else 0.0
    df_expenses = df_trip[df_trip["type"] == "expense"] if not df_trip.empty else pd.DataFrame()
    total_on_site = float(df_expenses["amount"].sum()) if not df_expenses.empty else 0.0
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    total_liters_sum, auto_fuel_money = 0.0, 0.0
    if not df_expenses.empty:
        for _, row in df_expenses.iterrows():
            if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
            if row["category"] == "Транспорт":
                if float(row.get("liters", 0)) > 0: total_liters_sum += float(row["liters"]); auto_fuel_money += float(row["amount"])
                elif any(k in str(row["description"]).lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): auto_fuel_money += float(row["amount"])
    total_liters_calculated = total_liters_sum + m_fuel
    max_current_km = float(df_expenses["current_km"].max()) if not df_expenses.empty and "current_km" in df_expenses.columns else 0.0
    eff_end_km = e_km if e_km > 0 else max_current_km; dist = eff_end_km - s_km if eff_end_km > s_km else 0.0
    progressive_avg_con = 0.0
    if dist > 0 and total_liters_calculated > 0: progressive_avg_con = (total_liters_calculated / dist * 100)
    color_gauge = "#00f2fe" if progressive_avg_con < 6.0 else ("#ffa500" if progressive_avg_con < 8.5 else "#ff4b4b")
    val_to_show, label_to_show = progressive_avg_con, "среден разход до момента"

    if st.session_state["view_photos"]:
        if st.button("🔙 ВРЪЩАНЕ КЪМ РАЗХОДИТЕ", use_container_width=True): st.session_state["view_photos"] = False; st.rerun()
        if not os.path.exists(papka_snimki): os.makedirs(papka_snimki)
        up = st.file_uploader("Добавете нови снимки:", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if up:
            for f in up:
                if not os.path.exists(os.path.join(papka_snimki, f.name)):
                    with open(os.path.join(papka_snimki, f.name), "wb") as out: out.write(f.getbuffer())
            st.rerun()
        saved = glob.glob(os.path.join(papka_snimki, "*"))
        if saved:
            img_grid = st.columns(2)
            for idx, p in enumerate(saved):
                with img_grid[idx % 2]:
                    st.image(p, use_container_width=True)
                    if st.button("❌ Изтрий", key=f"di_{idx}"): os.remove(p); st.rerun()
    else:
        col_space_top, col_btn_top = st.columns([0.8, 0.2])
        with col_btn_top:
            if st.button("📸 Галерия", key="open_gallery_top"): st.session_state["view_photos"] = True; st.rerun()
        st.markdown(f"<div style='text-align: center; margin-top: -10px;'><h2 style='color: #00f2fe;'>🌴 {trip_id.replace('_', ' ')}</h2><p style='color: #888;'>{st_date} - {en_date}</p></div>", unsafe_allow_html=True)
        if st.button("🔙 НАЗАД КЪМ ИЗБОР НА ПОЧИВКА", use_container_width=True): st.session_state["current_trip"] = None; st.rerun()
        
        v_id = st.session_state["form_version"]; col1, col2 = st.columns(2)
        with col1: s_input = st.number_input("СУМА (EUR)", value=None, format="%.2f", key=f"su_{v_id}")
        with col2: o_input = st.text_input("Описание", key=f"op_{v_id}"); is_trip_finished = (e_km > 0.0)

        @st.dialog("⛽ Зареждане на гориво")
        def fuel_modal(amount, category, description, is_dep):
            liters = st.number_input("Литри:", value=None, placeholder="Напишете литри...", step=0.1)
            km_input = st.number_input("Текущи километри на таблото (км):", value=None, step=1.0)
            if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
                lit, ckm = (float(liters) if liters is not None else 0.0), (float(km_input) if km_input is not None else 0.0)
                if add_expense(trip_id, amount, category, f"[ЗАРЕЖДАНЕ] {description}", is_dep, lit, ckm): st.session_state["form_version"] += 1; st.rerun()

        if o_input.strip() and s_input and s_input > 0:
            st.markdown("<div style='text-align: center;'><h3 style='color:#00f2fe;'>🎯 КАТЕГОРИЯ</h3></div>", unsafe_allow_html=True)
            grid = st.columns(3)
            for i, kat in enumerate(KATEGORII):
                with grid[i % 3]:
                    if st.button(kat, use_container_width=True, key=f"bt_{i}"):
                        desc, is_d = o_input.strip(), (kat == "Депозит/Резервация")
                        if kat == "Транспорт" and any(k in desc.lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): fuel_modal(s_input, kat, desc, is_d)
                        else:
                            if add_expense(trip_id, s_input, kat, desc, is_d): st.session_state["form_version"] += 1; st.rerun()
            if st.button("❌ ОТКАЗ", use_container_width=True): st.session_state["form_version"] += 1; st.rerun()
            st.stop()

        if car_trip == "Да":
            km_progress_pct = min(100, max(0, (dist / 1000 * 100))) if dist > 0 else 0
            finish_icon_html = f"<div style='position: absolute; right: 0; top: -8px; background: #1c1c1c; border: 2px solid #ff4b4b; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white;'>F</div>" if is_trip_finished else f"<div style='position: absolute; left: calc({km_progress_pct}% - 10px); top: -12px; font-size: 16px;'>🚗</div>"
            st.markdown(f"### 🚗 Километраж и пробег")
            st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center;'><div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); margin: 25px 15px 15px 15px;'><div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div><div style='position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white;'>S</div>{finish_icon_html}</div><div style='display: flex; justify-content: space-between; font-size: 13px;'><div style='text-align: left;'>Старт<br><b>{s_km:.0f} км</b></div><div style='text-align: center;'>Изминати<br><b style='color: #00f2fe;'>{dist:.0f} км</b></div><div style='text-align: right;'>Краен<br><b>{f'{eff_end_km:.0f} км' if eff_end_km > 0 else '—'}</b></div></div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 15px;'><div style='flex: 1; min-width: 280px; background: rgba(255,255,255,0.02); padding: 20px; border-radius: 16px; text-align: center;'><div style='font-size: 11px; margin-bottom: 15px;'>ТЕКУЩ РАЗХОД</div><div style='width: 110px; height: 110px; border-radius: 50%; border: 4px dashed {color_gauge}; display: inline-flex; flex-direction: column; justify-content: center; align-items: center; margin-bottom: 15px;'><div style='color: white; font-size: 28px; font-weight: 900;'>{val_to_show:.1f}</div><div style='color: #666; font-size: 10px;'>л/100км</div></div><div style='color: #666; font-size: 11px;'>{label_to_show}</div></div><div style='flex: 1; min-width: 280px; background: rgba(255,255,255,0.02); padding: 20px; border-radius: 16px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center;'><div style='width: 100%;'>💧 ОБЩО ЗАРЕДЕНО ГОРИВО<br><b style='font-size: 28px;'>{total_liters_calculated:.1f} литра</b></div><div style='width: 100%; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;'>💰 ОБЩА СТОЙНОСТ ТРАНСПОРТ<br><b style='font-size: 28px;'>{auto_fuel_money:.2f} EUR</b></div></div></div>", unsafe_allow_html=True)

        @st.dialog("⚙️ Настройки за автомобил")
        def edit_car_modal():
            v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=1 if car_trip == "Да" else 0)
            new_sk = st.number_input("Начални км:", value=s_km if s_km > 0 else None)
            new_mf = st.number_input("Добави пропуснато гориво (л):", value=m_fuel if m_fuel > 0 else None)
            if st.button("💾 Обнови", use_container_width=True, type="primary"):
                save_trip_settings(trip_id, str(v_car), t_fuel, float(new_sk) if new_sk else 0.0, e_km, float(new_mf) if new_mf else 0.0, st_date, en_date); st.rerun()

        @st.dialog("🏁 Край на пътуването")
        def finish_trip_modal():
            end_km_input = st.number_input("Финални километри:", value=e_km if e_km > 0 else None, step=1.0)
            if st.button("🔒 ЗАКЛЮЧИ", use_container_width=True, type="primary"):
                if end_km_input and end_km_input > s_km: save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date); st.rerun()

        if car_trip == "Да":
            col_m1, col_m2 = st.columns(2)
            with col_m1: st.button("⚙️ Настройки кола", use_container_width=True, on_click=edit_car_modal)
            with col_m2: st.button("🏁 Край на пътуването", use_container_width=True, on_click=finish_trip_modal)

        st.markdown("<br>### 📊 Анализ на разходите", unsafe_allow_html=True)
        stat_grid = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            with stat_grid[idx % 2]:
                pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
                st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 14px; border-radius: 14px; margin-bottom: 12px;'>{get_emoji(kat)} {kat} — <b style='color:#ff4b4b;'>{s_value:.2f} EUR</b><div style='background:rgba(0,0,0,0.4); height:16px; border-radius:20px; position:relative; overflow:hidden;'><div style='width:{pct}%; height:100%; background:linear-gradient(90deg, #4facfe, #00f2fe); border-radius:20px;'></div></div></div>", unsafe_allow_html=True)

        col_st1, col_st2 = st.columns(2)
        with col_st1: st.markdown(f"<div style='background:rgba(255,255,255,0.03); padding:15px; border-radius:12px; text-align:center;'>🏨 ДЕПОЗИТ<h2>{depozit_hotel:.2f} EUR</h2></div>", unsafe_allow_html=True)
        with col_st2: st.markdown(f"<div style='background:rgba(255,255,255,0.03); padding:15px; border-radius:12px; text-align:center;'>💰 НА МЯСТО<h2>{total_on_site:.2f} EUR</h2></div>", unsafe_allow_html=True)

        @st.dialog("📜 Хронология на плащанията", width="large")
        def hronologia_popup_dialog():
            if df_trip.empty: st.info("Няма разходи.")
            else:
                for _, r in df_trip.iterrows():
                    col_rec, col_del = st.columns([0.85, 0.15])
                    with col_rec: st.write(f"{get_emoji(r['category'])} {r['category']} — {r['amount']:.2f} EUR ({r['date']})")
                    with col_del:
                        if st.button("🗑️", key=f"dl_{r['id']}"): st.session_state["delete_idx"] = r["id"]; confirm_delete_dialog()

        if not df_trip.empty:
            st.markdown("---")
            if st.button("♾️ Хронология на Разходите", use_container_width=True):
                hronologia_popup_dialog()

        st.subheader("🗺️ Карта на спирките")
        df_points = get_map_points(trip_id)
        c_lat, c_lon = (df_points["lat"].mean(), df_points["lon"].mean()) if not df_points.empty else (42.7339, 25.4858)
        
        m = folium.Map(location=[c_lat, c_lon], zoom_start=6)
        if not df_points.empty:
            for _, pt in df_points.iterrows():
                folium.Marker(location=[pt["lat"], pt["lon"]], popup=pt["title"]).add_to(m)
                
        map_data = st_folium(m, width=700, height=400, key="static_map", returned_objects=["last_clicked"])
        
        if map_data and map_data.get("last_clicked") and not is_trip_finished:
            click_coords = map_data["last_clicked"]
            st.markdown(f"📌 Координати: {click_coords['lat']:.4f}, {click_coords['lng']:.4f}")
            title_in = st.text_input("Име на спирката:", key="map_t")
            if st.button("💾 Запис", use_container_width=True, type="primary") and title_in:
                if add_map_point(trip_id, click_coords["lat"], click_coords["lng"], title_in):
                    st.rerun()

        st.markdown("---")
        if st.button("🏠 ГЛАВНО МЕНЮ", use_container_width=True):
            st.session_state["current_trip"] = None
            st.rerun()
            
        if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True):
            confirm_delete_trip_dialog()
