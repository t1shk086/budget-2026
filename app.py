import streamlit as st
import pandas as pd
import datetime
import os
import glob
import base64

# 1. СТРАНИЦА И 3Д CSS ДИЗАЙН
st.set_page_config(page_title="Бюджет 2026", page_icon="💰", layout="centered")

st.markdown("""
<style>
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader, .stExpander {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4), -2px -2px 8px rgba(255, 255, 255, 0.02) !important;
        margin-bottom: 15px !important;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #2e2e2e, #1c1c1c) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
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

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"]).to_csv(DATA_FILE, index=False, encoding="utf-8")
if not os.path.exists(SETTINGS_FILE):
    pd.DataFrame(columns=["trip_id", "car_trip", "track_fuel", "start_km", "end_km", "manual_fuel"]).to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
def get_trip_data(t_id):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        return df[df["trip_id"] == t_id].copy()
    except: return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type", "liters"])

def get_trip_settings(t_id):
    d = {"car_trip": "Не", "track_fuel": "Добави впоследствие", "start_km": 0.0, "end_km": 0.0, "manual_fuel": 0.0}
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        f = df[df["trip_id"] == t_id]
        if not f.empty: return f.iloc[0].to_dict()
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

if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "form_version" not in st.session_state: st.session_state["form_version"] = 0

if st.session_state["current_trip"] is None:
    st.markdown("<h1 style='text-align: center;'>💰 Бюджет 2026</h1>", unsafe_allow_html=True)
    existing_trips = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    opts = ["-- Изберете почивка --"] + [t.replace("_", " ") for t in existing_trips] + ["➕ СЪЗДАЙ НОВО ПЪТУВАНЕ"]
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
    c_idx = 0 if str(c_s.get("car_trip", "Не")) == "Не" else 1
    car_choice = st.selectbox("Пътувате ли със собствен автомобил?", ["Не", "Да"], index=c_idx)
    t_fuel, s_km, e_km, m_fuel = "Добави впоследствие", float(c_s.get("start_km", 0)), float(c_s.get("end_km", 0)), float(c_s.get("manual_fuel", 0))
    
    if car_choice == "Да":
        t_idx = 0 if str(c_s.get("track_fuel", "Да")) == "Да" else 1
        t_fuel = st.selectbox("Искате ли изчисляване на разход на гориво?", ["Да", "Добави впоследствие"], index=t_idx)
        if t_fuel == "Да":
            colk1, colk2 = st.columns(2)
            with colk1: s_km = st.number_input("Начални км", value=s_km)
            with colk2: e_km = st.number_input("Крайни км", value=e_km)
            m_fuel = st.number_input("Допълнително гориво (EUR)", value=m_fuel)

    save_trip_settings(trip_id, car_choice, t_fuel, s_km, e_km, m_fuel)
    st.markdown("---")
    
    papka_snimki = f"snimki_{trip_id}_2026"
    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    v_id = st.session_state["form_version"]
    
    col1, col2 = st.columns(2)
    with col1: s_input = st.number_input("СУМА (EUR)", min_value=0.0, format="%.2f", key=f"su_{v_id}")
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
                        if add_expense(trip_id, s_input, kat, desc, is_d):
                            st.session_state["form_version"] += 1; st.rerun()
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    total_liters_sum, auto_fuel_money = 0.0, 0.0
    
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
        if row["category"] == "Транспорт":
            if float(row.get("liters", 0)) > 0: total_liters_sum += float(row["liters"]); auto_fuel_money += float(row["amount"])
            elif any(k in str(row["description"]).lower() for k in ["гориво", "зареждане", "бензин", "дизел"]): auto_fuel_money += float(row["amount"])

    st.markdown("### 📊 Анализ на разходите")
    stat_grid = st.columns(2)
    for idx, (kat, s_value) in enumerate(categories_totals.items()):
        pct = (s_value / total_on_site * 100) if total_on_site > 0 else 0.0
        b_c = "rgba(255,75,75,0.4)" if pct > 40 else "rgba(255,165,0,0.4)" if pct > 20 else "rgba(0,242,254,0.3)"
        b_g = "rgba(255,75,75,0.2)" if pct > 40 else "rgba(255,165,0,0.2)" if pct > 20 else "rgba(0,242,254,0.15)"
        with stat_grid[idx % 2]:
            st.markdown(f'<div style="background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); border: 1px solid {b_c}; padding: 12px; border-radius: 14px; margin-bottom: 12px; height: 110px; display: flex; flex-direction: column; justify-content: space-between;"><div style="display: flex; justify-content: space-between;"><span>{get_emoji(kat)} {kat}</span><span style="background:{b_g}; padding:2px 7px; border-radius:20px; font-size:11px;">{pct:.1f}%</span></div><h3 style="margin:0;">{s_value:.2f} EUR</h3><div style="background:rgba(255,255,255,0.05); width:100%; height:5px; border-radius:10px; overflow:hidden;"><div style="background:{b_c}; width:{pct}%; height:100%;"></div></div></div>', unsafe_allow_html=True)

    if car_choice == "Да" and t_fuel == "Да":
        dist = e_km - s_km
        if dist > 0:
            st.info(f"⛽ Изминати: {dist:.1f} км | Среден разход: **{(total_liters_sum / dist * 100):.1f} л / 100 км** | Гориво: {auto_fuel_money+m_fuel:.2f} EUR")

    st.markdown("---")
    col_st1, col_st2 = st.columns(2)
    with col_st1: st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:12px; border-radius:12px; text-align:center;'><small>🏨 ДЕПОЗИТ</small><h3>{depozit_hotel:.2f} EUR</h3></div>", unsafe_allow_html=True)
    with col_st2: st.markdown(f"<div style='background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:12px; border-radius:12px; text-align:center;'><small>💰 НА МЯСТО</small><h3>{total_on_site:.2f} EUR</h3></div>", unsafe_allow_html=True)

    if not df_trip.empty:
        st.subheader("📋 Хронология")
        try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            for idx in reversed(df_all[df_all["trip_id"] == trip_id].index.tolist()):
                r = df_all.loc[idx]
                st.markdown(f"{get_emoji(r['category'])} **{r['category']}** — {r['amount']:.2f} EUR ({r['description']})")
                if st.button("🗑️ Изтрий разход", key=f"dl_{idx}"):
                    df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8"); st.rerun()
        except: pass

    st.markdown("---")
    with st.expander("📸 Снимки и спомени"):
        if not os.path.exists(papka_snimki): os.makedirs(papka_snimki)
        up = st.file_uploader("Качете снимки:", type=["jpg", "png"], accept_multiple_files=True, key=f"u_{trip_id}")
        if up:
            for f in up:
                with open(os.path.join(papka_snimki, f.name), "wb") as out: out.write(f.getbuffer())
            st.rerun()
        img_grid = st.columns(3)
        for idx, p in enumerate(glob.glob(os.path.join(papka_snimki, "*"))):
            with img_grid[idx % 3]:
                st.image(p, use_container_width=True)
                if st.button("🗑️", key=f"di_{idx}", use_container_width=True): os.remove(p); st.rerun()

    st.markdown("---")
    potv = st.checkbox("Потвърждавам изтриването на цялото пътуване")
    if st.button("🗑️ ИЗТРИЙ ЦЯЛОТО ПЪТУВАНЕ", type="primary", use_container_width=True, disabled=not potv):
        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
        df_all[df_all["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
        st.session_state["current_trip"] = None; st.rerun()
