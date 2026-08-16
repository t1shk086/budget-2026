import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64

# 1. СТРАНИЦА И ОРИГИНАЛЕН ПРЕМIУМ 3Д CSS ДИЗАЙН
st.set_page_config(page_title="Бюджет 2026", page_icon="💰", layout="centered")

st.markdown("""
<style>
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader, .stExpander {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important; padding: 10px 15px !important;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4), -2px -2px 8px rgba(255, 255, 255, 0.02) !important;
        margin-bottom: 15px !important;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #2e2e2e, #1c1c1c) !important; color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 10px !important;
        box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5), -1px -1px 4px rgba(255, 255, 255, 0.05) !important;
        transition: all 0.2s ease !important; font-weight: bold !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #3d3d3d, #252525) !important;
        transform: translateY(-2px) !important; box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.6) !important;
    }
</style>
""", unsafe_allow_html=True)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"
def get_emoji(cat):
    m = {"Храна и напитки": "🍔", "Транспорт": "🚗", "Куче": "🐾", "Нощувки/Хотел": "🏨", "Депозит/Резервация": "📌", "Други": "🪙"}
    return m.get(cat, "💳")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters"]), (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel"])]:
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

def get_trip_data(t_id):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        r = df[df["trip_id"] == t_id].copy()
        if "liters" not in r.columns: r["liters"] = 0.0
        return r
    except: return pd.DataFrame(columns=["trip_id","date","amount","category","description","type","liters"])

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0}
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        f = df[df["trip_id"] == t_id]
        if not f.empty:
            res = f.iloc[0].to_dict()
            return {"car_trip": str(res.get("car_trip", "Не")), "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), "start_km": float(res.get("start_km", 0.0)), "end_km": float(res.get("end_km", 0.0)), "manual_fuel": float(res.get("manual_fuel", 0.0))}
    except: pass
    return d
def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        df = pd.concat([df, pd.DataFrame([{"trip_id": t_id, "car_trip": c_t, "track_fuel": t_f, "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f)}])], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: return False

def generate_html_pdf(trip_name, total_site, deposit, categories_totals, rows_data, fuel_info=None):
    html_content = f"<html><body><h1>Финансов отчет: {trip_name.upper()}</h1><p><b>ОБЩО:</b> {deposit + total_site:.2f} EUR</p></body></html>"
    return html_content.encode('utf-8')

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0

if st.session_state["current_trip"] is None:
    st.markdown("<h1 style='text-align: center;'>💰 Бюджет 2026</h1>", unsafe_allow_html=True)
    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    opts = ["-- Изберете почивка --"] + [t.replace("_", " ") for t in existing] + ["➕ СЪЗДАЙ НОВО ПЪТУВАНЕ"]
    choice = st.selectbox("Изберете или създайте почивка:", opts)
    if choice == "➕ СЪЗДАЙ НОВО ПЪТУВАНЕ":
        txt = st.text_input("Име на новата дестинация:").strip()
        if st.button("🚀 СЪЗДАЙ И ОТВОРИ", use_container_width=True) and txt:
            st.session_state["current_trip"] = txt.replace(" ", "_"); st.rerun()
    elif choice != "-- Изберете почивка --":
        if st.button("📂 ОТВОРИ ПОЧИВКАТА", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_"); st.rerun()
else:
    trip_id = st.session_state["current_trip"]
    if st.button("⬅️ НАЗАД КЪМ ВСИЧКИ ПОЧИВКИ", use_container_width=True):
        st.session_state["current_trip"] = None; st.rerun()
        
    st.markdown(f"<h2 style='text-align: center; color: #00f2fe;'>🌴 Дестинация: {trip_id.upper().replace('_', ' ')}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    c_s = get_trip_settings(trip_id)
    c_idx = 0 if c_s["car_trip"] == "Не" else 1
    car_choice = st.selectbox("Пътувате ли със собствен автомобил?", ["Не", "Да"], index=c_idx)
    
    t_fuel, s_km, e_km, m_fuel = str(c_s["track_fuel"]), float(c_s["start_km"]), float(c_s["end_km"]), float(c_s["manual_fuel"])
    
    @st.dialog("📊 Въвеждане на километраж")
    def km_modal(current_skm, current_ekm):
        st.write("Въведете километрите за засичане на средния разход:")
        new_skm = st.number_input("Начални километри (км)", value=current_skm, step=1.0)
        new_ekm = st.number_input("Крайни километри (км)", value=current_ekm, step=1.0)
        if st.button("💾 Запази километрите", use_container_width=True, type="primary"):
            save_trip_settings(trip_id, car_choice, "Да", new_skm, new_ekm, m_fuel)
            st.rerun()

    if car_choice == "Да":
        t_idx = 0 if t_fuel == "Да" else 1
        t_fuel_selected = st.selectbox("Искате ли изчисляване на разход на гориво?", ["Да", "Добави впоследствие"], index=t_idx)
        
        # АКО ИЗБЕРЕ ДА, ОТВАРЯМЕ ИЗСКАЧАЩИЯ ПРОЗОРЕЦ ВЕДНАГА
        if t_fuel_selected == "Да" and t_fuel != "Да":
            km_modal(s_km, e_km)
        t_fuel = t_fuel_selected
    else:
        t_fuel = "Добави впоследствие"

    save_trip_settings(trip_id, car_choice, t_fuel, s_km, e_km, m_fuel)
    st.markdown("---")
    
    papka_snimki = f"snimki_{trip_id}_2026"; df_trip = get_trip_data(trip_id); depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum()); v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1: s_input = st.number_input("СУМА (EUR)", min_value=0.0, step=1.0, format="%.2f", key=f"su_{v_id}")
    with col2: o_input = st.text_input("Описание", key=f"op_{v_id}")

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description, is_dep):
        st.write(f"Засякохме гориво за **{amount:.2f} EUR**.")
        liters = st.number_input("Литри:", min_value=0.0, step=0.1)
        if st.button("💾 Запиши", use_container_width=True, type="primary"):
            if add_expense(trip_id, amount, category, f"[ГОРИВО] {description}", is_dep, liters):
                st.session_state["form_version"] += 1; st.rerun()

    grid = st.columns(3)
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"bt_{i}"):
                if s_input and s_input > 0:
                    desc = o_input.strip() if o_input else "Без описание"
                    is_d = (kat == "Депозит/Резервация")
                    if kat == "Транспорт" and car_choice == "Да" and t_fuel == "Да" and any(k in desc.lower() for k in ["гориво", "зареждане", "бензин", "дизел"]):
                        fuel_modal(s_input, kat, desc, is_d)
                    else:
                        if add_expense(trip_id, s_input, kat, desc, is_d): st.session_state["form_version"] += 1; st.rerun()
    df_expenses = df_trip[df_trip["type"] == "expense"]; total_on_site = float(df_expenses["amount"].sum()); categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}; rows_data = []; total_liters_sum, auto_fuel_money = 0.0, 0.0
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
        rows_data.append([row["date"], float(row["amount"]), row["category"], row["description"]])
        if row["category"] == "Транспорт":
            if float(row.get("liters", 0)) > 0: total_liters_sum += float(row["liters"]); auto_fuel_money += float(row["amount"])
            elif any(k in str(row["description"]).lower() for k in ["гориво", "зареждане", "бензин", "дизел"]): auto_fuel_money += float(row["amount"])
    total_fuel_calculated = auto_fuel_money + m_fuel

    st.markdown("### 📊 Анализ на разходите")
    stat_grid = st.columns(2)
    for idx, (kat, s_value) in enumerate(categories_totals.items()):
        pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
        b_c = "rgba(255,75,75,0.4)" if pct > 40 else "rgba(255,165,0,0.4)" if pct > 20 else "rgba(0,242,254,0.3)" if pct > 0 else "rgba(255,255,255,0.08)"
        b_g = "rgba(255,75,75,0.2)" if pct > 40 else "rgba(255,165,0,0.2)" if pct > 20 else "rgba(0,242,254,0.15)" if pct > 0 else "rgba(255,255,255,0.1)"
        b_t = "#ff4b4b" if pct > 40 else "#ffa500" if pct > 20 else "#00f2fe" if pct > 0 else "#aaa"
        with stat_grid[idx % 2]:
            st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); border: 1px solid {b_c}; padding: 12px 15px; border-radius: 14px; box-shadow: 3px 3px 10px rgba(0,0,0,0.3); margin-bottom: 12px; height: 120px; display: flex; flex-direction: column; justify-content: space-between;"><div style="display: flex; justify-content: space-between; align-items: center;"><span>{get_emoji(kat)} {kat}</span><span style="background:{b_g}; color:{b_t}; font-size:11px; padding:2px 7px; border-radius:20px; font-weight:bold;">{pct:.1f}%</span></div><h3 style="margin:0; color:white; font-size:20px; font-weight:800;">{s_value:.2f} <span style="font-size:11px; color:#aaa;">EUR</span></h3><div style="background:rgba(255,255,255,0.05); width:100%; height:6px; border-radius:10px; overflow:hidden;"><div style="background:{b_t}; width:{pct}%; height:100%; border-radius:10px;"></div></div></div>', unsafe_allow_html=True)

    if car_choice == "Да" and t_fuel == "Да":
        st.markdown("#### ⛽ Справка за разхода и горивото")
        dist = e_km - s_km
        col_fuel1, col_fuel2 = st.columns(2)
        with col_fuel1: st.markdown(f'<div style="background: rgba(255, 165, 0, 0.05); border: 1px solid rgba(255, 165, 0, 0.2); padding: 15px; border-radius: 12px; text-align: center;"><small style="color: #ffa500; font-weight: bold;">⛽ ОБЩО ЗА ГОРИВО</small><h3 style="color: white; margin: 5px 0;">{total_fuel_calculated:.2f} EUR</h3><small style="color: #aaa;">Общо: {total_liters_sum:.1f} л</small></div>', unsafe_allow_html=True)
        with col_fuel2:
            if dist > 0:
                avg_con = (total_liters_sum / dist * 100) if total_liters_sum > 0 else 0.0
                st.markdown(f'<div style="background: rgba(0, 242, 254, 0.05); border: 1px solid rgba(0, 242, 254, 0.2); padding: 15px; border-radius: 12px; text-align: center;"><small style="color: #00f2fe; font-weight: bold;">📊 СРЕДЕН РАЗХОД ({dist:.0f} км)</small><h3 style="color: white; margin: 5px 0;">{avg_con:.1f} л / 100 км</h3><small style="color: #aaa;">От {s_km:.0f} до {e_km:.0f} км</small></div>', unsafe_allow_html=True)
            else:
                if st.button("📝 Въведи / Промени км", use_container_width=True): km_modal(s_km, e_km)

    st.markdown("---"); col_st1, col_st2 = st.columns(2)
    with col_st1: st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center;'><small style='color:#aaa; font-weight:bold;'>🏨 ДЕПОЗИТ</small><h2 style='color:#ff4b4b; margin:5px 0;'>{depozit_hotel:.2f} EUR</h2></div>", unsafe_allow_html=True)
    with col_st2: st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:12px; text-align:center;'><small style='color:#aaa; font-weight:bold;'>💰 НА МЯСТО</small><h2 style='color:#00f2fe; margin:5px 0;'>{total_on_site:.2f} EUR</h2></div>", unsafe_allow_html=True)

    if not df_trip.empty:
        st.markdown("---"); st.subheader("📋 Хронология на плащанията")
        try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            for idx in reversed(df_all[df_all["trip_id"] == trip_id].index.tolist()):
                r = df_all.loc[idx]; l_txt = f" | ⛽ {r['liters']:.1f} л" if float(r.get("liters", 0)) > 0 else ""
                st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); padding: 12px; border-radius: 10px; margin-bottom: 2px; border: 1px solid rgba(255,255,255,0.08);"><span style="font-size:18px;">{get_emoji(r["category"])}</span> <b>{r["category"]}</b> — <span style="color:#ff4b4b; font-weight:bold;">{r["amount"]:.2f} EUR</span><br><small style="color:#aaa;">📅 {r["date"]} | 📝 {r["description"]}{l_txt}</small></div>', unsafe_allow_html=True)
                if st.button("❌ Изтрий разход", key=f"dl_{idx}", use_container_width=True):
                    df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8"); st.rerun()
        except: pass

    st.markdown("---")
    with st.expander("📸 Снимки и спомени от почивката"):
        if not os.path.exists(papka_snimki): os.makedirs(papka_snimki)
        up = st.file_uploader("Качете снимки:", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"u_{trip_id}")
        if up:
            for f in up:
                if not os.path.exists(os.path.join(papka_snimki, f.name)):
                    with open(os.path.join(papka_snimki, f.name), "wb") as out: out.write(f.getbuffer())
            st.rerun()
        saved = glob.glob(os.path.join(papka_snimki, "*"))
        if saved:
            img_grid = st.columns(3)
            for idx, p in enumerate(saved):
                with img_grid[idx % 3]:
                    st.image(p, use_container_width=True)
                    if st.button("🗑️ Трий", key=f"di_{idx}", use_container_width=True): os.remove(p); st.rerun()

    st.markdown("---"); potv = st.checkbox("Потвърждавам изтриването на цялото пътуване")
    if st.button("🗑️ ИЗТРИЙ ЦЯЛОТО ПЪТУВАНЕ", type="primary", use_container_width=True, disabled=not potv):
        try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8"); df_all[df_all["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
            if os.path.exists(papka_snimki):
                for p in glob.glob(os.path.join(papka_snimki, "*")): os.remove(p)
                os.rmdir(papka_snimki)
            st.session_state["current_trip"] = None; st.rerun()
        except: pass
