import streamlit as st
import pandas as pd
import datetime
import io
import re
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

DRIVE_FOLDER_ID = "1YVkomBIaH0x9hkt4pS9iFq3QfDylSBQQ"

if "gcp_service_account" in st.secrets:
    info = dict(st.secrets["gcp_service_account"])
else:
    st.error("Моля, добавете gcp_service_account в Secrets в Streamlit Dashboard!")
    st.stop()

@st.cache_resource
def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(info, scopes=["https://googleapis.com"])
    return build("drive", "v3", credentials=creds)

drive_service = get_drive_service()
def find_file_in_drive(filename):
    try:
        q = f"'{DRIVE_FOLDER_ID}' in parents and name='{filename}' and trashed=false"
        res = drive_service.files().list(q=q, fields="files(id, name)").execute()
        files = res.get("files", [])
        return files["id"] if files else None
    except: return None

def read_csv_from_drive(filename, default_cols):
    file_id = find_file_in_drive(filename)
    if not file_id:
        df = pd.DataFrame(columns=default_cols)
        save_csv_to_drive(filename, df)
        return df
    try:
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        fh.seek(0)
        return pd.read_csv(fh, encoding="utf-8")
    except: return pd.DataFrame(columns=default_cols)
def save_csv_to_drive(filename, df):
    file_id = find_file_in_drive(filename)
    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8")
    csv_buffer.seek(0)
    media = MediaIoBaseUpload(csv_buffer, mimetype="text/csv", resumable=True)
    try:
        if file_id: drive_service.files().update(fileId=file_id, media_body=media).execute()
        else:
            body = {"name": filename, "parents": [DRIVE_FOLDER_ID]}
            drive_service.files().create(body=body, media_body=media).execute()
    except: pass

def create_drive_folder(folder_name, parent_id):
    try:
        q = f"'{parent_id}' in parents and name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        res = drive_service.files().list(q=q, fields="files(id)").execute().get("files", [])
        if res: return res["id"]
        body = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
        return drive_service.files().create(body=body, fields="id").execute().get("id")
    except: return None
def list_photos_in_drive(folder_id):
    if not folder_id: return []
    try: return drive_service.files().list(q=f"'{folder_id}' in parents and trashed=false", fields="files(id, name)").execute().get("files", [])
    except: return []

def upload_photo_to_drive(folder_id, file_name, file_bytes):
    try:
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="image/jpeg", resumable=True)
        return drive_service.files().create(body={"name": file_name, "parents": [folder_id]}, media_body=media, fields="id").execute().get("id")
    except: return None

def delete_file_from_drive(file_id):
    try: drive_service.files().delete(fileId=file_id).execute()
    except: pass

def download_photo_bytes(file_id):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        return fh.getvalue()
    except: return b""
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #090b0e 0%, #11151c 50%, #0d1117 100%) !important;
        background-attachment: fixed !important;
    }
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important; padding: 10px 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        backdrop-filter: blur(4px) !important;
    }
    button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-primary"], [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #252932, #16191f) !important; 
        color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; 
        border-radius: 12px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
        transition: all 0.25s ease !important; font-weight: 600 !important; width: 100% !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #2e343f, #1c2028) !important;
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.15) !important; border-color: rgba(0, 242, 254, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE, MAP_FILE = "budget_data_2026.csv", "trip_settings_2026.csv", "trip_map_points_2026.csv"

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")
def get_trip_data(t_id):
    df = read_csv_from_drive(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"])
    r = df[df["trip_id"] == t_id].copy()
    if "liters" not in r.columns: r["liters"] = 0.0
    if "current_km" not in r.columns: r["current_km"] = 0.0
    return r

def get_trip_settings(t_id):
    df = read_csv_from_drive(SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])
    f = df[df["trip_id"] == t_id]
    if not f.empty:
        res = f.iloc[0].to_dict()
        return {
            "trip_id": t_id, "car_trip": str(res.get("car_trip", "Не")), "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), 
            "start_km": float(res.get("start_km", 0.0)), "end_km": float(res.get("end_km", 0.0)), "manual_fuel": float(res.get("manual_fuel", 0.0)), 
            "start_date": str(res.get("start_date", "")), "end_date": str(res.get("end_date", ""))
        }
    return {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    df = read_csv_from_drive(SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])
    df = df[df["trip_id"] != t_id]
    new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
    save_csv_to_drive(SETTINGS_FILE, pd.concat([df, new_row], ignore_index=True))
def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    df = read_csv_from_drive(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"])
    row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
    save_csv_to_drive(DATA_FILE, pd.concat([df, pd.DataFrame([row])], ignore_index=True))
    return True

def get_map_points(t_id):
    return read_csv_from_drive(MAP_FILE, ["trip_id", "lat", "lon", "title", "color"])[lambda d: d["trip_id"] == t_id].copy()

def add_map_point(t_id, lat, lon, title, color="blue"):
    df = read_csv_from_drive(MAP_FILE, ["trip_id", "lat", "lon", "title", "color"])
    row = {"trip_id": t_id, "lat": float(lat), "lon": float(lon), "title": str(title), "color": str(color)}
    save_csv_to_drive(MAP_FILE, pd.concat([df, pd.DataFrame([row])], ignore_index=True))
    return True

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0
if "view_photos" not in st.session_state: st.session_state["view_photos"] = False
if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center;'><h1 style='background: linear-gradient(135deg, #00f2fe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 46px; font-weight:900;'>🐾 PixelApp</h1><p style='color:#ffd700; font-weight:500;'>Travel Manager</p></div>", unsafe_allow_html=True)
    df_init = read_csv_from_drive(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"])
    existing = list(df_init["trip_id"].unique()) if not df_init.empty else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    if existing:
        choice = st.selectbox("Изберете пътуване до:", [t.replace("_", " ") for t in existing])
        if st.button("✔️ Зареди", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_"); st.rerun()
            
    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:").strip()
        d_range = st.date_input("Изберете дати за почивката:", value=[datetime.date.today(), datetime.date.today()])
        viber_car = st.radio("🚗 Пътувате ли със собствен автомобил?", ["Не, с друг транспорт", "Да, със собствен автомобил"])
        new_skm = st.number_input("Начални километри (км):", value=0.0, step=1.0)
        if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True, type="primary") and txt:
            s_d_str = d_range[0].strftime("%d.%m.%Y") if isinstance(d_range, (list, tuple)) and len(d_range)>0 else ""
            e_d_str = d_range[-1].strftime("%d.%m.%Y") if isinstance(d_range, (list, tuple)) and len(d_range)>1 else s_d_str
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, "Да" if "Да" in viber_car else "Не", "Да" if "Да" in viber_car else "Добави впоследствие", new_skm, 0.0, 0.0, s_d_str, e_d_str)
            try:
                location = Nominatim(user_agent="pixelapp_2026").geocode(f"{txt}, Europe", language="bg,en")
                if location: add_map_point(target_id, location.latitude, location.longitude, f"🏁 Център: {txt}", "red")
            except: pass
            st.session_state["current_trip"] = target_id; st.rerun()

    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
else:
    trip_id = st.session_state["current_trip"]
    main_photos_id = create_drive_folder("PixelApp_Photos", DRIVE_FOLDER_ID)
    trip_photos_id = create_drive_folder(f"snimki_{trip_id}_2026", main_photos_id)
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    @st.dialog("🗑️ Потвърждение за изтриване")
    def confirm_delete_dialog():
        if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
            if st.button("✔️ ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                df_all = read_csv_from_drive(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"])
                save_csv_to_drive(DATA_FILE, df_all.drop(st.session_state["delete_idx"]))
                st.session_state["delete_idx"] = None; st.rerun()

    @st.dialog("🚨 Изтриване на цялото пътуване")
    def confirm_delete_trip_dialog():
        if st.button("✔️ ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
            df_all = read_csv_from_drive(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"])
            save_csv_to_drive(DATA_FILE, df_all[df_all["trip_id"] != trip_id])
            st.session_state["current_trip"] = None; st.rerun()

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
    max_current_km = float(df_expenses["current_km"].max()) if not df_expenses.empty else 0.0
    eff_end_km = e_km if e_km > 0 else max_current_km
    dist = eff_end_km - s_km if eff_end_km > s_km else 0.0
    progressive_avg_con = (total_liters_calculated / dist * 100) if dist > 0 and total_liters_calculated > 0 else 0.0
    if st.session_state["view_photos"]:
        if st.button("🔙 ВРЪЩАНЕ КЪМ РАЗХОДИТЕ", use_container_width=True): st.session_state["view_photos"] = False; st.rerun()
        up = st.file_uploader("Качете снимки:", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        if up:
            for f in up: upload_photo_to_drive(trip_photos_id, f.name, f.getbuffer())
            st.rerun()
        saved = list_photos_in_drive(trip_photos_id)
        grid_ph = st.columns(2)
        for idx, p in enumerate(saved):
            with grid_ph[idx % 2]:
                pb = download_photo_bytes(p["id"])
                if pb: st.image(pb, use_container_width=True)
                if st.button("❌ Изтрий", key=f"del_ph_{p['id']}", use_container_width=True): delete_file_from_drive(p["id"]); st.rerun()
    else:
        col_space, col_g_btn = st.columns([0.7, 0.3])
        with col_g_btn:
            if st.button("📸 Галерия", key="open_gallery_top_header_2026"): st.session_state["view_photos"] = True; st.rerun()
        
        st.markdown(f"<div style='text-align: center;'><h2 style='color:#00f2fe;'>🌴 Дестинация: {trip_id.replace('_', ' ')}</h2><p style='color:#888;'>{st_date} - {en_date}</p></div>", unsafe_allow_html=True)
        if st.button("🔙 НАЗАД КЪМ ИЗБОР НА ПОЧИВКА", use_container_width=True): st.session_state["current_trip"] = None; st.rerun()

        v_id = st.session_state["form_version"]
        col_s1, col_s2 = st.columns(2)
        with col_s1: s_input = st.number_input("СУМА (EUR)", value=None, format="%.2f", key=f"su_{v_id}")
        with col_s2: o_input = st.text_input("Описание", key=f"op_{v_id}")
        is_trip_finished = (e_km > 0.0)

        @st.dialog("⛽ Зареждане на гориво")
        def fuel_modal(amount, category, description, is_dep):
            liters = st.number_input("Литри:", value=None, step=0.1)
            fuel_type = st.radio("Тип:", ["Да, до горе (Пълен резервоар)", "Не, частично"])
            km_input = st.number_input("Текущи километри на таблото (км):", value=None, step=1.0)
            if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
                lit, ckm = (float(liters) if liters else 0.0), (float(km_input) if km_input else 0.0)
                full_desc = f"[{'ПЪЛНО' if 'до горе' in fuel_type.lower() else 'ЧАСТИЧНО'} ЗАРЕЖДАНЕ] {description}"
                if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm): st.session_state["form_version"] += 1; st.rerun()

        if o_input and s_input and s_input > 0:
            st.markdown("<h3 style='text-align:center; color:#00f2fe;'>🎯 ИЗБЕРЕТЕ КАТЕГОРИЯ</h3>", unsafe_allow_html=True)
            grid_cat = st.columns(3)
            for i, kat in enumerate(KATEGORII):
                with grid_cat[i % 3]:
                    if st.button(kat, use_container_width=True, key=f"bt_{i}"):
                        desc = o_input.strip()
                        if kat == "Транспорт" and any(k in desc.lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): fuel_modal(s_input, kat, desc, False)
                        else:
                            if add_expense(trip_id, s_input, kat, desc, (kat == "Депозит/Резервация")): st.session_state["form_version"] += 1; st.rerun()
            st.stop()

        if car_trip == "Да":
            km_pct = min(100, max(0, (dist / 1000 * 100))) if dist > 0 else 0
            st.markdown(f"### 🚗 Данни за пробег")
            st.markdown(f"<div style='background: rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); padding:20px; border-radius:16px; text-align:center;'><div style='position:relative; height:4px; background:rgba(255,255,255,0.1); border-radius:10px; margin:25px 15px;'><div style='position:absolute; left:0; top:0; height:100%; width:{km_pct}%; background:linear-gradient(90deg, #00f2fe, #4facfe); border-radius:10px;'></div></div><div style='display:flex; justify-content:space-between; font-size:13px;'><div>Старт<br><b>{s_km:.0f} км</b></div><div>Изминати<br><b style='color:#00f2fe;'>{dist:.0f} км</b></div><div>Краен<br><b>{eff_end_km:.0f} км</b></div></div></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex; gap:15px; margin-top:15px;'><div style='flex:1; background:rgba(255,255,255,0.02); padding:15px; border-radius:14px; text-align:center;'><b>СРЕДЕН РАЗХОД</b><h2>{progressive_avg_con:.1f} <span style='font-size:14px;'>л/100км</span></h2></div><div style='flex:1; background:rgba(255,255,255,0.02); padding:15px; border-radius:14px; text-align:center;'><b>ОБЩО ГОРИВО</b><h2>{total_liters_calculated:.1f} <span style='font-size:14px;'>л</span></h2></div></div>", unsafe_allow_html=True)

            @st.dialog("⚙️ Настройки за автомобил")
            def edit_car_modal():
                new_sk = st.number_input("Начални км:", value=s_km)
                new_mf = st.number_input("Добави пропуснато гориво (л):", value=m_fuel)
                if st.button("💾 Обнови", type="primary"):
                    save_trip_settings(trip_id, "Да", "Да", float(new_sk), e_km, float(new_mf), st_date, en_date); st.rerun()

            @st.dialog("🏁 Край на пътуването")
            def finish_trip_modal():
                end_km_input = st.number_input("Финални километри:", step=1.0)
                if st.button("🔒 ЗАКЛЮЧИ", type="primary"):
                    if end_km_input and end_km_input > s_km: save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date); st.rerun()

            c_m1, c_m2 = st.columns(2)
            with c_m1: st.button("⚙️ Настройки кола", on_click=edit_car_modal, use_container_width=True)
            with c_m2: st.button("🏁 Край на пътуването", on_click=finish_trip_modal, use_container_width=True)

        st.markdown("### 📊 Анализ на разходите")
        grid_stat = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            with grid_stat[idx % 2]:
                pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
                st.markdown(f"<div style='background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); padding:14px; border-radius:14px; margin-bottom:12px;'><b>{get_emoji(kat)} {kat}</b><span style='float:right; color:#ff4b4b; font-weight:bold;'>{s_value:.2f} EUR</span><br><small>{pct:.1f}% от общото</small></div>", unsafe_allow_html=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1: st.markdown(f"<div style='background:rgba(255,255,255,0.03); padding:15px; border-radius:12px; text-align:center;'>🏨 ДЕПОЗИТ<h3 style='color:#ff4b4b; margin:0;'>{depozit_hotel:.2f} EUR</h3></div>", unsafe_allow_html=True)
        with col_b2: st.markdown(f"<div style='background:rgba(255,255,255,0.03); padding:15px; border-radius:12px; text-align:center;'>💰 НА МЯСТО<h3 style='color:#00f2fe; margin:0;'>{total_on_site:.2f} EUR</h3></div>", unsafe_allow_html=True)

        @st.dialog("📜 Хронология на плащанията", width="large")
        def hronologia_popup_dialog():
            df_all = read_csv_from_drive(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"])
            for idx in reversed(df_all[df_all["trip_id"] == trip_id].index.tolist()):
                r = df_all.loc[idx]
                col_rec, col_del = st.columns([0.85, 0.15])
                with col_rec: st.write(f"{get_emoji(r['category'])} {r['category']}: -{r['amount']:.2f} EUR ({r['description']})")
                with col_del:
                    if st.button("🗑️", key=f"dl_{idx}"): st.session_state["delete_idx"] = idx; confirm_delete_dialog()

        if st.button("♾️ Хронология на Разходите", use_container_width=True): hronologia_popup_dialog()

        st.subheader("🗺️ Карта на спирките")
        df_points = get_map_points(trip_id)
        c_lat, c_lon = (df_points["lat"].mean(), df_points["lon"].mean()) if not df_points.empty else (42.7339, 25.4858)
        m = folium.Map(location=[c_lat, c_lon], zoom_start=6)
        for _, pt in df_points.iterrows(): folium.Marker(location=[pt["lat"], pt["lon"]], popup=pt["title"]).add_to(m)
        map_data = st_folium(m, width=700, height=400, key="static_folium_map", returned_objects=["last_clicked"])
        
        if map_data and map_data.get("last_clicked"):
            click = map_data["last_clicked"]
            st.write(f"📍 Координати: {click['lat']:.4f}, {click['lng']:.4f}")
            t_in = st.text_input("Име на новото място:")
            if st.button("Запази маркер") and t_in: add_map_point(trip_id, click["lat"], click["lng"], t_in); st.rerun()

        if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True): confirm_delete_trip_dialog()
