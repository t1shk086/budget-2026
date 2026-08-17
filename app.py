import streamlit as st

# Настройка на страницата
st.set_page_config(
    page_title="Бюджет & Разход на Гориво", page_icon="🚗", layout="centered"
)

# Заглавие
st.title("🚗 Калкулатор за Разход на Гориво")

# Интерактивни полета за въвеждане на данни
st.subheader("⚙️ Параметри на пътуването")

col1, col2 = st.columns(2)

with col1:
  start_km = st.number_input(
      "Начален километраж (км)",
      value=130749,
      step=1,
      help="Километраж в началото на отсечката",
  )
  fuel_liters = st.number_input(
      "Заредено гориво (литри)",
      value=32.0,
      step=0.1,
      format="%.1f",
      help="Количество заредено гориво",
  )

with col2:
  distance_km = st.number_input(
      "Изминато разстояние (км)",
      value=200,
      step=1,
      help="Изминати километри за периода",
  )
  total_cost = st.number_input(
      "Обща цена (EUR)",
      value=50.00,
      step=0.5,
      format="%.2f",
      help="Обща сума за зареждането",
  )

# Математически изчисления
end_km = start_km + distance_km
consumption = (
    (fuel_liters / distance_km * 100) if distance_km > 0 else 0.0
)
price_per_liter = (total_cost / fuel_liters) if fuel_liters > 0 else 0.0

st.divider()

# Сглобяване на HTML & CSS таблото
dashboard_html = f"""
<style>
    .dashboard-container {{
        background-color: #121212;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .km-display-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        text-align: center;
        margin-bottom: 15px;
        background-color: #1a1a1a;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #2a2a2a;
    }}
    .km-box-lbl {{
        font-size: 11px;
        color: #aaa;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .km-box-val {{
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
    }}
    .progress-bar-bg {{
        background-color: #2a2a2a;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 20px;
    }}
    .progress-bar-fill {{
        height: 100%;
        background: linear-gradient(90deg, #00f2fe, #4facfe);
        width: 100%;
    }}
    .gauge-card {{
        background: linear-gradient(145deg, #1e1e1e, #141414);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #2a2a2a;
        box-shadow: 0 0 20px rgba(255, 75, 75, 0.15), inset 0 0 15px rgba(0,0,0,0.8);
    }}
    .gauge-value {{
        font-size: 48px;
        font-weight: 800;
        color: #ff4b4b;
        text-shadow: 0 0 12px rgba(255, 75, 75, 0.6);
        line-height: 1.1;
    }}
    .gauge-unit {{
        font-size: 13px;
        color: #aaa;
        margin-top: 4px;
    }}
    .dashboard-footer-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }}
    .dash-subcard {{
        background-color: #1a1a1a;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #2a2a2a;
    }}
</style>

<div class="dashboard-container">
    <div class="km-display-grid">
        <div>
            <div class="km-box-lbl">СТАРТ</div>
            <div class="km-box-val">{start_km:,} <span style="font-size:10px; color:#888;">км</span></div>
        </div>
        <div>
            <div class="km-box-lbl">ИЗМИНАТИ</div>
            <div class="km-box-val" style="color:#00f2fe;">{distance_km:,} <span style="font-size:10px; color:#00f2fe;">км</span></div>
        </div>
        <div>
            <div class="km-box-lbl">КРАЙНИ</div>
            <div class="km-box-val">{end_km:,} <span style="font-size:10px; color:#888;">км</span></div>
        </div>
    </div>

    <div class="progress-bar-bg">
        <div class="progress-bar-fill"></div>
    </div>

    <div class="gauge-card">
        <div class="gauge-value">{consumption:.1f}</div>
        <div class="gauge-unit">л / 100 км</div>
        <div style="font-size: 9px; color: #666; margin-top: 6px; text-transform:uppercase; letter-spacing:1px;">Среден Разход</div>
    </div>

    <div class="dashboard-footer-grid">
        <div class="dash-subcard">
            <div style="font-size:10px; color:#aaa; margin-bottom:4px;">💧 ЗАРЕДЕНО ГОРИВО</div>
            <div style="font-size:16px; font-weight:bold; color:#fff;">{fuel_liters:.1f} л</div>
        </div>
        <div class="dash-subcard">
            <div style="font-size:10px; color:#aaa; margin-bottom:4px;">💰 ОБЩО ТРАНСПОРТ</div>
            <div style="font-size:16px; font-weight:bold; color:#00ffcc;">{total_cost:.2f} EUR</div>
        </div>
    </div>
</div>
"""

# Изход на карточката в Streamlit
st.markdown(dashboard_html, unsafe_allow_html=True)

# Допълнителна метрика отдолу
st.caption(f"💡 Изчислена цена на литър: **{price_per_liter:.3f} EUR/л**")
