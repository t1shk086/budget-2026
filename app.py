import streamlit as st
import pandas as pd
import datetime as dt
import os
import io
import html
import base64
import plotly.graph_objects as go

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="PixelApp Premium",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"

DEFAULT_CATEGORIES = [
    "Хотел/Нощувки",
    "Храна и напитки",
    "Транспорт",
    "Куче",
    "Други",
]

DATA_COLUMNS = [
    "trip_id", "date", "amount", "category",
    "description", "type", "current_km"
]
SETTINGS_COLUMNS = [
    "trip_id", "budget", "start_date", "end_date",
    "car_trip", "start_km", "end_km"
]

# ============================================================
# DATA HELPERS
# ============================================================
def ensure_file(path, columns):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def read_csv_safe(path, columns):
    ensure_file(path, columns)
    try:
        df = pd.read_csv(path)
    except Exception:
        df = pd.DataFrame(columns=columns)

    for col in columns:
        if col not in df.columns:
            df[col] = 0.0 if col in {"amount", "current_km", "budget", "start_km", "end_km"} else ""

    return df


def save_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8-sig")


def clean_trip_id(value):
    return str(value).strip().replace(" ", "_")


def trip_label(value):
    return str(value).replace("_", " ")


def money(value):
    return f"{float(value):,.2f} €"


def get_settings(df_settings, trip_id):
    row = df_settings[df_settings["trip_id"].astype(str) == str(trip_id)]
    if row.empty:
        return {
            "budget": 1500.0,
            "start_date": "",
            "end_date": "",
            "car_trip": False,
            "start_km": 0.0,
            "end_km": 0.0,
        }
    r = row.iloc[0]
    return {
        "budget": float(pd.to_numeric(r.get("budget", 1500), errors="coerce") or 1500),
        "start_date": str(r.get("start_date", "")),
        "end_date": str(r.get("end_date", "")),
        "car_trip": str(r.get("car_trip", "")).lower() in {"true", "1", "yes"},
        "start_km": float(pd.to_numeric(r.get("start_km", 0), errors="coerce") or 0),
        "end_km": float(pd.to_numeric(r.get("end_km", 0), errors="coerce") or 0),
    }


def all_trip_ids(df_data, df_settings):
    values = []
    for df in (df_settings, df_data):
        if "trip_id" in df.columns:
            values.extend(df["trip_id"].dropna().astype(str).tolist())
    return list(dict.fromkeys([x for x in values if x.strip()]))


def get_trip_df(df_data, trip_id):
    if df_data.empty:
        return pd.DataFrame(columns=DATA_COLUMNS)
    df = df_data[df_data["trip_id"].astype(str) == str(trip_id)].copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["current_km"] = pd.to_numeric(df["current_km"], errors="coerce").fillna(0.0)
    df["date"] = df["date"].fillna("").astype(str)
    df["category"] = df["category"].fillna("Други").astype(str)
    df["description"] = df["description"].fillna("").astype(str)
    return df


def add_expense(df_data, trip_id, amount, category, description, expense_date, current_km=0):
    row = {
        "trip_id": trip_id,
        "date": expense_date,
        "amount": float(amount),
        "category": category,
        "description": description or "Без описание",
        "type": "expense",
        "current_km": float(current_km or 0),
    }
    return pd.concat([df_data, pd.DataFrame([row])], ignore_index=True)


def make_download_link(data, filename, label):
    encoded = base64.b64encode(data).decode("utf-8")
    return (
        f'<a class="download-link" download="{html.escape(filename)}" '
        f'href="data:text/csv;base64,{encoded}">{html.escape(label)}</a>'
    )


# ============================================================
# FILES
# ============================================================
ensure_file(DATA_FILE, DATA_COLUMNS)
ensure_file(SETTINGS_FILE, SETTINGS_COLUMNS)

df_data = read_csv_safe(DATA_FILE, DATA_COLUMNS)
df_settings = read_csv_safe(SETTINGS_FILE, SETTINGS_COLUMNS)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "current_trip": None,
    "current_tab": "home",
    "expense_form_open": False,
    "flash_message": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# If a saved trip exists but the current session is empty, stay on home.
TRIPS = all_trip_ids(df_data, df_settings)

# ============================================================
# PREMIUM MOBILE-FIRST CSS
# ============================================================
st.markdown("""
<style>
:root {
    --bg: #070b11;
    --panel: #0e151f;
    --panel2: #111b27;
    --line: rgba(255,255,255,.08);
    --muted: #7e8da3;
    --text: #f4f7fb;
    --blue: #2798ff;
    --cyan: #00d7ff;
    --green: #20d49a;
    --orange: #ff9f43;
    --red: #ff5c67;
    --purple: #a66cff;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
}

[data-testid="stAppViewContainer"] > .main {
    padding-bottom: 92px;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    max-width: 760px !important;
    padding: 12px 14px 105px !important;
}

h1, h2, h3, h4, p {
    color: var(--text);
}

[data-testid="stMarkdownContainer"] p {
    margin-bottom: .35rem;
}

.px-top {
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding: 5px 2px 13px;
    border-bottom: 1px solid var(--line);
    margin-bottom: 12px;
}

.px-brand {
    font-size: 18px;
    font-weight: 850;
    letter-spacing: -.3px;
}

.px-brand span {
    color: var(--blue);
}

.px-icon {
    width: 35px;
    height: 35px;
    border-radius: 11px;
    display:flex;
    align-items:center;
    justify-content:center;
    background: linear-gradient(135deg,#1d75db,#38bdf8);
    box-shadow: 0 5px 20px rgba(39,152,255,.25);
}

.px-trip {
    background: linear-gradient(135deg,#111d2a,#0d151f);
    border:1px solid var(--line);
    border-radius:16px;
    padding:13px 14px;
    margin-bottom:12px;
}

.px-trip-title {
    font-size:15px;
    font-weight:800;
}

.px-trip-sub {
    color:var(--muted);
    font-size:11px;
    margin-top:3px;
}

.premium-card {
    background: linear-gradient(145deg,#101924,#0b1119);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 16px;
    margin: 0 0 12px;
    box-shadow: 0 12px 32px rgba(0,0,0,.22);
}

.section-title {
    font-size: 15px;
    font-weight: 800;
    margin-bottom: 10px;
}

.muted {
    color: var(--muted);
    font-size: 11px;
}

.big-value {
    font-size: 29px;
    font-weight: 900;
    letter-spacing: -1px;
}

.small-value {
    font-size: 17px;
    font-weight: 800;
}

.stat-grid {
    display:grid;
    grid-template-columns: repeat(2,1fr);
    gap:9px;
}

.stat {
    background: rgba(255,255,255,.025);
    border:1px solid rgba(255,255,255,.055);
    border-radius:14px;
    padding:12px;
}

.progress {
    height:9px;
    background:#1b2634;
    border-radius:99px;
    overflow:hidden;
    margin-top:7px;
}

.progress > div {
    height:100%;
    border-radius:99px;
    background:linear-gradient(90deg,var(--cyan),var(--blue));
}

.category-row {
    padding: 8px 0 4px;
}

.category-head {
    display:flex;
    justify-content:space-between;
    font-size:12px;
}

.expense-row {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    padding:10px 0;
    border-bottom:1px solid rgba(255,255,255,.05);
}

.expense-row:last-child { border-bottom:0; }

.expense-title {
    font-size:12px;
    font-weight:700;
}

.expense-sub {
    color:var(--muted);
    font-size:10px;
    margin-top:2px;
}

.expense-amount {
    font-size:13px;
    font-weight:800;
    white-space:nowrap;
}

.rank-row {
    display:flex;
    align-items:center;
    gap:10px;
    padding:11px 0;
    border-bottom:1px solid rgba(255,255,255,.05);
}

.rank-icon {
    width:37px;
    height:37px;
    border-radius:12px;
    background:rgba(255,255,255,.05);
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:19px;
}

.rank-main { flex:1; }
.rank-title { font-size:12px; font-weight:800; }
.rank-sub { font-size:10px; color:var(--muted); margin-top:2px; }
.rank-value { font-size:13px; font-weight:850; }

.bottom-spacer { height: 70px; }

.nav-shell {
    position:fixed;
    left:50%;
    transform:translateX(-50%);
    bottom:0;
    width:min(760px,100%);
    padding:8px 10px calc(8px + env(safe-area-inset-bottom));
    background:rgba(8,13,20,.96);
    border-top:1px solid var(--line);
    backdrop-filter:blur(18px);
    z-index:9999;
}

.nav-label {
    text-align:center;
    font-size:9px;
    color:#7d8ba0;
    margin-top:1px;
}

.download-link {
    display:block;
    text-align:center;
    padding:12px;
    border-radius:13px;
    background:#142131;
    color:#fff !important;
    text-decoration:none !important;
    border:1px solid var(--line);
    font-weight:700;
    margin-top:8px;
}

@media (min-width: 900px) {
    .block-container {
        max-width: 820px !important;
        padding-left: 24px !important;
        padding-right: 24px !important;
    }
}

@media (max-width: 520px) {
    .block-container {
        padding-left:10px !important;
        padding-right:10px !important;
    }
    .premium-card { padding:14px; border-radius:16px; }
    .big-value { font-size:26px; }
}

/* Streamlit controls */
div[data-baseweb="select"] > div,
div[data-baseweb="input"],
div[data-baseweb="textarea"] {
    background:#0f1823 !important;
    border-color:var(--line) !important;
    border-radius:13px !important;
}

div[data-testid="stNumberInput"] button {
    border-radius:0 !important;
}

button[kind] {
    border-radius:13px !important;
    min-height:42px !important;
}

.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#1477e9,#1d9bf0) !important;
    border:0 !important;
}

[data-testid="stMetric"] {
    background:#101923;
    border:1px solid var(--line);
    border-radius:14px;
    padding:10px;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# NAVIGATION
# ============================================================
def set_tab(tab):
    st.session_state.current_tab = tab


def nav_bar():
    st.markdown("<div class='nav-shell'>", unsafe_allow_html=True)
    n1, n2, n3, n4, n5 = st.columns(5, gap="small")

    with n1:
        if st.button("⌂", key="nav_home", use_container_width=True):
            set_tab("home")
            st.rerun()
        st.markdown("<div class='nav-label'>Начало</div>", unsafe_allow_html=True)

    with n2:
        disabled = st.session_state.current_trip is None
        if st.button("▤", key="nav_expenses", use_container_width=True, disabled=disabled):
            set_tab("expenses")
            st.rerun()
        st.markdown("<div class='nav-label'>Разходи</div>", unsafe_allow_html=True)

    with n3:
        if st.button("＋", key="nav_add", use_container_width=True, type="primary"):
            if st.session_state.current_trip:
                set_tab("expenses")
                st.session_state.expense_form_open = True
            else:
                set_tab("home")
            st.rerun()
        st.markdown("<div class='nav-label'>Добави</div>", unsafe_allow_html=True)

    with n4:
        if st.button("⌖", key="nav_map", use_container_width=True, disabled=disabled):
            set_tab("map")
            st.rerun()
        st.markdown("<div class='nav-label'>Карта</div>", unsafe_allow_html=True)

    with n5:
        if st.button("•••", key="nav_more", use_container_width=True):
            set_tab("more")
            st.rerun()
        st.markdown("<div class='nav-label'>Още</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def top_bar():
    st.markdown("""
    <div class="px-top">
        <div style="display:flex;align-items:center;gap:9px;">
            <div class="px-icon">🐾</div>
            <div class="px-brand">Pixel<span>App</span></div>
        </div>
        <div style="font-size:18px;">♧</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# CHART HELPERS
# ============================================================
def chart_layout(fig, height=250):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=25, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce5f0", size=11),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
        hoverlabel=dict(bgcolor="#101923", font_color="#fff"),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="rgba(255,255,255,.06)",
        tickfont=dict(color="#7e8da3"),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,.055)",
        zeroline=False,
        tickfont=dict(color="#7e8da3"),
    )
    return fig


def budget_donut(spent, remaining, pct):
    if spent <= 0 and remaining <= 0:
        spent, remaining = 0.001, 1

    fig = go.Figure(go.Pie(
        labels=["Изразходвано", "Оставащо"],
        values=[spent, remaining],
        hole=.73,
        sort=False,
        textinfo="none",
        marker=dict(
            colors=["#20d49a" if pct < 80 else "#ff5c67", "#1b2735"],
            line=dict(color="#0b1119", width=2)
        )
    ))
    fig.update_layout(
        height=205,
        showlegend=False,
        margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.add_annotation(
        text=f"<b>{pct}%</b><br><span style='font-size:11px'>изразходвано</span>",
        x=.5, y=.5, showarrow=False,
        font=dict(size=26, color="#fff")
    )
    return fig


def daily_chart(df_trip):
    if df_trip.empty:
        return None
    grouped = df_trip.groupby("date", sort=False)["amount"].sum().reset_index()
    grouped.columns = ["Дата", "Разход"]
    fig = go.Figure(go.Bar(
        x=grouped["Дата"],
        y=grouped["Разход"],
        text=[f"{x:.0f} €" for x in grouped["Разход"]],
        textposition="outside",
        marker=dict(color="#18bde5"),
        hovertemplate="%{x}<br>%{y:.2f} €<extra></extra>",
    ))
    fig.update_layout(title="Разход по дни", showlegend=False)
    return chart_layout(fig, 255)


def category_chart(df_trip):
    grouped = df_trip.groupby("category")["amount"].sum().reset_index()
    grouped = grouped[grouped["amount"] > 0]
    if grouped.empty:
        return None
    fig = go.Figure(go.Pie(
        labels=grouped["category"],
        values=grouped["amount"],
        hole=.58,
        textinfo="percent",
        hovertemplate="%{label}<br>%{value:.2f} €<extra></extra>",
    ))
    fig.update_layout(title="Разходи по категории")
    return chart_layout(fig, 260)


# ============================================================
# HOME
# ============================================================
def page_home():
    global df_data, df_settings
    top_bar()

    st.markdown("""
    <div style="padding:5px 2px 12px;">
        <div class="muted">TRAVEL MANAGER</div>
        <div style="font-size:25px;font-weight:900;margin-top:2px;">Моите пътувания</div>
    </div>
    """, unsafe_allow_html=True)

    if TRIPS:
        st.markdown("<div class='section-title'>Последни пътувания</div>", unsafe_allow_html=True)

        for idx, trip in enumerate(TRIPS):
            settings = get_settings(df_settings, trip)
            trip_df = get_trip_df(df_data, trip)
            total = trip_df["amount"].sum()
            days = 0

            if settings["start_date"] and settings["end_date"]:
                try:
                    s = pd.to_datetime(settings["start_date"], dayfirst=True)
                    e = pd.to_datetime(settings["end_date"], dayfirst=True)
                    days = max(1, (e - s).days + 1)
                except Exception:
                    days = 0

            st.markdown(
                f"""
                <div class="px-trip">
                    <div class="px-trip-title">🌴 {html.escape(trip_label(trip))}</div>
                    <div class="px-trip-sub">
                        {html.escape(settings["start_date"] or "")}
                        {" → " if settings["start_date"] and settings["end_date"] else ""}
                        {html.escape(settings["end_date"] or "")}
                        {" • " + str(days) + " дни" if days else ""}
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-top:10px;">
                        <span class="muted">Разходи</span>
                        <b>{money(total)}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Отвори • {trip_label(trip)}",
                key=f"open_trip_{idx}",
                use_container_width=True,
                type="primary" if idx == 0 else "secondary",
            ):
                st.session_state.current_trip = trip
                st.session_state.current_tab = "expenses"
                st.rerun()
    else:
        st.info("Все още няма записани пътувания.")

    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>＋ Ново пътуване</div>", unsafe_allow_html=True)

    with st.form("new_trip_form", clear_on_submit=True):
        destination = st.text_input(
            "Дестинация",
            placeholder="напр. Бургас → Гърция 2026",
        )
        budget = st.number_input(
            "Планиран бюджет (€)",
            min_value=0.0,
            value=1500.0,
            step=50.0,
        )
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("Начало", value=dt.date.today())
        with c2:
            end = st.date_input("Край", value=dt.date.today())

        car_trip = st.checkbox("Пътуването е с автомобил")
        submitted = st.form_submit_button(
            "🚀 Създай пътуване",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not destination.strip():
            st.error("Въведи дестинация.")
        elif end < start:
            st.error("Крайната дата не може да е преди началната.")
        else:
            trip_id = clean_trip_id(destination)
            existing_settings = df_settings[
                df_settings["trip_id"].astype(str) == trip_id
            ]

            if existing_settings.empty:
                new_setting = pd.DataFrame([{
                    "trip_id": trip_id,
                    "budget": float(budget),
                    "start_date": start.strftime("%d.%m.%Y"),
                    "end_date": end.strftime("%d.%m.%Y"),
                    "car_trip": bool(car_trip),
                    "start_km": 0.0,
                    "end_km": 0.0,
                }])
                df_settings = pd.concat(
                    [df_settings, new_setting], ignore_index=True
                )
                save_csv(df_settings, SETTINGS_FILE)

            if not (df_data["trip_id"].astype(str) == trip_id).any():
                init_row = pd.DataFrame([{
                    "trip_id": trip_id,
                    "date": start.strftime("%d.%m"),
                    "amount": 0.0,
                    "category": "Други",
                    "description": "Инициализация",
                    "type": "expense",
                    "current_km": 0.0,
                }])
                df_data = pd.concat([df_data, init_row], ignore_index=True)
                save_csv(df_data, DATA_FILE)

            st.session_state.current_trip = trip_id
            st.session_state.current_tab = "expenses"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# EXPENSES / DASHBOARD
# ============================================================
def page_expenses():
    global df_data, df_settings

    trip_id = st.session_state.current_trip
    if not trip_id:
        st.session_state.current_tab = "home"
        st.rerun()

    settings = get_settings(df_settings, trip_id)
    df_trip = get_trip_df(df_data, trip_id)

    top_bar()

    st.markdown(
        f"""
        <div class="px-trip">
            <div class="px-trip-title">🌴 {html.escape(trip_label(trip_id))}</div>
            <div class="px-trip-sub">
                {html.escape(settings["start_date"])} → {html.escape(settings["end_date"])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total = float(df_trip["amount"].sum())
    budget = max(0.0, settings["budget"])
    remaining = max(0.0, budget - total)
    pct = min(100, int(round((total / budget) * 100))) if budget else 0

    # Budget card
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Бюджет на пътуването</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='muted'>Планиран бюджет</div><div class='big-value'>{money(budget)}</div>", unsafe_allow_html=True)

    st.plotly_chart(
        budget_donut(total, remaining, pct),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="budget_donut",
    )

    st.markdown(
        f"""
        <div class="stat-grid">
            <div class="stat">
                <div class="muted">ИЗРАЗХОДВАНО</div>
                <div class="small-value" style="color:#ff5c67">{money(total)}</div>
            </div>
            <div class="stat">
                <div class="muted">ОСТАВАТ</div>
                <div class="small-value" style="color:#20d49a">{money(remaining)}</div>
            </div>
        </div>
        <div class="progress"><div style="width:{pct}%"></div></div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if pct >= 80:
        st.warning(f"Внимание: изразходвани са {pct}% от бюджета.")
    elif pct >= 60:
        st.info(f"Изразходвани са {pct}% от бюджета.")

    # Quick expense
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>＋ Бързо добавяне на разход</div>", unsafe_allow_html=True)

    with st.form("expense_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            amount = st.number_input(
                "Сума (€)",
                min_value=0.0,
                value=0.0,
                step=5.0,
            )
        with c2:
            expense_date = st.date_input("Дата", value=dt.date.today())

        category = st.selectbox("Категория", DEFAULT_CATEGORIES)
        description = st.text_input(
            "Описание",
            placeholder="напр. Вечеря в таверна",
        )

        km = 0.0
        if settings["car_trip"]:
            km = st.number_input(
                "Текущ километраж",
                min_value=0.0,
                value=0.0,
                step=1.0,
            )

        save_exp = st.form_submit_button(
            "💾 Запиши разхода",
            use_container_width=True,
            type="primary",
        )

    if save_exp:
        if amount <= 0:
            st.error("Въведи сума по-голяма от 0.")
        else:
            df_data = add_expense(
                df_data,
                trip_id,
                amount,
                category,
                description,
                expense_date.strftime("%d.%m"),
                km,
            )
            save_csv(df_data, DATA_FILE)
            st.success("Разходът е добавен.")
            st.session_state.expense_form_open = False
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Category budget
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Бюджет по категории</div>", unsafe_allow_html=True)

    category_limit = budget / len(DEFAULT_CATEGORIES) if DEFAULT_CATEGORIES else budget
    for cat in DEFAULT_CATEGORIES:
        spent = float(df_trip.loc[df_trip["category"] == cat, "amount"].sum())
        cpct = min(100, int(round(spent / category_limit * 100))) if category_limit else 0
        st.markdown(
            f"""
            <div class="category-row">
                <div class="category-head">
                    <span>{html.escape(cat)}</span>
                    <span class="muted">{spent:.2f} € / {category_limit:.0f} €</span>
                </div>
                <div class="progress"><div style="width:{cpct}%;"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Charts
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Анализ</div>", unsafe_allow_html=True)

    daily = daily_chart(df_trip[df_trip["amount"] > 0])
    if daily:
        st.plotly_chart(
            daily,
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
            key="daily_chart",
        )
    else:
        st.info("Добави разход, за да се появи графиката по дни.")

    cat_fig = category_chart(df_trip[df_trip["amount"] > 0])
    if cat_fig:
        st.plotly_chart(
            cat_fig,
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
            key="category_chart",
        )
    else:
        st.info("Няма разходи по категории за визуализиране.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Recent expenses
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Последни разходи</div>", unsafe_allow_html=True)

    visible = df_trip[df_trip["amount"] > 0].tail(10).iloc[::-1]
    if visible.empty:
        st.caption("Все още няма реални разходи.")
    else:
        for row_idx, row in visible.iterrows():
            st.markdown(
                f"""
                <div class="expense-row">
                    <div>
                        <div class="expense-title">{html.escape(str(row["description"]))}</div>
                        <div class="expense-sub">{html.escape(str(row["category"]))} • {html.escape(str(row["date"]))}</div>
                    </div>
                    <div class="expense-amount">{float(row["amount"]):,.2f} €</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.caption("За пълна история използвай „Още → История“.")

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# MAP
# ============================================================
def page_map():
    top_bar()
    st.markdown("<div class='section-title'>⌖ Карта на пътуването</div>", unsafe_allow_html=True)

    if not st.session_state.current_trip:
        st.info("Първо избери пътуване.")
        return

    settings = get_settings(df_settings, st.session_state.current_trip)

    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='big-value'>{html.escape(trip_label(st.session_state.current_trip))}</div>",
        unsafe_allow_html=True,
    )

    if settings["car_trip"]:
        distance = max(0, settings["end_km"] - settings["start_km"])
        st.markdown(
            f"""
            <div class="stat-grid">
                <div class="stat"><div class="muted">НАЧАЛЕН КМ</div><div class="small-value">{settings["start_km"]:.0f}</div></div>
                <div class="stat"><div class="muted">КРАЕН КМ</div><div class="small-value">{settings["end_km"]:.0f}</div></div>
            </div>
            <div style="margin-top:10px;" class="muted">Изминати километри: <b style="color:#fff">{distance:.0f} км</b></div>
            """,
            unsafe_allow_html=True,
        )
        st.info("За интерактивна карта са нужни GPS координати или адреси. Текущият CSV формат не ги съхранява, затова тук не измислям локации.")
    else:
        st.info("Това пътуване не е отбелязано като автомобилно.")

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# MORE / HISTORY / RANKINGS / EXPORT
# ============================================================
def page_more():
    top_bar()

    st.markdown("""
    <div style="padding:5px 2px 12px;">
        <div class="muted">TOOLS</div>
        <div style="font-size:25px;font-weight:900;">Още</div>
    </div>
    """, unsafe_allow_html=True)

    choice = st.radio(
        "Раздел",
        ["🏆 Класации", "📜 История", "📤 Експорт", "⚙️ Настройки"],
        horizontal=True,
        label_visibility="collapsed",
        key="more_section",
    )

    if choice == "🏆 Класации":
        render_rankings()
    elif choice == "📜 История":
        render_history()
    elif choice == "📤 Експорт":
        render_export()
    else:
        render_settings()


def render_rankings():
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>🏆 Сравнение и класации</div>", unsafe_allow_html=True)

    trips = all_trip_ids(df_data, df_settings)
    records = []

    for trip in trips:
        d = get_trip_df(df_data, trip)
        s = get_settings(df_settings, trip)
        total = float(d["amount"].sum())

        days = 1
        if s["start_date"] and s["end_date"]:
            try:
                start = pd.to_datetime(s["start_date"], dayfirst=True)
                end = pd.to_datetime(s["end_date"], dayfirst=True)
                days = max(1, (end - start).days + 1)
            except Exception:
                days = 1

        km = max(0.0, s["end_km"] - s["start_km"])
        records.append({
            "trip": trip_label(trip),
            "total": total,
            "per_day": total / days,
            "km": km,
            "days": days,
        })

    if not records:
        st.info("Няма пътувания за сравнение.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df_rank = pd.DataFrame(records)

    tabs = st.tabs(["💶 Общо", "📅 На ден", "🚗 Километри"])
    with tabs[0]:
        row = df_rank.sort_values("total").iloc[0]
        st.success(f"🥇 Най-нисък общ разход: {row['trip']} — {money(row['total'])}")
    with tabs[1]:
        row = df_rank.sort_values("per_day").iloc[0]
        st.success(f"🥇 Най-нисък разход на ден: {row['trip']} — {row['per_day']:.2f} €/ден")
    with tabs[2]:
        row = df_rank.sort_values("km", ascending=False).iloc[0]
        if row["km"] > 0:
            st.success(f"🥇 Най-дълго пътуване: {row['trip']} — {row['km']:.0f} км")
        else:
            st.info("Добави начален и краен километраж в настройките.")

    awards = [
        ("💶", "Най-евтино общо", df_rank.sort_values("total").iloc[0]["trip"], f"{df_rank.sort_values('total').iloc[0]['total']:.2f} €"),
        ("📅", "Най-евтино на ден", df_rank.sort_values("per_day").iloc[0]["trip"], f"{df_rank.sort_values('per_day').iloc[0]['per_day']:.2f} €/ден"),
    ]

    car_df = df_rank[df_rank["km"] > 0]
    if not car_df.empty:
        r = car_df.sort_values("km", ascending=False).iloc[0]
        awards.append(("🚗", "Най-дълго", r["trip"], f"{r['km']:.0f} км"))

    for icon, title, trip, value in awards:
        st.markdown(
            f"""
            <div class="rank-row">
                <div class="rank-icon">{icon}</div>
                <div class="rank-main">
                    <div class="rank-title">{title}</div>
                    <div class="rank-sub">{html.escape(str(trip))}</div>
                </div>
                <div class="rank-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Всички пътувания</div>", unsafe_allow_html=True)

    table = df_rank.copy()
    table["Общо"] = table["total"].map(lambda x: f"{x:.2f} €")
    table["€/ден"] = table["per_day"].map(lambda x: f"{x:.2f} €")
    table["Км"] = table["km"].map(lambda x: f"{x:.0f}")
    st.dataframe(
        table[["trip", "Общо", "€/ден", "Км"]].rename(columns={"trip": "Пътуване"}),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_history():
    global df_data
    if not st.session_state.current_trip:
        st.info("Избери пътуване от Начало.")
        return

    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📜 История на разходите</div>", unsafe_allow_html=True)

    d = get_trip_df(df_data, st.session_state.current_trip)
    d = d[d["amount"] > 0].copy()

    if d.empty:
        st.info("Няма въведени разходи.")
    else:
        d["_idx"] = d.index
        d = d.iloc[::-1]

        for _, row in d.iterrows():
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f"**{html.escape(str(row['description']))}**  \n"
                    f"<span class='muted'>{html.escape(str(row['date']))} • {html.escape(str(row['category']))}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("🗑", key=f"delete_{int(row['_idx'])}"):
                    df_data = df_data.drop(index=int(row["_idx"])).reset_index(drop=True)
                    save_csv(df_data, DATA_FILE)
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_export():
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📤 Експорт</div>", unsafe_allow_html=True)

    trips = all_trip_ids(df_data, df_settings)
    if not trips:
        st.info("Няма данни за експорт.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.write("Можеш да свалиш данните директно от телефона или компютъра.")

    csv_all = df_data.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "📥 CSV — всички разходи",
        data=csv_all,
        file_name="PixelApp_expenses.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if st.session_state.current_trip:
        trip = get_trip_df(df_data, st.session_state.current_trip)
        csv_trip = trip.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            "📥 CSV — текущо пътуване",
            data=csv_trip,
            file_name=f"{clean_trip_id(st.session_state.current_trip)}_expenses.csv",
            mime="text/csv",
            use_container_width=True,
        )

        s = get_settings(df_settings, st.session_state.current_trip)
        total = get_trip_df(df_data, st.session_state.current_trip)["amount"].sum()

        report = f"""PixelApp — Отчет за пътуване
Пътуване: {trip_label(st.session_state.current_trip)}
Период: {s["start_date"]} - {s["end_date"]}
Бюджет: {s["budget"]:.2f} EUR
Изразходвано: {total:.2f} EUR
Оставащо: {max(0, s["budget"] - total):.2f} EUR
"""
        st.download_button(
            "📄 TXT — кратък отчет",
            data=report.encode("utf-8"),
            file_name=f"{clean_trip_id(st.session_state.current_trip)}_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_settings():
    global df_settings

    if not st.session_state.current_trip:
        st.info("Избери пътуване от Начало.")
        return

    trip_id = st.session_state.current_trip
    s = get_settings(df_settings, trip_id)

    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>⚙️ Настройки на пътуването</div>", unsafe_allow_html=True)

    with st.form("trip_settings_form"):
        budget = st.number_input("Бюджет (€)", min_value=0.0, value=float(s["budget"]), step=50.0)
        c1, c2 = st.columns(2)
        with c1:
            start_text = st.text_input("Начало", value=s["start_date"])
        with c2:
            end_text = st.text_input("Край", value=s["end_date"])

        car = st.checkbox("Автомобилно пътуване", value=s["car_trip"])

        c3, c4 = st.columns(2)
        with c3:
            start_km = st.number_input("Начален км", min_value=0.0, value=float(s["start_km"]), step=1.0)
        with c4:
            end_km = st.number_input("Краен км", min_value=0.0, value=float(s["end_km"]), step=1.0)

        save_settings = st.form_submit_button(
            "💾 Запази настройките",
            use_container_width=True,
            type="primary",
        )

    if save_settings:
        mask = df_settings["trip_id"].astype(str) == str(trip_id)
        values = {
            "trip_id": trip_id,
            "budget": float(budget),
            "start_date": start_text,
            "end_date": end_text,
            "car_trip": bool(car),
            "start_km": float(start_km),
            "end_km": float(end_km),
        }

        if mask.any():
            for key, value in values.items():
                df_settings.loc[mask, key] = value
        else:
            df_settings = pd.concat(
                [df_settings, pd.DataFrame([values])],
                ignore_index=True,
            )

        save_csv(df_settings, SETTINGS_FILE)
        st.success("Настройките са запазени.")
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>↩️ Навигация</div>", unsafe_allow_html=True)

    if st.button("🏠 Към Начало", use_container_width=True):
        st.session_state.current_tab = "home"
        st.rerun()

    if st.button("📊 Към Разходи", use_container_width=True):
        st.session_state.current_tab = "expenses"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# APP ROUTER
# ============================================================
if st.session_state.current_tab == "home":
    page_home()
elif st.session_state.current_tab == "expenses":
    page_expenses()
elif st.session_state.current_tab == "map":
    page_map()
elif st.session_state.current_tab == "more":
    page_more()
else:
    st.session_state.current_tab = "home"
    page_home()

nav_bar()
