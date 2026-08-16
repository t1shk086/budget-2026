import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64

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
    /* Нов селектор за ПРЕМИУМ 3D БУТОНИ (Всички бутони в приложението) */
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
    /* Ефект при посочване с мишката (Hover) */
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
# === КРАЙ НА ЧАСТ 1 ===
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
# === КРАЙ НА ЧАСТ 2 ===
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
# === КРАЙ НА ЧАСТ 3 ===
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
            st.session_state["current_trip"] = target_id; st.rerun()
            
    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()

else:
    trip_id = st.session_state["current_trip"]
    papka_snimki = f"snimki_{trip_id}_2026"
    c_s = get_trip_settings(trip_id)
    car_trip, t_fuel, s_km, e_km, m_fuel = str(c_s["car_trip"]), str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    # Глобален стабилен диалог за сигурно триене на разход
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

    # Глобален стабилен диалог за сигурно триене на цялото пътуване
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
    dist = e_km - s_km

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
# === КРАЙ НА ЧАСТ 4 ===

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
            
            df_e = get_trip_data(trip_id)
            df_f = df_e[(df_e["category"] == "Транспорт") & (df_e["current_km"] > 0)]
            last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
            
            st.markdown(f"<small>ℹ️ Километри при последното зареждане (или старт): <b>{last_km:.0f} км</b></small>", unsafe_allow_html=True)
            km_input = st.number_input("Текущи километри на таблото (км):", value=None, placeholder="Въведете км от таблото в момента...", step=1.0)
            
            if liters and km_input:
                if km_input > last_km:
                    m_dist = km_input - last_km
                    m_avg = (liters / m_dist * 100)
                    st.success(f"📊 Моментен разход за този етап: **{m_avg:.1f} л / 100 км** (Изминати: {m_dist:.0f} км)")
                else:
                    st.warning("⚠️ Въведените километри трябва да са повече от предходните!")

            if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
                lit = float(liters) if liters is not None else 0.0
                ckm = float(km_input) if km_input is not None else 0.0
                full_desc = f"[ГОРИВО] {description}"
                if ckm > last_km and lit > 0:
                    m_dist = ckm - last_km
                    m_avg = (lit / m_dist * 100)
                    full_desc += f" (Моментен разход: {m_avg:.1f}л/100км, Етап: {m_dist:.0f}км)"
                
                if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm):
                    st.session_state["form_version"] += 1; st.rerun()
# === КРАЙ НА ЧАСТ 5 ===
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
                            
        st.markdown("### 📊 Анализ на разходите")
        stat_grid = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
            b_c = "rgba(255,75,75,0.4)" if pct > 40 else "rgba(255,165,0,0.4)" if pct > 20 else "rgba(0,242,254,0.3)" if pct > 0 else "rgba(255,255,255,0.08)"
            b_g = "rgba(255,75,75,0.2)" if pct > 40 else "rgba(255,165,0,0.2)" if pct > 20 else "rgba(0,242,254,0.15)" if pct > 0 else "rgba(255,255,255,0.1)"
            b_t = "#ff4b4b" if pct > 40 else "#ffa500" if pct > 20 else "#00f2fe" if pct > 0 else "#aaa"
            with stat_grid[idx % 2]:
                st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); border: 1px solid {b_c}; padding: 12px 15px; border-radius: 14px; box-shadow: 3px 3px 10px rgba(0,0,0,0.3); margin-bottom: 12px; height: 120px; display: flex; flex-direction: column; justify-content: space-between;"><div style="display: flex; justify-content: space-between; align-items: center;"><span>{get_emoji(kat)} {kat}</span><span style="background:{b_g}; color:{b_t}; font-size:11px; padding:2px 7px; border-radius:20px; font-weight:bold;">{pct:.1f}%</span></div><h3 style="margin:0; color:white; font-size:20px; font-weight:800;">{s_value:.2f} <span style="font-size:11px; color:#aaa;">EUR</span></h3><div style="background: rgba(255,255,255,0.05); width: 100%; height: 6px; border-radius: 10px; overflow: hidden;"><div style="background: {b_t}; width: {pct}%; height: 100%; border-radius: 10px;"></div></div></div>', unsafe_allow_html=True)

        if car_trip == "Да":
            st.markdown("#### ⛽ Автомобилно табло")
            status_lbl = " LOCKED" if is_trip_finished else ""
            
            # Изчисляване на стойностите за визуалния разход
            val_to_show = 0.0
            is_final_status = False
            if dist > 0:
                val_to_show = (total_liters_calculated / dist * 100) if total_liters_calculated > 0 else 0.0
                is_final_status = True
            elif has_progressive_data:
                val_to_show = progressive_avg_con

            # Динамичен цвят според икономичността на разхода
            if val_to_show == 0.0: color_gauge = "#666"
            elif val_to_show <= 5.5: color_gauge = "#00ffcc" # Еко
            elif val_to_show <= 8.0: color_gauge = "#00f2fe" # Нормален
            elif val_to_show <= 11.0: color_gauge = "#ffa500" # Висок
            else: color_gauge = "#ff4b4b" # Екстремен

            lbl_gauge = "ФИНАЛЕН РАЗХОД" if is_final_status else "ТЕКУЩ РАЗХОД"
            sub_lbl_gauge = "за целия пробег" if is_final_status else "изчислен от старта"

            # Стилна 3D Линия на Маршрута (Timeline пробег)
            km_progress_pct = 100 if is_final_status else min(100, max(15, (dist / 1000 * 100))) if dist > 0 else 0
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; box-shadow: 5px 5px 15px rgba(0,0,0,0.4); margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <span style="font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;">📍 СЛЕДЕНЕ НА ПРОБЕГА</span>
                    {"<span style='background:rgba(255,75,75,0.15); color:#ff4b4b; font-size:10px; padding:2px 8px; border-radius:10px; font-weight:bold;'>🔒 ЗАКЛЮЧЕН</span>" if is_trip_finished else ""}
                </div>
                <div style="position: relative; height: 4px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 25px 0 15px 0;">
                    <div style="position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;"></div>
                    <div style="position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;">S</div>
                    {"<div style='position: absolute; right: 0; top: -8px; background: #1c1c1c; border: 2px solid #ff4b4b; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>F</div>" if is_trip_finished else f"<div style='position: absolute; left: calc({km_progress_pct}% - 10px); top: -12px; font-size: 16px;'>🚗</div>"}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <div><span style="color: #666;">Старт:</span> <b style="color: white;">{s_km:.0f} км</b></div>
                    {f"<div><span style='color: #666;'>Общо изминати:</span> <b style='color: #00f2fe;'>{dist:.0f} км</b></div>" if dist > 0 else ""}
                    <div><span style="color: #666;">Текущи:</span> <b style="color: white;">{e_km if e_km > 0 else "—":.0f} км</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Две колони за 3D Спидометъра и Горивната Капсула
            col_dash1, col_dash2 = st.columns(2)
            
            with col_dash1:
                # Кръгов виртуален 3D Ограничител/Gauge за средния разход
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 15px; border-radius: 16px; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 4px 4px 12px rgba(0,0,0,0.3);">
                    <small style="color: #888; font-weight: bold; font-size: 10px; letter-spacing: 0.5px;">{lbl_gauge}</small>
                    <div style="margin: 10px 0; width: 85px; height: 85px; border-radius: 50%; border: 4px dashed {color_gauge}; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: inset 0 0 10px rgba(0,0,0,0.5);">
                        <h2 style="margin: 0; color: white; font-size: 22px; font-weight: 900;">{val_to_show:.1f}</h2>
                        <small style="color: #666; font-size: 9px; font-weight: bold; margin-top: -2px;">л/100км</small>
                    </div>
                    <small style="color: #555; font-size: 10px;">{sub_lbl_gauge}</small>
                </div>
                """, unsafe_allow_html=True)
                
            with col_dash2:
                # Модерна Хоризонтална Горивна Капсула (Резервоар)
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 15px; border-radius: 16px; height: 160px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 4px 4px 12px rgba(0,0,0,0.3);">
                    <div>
                        <small style="color: #ffa500; font-weight: bold; font-size: 10px; letter-spacing: 0.5px;">💧 ИЗРАЗХОДВАНО ГОРИВО</small>
                        <h3 style="color: white; margin: 8px 0 0 0; font-size: 26px; font-weight: 800;">{total_liters_calculated:.1f} <span style="font-size: 14px; color: #666; font-weight: normal;">литра</span></h3>
                    </div>
                    <div>
                        <small style="color: #888; font-weight: bold; font-size: 10px; letter-spacing: 0.5px;">💰 ОБЩА ФИНАНСОВА СТОЙНОСТ</small>
                        <h4 style="color: #ffa500; margin: 2px 0 0 0; font-size: 18px; font-weight: 700;">{auto_fuel_money:.2f} <span style="font-size: 11px; color: #666; font-weight: normal;">EUR</span></h4>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
# === КРАЙ НА ЧАСТ 6 ===

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
            except: current_start, current_end = datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)
            
            edit_range = st.date_input("Изберете нови дати:", value=[current_start, current_end], key="edit_dates_cal")
            
            if st.button("💾 Обнови", use_container_width=True, type="primary", disabled=is_trip_finished):
                sk_val = float(new_sk) if new_sk is not None else 0.0
                mf_val = float(new_mf) if new_mf is not None else 0.0
                
                if isinstance(edit_range, (list, tuple)) and len(edit_range) > 0:
                    s_d_str = edit_range[0].strftime("%d.%m.%Y")
                    e_d_str = edit_range[1].strftime("%d.%m.%Y") if len(edit_range) > 1 else s_d_str
                elif hasattr(edit_range, "strftime"):
                    s_d_str = edit_range.strftime("%d.%m.%Y")
                    e_d_str = s_d_str
                else: s_d_str, e_d_str = st_date, en_date
                    
                if has_cash_expense and manual_cash_amt and manual_cash_amt > 0:
                    add_expense(trip_id, manual_cash_amt, "Транспорт", f"[ПРОПУСНАТО ГОРИВО] Добавени {mf_val:.1f} литра", False, 0.0, 0.0)

                save_trip_settings(trip_id, str(v_car), "Да", sk_val, e_km, mf_val, s_d_str, e_d_str)
                st.session_state["form_version"] += 1; st.rerun()

        @st.dialog("🏁 Край на пътуването")
        def finish_trip_modal():
            st.write("🏁 Въведете финални данни за приключване на почивката:")
            end_km_input = st.number_input("Финални километри от таблото (км):", value=None if e_km == 0.0 else e_km, placeholder="Въведете краен пробег...", step=1.0)
            st.warning("⚠️ Внимание: Това действие ще заключи калкулациите за гориво!")
            if st.button("🔒 ЗАКЛЮЧИ И ПРИКЛЮЧИ", use_container_width=True, type="primary"):
                if end_km_input and end_km_input > s_km:
                    save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date)
                    st.session_state["form_version"] += 1; st.rerun()
                else: st.error(f"Крайните километри трябва да са по-големи от началните ({s_km:.0f} км)!")

        if car_trip == "Да":
            col_manage1, col_manage2 = st.columns(2)
            with col_manage1:
                btn_lbl = "🔒 Заключени настройки" if is_trip_finished else "⚙️ Настройки превозно средство"
                if st.button(btn_lbl, use_container_width=True, disabled=is_trip_finished): edit_car_modal()
            with col_manage2:
                if is_trip_finished: st.button("🏁 Пътуването е приключено 🔒", use_container_width=True, disabled=True)
                else:
                    if st.button("🏁 Край на пътуването", use_container_width=True): finish_trip_modal()
        else:
            if st.button("🚗 Добави автомобил към пътуването", use_container_width=True): edit_car_modal()

        st.markdown("---"); col_st1, col_st2 = st.columns(2)
        with col_st1: st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center; margin-bottom: 12px;'><small style='color:#aaa; font-weight:bold;'>🏨 ДЕПОЗИТ</small><h2 style='color:#ff4b4b; margin:5px 0;'>{depozit_hotel:.2f} EUR</h2></div>", unsafe_allow_html=True)
        with col_st2: st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center;'><small style='color:#aaa; font-weight:bold;'>💰 НА МЯСТО</small><h2 style='color:#00f2fe; margin:5px 0;'>{total_on_site:.2f} EUR</h2></div>", unsafe_allow_html=True)
# === КРАЙ НА ЧАСТ 7 ===
        if not df_trip.empty:
            st.markdown("---"); st.subheader("📋 Хронология на плащанията")
            try:
                df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                for idx in reversed(df_all[df_all["trip_id"] == trip_id].index.tolist()):
                    r = df_all.loc[idx]; l_txt = f" | ⛽ {r['liters']:.1f} л" if float(r.get("liters", 0)) > 0 else ""
                    col_rec, col_del = st.columns([0.88, 0.12])
                    with col_rec: st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); height: 75px;"><span style="font-size:16px;">{get_emoji(r["category"])}</span> <b>{r["category"]}</b> — <span style="color:#ff4b4b; font-weight:bold;">{r["amount"]:.2f} EUR</span><br><small style="color:#aaa;">📅 {r["date"]} — {r["description"]}{l_txt}</small></div>', unsafe_allow_html=True)
                    with col_del:
                        if st.button("❌", key=f"dl_{idx}", use_container_width=True):
                            st.session_state["delete_idx"] = idx
                            confirm_delete_dialog()
            except: pass

        st.markdown("---")
        if st.button("📸 Снимки и спомени", use_container_width=True): st.session_state["view_photos"] = True; st.rerun()
        st.markdown("---")
        
        avg_con_txt = f"{(total_liters_calculated / dist * 100):.1f} л / 100 км" if dist > 0 else (f"{progressive_avg_con:.1f} л / 100 км" if has_progressive_data else "Няма данни")
        grand_total = depozit_hotel + total_on_site
        date_pdf_txt = f" | <b>Период:</b> {st_date} - {en_date}" if st_date and st_date != "nan" else ""
        
        pdf_html = f"<html><head><meta charset='utf-8'><style>body{{font-family:sans-serif;padding:30px;color:#333;}}h2{{color:#222;border-bottom:2px solid #00f2fe;padding-bottom:8px;margin-bottom:15px;}}h3{{color:#4facfe;margin-top:20px;border-bottom:1px solid #eee;padding-bottom:5px;}}table{{width:100%;border-collapse:collapse;margin-top:15px;}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd;}}th{{background:#f5f5f5;}}.fuel-highlight{{color:#ff1493;font-weight:bold;}}.badge-km{{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:12px;color:#555;font-weight:bold;}}</style></head><body><h2>ОТЧЕТ: {trip_id.upper().replace('_', ' ')}</h2><p style='font-size:15px;'><b>Депозит:</b> {depozit_hotel:.2f} EUR | <b>На място:</b> {total_on_site:.2f} EUR{date_pdf_txt}</p><p style='font-size:18px; color:#ff4b4b; background:#fff5f5; padding:10px; border-left:4px solid #ff4b4b; margin-top:10px;'><b>💰 ОБЩА СУМА НА ПОЧИВКАТА: {grand_total:.2f} EUR</b></p><h3>🚗 Кола:</h3><ul><li><b>Начални:</b> {s_km:.0f} км | <b>Крайни:</b> {e_km:.0f} км</li><li><b>Гориво:</b> {total_liters_calculated:.1f} л | <b>Стойност:</b> {auto_fuel_money:.2f} EUR</li><li><b>Среден разход на почивката:</b> <span style='color:#00f2fe;font-weight:bold;'>{avg_con_txt}</span></li></ul><h3>📋 Разходи:</h3><table><tr><th>Дата и час</th><th>Описание</th><th>Километраж</th><th>Сума</th><th>Категория</th></tr>"
        
        for _, row in df_trip.iterrows():
            desc_val = str(row['description'])
            km_val = float(row.get('current_km', 0.0))
            km_td = f"<span class='badge-km'>{km_val:.0f} км</span>" if km_val > 0 else "<span style='color:#ccc;'>—</span>"
            
            if "Моментен разход:" in desc_val:
                parts = desc_val.split("Моментен разход:")
                before = parts[0]
                after = parts[1] if len(parts) > 1 else ""
                desc_val = f"{before} <span class='fuel-highlight'>Моментен разход:{after}</span>"
            
            pdf_html += f"<tr><td>{row['date']}</td><td>{desc_val}</td><td>{km_td}</td><td>{row['amount']:.2f} EUR</td><td>{row['category']}</td></tr>"
            
        pdf_html += f"<tr><td colspan='3' style='text-align:right; font-weight:bold;'>Общо:</td><td colspan='2' style='font-weight:bold; color:#ff4b4b;'>{grand_total:.2f} EUR</td></tr></table></body></html>"
        
        b64_pdf = base64.b64encode(pdf_html.encode('utf-8')).decode('utf-8')
        st.markdown(f'<a href="data:text/html;base64,{b64_pdf}" download="Otchet_{trip_id}_2026.html" style="text-decoration:none;"><button style="width:100%; background:linear-gradient(135deg, #00f2fe, #4facfe); color:white; border:none; padding:12px; font-weight:bold; border-radius:10px; cursor:pointer; box-shadow:0px 4px 10px rgba(0,242,254,0.3);">📄 СВАЛИ ПЪЛЕН ОТЧЕТ (PDF/HTML)</button></a>', unsafe_allow_html=True)
        st.markdown("---")
        
        # Премахнат стария чекбокс, бутонът директно извиква новия стабилен диалог
        if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True):
            confirm_delete_trip_dialog()
# === КРАЙ НА КОДА ===
