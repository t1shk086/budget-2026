import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go

# --- КОНФИГУРАЦИЯ НА СТРАНИЦАТА ---
st.set_page_config(page_title="PixelApp Premium", page_icon="🐾", layout="centered")

# --- БАЗА ДАННИ И КОНСТАНТИ ---
KATEGORII = ["Хотел/Нощувки", "Храна и напитки", "Транспорт", "Куче", "Други"]
DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"

# Инициализиране на файловете, ако не съществуват
for f, cols in [(DATA_FILE, ["trip_id", "date", "amount", "category", "description", "type", "current_km"]), 
                (SETTINGS_FILE, ["trip_id", "budget", "start_date", "end_date", "car_trip", "start_km", "end_km"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

# Инициализиране на сесийни състояния
if "current_trip" not in st.session_state: 
    st.session_state["current_trip"] = None
if "current_tab" not in st.session_state: 
    st.session_state["current_tab"] = "🏠 Начало"

# --- ПРЕМИУМ НЕОНОВ ТЪМЕН ДИЗАЙН (CSS) ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background: #090b10 !important;
        color: #fafafa !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Стилизиране на премиум контейнери */
    .premium-card {
        background: linear-gradient(135deg, #111622 0%, #0c1017 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 18px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-top: 5px;
    }
    
    .metric-label {
        font-size: 11px;
        font-weight: 700;
        color: #707e94;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Прогрес Барове */
    .progress-bg {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        height: 10px;
        width: 100%;
        margin-top: 8px;
        overflow: hidden;
        position: relative;
    }
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease-in-out;
    }
    
    /* Стилизиране на формите */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stDateInput {
        background: #111622 !important;
        border-radius: 14px !important;
    }
    
    /* Стилизиране на бутоните в долния навбар */
    .stButton > button {
        border-radius: 14px !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# Зареждане на списък с дестинации
try:
    existing_trips = list(pd.read_csv(DATA_FILE)["trip_id"].unique())
except:
    existing_trips = []
existing_trips = [t for t in existing_trips if pd.notna(t) and str(t).strip() != ""]

# ====================================================================
# МОДАЛЕН ДИАЛОГ ЗА СРЕДНИЯ БУТОН "+" (БЪРЗ РАЗХОД ОТВСЯКЪДЕ)
# ====================================================================
@st.dialog("➕ Добави бърз разход")
def quick_expense_modal():
    if not existing_trips:
        st.warning("Първо трябва да създадете поне едно пътуване от началния екран!")
        if st.button("Разбрах"):
            st.rerun()
        return

    st.markdown("Изберете дестинация и въведете разхода:")
    opts_map = {t.replace("_", " "): t for t in existing_trips}
    selected_trip_name = st.selectbox("Избери пътуване:", list(opts_map.keys()))
    target_trip_id = opts_map[selected_trip_name]
    
    amt_in = st.number_input("Сума (€):", min_value=0.01, step=5.0, value=None, placeholder="0.00 €")
    desc_in = st.text_input("Описание:", placeholder="напр. Магазин Лидл")
    cat_in = st.selectbox("Категория:", KATEGORII)
    
    if st.button("💾 Запиши разхода", use_container_width=True, type="primary"):
        if amt_in and amt_in > 0:
            df_all_data = pd.read_csv(DATA_FILE)
            new_row = pd.DataFrame([{
                "trip_id": target_trip_id,
                "date": datetime.datetime.now().strftime("%d.%m"),
                "amount": float(amt_in),
                "category": cat_in,
                "description": desc_in if desc_in else "Без описание",
                "type": "expense",
                "current_km": 0.0
            }])
            pd.concat([df_all_data, new_row]).to_csv(DATA_FILE, index=False)
            st.toast(f"Успешно добавен разход към {selected_trip_name}!", icon="✅")
            st.rerun()
        else:
            st.error("Моля, въведете валидна сума!")

# ====================================================================
# ЕКРАНИ НА ПРИЛОЖЕНИЕТО
# ====================================================================

# ЕКРАН 1: НАЧАЛО
if st.session_state["current_tab"] == "🏠 Начало":
    st.markdown("<h1 style='text-align:center; font-weight:900; background: linear-gradient(135deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px;'>🐾 PixelApp Premium</h1>", unsafe_allow_html=True)
    
    # Блок за Избор на активно пътуване
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label' style='margin-bottom:10px;'>🗂️ Избор на активно пътуване</div>", unsafe_allow_html=True)
    if existing_trips:
        opts = [t.replace("_", " ") for t in existing_trips]
        choice = st.selectbox("Изберете от хронологията:", opts, label_visibility="collapsed")
        if st.button("✔️ Отвори таблото на пътуването", use_container_width=True, type="primary"):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.session_state["current_tab"] = "📊 Разходи"
            st.rerun()
    else:
        st.info("Все още нямате записани почивки. Създайте нова от формата по-долу!")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Форма за Създаване на ново приключение
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label' style='margin-bottom:10px;'>➕ Ново приключение</div>", unsafe_allow_html=True)
    txt = st.text_input("Дестинация / Име на пътуването:", placeholder="напр. Гърция Септември 2026")
    b_input = st.number_input("Планиран Бюджет (EUR):", min_value=1.0, value=1500.0)
    
    if st.button("🚀 СЪЗДАЙ ПЪТУВАНЕ", use_container_width=True):
        if txt.strip():
            target_id = txt.strip().replace(" ", "_")
            df_s = pd.read_csv(SETTINGS_FILE)
            new_set = pd.DataFrame([{"trip_id": target_id, "budget": b_input, "start_date": datetime.date.today().strftime("%d.%m"), "end_date": "", "car_trip": False, "start_km": 0, "end_km": 0}])
            pd.concat([df_s, new_set]).to_csv(SETTINGS_FILE, index=False)
            
            # Добавяне на празен първоначален запис
            df_d = pd.read_csv(DATA_FILE)
            new_dat = pd.DataFrame([{"trip_id": target_id, "date": datetime.date.today().strftime("%d.%m"), "amount": 0.0, "category": "Други", "description": "Създаване на проект", "type": "expense", "current_km": 0.0}])
            pd.concat([df_d, new_dat]).to_csv(DATA_FILE, index=False)
            
            st.session_state["current_trip"] = target_id
            st.session_state["current_tab"] = "📊 Разходи"
            st.rerun()
        else:
            st.error("Моля, въведете име на дестинация!")
    st.markdown("</div>", unsafe_allow_html=True)

# ЕКРАН 2: ДЕТАЙЛНИ РАЗХОДИ ЗА ИЗБРАНОТО ПЪТУВАНЕ
elif st.session_state["current_tab"] == "📊 Разходи":
    trip_id = st.session_state["current_trip"]
    if not trip_id:
        st.warning("Моля, изберете или създайте пътуване от началния екран първо!")
        st.session_state["current_tab"] = "🏠 Начало"
        st.rerun()
        
    trip_name = trip_id.replace("_", " ")
    st.markdown(f"<h3 style='text-align:center; color:#707e94; font-weight:800; margin-bottom:20px;'>🌴 {trip_name}</h3>", unsafe_allow_html=True)
    
    # Зареждане на данни
    df_all_data = pd.read_csv(DATA_FILE)
    df_trip = df_all_data[df_all_data["trip_id"] == trip_id]
    
    df_all_sett = pd.read_csv(SETTINGS_FILE)
    sett_row = df_all_sett[df_all_sett["trip_id"] == trip_id]
    planned_budget = float(sett_row["budget"].iloc[0]) if not sett_row.empty else 1500.0
    
    total_spent = float(df_trip["amount"].sum())
    remaining_budget = max(0.0, planned_budget - total_spent)
    pct_spent = min(100, int((total_spent / planned_budget) * 100)) if planned_budget > 0 else 0
    
    # Поничка диаграма за прогреса на общия бюджет
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Оставащ Бюджет от общия лимит</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{remaining_budget:,.2f} €</div>", unsafe_allow_html=True)
    
    fig_donut = go.Figure(data=[go.Pie(
        labels=['Изразходван', 'Оставащ'],
        values=[total_spent, remaining_budget],
        hole=.73,
        marker=dict(colors=['#ff4b4b' if pct_spent > 85 else '#00f2fe', '#1a2234']),
        textinfo='none'
    )])
    fig_donut.update_layout(
        showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=170,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    fig_donut.add_annotation(text=f"{pct_spent}%", x=0.5, y=0.5, font_size=30, font_weight="bold", showarrow=False, font_color="white")
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown(f"<small style='color:#707e94;'>Изхарчени:</small><br><b style='color:#ff4b4b; font-size:16px;'>{total_spent:,.2f} €</b>", unsafe_allow_html=True)
    with col_b2:
        st.markdown(f"<small style='color:#707e94;'>Планирани общо:</small><br><b style='color:#fafafa; font-size:16px;'>{planned_budget:,.2f} €</b>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 2. ПРОГРЕС БАРОВЕ ПО КАТЕГОРИИ
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label' style='margin-bottom:10px;'>Бюджет по категории</div>", unsafe_allow_html=True)
    for cat in KATEGORII:
        cat_spent = float(df_trip[df_trip["category"] == cat]["amount"].sum())
        cat_limit = planned_budget / len(KATEGORII) 
        cat_pct = min(100, int((cat_spent / cat_limit) * 100)) if cat_limit > 0 else 0
        bar_color = "linear-gradient(90deg, #00f2fe, #4facfe)" if cat_pct < 75 else "linear-gradient(90deg, #ffaa00, #ff4b4b)"
        
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; margin-top:12px; font-size:13px;'>
            <span>{cat}</span>
            <span style='font-weight:bold; color:#707e94;'>{cat_spent:.2f} € / <span style='color:#fafafa;'>{cat_limit:.0f} €</span></span>
        </div>
        <div class='progress-bg'>
            <div class='progress-fill' style='width: {cat_pct}%; background: {bar_color};'></div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. ГРАФИКА: РАЗХОДИ ПО ДНИ
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label' style='margin-bottom:10px;'>Разходи по дни (EUR)</div>", unsafe_allow_html=True)
    df_days = df_trip.groupby("date")["amount"].sum().reset_index()
    if not df_days.empty and df_days["amount"].sum() > 0:
        fig_bar = px.bar(df_days, x="date", y="amount", text="amount", color_discrete_sequence=['#00f2fe'])
        fig_bar.update_traces(texttemplate='<b>%{text:.1f} €</b>', textposition='outside', marker_cornerradius=8)
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="", showgrid=False, tickfont=dict(color="#707e94")),
            yaxis=dict(title="", showgrid=False, showticklabels=False),
            margin=dict(l=10, r=10, t=30, b=10), height=200
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.caption("Няма регистрирани ежедневни разходи.")
    st.markdown("</div>", unsafe_allow_html=True)

# ЕКРАН 3: ГЛОБАЛНИ КЛАСАЦИИ
elif st.session_state["current_tab"] == "🏆 Класации":
    st.markdown("<h3 style='text-align:center; font-weight:800;'>🏆 Сравнения и Статистика</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='premium-card' style='border-left: 5px solid #ffd700;'>
        <div class='metric-label' style='color:#ffd700;'>🥇 НАЙ-ЕФЕКТИВНО ПЪТУВАНЕ</div>
        <div class='metric-value' style='font-size:24px;'>Румъния 2025</div>
        <div style='color:#707e94; font-size:13px; margin-top:5px;'>Среден разход: <b>62.40 € / ден</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label' style='margin-bottom:12px;'>Топ 4 класации</div>", unsafe_allow_html=True)
    awards = [
        {"icon": "🍃", "title": "Най-икономично гориво", "desc": "Гърция 2025 — 6.2 л/100 км", "c": "#2ebd59"},
        {"icon": "🛣️", "title": "Най-дълго трасе", "desc": "Италия 2024 — 2,845 км", "c": "#00f2fe"},
        {"icon": "🏨", "title": "Луксозна нощувка", "desc": "Испания 2025 — 158.00 € / нощ", "c": "#b800ff"},
        {"icon": "🍔", "title": "Гурме кулинария", "desc": "Париж 2026 — 312.40 €", "c": "#ffaa00"}
    ]
    for aw in awards:
        st.markdown(f"""
        <div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.04);'>
            <div style='display:flex; align-items:center; gap:12px;'>
                <span style='font-size:20px;'>{aw['icon']}</span>
                <div>
                    <div style='font-size:11px; color:#707e94; font-weight:700;'>{aw['title'].upper()}</div>
                    <div style='font-size:13px; color:#90a0b8;'>{aw['desc']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("👀 Преглед на всички филтри", key="view_all_filters", use_container_width=True):
        st.toast("Статистическите филтри са обновени!", icon="📊")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Списък и обобщена таблица
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label' style='margin-bottom:12px;'>Сравнителен анализ</div>", unsafe_allow_html=True)
    try:
        df_all = pd.read_csv(DATA_FILE)
        trips = [t for t in df_all["trip_id"].unique() if pd.notna(t) and str(t).strip() != ""]
        comp_data = []
        for t in trips:
            sub = df_all[df_all["trip_id"] == t]
            total = sub['amount'].sum()
            comp_data.append({"Дестинация": t.replace("_", " "), "Общ разход": f"{total:.2f} €", "Брой записи": len(sub)})
        if comp_data:
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
    except:
        st.caption("Няма данни.")
    st.markdown("</div>", unsafe_allow_html=True)

# ====================================================================
# ПОСТОЯНЕН МОБИЛЕН НАВБАР (НАЙ-ДОЛУ НА ЕКРАНА)
# ====================================================================
st.markdown("<br><br><br><br>", unsafe_allow_html=True)
nav_placeholder = st.container()
with nav_placeholder:
    st.markdown("<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #0d121f; padding: 10px 0; border-top: 1px solid rgba(255,255,255,0.08); z-index: 9999;'>", unsafe_allow_html=True)
    cols_nav = st.columns([1, 1, 1])
    
    with cols_nav[0]:
        if st.button("🏠 Начало", use_container_width=True, key="nav_home"):
            st.session_state["current_tab"] = "🏠 Начало"
            st.rerun()
            
    with cols_nav[1]:
        # Среден активен бутон "+" за бърз разход от всяка точка на приложението
        if st.button("➕", use_container_width=True, key="nav_add_quick"):
            quick_expense_modal()
            
    with cols_nav[2]:
        # Дезактивиран бутон за разходи, ако няма отворено конкретно пътуване
        is_disabled = st.session_state["current_trip"] is None
        if st.button("🏆 Класации" if is_disabled else "📊 Разходи", use_container_width=True, key="nav_dynamic"):
            st.session_state["current_tab"] = "🏆 Класации" if is_disabled else "📊 Разходи"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
