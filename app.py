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

# НОВА ФУНКЦИЯ: Светкавично изтриване без зацикляне
def delete_expense_direct(idx_to_del):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        df = df.drop(idx_to_del)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8")
        st.cache_data.clear()
        return True
    except: return False

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
            else:
                s_d_str, e_d_str = "", ""
            sk = float(new_skm) if new_skm is not None else 0.0
            target_id = txt.replace(" ", "_")
            save_trip_settings(target_id, "Да" if viber_car == "Да, със собствен автомобил" else "Не", "Да" if viber_car == "Да, със собствен автомобил" else "Не", sk, 0.0, 0.0, s_d_str, e_d_str)
            st.session_state["current_trip"] = target_id
            st.rerun()
            
    if st.button("➕ Ново пътуване", use_container_width=True):
        create_trip_modal()
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
        up = st.file_uploader("Добавете нови спомени:", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
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
        if is_finished:
            st.warning("🔒 Това пътуване е приключено и отчетът е заключен.")
        else:
            v_id = st.session_state["form_version"]
            col1, col2 = st.columns(2)
            with col1: s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Напишете сума...", format="%.2f", key=f"su_{v_id}")
            with col2: o_input = st.text_input("Описание", placeholder="Напишете описание...", key=f"op_{v_id}")

            @st.dialog("⛽ Зареждане на гориво")
            def fuel_modal(amount, category, description, is_dep):
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
                        st.session_state["form_version"] += 1; st.rerun()

            grid = st.columns(3)
            for i, kat in enumerate(KATEGORII):
                with grid[i % 3]:
                    if st.button(kat, use_container_width=True, key=f"bt_{i}"):
                        if s_input and s_input > 0:
                            desc = o_input.strip() if o_input else "Без описание"
                            is_d = (kat == "Депозит/Резервация")
                            if kat == "Транспорт" and any(k in desc.lower() for k in ["гориво", "зареждане", "бензин", "дизел"]): fuel_modal(s_input, kat, desc, is_d)
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
                st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); border: 1px solid {b_c}; padding: 12px 15px; border-radius: 14px; margin-bottom: 12px; height: 120px; display: flex; flex-direction: column; justify-content: space-between;"><div style="display: flex; justify-content: space-between; align-items: center;"><span>{get_emoji(kat)} {kat}</span><span style="background:{b_g}; color:{b_t}; font-size:11px; padding:2px 7px; border-radius:20px; font-weight:bold;">{pct:.1f}%</span></div><h3 style="margin:0; color:white; font-size:20px; font-weight:800;">{s_value:.2f} <span style="font-size:11px; color:#aaa;">EUR</span></h3><div style="background: rgba(255,255,255,0.05); width: 100%; height: 6px; border-radius: 10px; overflow: hidden;"><div style="background: {b_t}; width: {pct}%; height: 100%; border-radius: 10px;"></div></div></div>', unsafe_allow_html=True)

        st.markdown("#### ⛽ Бордов компютър")
        lbl_km = "🏁 <b>Крайни километри:</b>" if is_finished else "📍 <b>Последно засечени км:</b>"
        manual_fuel_html = f"<br>➕ <b>Ръчно добавено гориво:</b> {m_fuel:.1f} л" if m_fuel > 0 else ""
        st.markdown(f"""<div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px 18px; border-radius: 10px; margin-bottom: 15px; font-size: 14px; color: #ccc; line-height: 1.6;">📍 <b>Начални километри:</b> {s_km:.0f} км<br>{lbl_km} {e_km:.0f} км {"(Пробег: " + str(int(dist)) + " км)" if dist > 0 else ""}<br>💧 <b>Общо заредено:</b> {total_liters_sum:.1f} л{manual_fuel_html}<br>📊 <b>Финално количество гориво:</b> {total_liters_calculated:.1f} л</div>""", unsafe_allow_html=True)
        col_fuel1, col_fuel2 = st.columns(2)
        with col_fuel1: st.markdown(f'<div style="background: rgba(255, 165, 0, 0.05); border: 1px solid rgba(255, 165, 0, 0.2); padding: 15px; border-radius: 12px; text-align: center; height: 95px; display:flex; flex-direction:column; justify-content:center; margin-bottom: 12px;"><small style="color: #ffa500; font-weight: bold;">⛽ ОБЩО ЗА ГОРИВО</small><h3 style="color: white; margin: 5px 0;">{auto_fuel_money:.2f} <span style="font-size:14px; color:#aaa;">EUR</span></h3></div>', unsafe_allow_html=True)
        with col_fuel2:
            if dist > 0:
                avg_con = (total_liters_calculated / dist * 100) if total_liters_calculated > 0 else 0.0
                st.markdown(f'<div style="background: rgba(0, 242, 254, 0.05); border: 1px solid rgba(0, 242, 254, 0.2); padding: 15px; border-radius: 12px; text-align: center; height: 95px; display:flex; flex-direction:column; justify-content:center;"><small style="color: #00f2fe; font-weight: bold;">📊 СРЕДЕН РАЗХОД</small><h3 style="color: white; margin: 5px 0;">{avg_con:.1f} <span style="font-size:14px; color:#aaa;">л / 100 км</span></h3></div>', unsafe_allow_html=True)
            else: st.markdown('<div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; text-align: center; height: 95px; display: flex; align-items: center; justify-content: center;"><small style="color: #aaa;">Въведете моментни километри при горивото.</small></div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        @st.dialog("⚙️ Настройки на превозно средство и период")
        def edit_car_modal():
            v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=0 if car_trip == "Не" else 1)
            new_sk = st.number_input("Начални км:", value=None if s_km == 0.0 else s_km)
            new_ek = st.number_input("Финални (Крайни) км:", value=None if e_km == 0.0 else e_km)
            st.markdown("---")
            new_mf = st.number_input("Допълнителни ръчни литри (л):", value=None if m_fuel == 0.0 else m_fuel)
            has_money_cost = st.radio("Има ли паричен разход за това ръчно зареждане?", ["Не, само литри", "Да, добави и разход"], index=0)
            manual_cash = 0.0
            if has_money_cost == "Да, добави и разход": manual_cash = st.number_input("Цена на ръчното зареждане (EUR):", value=None)
            try:
                current_start = datetime.datetime.strptime(st_date, "%d.%m.%Y").date() if st_date and st_date != "nan" else datetime.date.today()
                current_end = datetime.datetime.strptime(en_date, "%d.%m.%Y").date() if en_date and en_date != "nan" else datetime.date.today()
            except: current_start, current_end = datetime.date.today(), datetime.date.today()
            st.markdown("---")
            edit_range = st.date_input("Дати на почивката:", value=[current_start, current_end])
            if st.button("💾 Запази промените", use_container_width=True, type="primary"):
                sk_val, ek_val, mf_val = float(new_sk) if new_sk is not None else 0.0, float(new_ek) if new_ek is not None else 0.0, float(new_mf) if new_mf is not None else 0.0
                if isinstance(edit_range, (list, tuple)) and len(edit_range) > 0:
                    s_d_str = edit_range.strftime("%d.%m.%Y") if hasattr(edit_range, "strftime") else ""
                    e_d_str = edit_range[-1].strftime("%d.%m.%Y") if len(edit_range) > 1 and hasattr(edit_range[-1], "strftime") else s_d_str
                elif hasattr(edit_range, "strftime"):
                    s_d_str = edit_range.strftime("%d.%m.%Y")
                    e_d_str = s_d_str
                else:
                    s_d_str, e_d_str = st_date, en_date
                if mf_val > 0 and has_money_cost == "Да, добави и разход" and manual_cash and manual_cash > 0:
                    add_expense(trip_id, manual_cash, "Транспорт", f"[РЪЧНО ГОРИВО] Добавено количество", False, 0.0, ek_val if ek_val > 0 else e_km)
                save_trip_settings(trip_id, str(v_car), t_fuel, sk_val, ek_val, mf_val, s_d_str, e_d_str)
                st.session_state["form_version"] += 1; st.rerun()

        if not is_finished:
            if st.button("⚙️ Настройки километри / период на пътуването", use_container_width=True): edit_car_modal()

        st.markdown("---"); col_st1, col_st2 = st.columns(2)
        with col_st1: st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center; margin-bottom: 12px;'><small style='color:#aaa; font-weight:bold;'>🏨 ДЕПОЗИТ</small><h2 style='color:#ff4b4b; margin:5px 0;'>{depozit_hotel:.2f} EUR</h2></div>", unsafe_allow_html=True)
        with col_st2: st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center;'><small style='color:#aaa; font-weight:bold;'>💰 НА МЯСТО</small><h2 style='color:#00f2fe; margin:5px 0;'>{total_on_site:.2f} EUR</h2></div>", unsafe_allow_html=True)

        @st.dialog("🗑️ Потвърждение за изтриване")
        def delete_expense_modal(idx_to_del):
            st.warning("⚠️ Сигурни ли сте, че искате да изтриете този разход?")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                if st.button("✅ ДА", use_container_width=True, type="primary"):
                    if delete_expense_direct(idx_to_del):
                        st.session_state["form_version"] += 1
                        st.rerun()
            with col_m2:
                if st.button("❌ НЕ", use_container_width=True): st.rerun()
            if not df_trip.empty:
            st.markdown("---"); st.subheader("📋 Хронология на плащанията")
            try:
                df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                for idx in reversed(df_all[df_all["trip_id"] == trip_id].index.tolist()):
                    r = df_all.loc[idx]; l_txt = f" | ⛽ {r['liters']:.1f} л" if float(r.get("liters", 0)) > 0 else ""
                    col_rec, col_del = st.columns([0.85, 0.15], vertical_alignment="center")
                    with col_rec: st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); min-height: 70px; display: flex; flex-direction: column; justify-content: center;"><div style="font-size:14px; color:white;"><span style="font-size:16px;">{get_emoji(r["category"])}</span> <b>{r["category"]}</b> — <span style="color:#ff4b4b; font-weight:bold;">{r["amount"]:.2f} EUR</span></div><div style="margin-top:4px;"><small style="color:#aaa;">📅 {r["date"]} — {r["description"]}{l_txt}</small></div></div>', unsafe_allow_html=True)
                    with col_del:
                        if st.button("❌", key=f"dl_{idx}", use_container_width=True, disabled=is_finished): delete_expense_modal(idx)
            except: pass

        st.markdown("---")
        if st.button("📸 Снимки и спомени от почивката", use_container_width=True): st.session_state["view_photos"] = True; st.rerun()
        st.markdown("---")
        
        @st.dialog("🏁 Приключване на пътуването")
        def finish_modal():
            st.write("Въведете финалните крайни километри, за да заключите отчета:")
            f_km = st.number_input("Финални километри (км):", value=None if e_km == 0.0 else e_km)
            if st.button("🔒 ПОТВЪРДИ И ЗАКЛЮЧИ", use_container_width=True, type="primary"):
                f_val = float(f_km) if f_km is not None else e_km
                save_trip_settings(trip_id, car_trip, "Приключило", s_km, f_val, m_fuel, st_date, en_date)
                st.rerun()

        if not is_finished:
            if st.button("🏁 Приключи Пътуването", use_container_width=True): finish_modal()
            st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)

        pdf_avg_con_txt = "0.0 л / 100 км"
        if dist > 0 and total_liters_calculated > 0: pdf_avg_con_txt = f"{(total_liters_calculated / dist * 100):.1f} л / 100 км"
        date_pdf_txt = f" | <b>Период:</b> {st_date} - {en_date}" if st_date and st_date != "nan" else ""
        pdf_html = f"<html><head><meta charset='utf-8'><style>body{{font-family:sans-serif;padding:30px;color:#333;}}h2{{color:#222;border-bottom:2px solid #00f2fe;padding-bottom:8px;}}table{{width:100%;border-collapse:collapse;margin-top:15px;}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd;}}th{{background:#f5f5f5;}}</style></head><body><h2>ОТЧЕТ: {trip_id.upper().replace('_', ' ')}</h2><p><b>Депозит:</b> {depozit_hotel:.2f} EUR | <b>На място:</b> {total_on_site:.2f} EUR{date_pdf_txt}</p><h3>🚗 Автомобил и Гориво:</h3><ul><li><b>Начални:</b> {s_km:.0f} км | <b>Крайни:</b> {e_km:.0f} км {"(Пробег: " + str(int(dist)) + " км)" if dist > 0 else ""}</li><li><b>Общо гориво:</b> {total_liters_calculated:.1f} л | <b>Стойност:</b> {auto_fuel_money:.2f} EUR</li><li><b>Среден разход за пътуването:</b> <b style='color:#00f2fe;'>{pdf_avg_con_txt}</b></li></ul><h3>📋 Разходи по категории:</h3><table><tr><th>Дата и час</th><th>Описание</th><th>Сума</th><th>Категория</th></tr>"
        for _, row in df_trip.iterrows(): pdf_html += f"<tr><td>{row['date']}</td><td>{row['description']}</td><td>{row['amount']:.2f} EUR</td><td>{row['category']}</td></tr>"
        pdf_html += "</table></body></html>"
        b64_pdf = base64.b64encode(pdf_html.encode('utf-8')).decode('utf-8')
        st.markdown(f'<a href="data:text/html;base64,{b64_pdf}" download="Otchet_{trip_id}_2026.html" style="text-decoration:none;"><button style="width:100%; background:linear-gradient(135deg, #00f2fe, #4facfe); color:white; border:none; padding:12px; font-weight:bold; border-radius:10px; cursor:pointer;">📄 СВАЛИ ПЪЛЕН ОТЧЕТ (PDF/HTML)</button></a>', unsafe_allow_html=True)
        st.markdown("---")
        
        @st.dialog("🚨 ИЗТРИВАНЕ НА ЦЯЛОТО ПЪТУВАНЕ")
        def delete_entire_trip_modal():
            st.error("⚠️ ВНИМАНИЕ! Това действие ще изтрие завинаги всички разходи и снимки за тази почивка!")
            st.write("Сигурни ли сте на 100%?")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                if st.button("🚨 ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
                    try:
                        # 1. ТИХО ИЗТРИВАНЕ НА ФАЙЛОВЕТЕ НА ДИСКА ПЪРВО
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
                            
                        # 2. ЧАК СЛЕД ТОВА НУЛИРАМЕ СЕСИЯТА И ЗАТВАРЯМЕ ПРОЗОРЕЦА
                        st.session_state["current_trip"] = None
                        st.cache_data.clear()
                        st.rerun()
                    except: pass
            with col_t2:
                if st.button("❌ ОТКАЗ", use_container_width=True): st.rerun()

        if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True): delete_entire_trip_modal()




