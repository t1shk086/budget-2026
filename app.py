import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64

st.set_page_config(page_title="PixelApp Travel", page_icon="🐾", layout="centered")

DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"
KATEGORII = ["Нощувки", "Транспорт", "Храна/Ресторанти", "Пазаруване/Подаръци", "Забавления/Атракции", "Депозит/Резервация"]

def get_emoji(cat):
    emojis = {"Нощувки": "🏨", "Транспорт": "🚗", "Храна/Ресторанти": "🍔", "Пазаруване/Подаръци": "🛍️", "Забавления/Атракции": "🎟️", "Депозит/Резервация": "💳"}
    return emojis.get(cat, "💰")

def get_trip_settings(t_id):
    if os.path.exists(SETTINGS_FILE):
        try:
            df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
            res = df[df["trip_id"] == t_id]
            if not res.empty: 
                return res.iloc[0].to_dict()
        except: pass
    return {"trip_id": t_id, "car_trip": "Не", "track_fuel": "Не", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0, "start_date": "", "end_date": ""}

def get_trip_data(t_id):
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding="utf-8")
            if "current_km" not in df.columns: df["current_km"] = 0.0
            return df[df["trip_id"] == t_id].copy()
        except: pass
    return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters", "current_km"])

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8") if os.path.exists(SETTINGS_FILE) else pd.DataFrame(columns=["trip_id", "car_trip", "track_fuel", "start_km", "end_km", "manual_fuel", "start_date", "end_date"])
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
        st.cache_data.clear()
    except: pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8") if os.path.exists(DATA_FILE) else pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters", "current_km"])
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False

def delete_expense_direct(idx_to_del):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        df = df.drop(idx_to_del)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8")
        st.cache_data.clear()
        return True
    except: return False

# --- ГЛОБАЛНИ ДИАЛОЗИ ЗА ИЗБЕГВАНЕ НА ЗАБИВАНЕ ПРИ ТРИЕНЕ ---
@st.dialog("➕ Създаване на ново приключение")
def create_trip_modal():
    txt = st.text_input("Име на дестинацията:").strip()
    d_range = st.date_input("Изберете дати за почивката:", value=[datetime.date.today(), datetime.date.today()])
    st.write("---")
    viber_car = st.radio("🚗 Пътувате ли със собствен автомобил?", ["Не, с друг транспорт", "Да, със собствен автомобил"], index=0)
    new_skm = 0.0
    if viber_car == "Да, със собствен автомобил":
        new_skm = st.number_input("Начални километри (км):", value=None, placeholder="Въведете км на тръгване...", step=1.0)
        
    if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True, type="primary") and txt:
        if isinstance(d_range, (list, tuple)) and len(d_range) > 0:
            s_d_str = d_range[0].strftime("%d.%m.%Y") if hasattr(d_range[0], "strftime") else ""
            e_d_str = d_range[-1].strftime("%d.%m.%Y") if len(d_range) > 1 and hasattr(d_range[-1], "strftime") else s_d_str
        elif hasattr(d_range, "strftime"):
            s_d_str = d_range.strftime("%d.%m.%Y")
            e_d_str = s_d_str
        else: s_d_str, e_d_str = "", ""
        sk = float(new_skm) if new_skm is not None else 0.0
        target_id = txt.replace(" ", "_")
        save_trip_settings(target_id, "Да" if viber_car == "Да, със собствен автомобил" else "Не", "Да" if viber_car == "Да, със собствен автомобил" else "Не", sk, 0.0, 0.0, s_d_str, e_d_str)
        st.session_state["current_trip"] = target_id
        st.rerun()

@st.dialog("⛽ Зареждане на гориво")
def fuel_modal(trip_id, amount, category, description, is_dep, s_km, car_trip, t_fuel, e_km, m_fuel, st_date, en_date):
    st.write(f"Зареждане за **{amount:.2f} EUR**.")
    col_m1, col_m2 = st.columns(2)
    with col_m1: liters = st.number_input("Литри (л):", value=None, placeholder="Литри...", step=0.1)
    with col_m2: mom_km = st.number_input("Моментни км:", value=None, placeholder="Километри...", step=1.0)
    if liters and mom_km and s_km > 0 and mom_km > s_km:
        st.info(f"📊 Текущ разход: **{(liters / (mom_km - s_km) * 100):.1f} л / 100 км**")
    if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
        lit, k_val = float(liters) if liters is not None else 0.0, float(mom_km) if mom_km is not None else 0.0
        if add_expense(trip_id, amount, category, f"[ГОРИВО] {description}", is_dep, lit, k_val):
            if k_val > 0 and (e_km == 0 or k_val > e_km): save_trip_settings(trip_id, car_trip, t_fuel, s_km, k_val, m_fuel, st_date, en_date)
            st.session_state["form_version"] += 1
            st.rerun()

@st.dialog("⚙️ Настройки на превозно средство")
def edit_car_modal(trip_id, car_trip, t_fuel, s_km, e_km, m_fuel, st_date, en_date):
    v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=0 if car_trip == "Не" else 1)
    new_sk = st.number_input("Начални км:", value=None if s_km == 0.0 else s_km)
    new_ek = st.number_input("Финални (Крайни) км:", value=None if e_km == 0.0 else e_km)
    st.markdown("---")
    new_mf = st.number_input("Допълнителни ръчни литри (л):", value=None if m_fuel == 0.0 else m_fuel)
    has_money_cost = st.radio("Има ли паричен разход за това?", ["Не", "Да"], index=0)
    manual_cash = 0.0
    if has_money_cost == "Да": manual_cash = st.number_input("Цена (EUR):", value=None)
    if st.button("💾 Запази промените", use_container_width=True, type="primary"):
        sk_val, ek_val, mf_val = float(new_sk) if new_sk is not None else 0.0, float(new_ek) if new_ek is not None else 0.0, float(new_mf) if new_mf is not None else 0.0
        if mf_val > 0 and has_money_cost == "Да" and manual_cash and manual_cash > 0:
            add_expense(trip_id, manual_cash, "Транспорт", f"[РЪЧНО ГОРИВО]", False, 0.0, ek_val if ek_val > 0 else e_km)
        save_trip_settings(trip_id, str(v_car), t_fuel, sk_val, ek_val, mf_val, st_date, en_date)
        st.session_state["form_version"] += 1
        st.rerun()

@st.dialog("🗑️ Потвърждение за изтриване")
def delete_expense_modal(idx_to_del):
    st.warning("⚠️ Изтриване на избрания разход?")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button("✅ ДА", use_container_width=True, type="primary"):
            if delete_expense_direct(idx_to_del):
                st.session_state["form_version"] += 1
                st.rerun()
    with col_m2:
        if st.button("❌ НЕ", use_container_width=True): st.rerun()

@st.dialog("🏁 Приключване на пътуването")
def finish_modal(trip_id, car_trip, s_km, e_km, m_fuel, st_date, en_date):
    f_km = st.number_input("Финални километри (км):", value=None if e_km == 0.0 else e_km)
    if st.button("🔒 ПОТВЪРДИ И ЗАКЛЮЧИ", use_container_width=True, type="primary"):
        f_val = float(f_km) if f_km is not None else e_km
        save_trip_settings(trip_id, car_trip, "Приключило", s_km, f_val, m_fuel, st_date, en_date)
        st.rerun()

def confirm_delete_trip_callback(t_id, p_snimki):
    try:
        if os.path.exists(DATA_FILE):
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            df_all[df_all["trip_id"] != t_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
        if os.path.exists(SETTINGS_FILE):
            df_set = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
            df_set[df_set["trip_id"] != t_id].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
        if os.path.exists(p_snimki):
            for p in glob.glob(os.path.join(p_snimki, "*")):
                try: os.remove(p)
                except: pass
            try: os.rmdir(p_snimki)
            except: pass
    except: pass
    st.session_state["current_trip"] = None
    st.cache_data.clear()

@st.dialog("🚨 ИЗТРИВАНЕ НА ЦЯЛОТО ПЪТУВАНЕ")
def delete_entire_trip_modal(trip_id, papka_snimki):
    st.error("⚠️ ВНИМАНИЕ! Изтриване на всичко завинаги?")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.button(
            "🚨 ДА, ИЗТРИЙ", 
            use_container_width=True, 
            type="primary", 
            key="execute_delete_trip_final",
            on_click=confirm_delete_trip_callback,
            args=(trip_id, papka_snimki)
        )
    with col_t2:
        if st.button("❌ ОТКАЗ", use_container_width=True, key="cancel_trip_btn"): 
            st.rerun()


if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0
if "view_photos" not in st.session_state: st.session_state["view_photos"] = False

st.markdown("""
<style>
    div.stButton > button {
        background: linear-gradient(135deg, #262730, #1c1d24) !important;
        color: #f0f2f6 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        box-shadow: 0px 3px 6px rgba(0, 0, 0, 0.3) !important;
    }
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #421c1c, #2d1313) !important;
        border: 1px solid rgba(255, 75, 75, 0.15) !important;
        color: #ff8c8c !important;
    }
</style>
""", unsafe_allow_html=True)

if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center; margin-bottom: 5px;'><h1 style='font-family: \"Segoe UI\", sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🐾 PixelApp</h1><p style='color: #ffd700; font-weight: 500;'>Travel Manager</p></div>", unsafe_allow_html=True)
    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    opts = ["-- Изберете почивка --"] + [t.replace("_", " ") for t in existing]
    choice = st.selectbox("Изберете Ваша почивка:", opts)
    if choice != "-- Изберете почивка --":
        if st.button("📂 ОТВОРИ ПОЧИВКАТА", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.rerun()
    st.markdown("<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>", unsafe_allow_html=True)
    if st.button("➕ Ново пътуване", use_container_width=True): create_trip_modal()
else:
    trip_id = st.session_state["current_trip"]
    papka_snimki = f"snimki_{trip_id}_2026"
    c_s = get_trip_settings(trip_id)
    
    car_trip = str(c_s.get("car_trip", "Не"))
    t_fuel = str(c_s.get("track_fuel", "Не"))
    s_km = float(c_s.get("start_km", 0.0)) if pd.notna(c_s.get("start_km")) else 0.0
    e_km = float(c_s.get("end_km", 0.0)) if pd.notna(c_s.get("end_km")) else 0.0
    m_fuel = float(c_s.get("manual_fuel", 0.0)) if pd.notna(c_s.get("manual_fuel")) else 0.0
    st_date, en_date = str(c_s.get("start_date", "")), str(c_s.get("end_date", ""))

    date_html = f"<p style='font-size: 14px; color: #888;'>{st_date} - {en_date}</p>" if st_date and st_date != "nan" else ""
    st.markdown(f"<div style='text-align: center;'><h2 style='font-family: \"Segoe UI\", sans-serif; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🌴 Дестинация: {trip_id.replace('_', ' ')}</h2>{date_html}</div>", unsafe_allow_html=True)
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
    is_finished = (t_fuel == "Приключило")

    if st.session_state["view_photos"]:
        if st.button("⬅️ НАЗАД КЪМ РАЗХОДИТЕ", use_container_width=True): st.session_state["view_photos"] = False; st.rerun()
        if not os.path.exists(papka_snimki): os.makedirs(papka_snimki)
        up = st.file_uploader("Снимки:", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
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
                    if st.button("🗑️ Изтрий", key=f"di_{idx}", use_container_width=True): os.remove(p); st.rerun()
    else:
        if st.button("⬅️ НАЗАД КЪМ ВСИЧКИ ПОЧИВКИ", use_container_width=True): st.session_state["current_trip"] = None; st.rerun()
        if is_finished: st.warning("🔒 Това пътуване е приключено.")
        else:
            v_id = st.session_state["form_version"]
            col1, col2 = st.columns(2)
            with col1: s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Сума...", format="%.2f", key=f"su_{v_id}")
            with col2: o_input = st.text_input("Описание", placeholder="Описание...", key=f"op_{v_id}")

            grid = st.columns(3)
            for i, kat in enumerate(KATEGORII):
                with grid[i % 3]:
                    if st.button(kat, use_container_width=True, key=f"bt_{i}"):
                        if s_input and s_input > 0:
                            desc = o_input.strip() if o_input else "Без описание"
                            is_d = (kat == "Депозит/Резервация")
                            if kat == "Транспорт" and any(k in desc.lower() for k in ["гориво", "зареждане", "бензин", "дизел"]): 
                                fuel_modal(trip_id, s_input, kat, desc, is_d, s_km, car_trip, t_fuel, e_km, m_fuel, st_date, en_date)
                            else:
                                if add_expense(trip_id, s_input, kat, desc, is_d): st.session_state["form_version"] += 1; st.rerun()

        st.markdown("### 📊 Анализ на разходите")
        stat_grid = st.columns(2)
        for idx, (kat, s_value) in enumerate(categories_totals.items()):
            pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
            b_c = "rgba(255,75,75,0.4)" if pct > 40 else "rgba(255,165,0,0.4)" if pct > 20 else "rgba(0,242,254,0.3)" if pct > 0 else "rgba(255,255,255,0.08)"
            b_t = "#ff4b4b" if pct > 40 else "#ffa500" if pct > 20 else "#00f2fe" if pct > 0 else "#aaa"
            with stat_grid[idx % 2]:
                st.markdown(f'<div style="background: rgba(255,255,255,0.02); border: 1px solid {b_c}; padding: 12px; border-radius: 14px; margin-bottom: 12px; height: 110px; display: flex; flex-direction: column; justify-content: space-between;"><div style="display: flex; justify-content: space-between;"><span>{get_emoji(kat)} {kat}</span><span style="color:{b_t}; font-weight:bold;">{pct:.1f}%</span></div><h3 style="margin:0; color:white; font-size:18px;">{s_value:.2f} EUR</h3></div>', unsafe_allow_html=True)

        st.markdown("#### ⛽ Бордов компютър")
        lbl_km = "🏁 Крайни километри:" if is_finished else "📍 Последно засечени км:"
        st.markdown(f'<div style="background: rgba(255,255,255,0.02); padding: 12px; border-radius: 10px; font-size: 14px; color: #ccc;">📍 Начални км: {s_km:.0f} км | {lbl_km} {e_km:.0f} км<br>💧 Общо гориво: {total_liters_calculated:.1f} л | Разход: {auto_fuel_money:.2f} EUR</div>', unsafe_allow_html=True)
        if dist > 0:
            avg_con = (total_liters_calculated / dist * 100) if total_liters_calculated > 0 else 0.0
            st.info(f"📊 Среден разход: **{avg_con:.1f} л / 100 км** (Пробег: {int(dist)} км)")
            
        if not is_finished:
            if st.button("⚙️ Настройки километри / период", use_container_width=True): edit_car_modal(trip_id, car_trip, t_fuel, s_km, e_km, m_fuel, st_date, en_date)

        st.markdown("---")
        col_st1, col_st2 = st.columns(2)
        with col_st1: st.markdown(f"<div style='background:rgba(255,255,255,0.03); padding:10px; border-radius:12px; text-align:center;'>🏨 ДЕПОЗИТ<h2 style='color:#ff4b4b; margin:0;'>{depozit_hotel:.2f} €</h2></div>", unsafe_allow_html=True)
        with col_st2: st.markdown(f"<div style='background:rgba(255,255,255,0.03); padding:10px; border-radius:12px; text-align:center;'>💰 НА МЯСТО<h2 style='color:#00f2fe; margin:0;'>{total_on_site:.2f} €</h2></div>", unsafe_allow_html=True)

        if not df_trip.empty:
            st.markdown("---"); st.subheader("📋 Хронология")
            try:
                df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                for idx in reversed(df_all[df_all["trip_id"] == trip_id].index.tolist()):
                    r = df_all.loc[idx]
                    col_rec, col_del = st.columns([0.85, 0.15], vertical_alignment="center")
                    with col_rec: st.markdown(f'<div style="background: rgba(255,255,255,0.02); padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); font-size:13px;">{get_emoji(r["category"])} <b>{r["category"]}</b> — <span style="color:#ff4b4b;">{r["amount"]:.2f} EUR</span><br><small style="color:#aaa;">📅 {r["date"]} - {r["description"]}</small></div>', unsafe_allow_html=True)
                    with col_del:
                        if st.button("❌", key=f"dl_{idx}", use_container_width=True, disabled=is_finished): delete_expense_modal(idx)
            except: pass

        st.markdown("---")
        if st.button("📸 Снимки и спомени", use_container_width=True):
            st.session_state["view_photos"] = True
            st.rerun()

        if not is_finished:
            if st.button("🏁 Приключи Пътуването", use_container_width=True):
                finish_modal(trip_id, car_trip, s_km, e_km, m_fuel, st_date, en_date)

        pdf_avg_con_txt = f"{(total_liters_calculated / dist * 100):.1f} л / 100 км" if dist > 0 else "0.0 л"
        pdf_html = f"<html><body><h2>ОТЧЕТ: {trip_id.upper()}</h2><p>Депозит: {depozit_hotel:.2f} EUR | На място: {total_on_site:.2f} EUR</p><p>Пробег: {dist:.0f} км | Среден разход: {pdf_avg_con_txt}</p></body></html>"
        b64_pdf = base64.b64encode(pdf_html.encode('utf-8')).decode('utf-8')
        st.markdown(f'<a href="data:text/html;base64,{b64_pdf}" download="Otchet_{trip_id}.html" style="text-decoration:none;"><button style="width:100%; background:linear-gradient(135deg, #00f2fe, #4facfe); color:white; border:none; padding:12px; font-weight:bold; border-radius:10px; cursor:pointer;">📄 СВАЛИ ПЪЛЕН ОТЧЕТ</button></a>', unsafe_allow_html=True)

        st.markdown("---")
                st.markdown("---")
        st.markdown("<b style='color:#ff4b4b;'>🚨 ЗОНА ЗА ИЗТРИВАНЕ</b>", unsafe_allow_html=True)
        
        suglasen_del = st.checkbox("Потвърждавам, че искам да изтрия това пътуване завинаги!", key=f"chk_del_{trip_id}")
        
        if suglasen_del:
            try:
                if os.path.exists(DATA_FILE):
                    df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                    df_all[df_all["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
                if os.path.exists(SETTINGS_FILE):
                    df_set = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
                    df_set[df_set["trip_id"] != trip_id].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
                if os.path.exists(papka_snimki):
                    for p in glob.glob(os.path.join(papka_snimki, "*")):
                        try: os.remove(p)
                        except: pass
                    try: os.rmdir(papka_snimki)
                    except: pass
                
                st.session_state["current_trip"] = None
                st.cache_data.clear()
                st.rerun()
            except:
                pass

