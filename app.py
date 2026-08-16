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
    
    # 🌟 ЕТО ТУК ЗАЛЕПВАШ НОВИЯ РЕД:
    is_trip_finished = (e_km > 0)

   

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

    # === НАЧАЛО НА ЧАСТ 5 ===
    @st.dialog("⛽ Добавяне на гориво")
    def fuel_modal(amount, category, description, is_deposit):
        st.markdown(f"### 📍 Детайли за зареждането")
        st.write(f"Сума: **{amount:.2f} EUR**")
        st.write("---")
        
        liters_input = st.number_input("Количество гориво (литри):", min_value=0.1, step=0.1, format="%.1f")
        
        last_km = float(s_km) if s_km else 0.0
        if e_km > 0:
            last_km = float(e_km)
            
        km_input = st.number_input(
            f"Текущ километраж на колата (трябва да е над {last_km:.0f} км):",
            min_value=float(last_km),
            value=float(last_km),
            step=1.0
        )
        
        st.write("")
        if st.button("💾 ЗАПИШИ СЕКРЕТНО", use_container_width=True, type="primary"):
            if km_input <= s_km:
                st.error(f"Километражът трябва да е по-голям от началния ({s_km:.0f} км)!")
                return
                
            final_desc = f"{description} | ⛽ {liters_input:.1f} л"
            try:
                df_set = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
                df_set.loc[df_set["trip_id"] == trip_id, "end_km"] = float(km_input)
                df_set.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
                
                add_expense(trip_id, amount, category, final_desc, is_deposit, float(liters_input), float(km_input))
                st.session_state["form_version"] += 1
                st.rerun()
            except Exception as e:
                st.error("Възникна грешка при запис.")

    col_v1, col_v2 = st.columns([0.35, 0.65])
    with col_v1:
        s_input = st.number_input("Сума (EUR):", min_value=0.01, step=0.01, format="%.2f", key=f"s_in_{st.session_state['form_version']}")
    with col_v2:
        o_input = st.text_input("Описание на разхода:", placeholder="Напр. Вечеря, Хотел, Гориво...", key=f"o_in_{st.session_state['form_version']}")
# === КРАЙ НА ЧАСТ 5 ===

   
    # === НАЧАЛО НА ЧАСТ 6 (ПОЛОВИНА 1) ===
    if not is_trip_finished:
        st.markdown("<p style='font-size:12px; color:#888; margin-bottom:5px; font-weight:bold;'>БЪРЗО ДОБАВЯНЕ В КАТЕГОРИЯ:</p>", unsafe_allow_html=True)
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
                            if add_expense(trip_id, s_input, kat, desc, is_d): 
                                st.session_state["form_version"] += 1
                                st.rerun()
                            
        st.markdown("### 📊 Анализ на разходите")
        stat_grid = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
            b_c = "rgba(255,75,75,0.4)" if pct > 40 else "rgba(255,165,0,0.4)" if pct > 20 else "rgba(0,242,254,0.3)" if pct > 0 else "rgba(255,255,255,0.08)"
            b_g = "rgba(255,75,75,0.2)" if pct > 40 else "rgba(255,165,0,0.2)" if pct > 20 else "rgba(0,242,254,0.15)" if pct > 0 else "rgba(255,255,255,0.1)"
            b_t = "#ff4b4b" if pct > 40 else "#ffa500" if pct > 20 else "#00f2fe" if pct > 0 else "#aaa"
            with stat_grid[idx % 2]:
                st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); border: 1px solid {b_c}; padding: 12px 15px; border-radius: 14px; box-shadow: 3px 3px 10px rgba(0,0,0,0.3); margin-bottom: 12px; height: 120px; display: flex; flex-direction: column; justify-content: space-between;"><div style="display: flex; justify-content: space-between; align-items: center;"><span>{get_emoji(kat)} {kat}</span><span style="background:{b_g}; color:{b_t}; font-size:11px; padding:2px 7px; border-radius:20px; font-weight:bold;">{pct:.1f}%</span></div><h3 style="margin:0; color:white; font-size:20px; font-weight:800;">{s_value:.2f} <span style="font-size:11px; color:#aaa;">EUR</span></h3><div style="background: rgba(255,255,255,0.05); width: 100%; height: 6px; border-radius: 10px; overflow: hidden;"><div style="background: {b_t}; width: {pct}%; height: 100%; border-radius: 10px;"></div></div></div>', unsafe_allow_html=True)
    # === НАЧАЛО НА ЧАСТ 6 (ПОЛОВИНА 2) ===
        if car_trip == "Да":
            st.markdown("#### ⛽ Автомобилно табло")
            
            val_to_show = 0.0
            is_final_status = False
            if dist > 0:
                val_to_show = (total_liters_calculated / dist * 100) if total_liters_calculated > 0 else 0.0
                is_final_status = True
            elif has_progressive_data:
                val_to_show = progressive_avg_con

            if val_to_show == 0.0: color_gauge = "#666"
            elif val_to_show <= 5.5: color_gauge = "#00ffcc"
            elif val_to_show <= 8.0: color_gauge = "#00f2fe"
            elif val_to_show <= 11.0: color_gauge = "#ffa500"
            else: color_gauge = "#ff4b4b"

            lbl_gauge = "ФИНАЛЕН РАЗХОД" if is_final_status else "ТЕКУЩ РАЗХОД"
            sub_lbl_gauge = "за целия пробег" if is_final_status else "изчислен от старта"

            km_progress_pct = 100 if is_final_status else min(100, max(0, (dist / 1000 * 100))) if dist > 0 else 0
            
            car_left_css = "left: 0px;" if km_progress_pct == 0 else f"left: calc({km_progress_pct}% - 10px);"
            lock_lbl_html = f"<span style='background:rgba(255,75,75,0.15); color:#ff4b4b; font-size:10px; padding:2px 8px; border-radius:10px; font-weight:bold;'>🔒 ЗАКЛЮЧЕН</span>" if is_trip_finished else ""
            finish_icon_html = f"<div style='position: absolute; right: 0; top: -8px; background: #1c1c1c; border: 2px solid #ff4b4b; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>F</div>" if is_trip_finished else f"<div style='position: absolute; {car_left_css} top: -12px; font-size: 16px;'>🚗</div>"
            
            start_km_txt = f"{s_km:.0f} км"
            current_km_txt = f"{e_km:.0f} км" if e_km > 0 else "—"
            dist_km_txt = f"{dist:.0f} км" if dist > 0 else "0 км"
            
            html_probel_box = (
                f"<div style='background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; box-shadow: 5px 5px 15px rgba(0,0,0,0.4); margin-bottom: 20px; text-align: center;'>"
                f"<div style='display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 5px; position: relative;'>"
                f"<span style='font-size: 11px; font-weight: bold; color: #888; letter-spacing: 1px;'>📍 СЛЕДЕНЕ НА ПРОБЕГА</span>"
                f"{lock_lbl_html}"
                f"</div>"
                f"<div style='position: relative; height: 4px; background: rgba(255,255,255,0.1); border-radius: 10px; margin: 25px 15px 15px 15px;'>"
                f"<div style='position: absolute; left: 0; top: 0; height: 100%; width: {km_progress_pct}%; background: linear-gradient(90deg, #00f2fe, #4facfe); border-radius: 10px;'></div>"
                f"<div style='position: absolute; left: 0; top: -8px; background: #1c1c1c; border: 2px solid #00f2fe; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; color: white; font-weight: bold;'>S</div>"
                f"{finish_icon_html}"
                f"</div>"
                f"<div style='display: flex; justify-content: space-between; font-size: 13px; padding: 0 10px; gap: 10px;'>"
                f"<div style='flex: 1; text-align: left;'><span style='color: #666; display: block; font-size: 11px;'>Старт</span><b style='color: white; font-size: 14px;'>{start_km_txt}</b></div>"
                f"<div style='flex: 1; text-align: center;'><span style='color: #666; display: block; font-size: 11px;'>Изминати</span><b style='color: #00f2fe; font-size: 14px;'>{dist_km_txt}</b></div>"
                f"<div style='flex: 1; text-align: right;'><span style='color: #666; display: block; font-size: 11px;'>Текущи</span><b style='color: white; font-size: 14px;'>{current_km_txt}</b></div>"
                f"</div>"
                f"</div>"
            )
            st.markdown(html_probel_box, unsafe_allow_html=True)

            html_dashboard_boxes = (
                f"<div style='display: flex; flex-wrap: wrap; gap: 15px; width: 100%;'>"
                f"<div style='flex: 1; min-width: 280px; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 20px; border-radius: 16px; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 4px 4px 12px rgba(0,0,0,0.3);'>"
                f"<div style='color: #888; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 15px; margin-top: 0;'>{lbl_gauge}</div>"
                f"<div style='width: 110px; height: 110px; border-radius: 50%; border: 4px dashed {color_gauge}; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: inset 0 0 15px rgba(0,0,0,0.6); margin-bottom: 15px; box-sizing: border-box; padding: 0;'>"
                f"<div style='color: white; font-size: 28px; font-weight: 900; margin: 0; padding: 0; line-height: 1.1; text-align: center;'>{val_to_show:.1f}</div>"
                f"<div style='color: #666; font-size: 10px; font-weight: bold; margin-top: 2px; padding: 0; text-align: center;'>л/100км</div>"
                f"</div>"
                f"<div style='color: #666; font-size: 11px; margin: 0;'>{sub_lbl_gauge}</div>"
                f"</div>"
                f"<div style='flex: 1; min-width: 280px; background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(255,255,255,0.08); padding: 25px 20px; border-radius: 16px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center; box-shadow: 4px 4px 12px rgba(0,0,0,0.3); box-sizing: border-box;'>"
                f"<div style='margin-bottom: 25px; width: 100%;'>"
                f"<div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin: 0 0 8px 0; text-align: center;'>💧 ИЗРАЗХОДВАНО ГОРИВО</div>"
                f"<div style='color: white; margin: 0; font-size: 28px; font-weight: 800; line-height: 1.2; text-align: center;'>{total_liters_calculated:.1f} <span style='font-size: 14px; color: #666; font-weight: normal;'>литра</span></div>"
                f"</div>"
                f"<div style='padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.06); width: 100%;'>"
                f"<div style='color: #ffa500; font-weight: bold; font-size: 11px; letter-spacing: 0.5px; margin: 0 0 8px 0; text-align: center;'>💰 ОБЩА ФИНАНСОВА СТОЙНОСТ</div>"
                f"<div style='color: white; margin: 0; font-size: 28px; font-weight: 800; line-height: 1.2; text-align: center;'>{auto_fuel_money:.2f} <span style='font-size: 14px; color: #666; font-weight: normal;'>EUR</span></div>"
                f"</div>"
                f"</div>"
                f"</div>"
                f"<br>"
            )
            st.markdown(html_dashboard_boxes, unsafe_allow_html=True)
    # === КРАЙ НА ЧАСТ 6 ===

    # === НАЧАЛО НА ЧАСТ 7 ===
    st.markdown("### 📜 История на разходите")
    if not df_trip.empty:
        for idx, row in current_expenses.sort_values(by="id", ascending=False).iterrows():
            with st.expander(f"{get_emoji(row['category'])} {row['amount']:.2f} EUR — {row['category']}"):
                st.write(f"📝 **Описание:** {row['description']}")
                st.write(f"📅 **Дата:** {row['timestamp']}")
                if not is_trip_finished:
                    if st.button("🗑️ Изтрий разхода", key=f"del_{row['id']}", use_container_width=True):
                        try:
                            df_exp = pd.read_csv(EXPENSES_FILE, encoding="utf-8")
                            df_exp = df_exp[df_exp["id"] != row["id"]]
                            df_exp.to_csv(EXPENSES_FILE, index=False, encoding="utf-8")
                            st.session_state["form_version"] += 1
                            st.rerun()
                        except Exception:
                            st.error("Възникна грешка при изтриване.")
    else:
        st.info("Все още няма добавени разходи за това пътуване.")
    # === КРАЙ НА ЧАСТ 7 ===
    # === НАЧАЛО НА ЧАСТ 8 ===
    st.write("---")
    if not is_trip_finished:
        if st.button("🏁 ПРИКЛЮЧИ ПЪТУВАНЕТО (АРХИВИРАЙ)", use_container_width=True, type="primary"):
            try:
                df_set = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
                df_set.loc[df_set["trip_id"] == trip_id, "status"] = "finished"
                df_set.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
                st.success("Пътуването беше успешно приключено и архивирано!")
                st.rerun()
            except Exception:
                st.error("Грешка при приключване на пътуването.")
    else:
        st.success("🔒 Това пътуване е приключено и данните са заключени за редакция.")
    # === КРАЙ НА ЧАСТ 8 ===
