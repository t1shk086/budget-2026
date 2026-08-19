import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from st_supabase_connection import SupabaseConnection

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

import requests

# Конфигурация за директни HTTP заявки към Supabase
SUPABASE_URL = "https://supabase.co"
SUPABASE_HEADERS = {
    "apikey": "sb_publishable_OuX6KWlKNzCtiFhGkwmfhA_3ibPLwT7",
    "Authorization": "Bearer sb_publishable_OuX6KWlKNzCtiFhGkwmfhA_3ibPLwT7",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

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
            "trip_id": str(t_id), "car_trip": str(c_t), "track_fuel": str(t_f),
            "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f),
            "start_date": str(s_d), "end_date": str(e_d)
        }
        # Използваме upsert през HTTP за избягване на дублиране
        headers = SUPABASE_HEADERS.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        st.error(f"Грешка настройки: {e}")

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        url = f"{SUPABASE_URL}/budget_data"
        payload = {
            "trip_id": str(t_id), 
            "date": datetime.datetime.now().strftime("%d.%m %H:%M"),
            "amount": float(amt), 
            "category": str(cat), 
            "description": str(desc) if desc else "Без описание",
            "type": "deposit" if is_dep else "expense", 
            "liters": float(lit), 
            "current_km": float(c_km)
        }
        res = requests.post(url, json=payload, headers=SUPABASE_HEADERS)
        if res.status_code == 200 or res.status_code == 201:
            return True
        else:
            st.error(f"Грешка при запис в базата: {res.text}")
            return False
    except Exception as e:
        st.error(f"Грешка връзка: {e}")
        return False



def get_map_points(t_id):
    try:
        url = f"{SUPABASE_URL}/map_points?trip_id=eq.{t_id}"
        res = requests.get(url, headers=SUPABASE_HEADERS)
        if res.status_code == 200 and res.json():
            return pd.DataFrame(res.json())
    except: pass
    return pd.DataFrame(columns=["id", "trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        url = f"{SUPABASE_URL}/map_points"
        payload = {
            "trip_id": str(t_id), "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)
        }
        requests.post(url, json=payload, headers=SUPABASE_HEADERS)
        return True
    except: return False




def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")
def get_trip_data(t_id):
    try:
        res = conn.table("budget_data").select("*").eq("trip_id", t_id).execute()
        if res.data:
            r = pd.DataFrame(res.data)
            if "liters" not in r.columns: r["liters"] = 0.0
            if "current_km" not in r.columns: r["current_km"] = 0.0
            return r
    except: pass
    return pd.DataFrame(columns=["id","trip_id","date","amount","category","description","type","liters","current_km"])

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
    try:
        res = conn.table("trip_settings").select("*").eq("trip_id", t_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0] if isinstance(res.data, list) else res.data
    except: pass
    return d

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        row_data = {
            "trip_id": str(t_id), 
            "car_trip": str(c_t), 
            "track_fuel": str(t_f), 
            "start_km": float(s_k), 
            "end_km": float(e_k), 
            "manual_fuel": float(m_f), 
            "start_date": str(s_d), 
            "end_date": str(e_d)
        }
        conn.table("trip_settings").upsert(row_data).execute()
    except Exception as e:
        st.error(f"Supabase Грешка (Настройки): {e}")

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        row = {
            "trip_id": str(t_id), 
            "date": datetime.datetime.now().strftime("%d.%m %H:%M"), 
            "amount": float(amt), 
            "category": str(cat), 
            "description": str(desc) if desc else "Без описание", 
            "type": "deposit" if is_dep else "expense", 
            "liters": float(lit), 
            "current_km": float(c_km)
        }
        conn.table("budget_data").insert(row).execute()
        return True
    except Exception as e:
        st.error(f"Supabase Грешка (Разход): {e}")
        return False

def get_map_points(t_id):
    try:
        res = conn.table("map_points").select("*").eq("trip_id", t_id).execute()
        if res.data: return pd.DataFrame(res.data)
    except: pass
    return pd.DataFrame(columns=["id", "trip_id", "lat", "lon", "title", "color"])

def add_map_point(t_id, lat, lon, title, color="blue"):
    try:
        row = {
            "trip_id": str(t_id), 
            "lat": float(lat), 
            "lon": float(lon), 
            "title": str(title), 
            "color": str(color)
        }
        conn.table("map_points").insert(row).execute()
        return True
    except Exception as e:
        st.error(f"Supabase Грешка (Карта): {e}")
        return False



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
            s_d_str = d_range.strftime("%d.%m.%Y")
            e_d_str = s_d_str
        sk = float(new_skm) if new_skm is not None else 0.0
        target_id = txt.replace(" ", "_")
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
        res_trips = conn.table("trip_settings").select("trip_id").execute()
        if res_trips.data: existing = list(set([r["trip_id"] for r in res_trips.data if r.get("trip_id")]))
    except: pass
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("✔️ Зареди", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_"); st.rerun()
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-bottom:15px;'>Все още нямате записани почивки. Създайте първото си приключение по-долу!</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>", unsafe_allow_html=True)
    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
    st.stop()
else:
    trip_id = st.session_state["current_trip"]
    papka_snimki = f"snimki_{trip_id}_2026"
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s.get("car_trip", "Не")), str(c_s.get("track_fuel", "Не")), float(c_s.get("start_km", 0.0)), float(c_s.get("end_km", 0.0)), float(c_s.get("manual_fuel", 0.0))
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))
    @st.dialog("🗑️ Потвърждение за изтриване")
    def confirm_delete_dialog():
        if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
            st.write("Сигурни ли сте, че искате да изтриете този разход?")
            record_id = st.session_state["delete_idx"]
            try:
                res = conn.table("budget_data").select("*").eq("id", record_id).execute()
                if res.data:
                    r = res.data
                    st.markdown(f"**{get_emoji(r['category'])} {r['category']}** — <span style='color:#ff4b4b; font-weight:bold;'>{r['amount']:.2f} EUR</span><br><small>{r['description']}</small>", unsafe_allow_html=True)
            except: pass
            c_del1, c_del2 = st.columns(2)
            with c_del1:
                if st.button("✔️ ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                    try: conn.table("budget_data").delete().eq("id", record_id).execute()
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
                    conn.table("budget_data").delete().eq("trip_id", trip_id).execute()
                    conn.table("trip_settings").delete().eq("trip_id", trip_id).execute()
                    conn.table("map_points").delete().eq("trip_id", trip_id).execute()
                    if os.path.exists(papka_snimki):
                        for p in glob.glob(os.path.join(papka_snimki, "*")): os.remove(p)
                        os.rmdir(papka_snimki)
                except: pass
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
    eff_end_km = e_km if e_km > 0 else max_current_km
    dist = eff_end_km - s_km if eff_end_km > s_km else 0.0

    progressive_avg_con, has_progressive_data = 0.0, False
    try:
        if not df_expenses.empty:
            df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
            df_full_points = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
            if not df_full_points.empty:
                last_full_km = float(df_full_points.iloc[-1]["current_km"])
                total_dist = last_full_km - s_km
                total_liters = float(df_trans_fuel[df_trans_fuel["current_km"] <= last_full_km]["liters"].sum()) + m_fuel
                if total_dist > 0 and total_liters > 0: progressive_avg_con = (total_liters / total_dist * 100); has_progressive_data = True
    except: pass

    if st.session_state["view_photos"]:
        if st.button("🔙 ВРЪЩАНЕ КЪМ РАЗХОДИТЕ", use_container_width=True, key="clean_gallery_back_btn"):
            st.session_state["view_photos"] = False; st.rerun()
        st.markdown("---")
        if not os.path.exists(papka_snimki): os.makedirs(papka_snimki)
        up = st.file_uploader("Добавете нови снимки:", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"u_{trip_id}_gallery")
        if up:
            for f in up:
                if not os.path.exists(os.path.join(papka_snimki, f.name)):
                    with open(os.path.join(papka_snimki, f.name), "wb") as out: out.write(f.getbuffer())
            st.rerun()
        st.markdown("---")
        if "show_images_grid" not in st.session_state: st.session_state["show_images_grid"] = False
        if not st.session_state["show_images_grid"]:
            if st.button("👁️ ПОКАЖИ ЗАПАЗЕНИТЕ СНИМКИ", use_container_width=True, type="primary"): st.session_state["show_images_grid"] = True; st.rerun()
        else:
            if st.button("🙈 СКРИЙ СНИМКИТЕ", use_container_width=True): st.session_state["show_images_grid"] = False; st.rerun()
            saved = glob.glob(os.path.join(papka_snimki, "*"))
            if saved:
                st.markdown("<br>", unsafe_allow_html=True)
                img_grid = st.columns(2)
                for idx, p in enumerate(saved):
                    with img_grid[idx % 2]:
                        st.image(p, use_container_width=True)
                        if st.button("❌ Изтрий", key=f"di_{idx}", use_container_width=True): os.remove(p); st.rerun()
            else: st.markdown("<div style='text-align:center; margin-top:20px; color:#666;'>Все още няма снимки.</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                div[data-testid="stColumn"]:nth-of-type(2):has(button[key="open_gallery_top_header_2026"]) { display: flex !important; justify-content: flex-end !important; align-items: center !important; width: 100% !important; }
                button[key="open_gallery_top_header_2026"] { display: inline-block !important; width: auto !important; min-width: unset !important; background: rgba(22, 25, 31, 0.6) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; color: #ffffff !important; padding: 4px 12px !important; font-size: 12px !important; font-weight: 600 !important; border-radius: 8px !important; backdrop-filter: blur(8px) !important; transition: all 0.2s ease-in-out !important; }
                button[key="open_gallery_top_header_2026"]:hover { background: rgba(0, 242, 254, 0.12) !important; border-color: rgba(0, 242, 254, 0.5) !important; }
                button:not([key="open_gallery_top_header_2026"]) { position: static !important; }
            </style>
        """, unsafe_allow_html=True)
        col_space_top, col_btn_top = st.columns([0.7, 0.3])
        with col_btn_top:
            if st.button("📸 Галерия", key="open_gallery_top_header_2026"): st.session_state["view_photos"] = True; st.rerun()
        date_html = f"<p style='font-size: 14px; color: #888; font-weight: 500; margin-top: 5px; margin-bottom: 0;'>{st_date} - {en_date}</p>" if st_date and st_date != "nan" else ""
        st.markdown(f"<div style='text-align: center; margin-top: -10px; margin-bottom: 10px; width: 100%;'><h2 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 500; font-size: 26px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; padding: 0;'>🌴 Дестинация: {trip_id.replace('_', ' ')}</h2>{date_html}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("<div id='trip_top_anchor' style='scroll-margin-top: 20px;'></div>", unsafe_allow_html=True)
        ekran_za_kategorii = st.empty()
        if st.button("🔙 НАЗАД КЪМ ИЗБОР НА ПОЧИВКА", use_container_width=True): st.session_state["current_trip"] = None; st.rerun()
        v_id = st.session_state["form_version"]
        col1, col2 = st.columns(2)
        with col1: s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Напишете сума...", format="%.2f", key=f"su_{v_id}")
        with col2: o_input = st.text_input("Описание", placeholder="Напишете описание...", key=f"op_{v_id}")
        is_trip_finished = (e_km > 0.0)

        @st.dialog("⛽ Зареждане на гориво")
        def fuel_modal(amount, category, description, is_dep):
            if is_trip_finished: st.error("🔒 Пътуването е приключено!"); return
            liters = st.number_input("Литри:", value=None, placeholder="Напишете литри...", step=0.1)
            fuel_type = st.radio("Тип на зареждането:", ["Да, до горе (Пълен резервоар)", "Не, частично"], index=0)
            df_f = get_trip_data(trip_id)[lambda d: (d["category"] == "Транспорт") & (d["current_km"] > 0)].sort_index() if not df_trip.empty else pd.DataFrame()
            last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
            km_input = st.number_input("Текущи километри на таблото (км):", value=None, placeholder="Въведете км...", step=1.0)
            if liters and km_input and km_input > last_km and "до горе" in fuel_type.lower() and not df_f.empty:
                df_since_full = df_f[df_f["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
                t_seg_liters = (float(df_f[df_f["current_km"] > float(df_since_full.iloc[-1]["current_km"])]["liters"].sum()) + liters) if not df_since_full.empty else (float(df_f["liters"].sum()) + liters + m_fuel)
                seg_dist = (km_input - float(df_since_full.iloc[-1]["current_km"])) if not df_since_full.empty else (km_input - s_km)
                if seg_dist > 0 and t_seg_liters > 0: st.success(f"📊 Реален разход: **{(t_seg_liters / seg_dist * 100):.1f} л / 100 км**")
            if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
                lit, ckm = (float(liters) if liters is not None else 0.0), (float(km_input) if km_input is not None else 0.0)
                is_full = "ПЪЛНО" if "до горе" in fuel_type.lower() else "ЧАСТИЧНО"
                full_desc = f"[{is_full} ЗАРЕЖДАНЕ] {description}"
                if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm): st.session_state["form_version"] += 1; st.rerun()

        if o_input.strip() and s_input and s_input > 0:
            header_text = f"Записване на: <b>{s_input:.2f} EUR</b> за <i>\"{o_input.strip()}\"</i>"
            with ekran_za_kategorii.container():
                st.markdown(f"<div style='text-align: center; margin: 10px 0 20px 0;'><h3 style='color:#00f2fe;'>🎯 КАТЕГОРИЯ</h3><p style='color:#aaa;'>{header_text}</p></div>", unsafe_allow_html=True)
                grid = st.columns(3)
                for i, kat in enumerate(KATEGORII):
                    with grid[i % 3]:
                        is_disabled = is_trip_finished and (kat == "Транспорт")
                        if st.button(f"🔒 {kat}" if is_disabled else kat, use_container_width=True, key=f"bt_{i}", disabled=is_disabled):
                            desc, is_d = o_input.strip(), (kat == "Депозит/Резервания")
                            if kat == "Транспорт" and any(k in desc.lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): fuel_modal(s_input, kat, desc, is_d)
                            else:
                                if add_expense(trip_id, s_input, kat, desc, is_d): st.session_state["form_version"] += 1; st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("❌ ОТКАЗ", use_container_width=True): st.session_state["form_version"] += 1; st.rerun()
                st.markdown("---"); st.stop()

        if car_trip == "Да":
            val_to_show, label_to_show = 0.0, "последен затворен етап"
            km_progress_pct = 100 if e_km > 0 else min(100, max(0, (dist / 1000 * 100))) if dist > 0 else 0
            finish_icon_html = f"<div style='position: absolute; right: 0; top: -8px; background: #1c1c1c; border: 2px solid #ff4b4b; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white;'>F</div>" if is_trip_finished else f"<div style='position: absolute; left: calc({km_progress_pct}% - 10px); top: -12px; font-size: 16px;'>🚗</div>"
            if is_trip_finished: val_to_show, label_to_show = progressive_avg_con, "финален среден разход"
            else:
                try:
                    if not df_expenses.empty:
                        df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
                        df_only_full = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
                        if not df_only_full.empty:
                            import re
                            match = re.search(r"(?:Реален разход:|Разход:)\s*([0-9.]+)", df_only_full.iloc[-1]["description"])
                            val_to_show = float(match.group(1)) if match else progressive_avg_con
                        else:
                            c_dist = float(df_trans_fuel.iloc[-1]["current_km"]) - s_km
                            c_liters = float(df_trans_fuel["liters"].sum()) + m_fuel
                            if c_dist > 0 and c_liters > 0: val_to_show, label_to_show = (c_liters / c_dist * 100), "среден разход до момента"
                except: pass
            color_gauge = "#00f2fe" if val_to_show < 6.0 else ("#ffa500" if val_to_show < 8.5 else "#ff4b4b")
            transport_liters = float(df_expenses[df_expenses['category'] == 'Транспорт']['liters'].sum()) + m_fuel if not df_expenses.empty else m_fuel
            st.markdown(f"### 🚗 Данни за километраж и пробег")
            transport_liters = float(df_expenses[df_expenses['category'] == 'Транспорт']['liters'].sum()) + m_fuel if not df_expenses.empty else m_fuel
            st.markdown(f"### 🚗 Данни за километраж и пробег")
            st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center;'><div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); margin: 25px 15px 15px 15px;'><div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div><div style='position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white;'>S</div>{finish_icon_html}</div><div style='display: flex; justify-content: space-between; font-size: 13px;'><div style='text-align: left;'>Старт<br><b>{s_km:.0f} км</b></div><div style='text-align: center;'>Изминати<br><b style='color: #00f2fe;'>{dist:.0f} км</b></div><div style='text-align: right;'>Краен<br><b>{f'{eff_end_km:.0f} км' if eff_end_km > 0 else '—'}</b></div></div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 15px;'><div style='flex: 1; min-width: 280px; background: rgba(255,255,255,0.02); padding: 20px; border-radius: 16px; text-align: center;'><div style='font-size: 11px; margin-bottom: 15px;'>ТЕКУЩ РАЗХОД</div><div style='width: 110px; height: 110px; border-radius: 50%; border: 4px dashed {color_gauge}; display: inline-flex; flex-direction: column; justify-content: center; align-items: center; margin-bottom: 15px;'><div style='color: white; font-size: 28px; font-weight: 900;'>{val_to_show:.1f}</div><div style='color: #666; font-size: 10px;'>л/100км</div></div><div style='color: #666; font-size: 11px;'>{label_to_show}</div></div><div style='flex: 1; min-width: 280px; background: rgba(255,255,255,0.02); padding: 20px; border-radius: 16px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center;'><div style='width: 100%;'>💧 ОБЩО ЗАРЕДЕНО ГОРИВО<br><b style='font-size: 28px;'>{transport_liters:.1f} литра</b></div><div style='width: 100%; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;'>💰 ОБЩА СТОЙНОСТ ТРАНСПОРТ<br><b style='font-size: 28px;'>{auto_fuel_money:.2f} EUR</b></div></div></div>", unsafe_allow_html=True)

        @st.dialog("⚙️ Настройки за автомобил и период")
        def edit_car_modal():
            v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=0 if car_trip == "Не" else 1, disabled=is_trip_finished)
            new_sk = st.number_input("Начални км:", value=None if s_km == 0.0 else s_km, disabled=is_trip_finished)
            new_mf = st.number_input("Добави пропуснато гориво (л):", value=None if m_fuel == 0.0 else m_fuel, disabled=is_trip_finished)
            has_cash = st.checkbox("💵 Финансов разход за горивото?") if (new_mf and new_mf > 0 and not is_trip_finished) else False
            m_cash = st.number_input("Платена сума (EUR):", value=None, format="%.2f") if has_cash else 0.0
            edit_range = st.date_input("Изберете нови дати:", value=[datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)])
            if st.button("💾 Обнови", use_container_width=True, type="primary", disabled=is_trip_finished):
                sk_val, mf_val = (float(new_sk) if new_sk is not None else 0.0), (float(new_mf) if new_mf is not None else 0.0)
                s_d_str = edit_range.strftime("%d.%m.%Y") if isinstance(edit_range, (list, tuple)) and len(edit_range) > 0 else st_date
                e_d_str = edit_range[-1].strftime("%d.%m.%Y") if isinstance(edit_range, (list, tuple)) and len(edit_range) > 1 else s_d_str
                if has_cash and m_cash and m_cash > 0: add_expense(trip_id, m_cash, "Транспорт", f"[ПРОПУСНАТО ГОРИВО] {mf_val:.1f} литра", False, 0.0, 0.0)
                save_trip_settings(trip_id, str(v_car), "Да", sk_val, e_km, mf_val, s_d_str, e_d_str); st.session_state["form_version"] += 1; st.rerun()
        @st.dialog("🏁 Край на пътуването")
        def finish_trip_modal():
            end_km_input = st.number_input("Финални километри:", value=None if e_km == 0.0 else e_km, step=1.0)
            if st.button("🔒 ЗАКЛЮЧИ", use_container_width=True, type="primary"):
                if end_km_input and end_km_input > s_km: save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date); st.session_state["form_version"] += 1; st.rerun()
                else: st.error("Километрите трябва да са по-високи!")

        if car_trip == "Да":
            col_m1, col_m2 = st.columns(2)
            with col_m1: st.button("⚙️ Настройки кола", use_container_width=True, disabled=is_trip_finished, on_click=edit_car_modal)
            with col_m2: st.button("🏁 Край на пътуването", use_container_width=True, disabled=is_trip_finished, on_click=finish_trip_modal)
        else:
            if st.button("🚗 Добави автомобил към пътуването", use_container_width=True): edit_car_modal()

        st.markdown("<br>### 📊 Анализ на разходите")
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
            if st.button("❌ Изход", use_container_width=True): st.rerun()

        if not df_trip.empty:
            st.markdown("---")
            if st.button("♾️ Хронология на Разходите", use_container_width=True): hronologia_popup_dialog()
        st.subheader("🗺️ Карта на спирките")
        df_points = get_map_points(trip_id)
        c_lat, c_lon = (df_points["lat"].mean(), df_points["lon"].mean()) if not df_points.empty else (42.7339, 25.4858)
        m = folium.Map(location=[c_lat, c_lon], zoom_start=6)
        if not df_points.empty:
            for _, pt in df_points.iterrows(): folium.Marker(location=[pt["lat"], pt["lon"]], popup=pt["title"]).add_to(m)
        map_data = st_folium(m, width=700, height=400, key="static_map", returned_objects=["last_clicked"])
        if map_data and map_data.get("last_clicked"):
            new_click = map_data["last_clicked"]
            if st.session_state.get("active_click") != new_click: st.session_state["active_click"] = new_click; st.rerun()
        if "active_click" in st.session_state and st.session_state["active_click"] is not None and not is_trip_finished:
            click_coords = st.session_state["active_click"]
            st.markdown(f"📌 Координати: {click_coords['lat']:.4f}, {click_coords['lng']:.4f}")
            title_in = st.text_input("Име на спирката:", key="map_t")
            if st.button("💾 Запис", use_container_width=True, type="primary") and title_in:
                if add_map_point(trip_id, click_coords["lat"], click_coords["lng"], title_in): st.session_state["active_click"] = None; st.rerun()

        st.markdown("---")
        if st.button("🏠 ГЛАВНО МЕНЮ", use_container_width=True): st.session_state["current_trip"] = None; st.rerun()
        if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True): confirm_delete_trip_dialog()
