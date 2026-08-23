import streamlit as st
import pandas as pd
import datetime
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import io

st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #090b0e 0%, #11151c 50%, #0d1117 100%) !important;
        background-attachment: fixed !important;
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.15) !important;
        z-index: -1;
        pointer-events: none;
    }
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important; 
        padding: 10px 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        backdrop-filter: blur(4px) !important;
        margin-bottom: 15px !important;
    }
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"] {
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
    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover {
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

pet_name = st.session_state.get("custom_pet_name", "Куче")
hotel_name = st.session_state.get("custom_hotel_name", "Нощувки/Хотел")
deposit_name = st.session_state.get("custom_deposit_name", "Депозит/Резервация")

if not os.path.exists(MAP_FILE):
    pd.DataFrame(columns=["trip_id", "lat", "lon", "title", "color"]).to_csv(MAP_FILE, index=False, encoding="utf-8")

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","liters","current_km"]), 
                (SETTINGS_FILE, ["trip_id","car_trip","track_fuel","start_km","end_km","manual_fuel","start_date","end_date"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

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
                "trip_id": t_id, 
                "car_trip": str(res.get("car_trip", "Не")), 
                "track_fuel": str(res.get("track_fuel", "Добави впоследствие")), 
                "start_km": float(res.get("start_km", 0.0)), 
                "end_km": float(res.get("end_km", 0.0)), 
                "manual_fuel": float(res.get("manual_fuel", 0.0)), 
                "start_date": str(res.get("start_date", "")), 
                "end_date": str(res.get("end_date", ""))
            }
    except: 
        pass
    return d

def save_trip_settings(t_id, c_t, t_f, s_k, e_k, m_f=0.0, s_d="", e_d=""):
    try:
        df = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
        df = df[df["trip_id"] != t_id]
        new_row = pd.DataFrame([{"trip_id": t_id, "car_trip": str(c_t), "track_fuel": str(t_f), "start_km": float(s_k), "end_km": float(e_k), "manual_fuel": float(m_f), "start_date": str(s_d), "end_date": str(e_d)}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
    except: 
        pass

def add_expense(t_id, amt, cat, desc, is_dep=False, lit=0.0, c_km=0.0):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        if "current_km" not in df.columns: df["current_km"] = 0.0
        row = {"trip_id": t_id, "date": datetime.datetime.now().strftime("%d.%m %H:%M"), "amount": float(amt), "category": cat, "description": desc if desc else "Без описание", "type": "deposit" if is_dep else "expense", "liters": float(lit), "current_km": float(c_km)}
        pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except: 
        return False

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
if st.session_state["current_trip"] is None:
    st.markdown("<div style='text-align: center; margin-bottom: 5px;'><h1 style='font-family: \"Segoe UI\", Roboto, sans-serif; font-weight: 900; font-size: 46px; background: linear-gradient(135deg, #00f2fe, #4facfe, #ff4b4b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 10px rgba(0, 242, 254, 0.2); margin-bottom: 0px;'>🐾 PixelApp</h1><p style='font-family: \"Segoe UI\", Roboto, sans-serif; font-size: 16px; color: #ffd700; font-weight: 500; margin-top: 4px; margin-bottom: 30px;'>Travel Manager</p></div>", unsafe_allow_html=True)
    
    existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique()) if os.path.exists(DATA_FILE) else []
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете пътуване до:", opts)
        if st.button("✔️ Зареди", use_container_width=True):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.rerun()
    else:
        st.markdown("<div style='text-align:center; padding:20px; color:#aaa; background:rgba(255,255,255,0.02); border-radius:10px; border:1px dashed rgba(255,255,255,0.1); margin-bottom:15px;'>Все още нямате записани почивки. Създайте първото си приключение по-долу!</div>", unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; margin: 10px 0; color:#555;'>или</div>", unsafe_allow_html=True)
    
    @st.dialog("➕ Създаване на ново приключение")
    def create_trip_modal():
        txt = st.text_input("Име на дестинацията:",placeholder="Въведете име...").strip()
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

    if st.button("➕ Ново пътуване", use_container_width=True): 
        create_trip_modal()

    st.markdown("---")
    
    st.html("""
    <style>
        div[data-testid="stCheckbox"] > label {
            display: inline-flex !important;
            flex-direction: row-reverse !important;
            align-items: center !important;
            gap: 10px !important;
            width: auto !important;
        }
        div[data-testid="stCheckbox"] p {
            white-space: nowrap !important;
            margin: 0 !important;
        }
    </style>
    """)

    show_comparison = st.toggle(label="Сравнителен панел", value=False, key="stable_comparison_toggle")
        
    if show_comparison:
        @st.dialog("📊 Сравнителен панел", width="large")
        def show_global_analytics_dialog():
            st.markdown("<p style='color: #888; margin-bottom: 20px;'>Завъртете дисплея, за да видите графиката в по-добър мащаб!</p>", unsafe_allow_html=True)
            
            chosen_criteria = st.segmented_control(
                label="Изберете критерий:",
                options=["Цена за 1 км", "Пари на Ден", "Обща Стойност", "Изминати км", "Нощувки и Депозити"],
                default="Цена за 1 км",
                key="modal_segmented_metric_selector"
            )

            all_trips_computed = []
            try:
                df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8")
                df_all_settings = pd.read_csv(SETTINGS_FILE, encoding="utf-8")
                unique_trips = df_all_data["trip_id"].dropna().unique()

                for t in unique_trips:
                    if not t or str(t).strip() == "": continue
                    
                    df_t_data = df_all_data[df_all_data["trip_id"] == t]
                    df_t_sett = df_all_settings[df_all_settings["trip_id"] == t]

                    t_dep = float(df_t_data[df_t_data["type"] == "deposit"]["amount"].sum())
                    t_site = float(df_t_data[df_t_data["type"] == "expense"]["amount"].sum())
                    t_total = t_dep + t_site

                    t_hotel_only = float(df_t_data[df_t_data["category"] == "Нощувки/Хотел"]["amount"].sum())
                    t_deposit_only = float(df_t_data[df_t_data["category"] == "Депозит/Резервация"]["amount"].sum())
                    t_accommodation_total = t_hotel_only + t_deposit_only

                    t_dist, s_k, e_k = 0.0, 0.0, 0.0
                    days_count = 1

                    if not df_t_sett.empty:
                        s_k = float(df_t_sett["start_km"].iloc[0]) if "start_km" in df_t_sett.columns and not df_t_sett["start_km"].empty else 0.0
                        e_k = float(df_t_sett["end_km"].iloc[0]) if "end_km" in df_t_sett.columns and not df_t_sett["end_km"].empty else 0.0
                        st_d_str = str(df_t_sett["start_date"].iloc[0]) if "start_date" in df_t_sett.columns and not df_t_sett["start_date"].empty else ""
                        en_d_str = str(df_t_sett["end_date"].iloc[0]) if "end_date" in df_t_sett.columns and not df_t_sett["end_date"].empty else ""

                        max_k = float(df_t_data[df_t_data["type"] == "expense"]["current_km"].max()) if not df_t_data.empty else 0.0
                        eff_e = e_k if e_k > 0 else max_k
                        t_dist = eff_e - s_k if eff_e > s_k else 0.0

                        try:
                            d1 = datetime.datetime.strptime(st_d_str, "%d.%m.%Y")
                            d2 = datetime.datetime.strptime(en_d_str, "%d.%m.%Y")
                            days_count = max(1, (d2 - d1).days + 1)
                        except:
                            days_count = 1

                    all_trips_computed.append({
                        "Пътуване": str(t).replace("_", " ").upper(),
                        "Обща Стойност (EUR)": t_total,
                        "Цена за 1 км (EUR)": (t_total / t_dist) if t_dist > 0 else 0.0,
                        "Дневен Разход (EUR)": (t_total / days_count),
                        "Изминато разстояние (км)": t_dist,
                        "Нощувки и Депозити (EUR)": t_accommodation_total,
                        "DistValid": t_dist > 0
                    })
            except:
                pass

            if all_trips_computed:
                df_pixel = pd.DataFrame(all_trips_computed)
                import plotly.express as px

                if chosen_criteria == "Цена за 1 км":
                    x_col = "Цена за 1 км (EUR)"
                    t_format = "%{text:.2f} EUR/км"
                    df_filtered = df_pixel[df_pixel["DistValid"] == True]
                    if df_filtered.empty: df_filtered = df_pixel
                    df_sorted = df_filtered.sort_values(by=x_col, ascending=True)
                    graph_title = "💰 Сравнение на ефективността (EUR/1км)"
                elif chosen_criteria == "Обща Стойност":
                    x_col = "Обща Стойност (EUR)"
                    t_format = "%{text:,.2f} EUR"
                    df_sorted = df_pixel.sort_values(by=x_col, ascending=False)
                    graph_title = "💸 Тотална СУМА"
                elif chosen_criteria == "Изминати км":
                    x_col = "Изминато разстояние (км)"
                    t_format = "%{text:.0f} км"
                    df_sorted = df_pixel.sort_values(by=x_col, ascending=False)
                    graph_title = "🚗 Общо изминато разстояние"
                elif chosen_criteria == "Нощувки и Депозити":
                    x_col = "Нощувки и Депозити (EUR)"
                    t_format = "%{text:,.2f} EUR"
                    df_sorted = df_pixel.sort_values(by=x_col, ascending=False)
                    graph_title = "🏨 Разходи за Спане, Хотели и Депозити"
                else: 
                    x_col = "Дневен Разход (EUR)"
                    t_format = "%{text:.2f} EUR/ден"
                    df_sorted = df_pixel.sort_values(by=x_col, ascending=False)
                    graph_title = "📅 Среднодневен разход"

                fig_pixel = px.bar(df_sorted, x=x_col, y="Пътуване", orientation='h', text=x_col)

                if chosen_criteria == "Изминати км":
                    c_scale = [[0, '#ff3b30'], [0.5, '#ffaa00'], [1, '#2ebd59']]
                else:
                    c_scale = [[0, '#2ebd59'], [0.5, '#ffaa00'], [1, '#ff3b30']]

                fig_pixel.update_traces(
                    marker=dict(
                        color=df_sorted[x_col],
                        colorscale=c_scale,
                        line=dict(width=0),
                        cornerradius=15
                    ),
                    texttemplate=f"<b>{t_format}</b>",
                    textposition='outside',
                    cliponaxis=False
                )

                fig_pixel.update_layout(
                    title=dict(text=graph_title, font=dict(color="white")),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, showline=False, showticklabels=False, title=""),
                    yaxis=dict(showgrid=False, showline=False, title="", tickfont=dict(color="white")),
                    margin=dict(l=10, r=110, t=50, b=10),
                    height=320,
                    bargap=0.35
                )
                st.plotly_chart(fig_pixel, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Няма достатъчно база данни за сравнение.")

            st.write("---")
            if st.button("❌ Затвори", key="bottom_modal_close_btn", use_container_width=True):
                st.session_state["stable_comparison_toggle"] = False
                st.rerun()

        show_global_analytics_dialog()

else:
    trip_id = st.session_state["current_trip"]
    c_s = get_trip_settings(trip_id)
    car_trip = str(c_s["car_trip"])
    t_fuel = str(c_s["track_fuel"])
    s_km = float(c_s["start_km"])
    e_km = float(c_s["end_km"])
    m_fuel = float(c_s["manual_fuel"])
    st_date = str(c_s.get("start_date", ""))
    en_date = str(c_s.get("end_date", ""))

    @st.dialog("🗑️ Потвърждение за изтриване")
    def confirm_delete_dialog():
        if "delete_idx" in st.session_state and st.session_state["delete_idx"] is not None:
            st.write("Сигурни ли сте, че искате да изтриете този разход?")
            idx = st.session_state["delete_idx"]
            try:
                df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                r = df_all.loc[idx]
                st.markdown(f"**{get_emoji(r['category'])} {r['category']}** — {r['amount']:.2f} EUR")
            except: 
                pass
            c_del1, c_del2 = st.columns(2)
            with c_del1:
                if st.button("✔️ ДА, ИЗТРИЙ", use_container_width=True, type="primary"):
                    try:
                        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
                        df_all.drop(idx).to_csv(DATA_FILE, index=False, encoding="utf-8")
                    except: 
                        pass
                    st.session_state["delete_idx"] = None
                    st.rerun()
            with c_del2:
                if st.button("✖️ ОТКАЗ", use_container_width=True): 
                    st.session_state["delete_idx"] = None
                    st.rerun()

    @st.dialog("🚨 Изтриване на цялото пътуване")
    def confirm_delete_trip_dialog():
        st.error(f"ВНИМАНИЕ! Изтриване на почивката?")
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            if st.button("✔️ ДА, ИЗТРИЙ ВСИЧКО", use_container_width=True, type="primary"):
                try:
                    pd.read_csv(DATA_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(DATA_FILE, index=False, encoding="utf-8")
                    pd.read_csv(SETTINGS_FILE, encoding="utf-8")[lambda d: d["trip_id"] != trip_id].to_csv(SETTINGS_FILE, index=False, encoding="utf-8")
                except: 
                    pass
                st.session_state["current_trip"] = None
                st.rerun()
        with c_tr2:
            if st.button("✖️ ОТКАЗ", use_container_width=True): 
                st.rerun()

    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    total_liters_sum, auto_fuel_money = 0.0, 0.0
    
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: 
            categories_totals[row["category"]] += float(row["amount"])
        if row["category"] == "Транспорт":
            if float(row.get("liters", 0)) > 0: 
                total_liters_sum += float(row["liters"])
                auto_fuel_money += float(row["amount"])
            elif any(k in str(row["description"]).lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): 
                auto_fuel_money += float(row["amount"])
    
    total_liters_calculated = total_liters_sum + m_fuel
    max_current_km = float(df_expenses["current_km"].max()) if not df_expenses.empty and "current_km" in df_expenses.columns else 0.0
    eff_end_km = e_km if e_km > 0 else max_current_km
    dist = eff_end_km - s_km if eff_end_km > s_km else 0.0

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
    except: 
        pass

    if st_date and st_date != "nan":
        st.markdown(f"<p style='text-align:center;color:#888;'>{st_date} - {en_date}</p>", unsafe_allow_html=True)
    
    st.markdown(f"<h2 style='text-align:center;'>🌴 {str(trip_id).replace('_', ' ')}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div id='trip_top_anchor'></div>", unsafe_allow_html=True)
    
    ekran_za_kategorii = st.empty()

    if st.button("🔙 НАЗАД КЪМ НАЧАЛЕН ЕКРАН", use_container_width=True): 
        st.session_state["current_trip"] = None
        st.rerun()

    v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1: 
        s_input = st.number_input("СУМА (EUR)", value=None, placeholder="Сума...", format="%.2f", key=f"su_{v_id}")
    with col2: 
        o_input = st.text_input("Описание", placeholder="Описание...", key=f"op_{v_id}")

    is_trip_finished = (e_km > 0.0)

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description, is_dep):
        if is_trip_finished: 
            st.error("🔒 Пътуването е приключено!")
            return
        liters = st.number_input("Литри:", value=None, placeholder="Литри...", step=0.1)
        fuel_type = st.radio("Тип:", ["Да, до горе (Пълен резервоар)", "Не, частично"], index=0)
        
        df_f = get_trip_data(trip_id)[lambda d: (d["category"] == "Транспорт") & (d["current_km"] > 0)].sort_index()
        last_km = float(df_f["current_km"].max()) if not df_f.empty else s_km
        km_input = st.number_input("Километри на таблото:", value=None, placeholder="Км...", step=1.0)
        
        if st.button("💾 Запиши зареждането", use_container_width=True, type="primary"):
            lit = float(liters) if liters is not None else 0.0
            ckm = float(km_input) if km_input is not None else 0.0
            is_full = "ПЪЛНО" if "до горе" in fuel_type.lower() else "ЧАСТИЧНО"
            full_desc = f"[{is_full} ЗАРЕЖДАНЕ] {description}"
            
            if add_expense(trip_id, amount, category, full_desc, is_dep, lit, ckm): 
                st.session_state["form_version"] += 1
                st.rerun()

    if o_input.strip() and s_input and s_input > 0:
        with ekran_za_kategorii.container():
            st.markdown("### 🎯 ИЗБЕРЕТЕ КАТЕГОРИЯ")
            grid = st.columns(3)
            
            alias_map = {
                "Храна и напитки": "Храна и напитки",
                "Транспорт": "Транспорт",
                "Куче": pet_name,
                "Други": "Други",
                "Нощувки/Хотел": hotel_name,
                "Депозит/Резервация": deposit_name
            }
            
            for i, kat in enumerate(KATEGORII):
                display_label = alias_map.get(kat, kat)
                with grid[i % 3]:
                    is_disabled = is_trip_finished and (kat == "Транспорт")
                    if st.button(f"🔒 {display_label}" if is_disabled else display_label, use_container_width=True, key=f"bt_{i}", disabled=is_disabled):
                        desc = o_input.strip()
                        is_d = (kat == "Депозит/Резервация")
                        if kat == "Транспорт" and any(k in desc.lower() for k in ["газ", "гориво", "зареждане", "бензин", "дизел"]): 
                            fuel_modal(s_input, kat, desc, is_d)
                        else:
                            if add_expense(trip_id, s_input, kat, desc, is_d): 
                                st.session_state["form_version"] += 1
                                st.rerun()
            
            if st.button("❌ ОТКАЗ", use_container_width=True):
                st.session_state["form_version"] += 1
                st.rerun()
            st.stop()

    if car_trip == "Да":
        val_real = 0.0
        val_average = 0.0
        try:
            df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
            df_only_full = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
            if not df_only_full.empty:
        try:
            df_trans_fuel = df_expenses[(df_expenses["category"] == "Транспорт") & (df_expenses["current_km"] > s_km)].sort_index()
            df_only_full = df_trans_fuel[df_trans_fuel["description"].str.contains("ПЪЛЕН|ПЪЛНО", na=False)]
            if not df_only_full.empty:
                last_full_row = df_only_full.iloc[-1]["description"]
                import re
                match = re.search(r"(?:Реален разход:|Разход:)\s*([0-9.]+)", last_full_row)
                if match: 
                    val_real = float(match.group(1))
        except: 
            pass

        try:
            current_dist = (eff_end_km - s_km) if e_km > 0 else (float(df_expenses["current_km"].max()) - s_km)
            current_liters = float(df_expenses["liters"].sum()) + m_fuel
            if current_dist > 0 and current_liters > 0: 
                val_average = (current_liters / current_dist * 100)
        except: 
            pass

        transport_liters = float(df_expenses[df_expenses['category'] == 'Транспорт']['liters'].sum()) + m_fuel

        st.markdown("### ⏲ Данни за разход и пробег:")
        c_box1, c_box2 = st.columns(2)
        with c_box1:
            st.metric("Изминати км", f"{dist:.0f} км")
            if val_real > 0: 
                st.metric("Реален разход", f"{val_real:.1f} л/100км")
        with c_box2:
            st.metric("Общо литри", f"{transport_liters:.1f} л")
            st.metric("Среден разход", f"{val_average:.1f} л/100км")

    @st.dialog("⚙️ Настройки за автомобил")
    def edit_car_modal():
        v_car = st.radio("Автомобил ли използвате?", ["Не", "Да"], index=1 if car_trip == "Да" else 0)
        new_sk = st.number_input("Начални километри:", value=None if s_km == 0.0 else s_km)
        new_mf = st.number_input("Добави пропуснато гориво (л):", value=0.0, min_value=0.0)
        
        if st.button("💾 Обнови настройките", use_container_width=True, type="primary"):
            sk_val = float(new_sk) if new_sk is not None else 0.0
            mf_val = m_fuel + float(new_mf)
            save_trip_settings(trip_id, str(v_car), "Да", sk_val, e_km, mf_val, st_date, en_date)
            st.session_state["form_version"] += 1
            st.rerun()

    @st.dialog("🏁 Край на пътуването")
    def finish_trip_modal():
        end_km_input = st.number_input("Финални километри:", value=None if e_km == 0.0 else e_km)
        if st.button("🔒 ЗАКЛЮЧИ И ПРИКЛЮЧИ", use_container_width=True, type="primary"):
            if end_km_input and end_km_input > s_km: 
                save_trip_settings(trip_id, car_trip, t_fuel, s_km, float(end_km_input), m_fuel, st_date, en_date)
                st.session_state["form_version"] += 1
                st.rerun()

    if car_trip == "Да":
        col_m1, col_m2 = st.columns(2)
        with col_m1: 
            st.button("⚙️ Настройки автомобил", use_container_width=True, on_click=edit_car_modal)
        with col_m2: 
            st.button("🏁 Край на пътуването", use_container_width=True, on_click=finish_trip_modal)

    st.markdown("### 📊 Анализ на разходите:")
    stat_grid = st.columns(2)
    for idx, (kat, s_value) in enumerate(categories_totals.items()):
        display_label = pet_name if kat == 'Куче' else (hotel_name if kat == 'Нощувки/Хотел' else kat)
        with stat_grid[idx % 2]:
            st.markdown(f"**{get_emoji(kat)} {display_label}:** {s_value:.2f} EUR")

    @st.dialog("📊 Разходи по Категории", width="large")
    def разходи_по_категории_dialog():
        try:
            df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
            df_trip_rows = df_all[df_all["trip_id"] == trip_id]
            for kat in KATEGORII:
                if kat in df_trip_rows["category"].unique():
                    df_cat = df_trip_rows[df_trip_rows["category"] ==  kat]
                    display_label = pet_name if kat == 'Куче' else (hotel_name if kat == 'Нощувки/Хотел' else kat)
                    st.markdown(f"#### {get_emoji(kat)} {display_label}")
                    for _, r in df_cat.iterrows():
                        st.write(f"• {r['date']} — {r['description']}: {r['amount']:.2f} EUR")
        except: 
            pass
        if st.button("❌ Затвори", use_container_width=True): 
            st.rerun()

    if st.button("📊 Преглед по Категории", use_container_width=True):
        разходи_по_категории_dialog()

    st.markdown("---")
    st.write(f"🏨 Депозити: {depozit_hotel:.2f} EUR")
    st.write(f"💰 На място: {total_on_site:.2f} EUR")

    if st.button("❌ Изтрий цялото пътуване", type="primary", use_container_width=True):
        confirm_delete_trip_dialog()

    # --- АДМИНИСТРАТИВНИ ИНСТРУМЕНТИ С НОВИТЕ ОПЦИИ ---
    if "show_admin_panel" not in st.session_state: 
        st.session_state["show_admin_panel"] = False

    if st.button("🛠️ Административни Инструменти", use_container_width=True):
        st.session_state["show_admin_panel"] = not st.session_state["show_admin_panel"]
        st.rerun()

    if st.session_state["show_admin_panel"]:
        st.markdown("### ⚙️ Персонализиране на категориите")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            current_pet_opt = st.session_state.get("custom_pet_name", "Куче")
            pet_options = ["Куче", "Котка", "Домашен любимец"]
            pet_idx = pet_options.index(current_pet_opt) if current_pet_opt in pet_options else 0
            chosen_pet = st.selectbox("Категория 'Куче' да пише:", pet_options, index=pet_idx)
            if chosen_pet != current_pet_opt:
                st.session_state["custom_pet_name"] = chosen_pet
                st.rerun()

        with col_c2:
            current_hotel_opt = st.session_state.get("custom_hotel_name", "Нощувки/Хотел")
            hotel_toggle = st.toggle("Детайлни имена за Хотел", value=(current_hotel_opt == "Хотелски такси"))
            new_hotel = "Хотелски такси" if hotel_toggle else "Нощувки/Хотел"
            new_deposit = "Депозит за резервация" if hotel_toggle else "Депозит/Резервация"
            if new_hotel != current_hotel_opt:
                st.session_state["custom_hotel_name"] = new_hotel
                st.session_state["custom_deposit_name"] = new_deposit
                st.rerun()
