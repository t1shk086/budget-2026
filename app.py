# Изпълнявам скрипта, за да подготвя файла за вас
import os

code_content = """import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
import io

st.set_page_config(page_title="PixelApp Premium", page_icon="🐾", layout="centered")

# --- ПРЕМИУМ НЕОНОВ ТЪМЕН ДИЗАЙН (CSS) ---
st.markdown(\"\"\"
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background: #090b10 !important;
        color: #fafafa !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Скриване на Streamlit елементи за native app усещане */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Картите на категориите и статистиките */
    .premium-card {
        background: linear-gradient(135deg, #111622 0%, #0c1017 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 15px;
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
    
    /* Навигационната Долна Лента */
    .nav-wrapper {
        position: fixed;
        bottom: 0; left: 0; width: 100%;
        background: #0d121f;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        padding: 10px 0;
        z-index: 999;
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
        background: linear-gradient(90deg, #00f2fe, #4facfe);
    }
    
    /* Входове и Бутони */
    div.stSelectbox, div.stNumberInput, div.stTextInput {
        background: #111622 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
    }
    
    button {
        border-radius: 14px !important;
        font-weight: 600 !important;
    }
</style>
\"\"\", unsafe_allow_html=True)

# --- ИНТЕЛЕКТУАЛНО ЯДРО И БАЗА ДАННИ ---
KATEGORII = ["Хотел/Нощувки", "Храна и напитки", "Транспорт", "Куче", "Други"]
DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"

for f, cols in [(DATA_FILE, ["trip_id","date","amount","category","description","type","current_km"]), 
                (SETTINGS_FILE, ["trip_id","budget","start_date","end_date","car_trip","start_km","end_km"])]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False, encoding="utf-8")

# Сесиен мениджмънт
if "current_trip" not in st.session_state: st.session_state["current_trip"] = None
if "current_tab" not in st.session_state: st.session_state["current_tab"] = "🏠 Начало"

# --- ДОЛНА МОБИЛНА НАВИГАЦИОННА ЛЕНТА ---
st.markdown("<br><br><br>", unsafe_allow_html=True) # Резерва за съдържанието
cols_nav = st.columns(3)
with cols_nav[0]:
    if st.button("🏠 Начало", use_container_width=True): st.session_state["current_tab"] = "🏠 Начало"
with cols_nav[1]:
    if st.button("📊 Разходи", use_container_width=True, disabled=(st.session_state["current_trip"] is None)): 
        st.session_state["current_tab"] = "📊 Разходи"
with cols_nav[2]:
    if st.button("🏆 Класации", use_container_width=True): st.session_state["current_tab"] = "🏆 Класации"

# ====================================================================
# ЕКРАН 1: НАЧАЛО (ИЗБОР ИЛИ СЪЗДАВАНЕ НА ПЪТУВАНЕ)
# ====================================================================
if st.session_state["current_tab"] == "🏠 Начало":
    st.markdown("<h1 style='text-align:center; font-weight:900; background: linear-gradient(135deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🐾 PixelApp Premium</h1>", unsafe_allow_html=True)
    
    # Списък с активни дестинации
    try:
        existing = list(pd.read_csv(DATA_FILE)["trip_id"].unique())
    except:
        existing = []
        
    existing = [t for t in existing if pd.notna(t) and str(t).strip() != ""]
    
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.subheader("🗂️ Избор на пътуване")
    if existing:
        opts = [t.replace("_", " ") for t in existing]
        choice = st.selectbox("Изберете от хронологията:", opts, label_visibility="collapsed")
        if st.button("✔️ Отвори таблото", use_container_width=True, type="primary"):
            st.session_state["current_trip"] = choice.replace(" ", "_")
            st.session_state["current_tab"] = "📊 Разходи"
            st.rerun()
    else:
        st.info("Все още нямате записани почивки. Създайте нова по-долу!")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Форма за ново приключение
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.subheader("➕ Ново приключение")
    txt = st.text_input("Дестинация:", placeholder="напр. Бургас -> Гърция 2026")
    b_input = st.number_input("Планиран Бюджет (EUR):", value=1500.0)
    
    if st.button("🚀 СЪЗДАЙ", use_container_width=True):
        if txt.strip():
            target_id = txt.strip().replace(" ", "_")
            df_s = pd.read_csv(SETTINGS_FILE)
            new_set = pd.DataFrame([{"trip_id": target_id, "budget": b_input, "start_date": "15.08", "end_date": "22.08"}])
            pd.concat([df_s, new_set]).to_csv(SETTINGS_FILE, index=False)
            
            # Първоначален запис, за да се инициализира
            df_d = pd.read_csv(DATA_FILE)
            new_dat = pd.DataFrame([{"trip_id": target_id, "date": "15.08", "amount": 0.0, "category": "Други", "description": "Инициализация", "type": "expense", "current_km": 0.0}])
            pd.concat([df_d, new_dat]).to_csv(DATA_FILE, index=False)
            
            st.session_state["current_trip"] = target_id
            st.session_state["current_tab"] = "📊 Разходи"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ====================================================================
# ЕКРАН 2: РАЗХОДИ И ПРОГРЕС (МАКЕТ 1 И 2)
# ====================================================================
elif st.session_state["current_tab"] == "📊 Разходи":
    trip_id = st.session_state["current_trip"]
    trip_name = trip_id.replace("_", " ")
    
    st.markdown(f"<h3 style='text-align:center; color:#707e94;'>🌴 {trip_name}</h3>", unsafe_allow_html=True)
    
    # Зареждане на данни
    df_all_data = pd.read_csv(DATA_FILE)
    df_trip = df_all_data[df_all_data["trip_id"] == trip_id]
    
    df_all_sett = pd.read_csv(SETTINGS_FILE)
    sett_row = df_all_sett[df_all_sett["trip_id"] == trip_id]
    planned_budget = float(sett_row["budget"].iloc[0]) if not sett_row.empty else 1500.0
    
    total_spent = float(df_trip["amount"].sum())
    remaining_budget = max(0.0, planned_budget - total_spent)
    pct_spent = min(100, int((total_spent / planned_budget) * 100)) if planned_budget > 0 else 0
    
    # 1. СЕКЦИЯ БЮДЖЕТ (МАКЕТ 1)
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Планиран Бюджет</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{planned_budget:,.2f} €</div>", unsafe_allow_html=True)
    
    # Премиум Donut Chart за оставащ бюджет
    fig_donut = go.Figure(data=[go.Pie(
        labels=['Изразходван', 'Оставащ'],
        values=[total_spent, remaining_budget],
        hole=.7,
        marker=dict(colors=['#ff4b4b' if pct_spent > 80 else '#00f2fe', '#111622']),
        textinfo='none'
    )])
    fig_donut.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=180,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    # Поставяне на процентите в центъра
    fig_donut.add_annotation(text=f"{pct_spent}%", x=0.5, y=0.5, font_size=32, font_weight="bold", showarrow=False, font_color="white")
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown(f"<small style='color:#707e94;'>Изразходвано:</small><br><b style='color:#ff4b4b; font-size:18px;'>{total_spent:,.2f} €</b>", unsafe_allow_html=True)
    with col_b2:
        st.markdown(f"<small style='color:#707e94;'>Остават:</small><br><b style='color:#2ebd59; font-size:18px;'>{remaining_budget:,.2f} €</b>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # БЪРЗО ДОБАВЯНЕ НА РАЗХОД С КАТЕГОРИИ
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("#### ➕ Добави бърз разход")
    amt_in = st.number_input("Сума (€):", min_value=0.0, step=5.0, value=None, placeholder="0.00 €")
    desc_in = st.text_input("Описание:", placeholder="напр. Вечеря в таверна")
    cat_in = st.selectbox("Категория:", KATEGORII)
    
    if st.button("💾 Запиши разхода", use_container_width=True, type="primary"):
        if amt_in and amt_in > 0:
            new_row = pd.DataFrame([{
                "trip_id": trip_id,
                "date": datetime.datetime.now().strftime("%d.%m"),
                "amount": float(amt_in),
                "category": cat_in,
                "description": desc_in if desc_in else "Без описание",
                "type": "expense",
                "current_km": 0.0
            }])
            pd.concat([df_all_data, new_row]).to_csv(DATA_FILE, index=False)
            st.success("Разходът е добавен успешно!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ====================================================================
    # ЧАСТ ОТ ЕКРАН 2: ПЛАНИРАН БЮДЖЕТ ПО КАТЕГОРИИ И РАЗХОДИ ПО ДНИ
    # ====================================================================

    # 2. ПЛАНИРАН БЮДЖЕТ ПО КАТЕГОРИИ (Прогрес ленти - Макет 1)
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("#### Бюджет по категории")

    for cat in KATEGORII:
        # Вземаме сбора на разходите за текущата категория за избраното пътуване
        cat_spent = float(df_trip[df_trip["category"] == cat]["amount"].sum())
        
        # Примерно пропорционално разпределение на лимита на категорията спрямо общия бюджет
        cat_limit = planned_budget / len(KATEGORII) 
        cat_pct = min(100, int((cat_spent / cat_limit) * 100)) if cat_limit > 0 else 0
        
        # Определяне на динамичен цвят на лентата в зависимост от натоварването на бюджета
        bar_color = "linear-gradient(90deg, #00f2fe, #4facfe)" if cat_pct < 75 else "linear-gradient(90deg, #ffaa00, #ff4b4b)"
        
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; margin-top:14px; font-size:13px;'>
            <span style='font-weight: 500;'>{cat}</span>
            <span style='font-weight:bold; color:#707e94;'>{cat_spent:.2f} € / <span style='color:#fafafa;'>{cat_limit:.0f} €</span></span>
        </div>
        <div class='progress-bg' style='background: rgba(255,255,255,0.05); border-radius: 10px; height: 10px; width: 100%; margin-top: 8px; overflow: hidden; position: relative;'>
            <div class='progress-fill' style='height: 100%; border-radius: 10px; width: {cat_pct}%; background: {bar_color}; transition: width 0.5s ease-in-out;'></div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


    # 3. РАЗХОДИ ПО ДНИ (Интерактивна хистограма - Макет 2)
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("#### Разходи по дни (EUR)")

    # Групиране на сумите по дати
    df_days = df_trip.groupby("date")["amount"].sum().reset_index()

    if not df_days.empty and df_days["amount"].sum() > 0:
        # Създаване на неон-зелена/неон-синя стълбовидна графика
        fig_bar = px.bar(
            df_days, 
            x="date", 
            y="amount", 
            text="amount", 
            color_discrete_sequence=['#00f2fe']
        )
        
        # Стилизиране на текста над стълбовете и заобляне на ъглите им
        fig_bar.update_traces(
            texttemplate='<b>%{text:.1f} €</b>', 
            textposition='outside', 
            marker_cornerradius=8,
            textfont=dict(color="white")
        )
        
        # Изчистване на фона на графиката, за да пасне на тъмния премиум режим
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="", showgrid=False, tickfont=dict(color="#707e94", size=11)),
            yaxis=dict(title="", showgrid=False, showticklabels=False),
            margin=dict(l=10, r=10, t=30, b=10),
            height=220
        )
        
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
    else:
        st.markdown("<p style='color:#707e94; font-size:13px; text-align:center; padding:20px;'>Все още няма регистрирани ежедневни разходи за този трип.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# 3. РАЗХОДИ ПО ДНИ (Интерактивна хистограма - Макет 2)
st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
st.markdown("#### Разходи по дни (EUR)")

# Групиране на сумите по дати
df_days = df_trip.groupby("date")["amount"].sum().reset_index()

if not df_days.empty and df_days["amount"].sum() > 0:
    # Създаване на неон-зелена/неон-синя стълбовидна графика
    fig_bar = px.bar(
        df_days, 
        x="date", 
        y="amount", 
        text="amount", 
        color_discrete_sequence=['#00f2fe']
    )
    
    # Стилизиране на текста над стълбовете и заобляне на ъглите им
    fig_bar.update_traces(
        texttemplate='<b>%{text:.1f} €</b>', 
        textposition='outside', 
        marker_cornerradius=8,
        textfont=dict(color="white")
    )
    
    # Изчистване на фона на графиката, за да пасне на тъмния премиум режим
    fig_bar.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="", showgrid=False, tickfont=dict(color="#707e94", size=11)),
        yaxis=dict(title="", showgrid=False, showticklabels=False),
        margin=dict(l=10, r=10, t=30, b=10),
        height=220
    )
    
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
else:
    st.markdown("<p style='color:#707e94; font-size:13px; text-align:center; padding:20px;'>Все още няма регистрирани ежедневни разходи за този трип.</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
# ====================================================================
# ЕКРАН 3: ИСТОРИЯ, СРАВНЕНИЯ И КЛАСАЦИИ (МАКЕТ 5)
# ====================================================================
elif st.session_state["current_tab"] == "🏆 Класации":
    st.markdown("<h3 style='text-align:center; font-weight:800; letter-spacing:0.5px;'>🏆 Сравнения и Класации</h3>", unsafe_allow_html=True)
    
    # 1. Сегментиран контрол за филтриране (Общо / Цена/км / Километри / На ден)
    chosen_filter = st.segmented_control(
        label="Филтриране на резултатите:",
        options=["Общо", "Цена/км", "Километри", "На ден"],
        default="Общо",
        key="global_leaderboard_filter",
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Главна акцентна карта (Най-евтино пътуване - Златен медал)
    st.markdown("""
    <div class='premium-card' style='border-left: 5px solid #ffd700; background: linear-gradient(135deg, #161b26 0%, #0c1017 100%);'>
        <div class='metric-label' style='color:#ffd700; font-size:10px; font-weight:800;'>🥇 НАЙ-ЕФЕКТИВНО ПЪТУВАНЕ</div>
        <div class='metric-value' style='font-size:24px; margin-top:2px;'>Румъния 2025</div>
        <div style='display:flex; justify-content:space-between; margin-top:8px; font-size:13px; color:#90a0b8;'>
            <span>Общо: <b>624.20 €</b></span>
            <span style='color:#2ebd59;'><b>62.40 € / ден</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Списък ТОП 6 КЛАСАЦИИ (Зала на славата от Макет 5)
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label' style='margin-bottom:15px;'>Топ 6 класации</div>", unsafe_allow_html=True)
    
    awards = [
        {"icon": "🍃", "title": "Най-икономично пътуване", "desc": "Гърция 2025", "val": "6.2 л/100 км", "color": "#2ebd59"},
        {"icon": "🚙", "title": "Най-дълго пътуване", "desc": "Италия 2024", "val": "2 845 км", "color": "#00f2fe"},
        {"icon": "🏨", "title": "Най-скъп хотел", "desc": "Испания 2025", "val": "158.00 € / нощувка", "color": "#b800ff"},
        {"icon": "🍔", "title": "Най-много за храна", "desc": "Париж 2026", "val": "312.40 €", "color": "#ffaa00"},
        {"icon": "📊", "title": "Най-добро съотношение", "desc": "Румъния 2025", "val": "86.20 € / ден", "color": "#ff4b4b"}
    ]
    
    for aw in awards:
        st.markdown(f"""
        <div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.04);'>
            <div style='display:flex; align-items:center; gap:12px;'>
                <span style='font-size:22px; background:rgba(255,255,255,0.03); padding:6px; border-radius:10px;'>{aw['icon']}</span>
                <div>
                    <div style='font-size:11px; color:#707e94; font-weight:700; letter-spacing:0.5px;'>{aw['title'].upper()}</div>
                    <div style='font-size:13px; color:#90a0b8;'>{aw['desc']}</div>
                </div>
            </div>
            <div style='font-size:14px; font-weight:700; color:{aw['color']}; text-align:right;'>
                {aw['val']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<button style='width:100%; background:transparent; border:1px solid rgba(255,255,255,0.1); color:#707e94; font-size:12px; padding:8px; border-radius:10px;'>👀 Виж всички класации</button>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 4. ВСИЧКИ ПЪТУВАНИЯ И ПЪЛНО СРАВНЕНИЕ (Долната таблица/списък)
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label' style='margin-bottom:15px;'>Всички пътувания</div>", unsafe_allow_html=True)
    
    try:
        df_all = pd.read_csv(DATA_FILE)
        trips = [t for t in df_all["trip_id"].unique() if pd.notna(t) and str(t).strip() != ""]
        
        if trips:
            comp_data = []
            for t in trips:
                sub_df = df_all[df_all["trip_id"] == t]
                total_spent = sub_df["amount"].sum()
                
                # Рендериране на малки персонални карти за бърз преглед на всяка дестинация
                st.markdown(f"""
                <div style='background:rgba(255,255,255,0.01); border:1px solid rgba(255,255,255,0.03); border-radius:12px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <div style='font-size:14px; font-weight:600;'>📍 {str(t).replace("_", " ")}</div>
                        <div style='font-size:11px; color:#707e94; margin-top:2px;'>15.08 - 22.08.2026 (8 дни)</div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='font-size:14px; font-weight:700; color:#00f2fe;'>{total_spent:.2f} €</div>
                        <div style='font-size:11px; color:#2ebd59;'>{(total_spent/8 if total_spent > 0 else 0):.2f} €/ден</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                comp_data.append({
                    "Дестинация": str(t).replace("_", " "),
                    "Общо": f"{total_spent:.2f} €",
                    "Разходи/Ден": f"{(total_spent/8 if total_spent > 0 else 0):.2f} €"
                })
                
            st.markdown("<br><div class='metric-label' style='margin-bottom:10px;'>Пълно Сравнение (Таблица)</div>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
            
        else:
            st.info("Няма намерени записи за сравнение.")
    except Exception as e:
        st.error("Грешка при зареждане на сравнителните данни.")
        
    st.markdown("<br><button style='width:100%; background:rgba(0, 242, 254, 0.1); border:1px solid rgba(0, 242, 254, 0.2); color:#00f2fe; font-size:13px; padding:10px; border-radius:12px; font-weight:600;'>📥 Експорт (PDF/CSV)</button>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
