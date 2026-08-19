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
        return files[0]["id"] if files else None
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
        if res: return res[0]["id"]
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

    /* 🔥 КОРИГИРАН СЕЛЕКТОР: Променя само рамките за въвеждане, без да скрива логото и заглавията */
    div[data-testid="stWidgetByPassId"] [data-baseweb="select"],
    div[data-testid="stWidgetByPassId"] [data-baseweb="input"],
    div[data-testid="stWidgetByPassId"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important; 
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        backdrop-filter: blur(4px) !important;
        -webkit-backdrop-filter: blur(4px) !important;
    }
    
    /* Отстояния между самите полета */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
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
                "trip_id": t_id, "car_trip": str(res.get("car_trip", "Не")), 
                "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), 
                "start_km": float(res.get("start_km", 0.0)), "end_km": float(res.get("end_km", 0.0)), 
                "manual_fuel": float(res.get("manual_fuel", 0.0)), "start_date": str(res.get("start_date", "")), "end_date": str(res.get("end_date", ""))
            }
    except: pass
    return d

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass
# Изчисляване на прогресивния разход по метода "до горе" от вашия код
progressive_avg_con, has_progressive_data = 0.0, False
try:
    df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
    df_full_points = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
    
    if not df_full_points.empty:
        last_full_km = float(df_full_points.iloc[-1]["current_km"])
        total_dist = last_full_km - s_km
        total_liters = float(df_trans_fuel[df_trans_fuel["current_km"] <= last_full_km]["liters"].sum()) + m_fuel
        if total_dist > 0 and total_liters > 0:
            progressive_avg_con = (total_liters / total_dist * 100)
            has_progressive_data = True
except: pass

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
                if match: val_to_show = float(match.group(1))
                else: val_to_show = progressive_avg_con if 'progressive_avg_con' in locals() else 0.0
            else:
                if not df_trans_fuel.empty:
                    current_dist = float(df_trans_fuel.iloc[-1]["current_km"]) - s_km
                    current_liters = float(df_trans_fuel["liters"].sum()) + m_fuel
                    if current_dist > 0 and current_liters > 0:
                        val_to_show = (current_liters / current_dist * 100)
                        label_to_show = "среден разход до момента"
        except: pass

    color_gauge = "#00f2fe" if val_to_show < 6.0 else ("#ffa500" if val_to_show < 8.5 else "#ff4b4b")
    transport_liters = float(df_expenses[df_expenses['category'] == 'Транспорт']['liters'].sum()) + m_fuel

        st.markdown(f"### 🚗 Данни за километраж и пробег")
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; margin-bottom: 20px; text-align: center;'><div style='display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 5px; position: relative;'><span style='font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;'>📍 СЛЕДЕНЕ НА ПРОБЕГА</span>{f'<span style=\"background:rgba(255,75,75,0.15); color:#ff4b4b; font-size:10px; padding:2px 8px; border-radius:10px; font-weight:bold;\">🔒 ЗАКЛЮЧЕН</span>' if is_trip_finished else ''}</div><div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 25px 15px 15px 15px;'><div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div><div style='position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>S</div>{finish_icon_html}</div><div style='display: flex; justify-content: space-between; font-size: 13px; padding: 0 10px; gap: 10px;'><div style='text-align: left;'><span style='color: #666; display: block; font-size: 11px;'>Старт</span><b style='color: white; font-size: 14px;'>{s_km:.0f} км</b></div><div style='text-align: center;'><span style='color: #666; display: block; font-size: 11px;'>Изминати</span><b style='color: #00f2fe; font-size: 14px;'>{dist:.0f} км</b></div><div style='text-align: right;'><span style='color: #666; display: block; font-size: 11px;'>Краен</span><b style='color: white; font-size: 14px;'>{f'{eff_end_km:.0f} км' if eff_end_km > 0 else '—'}</b></div></div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 15px; width: 100%;'><div style='flex: 1; min-width: 280px; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center;'><div style='color: #888; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 15px;'>ТЕКУЩ РАЗХОД</div><div style='width: 110px; height: 110px; border-radius: 50%; border: 4px dashed {color_gauge}; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: inset 0 0 15px rgba(0,0,0,0.6); margin-bottom: 15px;'><div style='color: white; font-size: 28px; font-weight: 900; line-height: 1.1;'>{val_to_show:.1f}</div><div style='color: #666; font-size: 10px; font-weight: bold; margin-top: 2px;'>л/100км</div></div><div style='color: #666; font-size: 11px;'>{label_to_show}</div></div><div style='flex: 1; min-width: 280px; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 25px 20px; border-radius: 16px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center; box-shadow: 4px 4px 12px rgba(0,0,0,0.3);'><div style='margin-bottom: 25px; width: 100%; text-align: center;'><div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 8px;'>💧 ОБЩО ЗАРЕДЕНО ГОРИВО</div><div style='color: white; font-size: 28px; font-weight: 800;'>{transport_liters:.1f} <span style='font-size: 14px; color: #666; font-weight: normal;'>литра</span></div></div><div style='padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.06); width: 100%; text-align: center;'><div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 8px;'>💰 ОБЩА СТОЙНОСТ ТРАНСПОРТ</div><div style='color: white; font-size: 28px; font-weight: 800;'>{auto_fuel_money:.2f} <span style='font-size: 14px; color: #666; font-weight: normal;'>EUR</span></div></div></div></div><br>", unsafe_allow_html=True)
            
        if not df_trip.empty:
            st.markdown("---")
            @st.dialog("📜 Хронология на плащанията", width="large")
            def hronologia_popup_dialog():
                st.markdown("<p style='color: #888; margin-bottom: 20px;'>Всички записани разходи за текущото пътуване по категории и дати:</p>", unsafe_allow_html=True)
                st.markdown("""
                    <style>
                        .premium-expense-card {
                            background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%) !important;
                            padding: 14px 18px !important; border-radius: 12px !important; border: 1px solid rgba(250, 250, 250, 0.2) !important;
                            box-shadow: 0px 4px 12px rgba(0,0,0,0.2) !important; margin-bottom: 2px !important; min-height: 52px !important;
                            display: flex !important; flex-direction: column !important; justify-content: center !important;
                        }
                    </style>
                """, unsafe_allow_html=True)
                try:
                    df_all = read_csv_from_drive(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"])
                    valid_expenses = df_all[df_all["trip_id"] == trip_id].index.tolist()
                    if not valid_expenses:
                        st.info("Няма регистрирани разходи за това пътуване.")
                    else:
                        for idx in reversed(valid_expenses):
                            r = df_all.loc[idx]
                            l_txt = f" | ⛽ {r['liters']:.1f} л" if float(r.get("liters", 0)) > 0 else ""
                            col_rec, col_del = st.columns([0.88, 0.12])
                            with col_rec:
                                st.markdown(f'''<div class="premium-expense-card"><div style="display: flex; justify-content: space-between; align-items: center; width: 100%;"><div style="font-size: 16px; font-weight: 600; color: #fafafa;"><span>{get_emoji(r["category"])}</span> {r["category"]}</div><div style="font-size: 16px; font-weight: 700; color: #ff4b4b; letter-spacing: 0.5px;">-{r["amount"]:.2f} EUR</div></div><div style="margin-top: 6px; font-size: 12.5px; color: rgba(250,250,250,0.5); font-family: sans-serif;">📅 {r["date"]} — <span style="color: rgba(250,250,250,0.75);">{r["description"]}</span>{l_txt}</div></div>''', unsafe_allow_html=True)
                            with col_del:
                                if st.button("🗑️", key=f"dl_{idx}", use_container_width=True): 
                                    st.session_state["delete_idx"] = idx
                                    confirm_delete_dialog()
                except:
                    st.error("Грешка при зареждане на хронологията.")
                st.markdown("---")
                if st.button("❌ Изход", use_container_width=True, key="close_hronologia_popup_btn"):
                    st.rerun()

            if st.button("♾️ Хронология на Разходите", use_container_width=True, key="open_hronologia_popup_trigger"):
                hronologia_popup_dialog()

            avg_con_txt = f"{(total_liters_calculated / dist * 100):.1f} л / 100 км" if dist > 0 else (f"{progressive_avg_con:.1f} л / 100 км" if has_progressive_data else "Няма данни")
            grand_total = depozit_hotel + total_on_site
            period_html = f" | <b>Период:</b> {st_date} - {en_date}" if st_date and st_date != "nan" else ""
            dist_html = f" | <b>Общо изминати км. :</b> {dist:.0f} км" if dist > 0 else ""
            
            pdf_html = f"<html><head><meta charset='utf-8'><style>body{{font-family:sans-serif;padding:30px;color:#333;}}h2{{color:#222;border-bottom:2px solid #00f2fe;padding-bottom:8px;margin-bottom:15px;}}h3{{color:#4facfe;margin-top:20px;border-bottom:1px solid #eee;padding-bottom:5px;}}table{{width:100%;border-collapse:collapse;margin-top:15px;}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd;}}th{{background:#f5f5f5;}}.fuel-highlight{{color:#ff1493;font-weight:bold;}}.badge-km{{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:12px;color:#555;font-weight:bold;}}</style></head><body><h2>ОТЧЕТ: {trip_id.upper().replace('_', ' ')}</h2><p style='font-size:15px;'><b>Депозит:</b> {depozit_hotel:.2f} EUR | <b>На място:</b> {total_on_site:.2f} EUR{period_html}{dist_html}</p><p style='font-size:18px; color:#ff4b4b; background:#fff5f5; padding:10px; border-left:4px solid #ff4b4b; margin-top:10px;'><b>💰 ОБЩА СУМА: {grand_total:.2f} EUR</b></p><h3>🚗 Кола:</h3><ul><li><b>Начални:</b> {s_km:.0f} км | <b>Крайна:</b> {eff_end_km:.0f} км</li><li><b>Гориво:</b> {total_liters_calculated:.1f} л | <b>Стойност:</b> {auto_fuel_money:.2f} EUR</li><li><b>Среден разход:</b> {avg_con_txt}</li></ul><h3>📋 Разходи:</h3><table><tr><th>Дата и час</th><th>Описание</th><th>Километраж</th><th>Сума</th><th>Категория</th></tr>"
            
            for _, row in df_trip.iterrows():
                desc_val = str(row['description'])
                if "Моментен разход:" in desc_val: desc_val = desc_val.replace("Моментен разход:", "<span class='fuel-highlight'>Моментен разход:</span>")
                cur_km_val = float(row.get('current_km', 0.0))
                km_td_html = f"<span class='badge-km'>{cur_km_val:.0f} км</span>" if cur_km_val > 0 else "<span style='color:#ccc;'>—</span>"
                pdf_html += f"<tr><td>{row['date']}</td><td>{desc_val}</td><td>{km_td_html}</td><td>{row['amount']:.2f} EUR</td><td>{row['category']}</td></tr>"
            pdf_html += f"<tr><td colspan='3' style='text-align:right; font-weight:bold;'>Общо:</td><td colspan='2' style='font-weight:bold; color:#ff4b4b;'>{grand_total:.2f} EUR</td></tr></table></body></html>"
            
            st.markdown("<a id='click_scroll_trigger' href='#top_of_page' style='display:none;'></a>", unsafe_allow_html=True)
            if st.button("♾️ Хронология на Разходите", use_container_width=True, key="open_hronologia_popup_trigger"): hronologia_popup_dialog()
            st.download_button(label="Отчет в PDF", data=pdf_html, file_name=f"Otchet_{trip_id}_2026.html", mime="text/html", use_container_width=True, key="st_premium_report_download_btn")
            st.markdown("---")

        st.subheader("🗺️ Карта на спирките и дестинациите")
        df_points = get_map_points(trip_id)
        c_lat, c_lon = (df_points["lat"].mean(), df_points["lon"].mean()) if not df_points.empty else (42.7339, 25.4858)
        m = folium.Map(location=[c_lat, c_lon], zoom_start=6)
        m.get_root().html.add_child(folium.Element("<script>document.documentElement.lang = 'bg';</script>"))
        folium.LatLngPopup().add_to(m)
        for _, pt in df_points.iterrows(): folium.Marker(location=[pt["lat"], pt["lon"]], popup=pt["title"], icon=folium.Icon(color=pt["color"], icon="info-sign")).add_to(m)
        
        map_data = st_folium(m, width=700, height=400, key="static_folium_trip_map", returned_objects=["last_clicked"])
        if map_data and map_data.get("last_clicked"):
            new_click = map_data["last_clicked"]
            if st.session_state.get("active_click") != new_click:
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
                        st.session_state["active_click"] = None; st.rerun()
            with cb2:
                if st.button("❌ Отказ", use_container_width=True): st.session_state["active_click"] = None; st.rerun()

        if not df_points.empty:
            st.markdown("#### 📍 Любими места от пътуването")
            st.markdown("---")
            try:
                df_all_map = read_csv_from_drive(MAP_FILE, ["trip_id", "lat", "lon", "title", "color"])
                color_emojis = {"blue": "🔵", "green": "🟢", "red": "🔴", "purple": "🟣", "orange": "🟠"}
                for idx in df_all_map[df_all_map["trip_id"] == trip_id].index.tolist():
                    pt_row = df_all_map.loc[idx]
                    col_p_txt, col_p_del = st.columns([0.85, 0.15])
                    with col_p_txt: st.markdown(f"{color_emojis.get(pt_row['color'], '🔵')} **{pt_row['title']}** <small>({pt_row['lat']:.4f}, {pt_row['lon']:.4f})</small>", unsafe_allow_html=True)
                    with col_p_del:
                        if st.button("❌", key=f"del_pin_{idx}", use_container_width=True, disabled=is_trip_finished):
                            df_all_map = df_all_map.drop(idx)
                            save_csv_to_drive(MAP_FILE, df_all_map); st.rerun()
            except: pass

        st.markdown("---")
        if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True, key="delete_whole_trip_final_btn"): confirm_delete_trip_dialog()
            
        st.markdown("""
            <style>
                html { scroll-behavior: smooth !important; }
                .twin-premium-3d-btn {
                    display: inline-flex !important; align-items: center !important; justify-content: center !important;
                    width: 100% !important; height: 38.4px !important;
                    background: linear-gradient(to bottom, #262730 0%, #1a1c23 100%) !important; color: #ffffff !important; 
                    border: 1px solid rgba(255, 255, 255, 0.12) !important; padding: 0.25rem 0.75rem !important;
                    font-weight: 600 !important; font-size: 14px !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                    border-radius: 0.5rem !important; cursor: pointer !important; user-select: none !important;
                    box-shadow: 0px 3px 0px #0e1117, 0px 5px 10px rgba(0,0,0,0.35) !important; transition: all 0.15s ease-in-out !important;
                }
                .twin-premium-3d-btn:hover {
                    background: linear-gradient(to bottom, #31333e 0%, #22242d 100%) !important; border-color: rgba(255, 255, 255, 0.3) !important;
                    box-shadow: 0px 3px 0px #0e1117, 0px 7px 14px rgba(0,0,0,0.45) !important;
                }
                .twin-premium-3d-btn:active {
                    transform: translateY(2px) !important; box-shadow: 0px 1px 0px #0e1117, 0px 2px 4px rgba(0,0,0,0.2) !important; transition: all 0.05s ease !important;
                }
                .twin-grid-wrapper a { text-decoration: none !important; width: 100% !important; display: block !important; }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        bottom_cols = st.columns(2)
        with bottom_cols[0]:
            if st.button("🏠 ГЛАВНО МЕНЮ", use_container_width=True, key="fallback_home_trigger_btn"):
                st.session_state["current_trip"] = None; st.rerun()
        with bottom_cols[1]:
            st.markdown("""<div class="twin-grid-wrapper"><a href="#trip_top_anchor" target="_self"><button class="twin-premium-3d-btn">🔝 КЪМ РАЗХОДИТЕ</button></a></div>""", unsafe_allow_html=True)
