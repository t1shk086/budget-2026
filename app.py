import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Страница и оригинален премиум 3D CSS дизайн за PixelApp
st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

st.markdown("""
<style>
    /* Модерни кутии за въвеждане на данни */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important; padding: 10px 15px !important;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4), -2px -2px 8px rgba(255, 255, 255, 0.02) !important;
        margin-bottom: 15px !important;
    }
    /* Нов селектор за ПРЕМИУМ 3D БУТОНИ */
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"],
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(135deg, #2e2e2e, #1c1c1c) !important; 
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important; 
        border-radius: 10px !important;
        box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5), -1px -1px 4px rgba(255, 255, 255, 0.05) !important;
        transition: all 0.2s ease !important; 
        font-weight: bold !important;
        width: 100% !important;
    }
    /* Ефект при посочване с мишката */
    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFileUploaderDropzone"] button:hover {
        background: linear-gradient(135deg, #3d3d3d, #252525) !important;
        transform: translateY(-2px) !important; 
        box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.6) !important;
    }
    small { color: #888 !important; }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"

# Автоматично създаване на файла за картата, ако не съществува
if not os.path.exists(MAP_FILE):
    pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(MAP_FILE, index=False, encoding="utf-8")

def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])]:
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

def get_trip_data(t_id):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        r = df[df["trip_id"] == t_id].copy()
        if "liters" not in r.columns: r["liters"] = 0.0
        if "current_km" not in r.columns: r["current_km"] = 0.0
        return r
    except: return pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters","current_km"])

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        f = df[df["trip_id"] == t_id]
        if not f.empty:
            res = f.iloc[0].to_dict()
            return {"trip_id": t_id, "car_trip": str(res.get("car_trip", "Не")), "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), "start_km": float(res.get("start_km", 0.0)), "end_km": float(res.get("end_km", 0.0)), "manual_fuel": float(res.get("manual_fuel", 0.0)), "start_date": str(res.get("start_date", "")), "end_date": str(res.get("end_date", ""))}
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

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "current_km" not in df.columns: df["current_km"] = 0.0
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False

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
    st.markdown("""
    <div style='text-align: center; margin-bottom: 5px;'>
        <h1 style='font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 10px rgba(0, 242, 254, 0.2); margin-bottom: 0px;'>🐾 PixelApp</h1>
        <p style='font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; letter-spacing: normal; text-transform: none; margin-top: 4px; margin-bottom: 30px; text-shadow: 1px 1px 6px rgba(255, 215, 0, 0.15);'>Travel Manager</p>
    </div>
    """, unsafe_allow_html=True)
    
    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("📂 ОТВОРИ ПЪТУВАНЕ", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.rerun()
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-bottom:15px;'>Все още нямате записани почивки. Създайте първото си приключение по-долу!</div>", unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>", unsafe_allow_html=True)
    
    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:").strip()
        d_range = st.date_input("Изберете дати за почивката:", value=[datetime.date.today(), datetime.date.today()])
        st.write("---")
        st.write("🚗 Пътувате ли със собствен автомобил?")
        viber_car = st.radio("Изберете вариант:", ["Не, с друг транспорт", "Да, със собствен автомобил"], index=0)
        new_skm = 0.0
        if viber_car == "Да, със собствен автомобил":
            new_skm = st.number_input("Начални километри (км):", value=None, placeholder="Въведете км на тръгване...", step=1.0)
            
        if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True, type="primary") and txt:
            if isinstance(d_range, (list, tuple)):
                s_d_str = d_range[0].strftime("%d.%m.%Y") if len(d_range) > 0 else ""
                e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 else s_d_str
            elif hasattr(d_range, "strftime"):
                s_d_str = d_range.strftime("%d.%m.%Y")
                e_d_str = s_d_str
            else:
                s_d_str, e_d_str = "", ""
                
            sk = float(new_skm) if new_skm is not None else 0.0
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, "Да" if viber_car == "Да, със собствен автомобил" else "Не", "Да" if viber_car == "Да, със собствен автомобил" else "Добави впоследствие", sk, 0.0, 0.0, s_d_str, e_d_str)
            
            try:
                geolocator = Nominatim(user_agent="pixelapp_travel_manager_2026")
                location = geolocator.geocode(f"{txt}, Europe", language="bg,en")
                if location:
                    add_map_point(target_id, location.latitude, location.longitude, f"🏁 Център: {txt}", "red")
            except:
                pass
                
            st.session_state["current_trip"] = target_id
            st.rerun()

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
            st.write("")
            c_del1, c_del2 = st.columns(2)
            with c_del1:
                if st.button("👍 ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                    try:
                        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                        df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8")
                    except: pass
                    st.session_state["delete_idx"] = None
                    st.rerun()
            with c_del2:
                if st.button("🛟 ОТКАЗ", use_container_width=True):
                    st.session_state["delete_idx"] = None
                    st.rerun()

    @st.dialog("🚨 Изтриване на цялото пътуване")
    def confirm_delete_trip_dialog():
        st.error(f"ВНИМАНИЕ! Сигурни ли сте, че искате да изтриете напълно пътуването до {trip_id.replace('_', ' ')}?")
        st.write("Това действие ще премахне завинаги всички записани разходи, настройки и снимки от базата данни.")
        st.write("")
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            if st.button("💥 ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
                try:
                    df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                    df_all[df_all["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
                    
                    df_set = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
                    df_set[df_set["trip_id"] != trip_id].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
                    
                    if os.path.exists(papka_snimki):
                        for p in glob.glob(os.path.join(papka_snimki, "*")): os.remove(p)
                        os.rmdir(papka_snimki)
                except: pass
                st.session_state["current_trip"] = None
                st.rerun()
        with c_tr2:
            if st.button("🛟 ОТКАЗ", use_container_width=True):
                st.rerun()

    date_html = f"<p style='font-size: 14px; color: #888; font-weight: 500; margin-top: 5px;'>{st_date} - {en_date}</p>" if st_date and st_date != "nan" else ""
    st.markdown(f"""
    <div style='text-align: center; margin-top: 10px; margin-bottom: 15px;'>
        <h2 style='font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-weight: 500; font-size: 28px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 8px rgba(0, 242, 254, 0.1); margin-bottom: 0px;'>
            🌴 Дестинация: {trip_id.replace('_', ' ')}
        </h2>
        {date_html}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

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
            elif any(k in str(row["description"]).lower() for k in ["гориво", "зареждане", "бензин", "дизел"]): auto_fuel_money += float(row["amount"])
    
    total_liters_calculated = total_liters_sum + m_fuel
    
    max_current_km = 0.0
    if not df_expenses.empty and "current_km" in df_expenses.columns:
        max_current_km = float(df_expenses["current_km"].max())
        
    eff_end_km = e_km if e_km > 0 else max_current_km
    dist = eff_end_km - s_km if eff_end_km > s_km else 0.0

    progressive_avg_con = 0.0
    has_progressive_data = False
    try:
        df_trans = df_expenses[df_expenses["category"] == "Транспорт"].copy()
        df_trans_fuel = df_trans[df_trans["current_km"] > s_km].sort_index()
        if not df_trans_fuel.empty:
            last_recorded_km = float(df_trans_fuel.iloc[-1]["current_km"])
            progressive_dist = last_recorded_km - s_km
            progressive_liters = float(df_trans_fuel["liters"].sum()) + m_fuel
            if progressive_dist > 0 and progressive_liters > 0:
                progressive_avg_con = (progressive_liters / progressive_dist * 100)
                has_progressive_data = True
    except: pass

    if st.session_state["view_photos"]:
        if st.button("⬅️ НАЗАД КЪМ РАЗХОДИТЕ", use_container_width=True):
            st.session_state["view_photos"] = False; st.rerun()
            
        if not os.path.exists(papka_snimki): os.makedirs(papka_snimki)
        up = st.file_uploader("Добавете нови спомени в албума:", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"u_{trip_id}")
        if up:
            for f in up:
                if not os.path.exists(os.path.join(papka_snimki, f.name)):
                    with open(os.path.join(papka_snimki, f.name), "wb") as out: out.write(f.getbuffer())
            st.rerun()
            
        saved = glob.glob(os.path.join(papka_snimki, "*"))
        if saved:
            st.markdown("<br>", unsafe_allow_html=True)
            img_grid = st.columns(2)
            for idx, p in enumerate(saved):
                with img_grid[idx % 2]:
                    st.image(p, use_container_width=True)
                    if st.button("🗑️ Изтрий", key=f"di_{idx}", use_container_width=True): os.remove(p); st.rerun()
        else:
            st.markdown("<div style='text-align:center; margin-top:40px; color:#666;'>Все още няма качени снимки в този албум.</div>", unsafe_allow_html=True)

    else:
        if st.button("⬅️ НАЗАД ", use_container_width=True):
            st.session_state["current_trip"] = None; st.rerun()
            
        v_id = st.session_state["form_version"]
        col1, col2 = st.columns(2)
        with col1: s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Напишете сума...", format="%.2f", key=f"su_{v_id}")
        with col2: o_input = st.text_input("Описание", placeholder="Напишете описание...", key=f"op_{v_id}")

        is_trip_finished = (e_km > 0.0)

        @st.dialog("⛽ Зареждане на гориво")
        def fuel_modal(amount, category, description, is_dep):
            if is_trip_finished:
                st.error("🔒 Пътуването е приключено! Настройките са заключени.")
                return
            st.write(f"Засякохме гориво за **{amount:.2f} EUR**.")
            
            liters = st.number_input("Литри:", value=None, placeholder="Напишете литри...", step=0.1)
            fuel_type = st.radio("Тип на зареждането:", ["Да, до горе (Пълен резервоар)", "Не, частично (за конкретна сума)"], index=0)
            
            df_e = get_trip_data(trip_id)
            df_f = df_e[(df_e["category"] == "Транспорт") & (df_e["current_km"] > 0)]
            last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
            
            st.markdown(f"<small>ℹ️ Километри при последното зареждане (или старт): <b>{last_km:.0f} км</b></small>", unsafe_allow_html=True)
            km_input = st.number_input("Текущи километри на таблото (км):", value=None, placeholder="Въведете км от таблото в момента...", step=1.0)
            
            if liters and km_input:
                if km_input > last_km:
                    m_dist = km_input - last_km
                    if "до горе" in fuel_type.lower():
                        m_avg = (liters / m_dist * 100)
                        st.success(f"📊 Точен разход за този етап: **{m_avg:.1f} л / 100 км** (Изминати: {m_dist:.0f} км)")
                    else:
                        st.info(f"ℹ️ Изминати {m_dist:.0f} км в този етап. Разходът ще се преизчисли при следващ пълен резервоар.")
                else:
                    st.warning("⚠️ Въведените километри трябва да са повече от предходните!")

            if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
                lit = float(liters) if liters is not None else 0.0
                ckm = float(km_input) if km_input is not None else 0.0
                
                is_full = "ПЪЛЕН" if "до горе" in fuel_type.lower() else "ЧАСТИЧЕН"
                full_desc = f"[{is_full} ГОРИВО] {description}"
                
                if ckm > last_km and lit > 0 and is_full == "ПЪЛЕН":
                    m_dist = ckm - last_km
                    m_avg = (lit / m_dist * 100)
                    full_desc += f" (Етап: {m_dist:.0f}км, Разход: {m_avg:.1f}л/100км)"
                
                if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm):
                    st.session_state["form_version"] += 1; st.rerun()

        grid = st.columns(3)
        for i, kat in enumerate(KATEGORII):
            with grid[i % 3]:
                is_disabled = is_trip_finished and (kat == "Транспорт")
                btn_label = f"🔒 {kat}" if is_disabled else kat
                if st.button(btn_label, use_container_width=True, key=f"bt_{i}", disabled=is_disabled):
                    if s_input and s_input > 0:
                        desc = o_input.strip() if o_input else "Без описание"
                        is_d = (kat == "Депозит/Резервация")
                        if kat == "Транспорт" and any(k in desc.lower() for k in ["гориво", "зареждане", "бензин", "дизел"]):
                            fuel_modal(s_input, kat, desc, is_d)
                        else:
                            if add_expense(trip_id, s_input, kat, desc, is_d): st.session_state["form_version"] += 1; st.rerun()

        # --- ЧАСТ 7А: МАТЕМАТИКА И ВИЗУАЛИЗАЦИЯ НА РАЗХОДА ---
        val_to_show = 0.0
        is_final_status = False

        try:
            df_trans = df_expenses[df_expenses["category"] == "Транспорт"].copy()
            df_fuel = df_trans[df_trans["current_km"] >= s_km].sort_values(by="current_km")
            
            total_valid_liters = 0.0
            total_valid_dist = 0.0
            prev_km = s_km
            temp_liters = 0.0
            
            for _, row in df_fuel.iterrows():
                desc_upper = str(row["description"]).upper()
                current_entry_km = float(row["current_km"])
                entry_liters = float(row.get("liters", 0.0))
                
                if current_entry_km == s_km:
                    prev_km = current_entry_km
                    continue
                    
                stage_dist = current_entry_km - prev_km
                if stage_dist > 0:
                    temp_liters += entry_liters
                    if "ПЪЛЕН" in desc_upper:
                        total_valid_dist += stage_dist
                        total_valid_liters += temp_liters
                        temp_liters = 0.0 
                        prev_km = current_entry_km

            total_valid_liters += m_fuel
            if total_valid_dist > 0 and total_valid_liters > 0:
                val_to_show = (total_valid_liters / total_valid_dist) * 100
            
            if e_km > s_km:
                is_final_status = True
                if val_to_show == 0.0 and total_liters_calculated > 0:
                    val_to_show = (total_liters_calculated / dist) * 100
                    
        except Exception as e:
            st.error(f"Грешка при изчисление: {e}")

        if val_to_show == 0.0: color_gauge = "#666"
        elif val_to_show <= 5.5: color_gauge = "#00ffcc"
        elif val_to_show <= 8.0: color_gauge = "#00f2fe"
        elif val_to_show <= 11.0: color_gauge = "#ffa500"
        else: color_gauge = "#ff4b4b"

        lbl_gauge = "ФИНАЛЕН РАЗХОД" if is_final_status else "ТЕКУЩ РАЗХОД"
        sub_lbl_gauge = "за затворените етапи" if not is_final_status else "за целия пробег"
        km_progress_pct = 100 if is_final_status else min(100, max(0, (dist / 1000 * 100))) if dist > 0 else 0
        car_left_css = "left: 0px;" if km_progress_pct == 0 else f"left: calc({km_progress_pct}% - 10px);"
        lock_lbl_html = f"<span style='background:rgba(255,75,75,0.15); color:#ff4b4b; font-size:10px; padding:2px 8px; border-radius:10px; font-weight:bold;'>🔒 ЗАКЛЮЧЕН</span>" if is_trip_finished else ""
        finish_icon_html = f"<div style='position: absolute; right: 0; top: -8px; background: #1c1c1c; border: 2px solid #ff4b4b; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>F</div>" if is_trip_finished else f"<div style='position: absolute; {car_left_css} top: -12px; font-size: 16px;'>🚗</div>"

        start_km_txt = f"{s_km:.0f} км"
        current_km_txt = f"{eff_end_km:.0f} км" if eff_end_km > 0 else "—"
        dist_km_txt = f"{dist:.0f} км" if dist > 0 else "0 км"
        label_status_txt = "Крайни" if is_trip_finished else "Текущи"

        html_probel_box = f"<div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; box-shadow: 5px 5px 15px rgba(0,0,0,0.4); margin-bottom: 20px; text-align: center;'><div style='display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 5px; position: relative;'><span style='font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;'>📍 СЛЕДЕНЕ НА ПРОБЕГА</span>{lock_lbl_html}</div><div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 25px 15px 15px 15px;'><div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div><div style='position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>S</div>{finish_icon_html}</div><div style='display: flex; justify-content: space-between; font-size: 13px; padding: 0 10px; gap: 10px;'><div style='flex: 1; text-align: left;'><span style='color: #666; display: block; font-size: 11px;'>Старт</span><b style='color: white; font-size: 14px;'>{start_km_txt}</b></div><div style='flex: 1; text-align: center;'><span style='color: #666; display: block; font-size: 11px;'>Изминати</span><b style='color: #00f2fe; font-size: 14px;'>{dist_km_txt}</b></div><div style='flex: 1; text-align: right;'><span style='color: #666; display: block; font-size: 11px;'>{label_status_txt}</span><b style='color: white; font-size: 14px;'>{current_km_txt}</b></div></div></div>"
        st.markdown(html_probel_box, unsafe_allow_html=True)

        total_liters_all = float(df_trans["liters"].sum()) + m_fuel
        html_dashboard_boxes = f"<div style='display: flex; flex-wrap: wrap; gap: 15px; width: 100%;'><div style='flex: 1; min-width: 280px; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 4px 4px 12px rgba(0,0,0,0.3);'><div style='color: #888; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 15px; margin-top: 0;'>{lbl_gauge}</div><div style='width: 110px; height: 110px; border-radius: 50%; border: 4px dashed {color_gauge}; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: inset 0 0 15px rgba(0,0,0,0.6); margin-bottom: 15px; box-sizing: border-box; padding: 0;'><div style='color: white; font-size: 28px; font-weight: 900; margin: 0; padding: 0; line-height: 1.1; text-align: center;'>{val_to_show:.1f}</div><div style='color: #666; font-size: 10px; font-weight: bold; margin-top: 2px; padding: 0; text-align: center;'>л/100км</div></div><div style='color: #666; font-size: 11px; margin: 0;'>{sub_lbl_gauge}</div></div><div style='flex: 1; min-width: 280px; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 25px 20px; border-radius: 16px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center; box-shadow: 4px 4px 12px rgba(0,0,0,0.3); box-sizing: border-box;'><div style='margin-bottom: 25px; width: 100%;'><div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin: 0 0 8px 0; text-align: center;'>💧 ОБЩО ЗАРЕДЕНО ГОРИВО</div><div style='color: white; margin: 0; font-size: 28px; font-weight: 800; line-height: 1.2; text-align: center;'>{total_liters_all:.1f} <span style='font-size: 14px; color: #666; font-weight: normal;'>литра</span></div></div><div style='padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.06); width: 100%;'><div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin: 0 0 8px 0; text-align: center;'>💰 ОБЩА СТОЙНОСТ ТРАНСПОРТ</div><div style='color: white; margin: 0; font-size: 28px; font-weight: 800; line-height: 1.2; text-align: center;'>{auto_fuel_money:.2f} <span style='font-size: 14px; color: #666; font-weight: normal;'>EUR</span></div></div></div></div><br>"
        st.markdown(html_dashboard_boxes, unsafe_allow_html=True)

        # --- ЧАСТ 7Б: НАСТРОЙКИ, ФИНАЛИЗИРАНЕ, КАРТА И РАЗХОДИ ---
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        
        @st.dialog("⚙️ Настройки на превозно средство и период")
        def edit_car_modal():
            st.write("Променете настройките на почивката:")
            v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=0 if car_trip == "Не" else 1, disabled=is_trip_finished)
            new_sk = st.number_input("Начални км:", value=None if s_km == 0.0 else s_km, placeholder="Напишете км...", disabled=is_trip_finished)
            new_mf = st.number_input("Добави пропуснато гориво (л):", value=None if m_fuel == 0.0 else m_fuel, placeholder="Напишете литри...", disabled=is_trip_finished)
            
            has_cash_expense = False
            manual_cash_amt = 0.0
            if new_mf and new_mf > 0 and not is_trip_finished:
                has_cash_expense = st.checkbox("💵 Има ли финансов разход (плащане) за добавеното гориво?")
                if has_cash_expense:
                    manual_cash_amt = st.number_input("Въведете платена сума (EUR):", value=None, placeholder="Сума в EUR...", format="%.2f")

            st.write("📅 Промяна на датите на почивката:")
            try:
                current_start = datetime.datetime.strptime(st_date, "%d.%m.%Y").date() if st_date and st_date != "nan" else datetime.date.today()
                current_end = datetime.datetime.strptime(en_date, "%d.%m.%Y").date() if en_date and en_date != "nan" else datetime.date.today() + datetime.timedelta(days=5)
            except: 
                current_start, current_end = datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)
            
            edit_range = st.date_input("Изберете нови дати:", value=[current_start, current_end], key="edit_dates_cal")
            
            if st.button("💾 Обнови", use_container_width=True, type="primary", disabled=is_trip_finished):
                sk_val = float(new_sk) if new_sk is not None else s_km
                mf_val = float(new_mf) if new_mf is not None else m_fuel
                
                if isinstance(edit_range, (list, tuple)) and len(edit_range) > 0:
                    s_d_str = edit_range[0].strftime("%d.%m.%Y")
                    e_d_str = edit_range[-1].strftime("%d.%m.%Y") if len(edit_range) > 1 else s_d_str
                elif hasattr(edit_range, "strftime"):
                    s_d_str = edit_range.strftime("%d.%m.%Y")
                    e_d_str = s_d_str
                else:
                    s_d_str, e_d_str = st_date, en_date

                save_trip_settings(trip_id, v_car, t_fuel, sk_val, e_km, mf_val, s_d_str, e_d_str)

                if has_cash_expense and manual_cash_amt and manual_cash_amt > 0:
                    add_expense(trip_id, manual_cash_amt, "Транспорт", f"[ДОБАВЕНО ГОРИВО] Ръчно въведено гориво ({mf_val:.1f} л)", is_dep=False, lit=0.0, c_km=0.0)

                st.rerun()

        @st.dialog("🏁 Приключване на пътуването")
        def finish_trip_modal():
            st.write("Въведете финалния километраж на автомобила при пристигане:")
            df_e = get_trip_data(trip_id)
            df_f = df_e[(df_e["category"] == "Транспорт") & (df_e["current_km"] > 0)]
            last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
            
            st.markdown(f"<small>ℹ️ Последен записан километраж: <b>{last_km:.0f} км</b></small>", unsafe_allow_html=True)
            final_km_input = st.number_input("Финални километри (км):", value=None, placeholder="Въведете км от таблото...", step=1.0)

            if final_km_input:
                if final_km_input >= last_km:
                    f_dist = final_km_input - s_km
                    st.success(f"Общ пробег за целия престой: **{f_dist:.0f} км**")
                else:
                    st.warning("⚠️ Крайните километри трябва да са повече или равни на последните записани!")

            if st.button("🏁 Финализирай пътуването", use_container_width=True, type="primary"):
                if final_km_input and final_km_input >= last_km:
                    save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(final_km_input), m_fuel, st_date, en_date)
                    st.rerun()

        cfg_col1, cfg_col2 = st.columns(2)
        with cfg_col1:
            if st.button("⚙️ Настройки", use_container_width=True):
                edit_car_modal()
        with cfg_col2:
            if not is_trip_finished:
                if st.button("🏁 Финализирай", use_container_width=True):
                    finish_trip_modal()
            else:
                if st.button("🔓 Отключи пътуването", use_container_width=True):
                    save_trip_settings(trip_id, car_trip, t_fuel, s_km, 0.0, m_fuel, st_date, en_date)
                    st.rerun()

        st.markdown("---")

        # --- ИНТЕРАКТИВНА КАРТА С ПИНОВЕ ---
        st.markdown("<h3 style='font-size: 20px; font-weight: bold; margin-bottom: 10px;'>🗺️ Карта на приключението</h3>", unsafe_allow_html=True)
        
        map_df = get_map_points(trip_id)
        
        start_lat, start_lon = 42.6977, 23.3219
        zoom_level = 6
        if not map_df.empty:
            start_lat = map_df["lat"].mean()
            start_lon = map_df["lon"].mean()
            zoom_level = 9

        m = folium.Map(location=[start_lat, start_lon], zoom_start=zoom_level, tiles="CartoDB positron")

        for _, r_map in map_df.iterrows():
            folium.Marker(
                location=[r_map["lat"], r_map["lon"]],
                popup=r_map["title"],
                tooltip=r_map["title"],
                icon=folium.Icon(color=r_map.get("color", "blue"), icon="info-sign")
            ).add_to(m)

        m.add_child(folium.LatLngPopup())
        map_data = st_folium(m, width="100%", height=350)

        with st.expander("📍 Добави нова точка / локация по картата"):
            clicked_lat = map_data.get("last_point", {}).get("lat", None) if map_data else None
            clicked_lon = map_data.get("last_point", {}).get("lng", None) if map_data else None
            
            p_title = st.text_input("Име на точката (напр. Хотел, Забележителност, Ресторант):", placeholder="Напишете име...")
            p_color = st.selectbox("Цвят на пина:", ["blue", "red", "green", "purple", "orange", "darkred", "cadetblue"])
            
            c_lat_col, c_lon_col = st.columns(2)
            with c_lat_col:
                p_lat = st.number_input("Ширина (Lat):", value=clicked_lat if clicked_lat else 0.0, format="%.6f")
            with c_lon_col:
                p_lon = st.number_input("Дължина (Lon):", value=clicked_lon if clicked_lon else 0.0, format="%.6f")
                
            if st.button("📍 Запази точката", use_container_width=True, type="primary"):
                if p_title and p_lat != 0.0 and p_lon != 0.0:
                    add_map_point(trip_id, p_lat, p_lon, p_title, p_color)
                    st.rerun()
                else:
                    st.warning("⚠️ Моля, въведете валидно име и координати (можете да кликнете върху картата, за да ги попълните автоматично)!")

        st.markdown("---")

        # --- ТАБЛИЦА С РАЗХОДИ И ФИЛТРИ ---
        st.markdown("<h3 style='font-size: 20px; font-weight: bold; margin-bottom: 10px;'>📜 История на разходите</h3>", unsafe_allow_html=True)
        
        if not df_trip.empty:
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 15px; margin-bottom: 15px; text-align: center;'>
                <span style='color: #888; font-size: 12px; display: block;'>ОБЩО ТЕКУЩИ РАЗХОДИ</span>
                <b style='color: #00f2fe; font-size: 26px;'>{total_on_site:.2f} EUR</b>
                {f"<br><small style='color: #ffa500;'>+ {depozit_hotel:.2f} EUR (Депозити/Резервации)</small>" if depozit_hotel > 0 else ""}
            </div>
            """, unsafe_allow_html=True)

            if st.button("📸 Към фотоалбума на пътуването", use_container_width=True):
                st.session_state["view_photos"] = True
                st.rerun()

            st.write("")

            for idx, r in df_trip.iloc[::-1].iterrows():
                is_dep = (r["type"] == "deposit")
                bg_color = "rgba(255, 165, 0, 0.05)" if is_dep else "rgba(255, 255, 255, 0.02)"
                border_color = "rgba(255, 165, 0, 0.2)" if is_dep else "rgba(255, 255, 255, 0.08)"
                badge_html = "<span style='background:#ffa500; color:black; font-size:10px; padding:2px 6px; border-radius:4px; font-weight:bold; margin-left:5px;'>ДЕПОЗИТ</span>" if is_dep else ""

                liters_info = f" • <span style='color:#00f2fe;'>{r['liters']:.1f} л</span>" if float(r.get("liters", 0)) > 0 else ""
                km_info = f" • <span style='color:#888;'>{r['current_km']:.0f} км</span>" if float(r.get("current_km", 0)) > 0 else ""

                st.markdown(f"""
                <div style='background: {bg_color}; border: 1px solid {border_color}; border-radius: 10px; padding: 12px 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-size: 14px; font-weight: bold; color: white;'>
                            {get_emoji(r['category'])} {r['category']} {badge_html}
                        </div>
                        <div style='font-size: 12px; color: #aaa; margin-top: 2px;'>
                            {r['description']}
                        </div>
                        <div style='font-size: 10px; color: #666; margin-top: 4px;'>
                            🕒 {r['date']}{liters_info}{km_info}
                        </div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 16px; font-weight: bold; color: #ff4b4b;'>
                            -{r['amount']:.2f} EUR
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🗑️ Изтрий запис", key=f"del_btn_{idx}", use_container_width=True):
                    st.session_state["delete_idx"] = idx
                    confirm_delete_dialog()

        else:
            st.info("Все още няма добавени разходи за това пътуване.")

        st.markdown("---")
        
        if st.button("🚨 Изтрий цялото пътуване", use_container_width=True):
            confirm_delete_trip_dialog()
