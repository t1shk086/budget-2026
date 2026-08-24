import streamlit as st
from datetime import date
import json
from pathlib import Path


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Travel Manager",
    page_icon="✈️",
    layout="wide"
)


# =========================================================
# SESSION STATE & PERSISTENCE
# =========================================================

DATA_FILE = Path("trips.json")


def load_trips():
    if not DATA_FILE.exists():
        return {}

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))

        for trip in raw.values():
            trip["start_date"] = date.fromisoformat(trip["start_date"])
            trip["end_date"] = date.fromisoformat(trip["end_date"])

            for expense in trip.get("expenses", []):
                expense["date"] = date.fromisoformat(expense["date"])
                expense["is_fuel"] = expense.get("is_fuel", False)
                expense["fuel_liters"] = expense.get("fuel_liters", 0.0)
                expense["fuel_odometer"] = expense.get("fuel_odometer", 0.0)
                expense["fuel_full_tank"] = expense.get("fuel_full_tank", False)

        return raw
    except (json.JSONDecodeError, OSError, ValueError):
        return {}


def save_trips():
    serializable = {}
    for trip_id, trip in st.session_state.trips.items():
        serializable[trip_id] = {
            "destination": trip["destination"],
            "start_date": trip["start_date"].isoformat(),
            "end_date": trip["end_date"].isoformat(),
            "budget": trip["budget"],
            "expenses": [
                {
                    "amount": expense["amount"],
                    "category": expense["category"],
                    "date": expense["date"].isoformat(),
                    "note": expense["note"],
                    "is_fuel": expense.get("is_fuel", False),
                    "fuel_liters": expense.get("fuel_liters", 0.0),
                    "fuel_odometer": expense.get("fuel_odometer", 0.0),
                    "fuel_full_tank": expense.get("fuel_full_tank", False),
                }
                for expense in trip["expenses"]
            ],
        }

    DATA_FILE.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


FUEL_KEYWORDS = ("газ", "гориво", "зареждане", "бензин", "дизел")


def is_fuel_expense(text):
    text = (text or "").lower()
    return any(keyword in text for keyword in FUEL_KEYWORDS)


# =========================================================
# INITIAL STATE
# =========================================================

if "trips" not in st.session_state:
    st.session_state.trips = load_trips()

if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_trip" not in st.session_state:
    st.session_state.selected_trip = None

if "expense_trip" not in st.session_state:
    st.session_state.expense_trip = None


# =========================================================
# DATA HELPERS
# =========================================================

def total_expenses():
    return sum(
        expense["amount"]
        for trip in st.session_state.trips.values()
        for expense in trip["expenses"]
    )


def total_budget():
    return sum(trip["budget"] for trip in st.session_state.trips.values())


def trip_expenses(trip):
    return sum(expense["amount"] for expense in trip["expenses"])


def delete_expense(trip_id, expense_index):
    expenses = st.session_state.trips[trip_id]["expenses"]
    if 0 <= expense_index < len(expenses):
        del expenses[expense_index]
        save_trips()


# =========================================================
# NAVIGATION
# =========================================================

def go_home():
    st.session_state.page = "home"
    st.session_state.selected_trip = None
    st.session_state.expense_trip = None
    st.rerun()


def open_trip(trip_id):
    st.session_state.selected_trip = trip_id
    st.session_state.page = "trip"
    st.rerun()


def open_add_expense(trip_id=None):
    st.session_state.expense_trip = trip_id
    st.session_state.page = "add_expense"
    st.rerun()


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp, button, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.stApp {
    background: #08111a;
}

.block-container {
    max-width: 1080px;
    padding-top: 1.8rem;
    padding-bottom: 4rem;
}

section[data-testid="stSidebar"] {
    background: #09141f;
    border-right: 1px solid #1a2b3a;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

.stButton > button {
    width: 100%;
    min-height: 44px;
    border-radius: 12px;
    border: 1px solid #263c4f;
    background: #101e2a;
    color: #eef5f9;
    font-weight: 650;
    transition: background .18s ease, border-color .18s ease, transform .18s ease;
}

.stButton > button:hover {
    background: #15283a;
    border-color: #2b9cff;
    color: #ffffff;
    transform: translateY(-1px);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #147bd1, #239de5) !important;
    border: 1px solid #2aa9f0 !important;
    color: #ffffff !important;
    box-shadow: 0 8px 22px rgba(20,123,209,.22);
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1889e5, #2aaaf0) !important;
    border-color: #48b9f5 !important;
    color: #ffffff !important;
}

div[data-testid="stMetric"] {
    background: #0d1a26;
    border: 1px solid #1c3041;
    border-radius: 16px;
    padding: 14px 16px;
}

div[data-testid="stMetricLabel"] { color: #8fa1b2; }
div[data-testid="stMetricValue"] { color: #f4f8fb; }

div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
    background: #0d1925;
    border: 1px solid #22374a;
    border-radius: 10px;
}

div[data-baseweb="input"] input, div[data-baseweb="select"] * {
    color: #f4f8fb !important;
}

.tm-card {
    background: linear-gradient(145deg, #102130, #0c1823);
    border: 1px solid #203446;
    border-radius: 20px;
    padding: 20px;
    min-height: 116px;
    box-shadow: 0 10px 28px rgba(0,0,0,.18);
    box-sizing: border-box;
}

.tm-card-primary {
    border-color: #235d83;
    background: linear-gradient(145deg, #12314a, #0c1c29);
}

.tm-card-title {
    color: #f5f8fb;
    font-size: 1.12rem;
    font-weight: 750;
    margin-bottom: 6px;
}

.tm-card-text {
    color: #8fa1b2;
    font-size: .9rem;
    line-height: 1.45;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px;
}

hr { border-color: #1a2a39; }

@media (max-width: 700px) {
    .block-container { padding: 1rem; }
    .tm-card { min-height: auto; padding: 17px; }
    div[data-testid="stMetric"] { padding: 11px 12px; }
    div[data-testid="stMetricValue"] { font-size: 1.35rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div style="font-family:Inter,sans-serif; font-size:1.35rem; font-weight:800; letter-spacing:-.04em; color:#f4f8fb; line-height:1.15;">
            ✈️ Travel Manager
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Пътувания и разходи")
    st.divider()

    if st.button("⌂  Начало", use_container_width=True, key="nav_home"):
        go_home()

    if st.button("✈️  Пътувания", use_container_width=True, key="nav_trips"):
        st.session_state.page = "trips"
        st.rerun()

    if st.button("＋  Добави разход", use_container_width=True, key="nav_expense"):
        open_add_expense()

    st.divider()
    st.caption("Планиране")

    if st.button("📊  Анализи", use_container_width=True, key="nav_analysis"):
        st.session_state.page = "analytics"
        st.rerun()

    if st.button("🕘  История", use_container_width=True, key="nav_history"):
        st.session_state.page = "history"
        st.rerun()

    if st.button("⇄  Сравнение", use_container_width=True, key="nav_comparison"):
        st.session_state.page = "comparison"
        st.rerun()

    if st.button("⚙️  Настройки", use_container_width=True, key="nav_settings"):
        st.session_state.page = "settings"
        st.rerun()


# =========================================================
# PAGE ROUTING
# =========================================================

# --- HOME PAGE ---
if st.session_state.page == "home":
    st.markdown(
        """
        <div style="width:100%; padding:10px 0 24px 0;">
            <div style="color:#f4f8fb; font-family:Inter, sans-serif; font-size:clamp(32px, 5vw, 46px); font-weight:800; line-height:1.1; letter-spacing:-1.8px;">
                ✈️ Travel Manager
            </div>
            <div style="color:#9aaaba; font-family:Inter, sans-serif; font-size:16px; font-weight:500; line-height:1.5; margin-top:10px;">
                Всичко за твоите пътувания и разходи на едно място.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    expenses = total_expenses()
    budget = total_budget()
    remaining = budget - expenses

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("✈️ Пътувания", len(st.session_state.trips))
    with c2:
        st.metric("💳 Общо разходи", f"€{expenses:.2f}")
    with c3:
        st.metric("💰 Оставащ бюджет", f"€{remaining:.2f}")

    st.write("")

    st.markdown(
        """<div style="color:#f4f8fb; font-family:Inter, sans-serif; font-size:24px; font-weight:750; margin:8px 0 16px 0;">Бързи действия</div>""",
        unsafe_allow_html=True,
    )

    q1, q2 = st.columns(2)
    with q1:
        st.markdown(
            """
            <div class="tm-card tm-card-primary">
                <div class="tm-card-title">➕ Добави разход</div>
                <div class="tm-card-text">Бързо добавяне на разход към избрано пътуване.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Добави разход →", use_container_width=True, type="primary", key="quick_add"):
            open_add_expense()

    with q2:
        st.markdown(
            """
            <div class="tm-card">
                <div class="tm-card-title">✈️ Ново пътуване</div>
                <div class="tm-card-text">Създай ново пътуване и задай неговия бюджет.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Създай пътуване →", use_container_width=True, key="quick_trip"):
            st.session_state.page = "new_trip"
            st.rerun()

    st.write("")
    st.divider()

    st.markdown(
        """<div style="color:#f4f8fb; font-family:Inter, sans-serif; font-size:24px; font-weight:750; margin:8px 0 16px 0;">Моите пътувания</div>""",
        unsafe_allow_html=True,
    )

    if not st.session_state.trips:
        st.info("Все още нямаш пътувания. Създай първото си пътуване от бутона по-горе.")
    else:
        for trip_id, trip in st.session_state.trips.items():
            spent = trip_expenses(trip)
            trip_budget = trip["budget"]
            progress = min(spent / trip_budget, 1.0) if trip_budget > 0 else 0.0

            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"✈️ {trip['destination']}")
                    st.caption(f"{trip['start_date'].strftime('%d.%m.%Y')} – {trip['end_date'].strftime('%d.%m.%Y')}")
                    st.progress(progress)
                    st.caption(f"€{spent:.2f} от €{trip_budget:.2f}")
                with col2:
                    st.write("")
                    if st.button("Отвори →", key=f"home_open_{trip_id}", use_container_width=True):
                        open_trip(trip_id)


# --- NEW TRIP PAGE ---
elif st.session_state.page == "new_trip":
    st.title("✈️ Ново пътуване")

    if st.button("← Назад", key="new_trip_back"):
        go_home()

    st.divider()

    destination = st.text_input("Дестинация", placeholder="Например: Париж")
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Начална дата", value=date.today())
    with c2:
        end_date = st.date_input("Крайна дата", value=date.today())

    budget = st.number_input("Бюджет (€)", min_value=0.0, step=50.0)
    st.write("")

    if st.button("Създай пътуването", type="primary", use_container_width=True, key="create_trip"):
        if not destination.strip():
            st.error("Моля, въведи дестинация.")
        elif end_date < start_date:
            st.error("Крайната дата не може да бъде преди началната.")
        else:
            trip_id = f"{destination.strip()}_{start_date.strftime('%Y%m%d')}"
            st.session_state.trips[trip_id] = {
                "destination": destination.strip(),
                "start_date": start_date,
                "end_date": end_date,
                "budget": budget,
                "expenses": [],
            }
            save_trips()
            st.session_state.selected_trip = trip_id
            st.session_state.page = "trip"
            st.rerun()


# --- ADD EXPENSE PAGE ---
elif st.session_state.page == "add_expense":
    st.title("➕ Добави разход")

    if st.button("← Назад", key="expense_back"):
        if st.session_state.expense_trip:
            open_trip(st.session_state.expense_trip)
        else:
            go_home()

    st.divider()

    if not st.session_state.trips:
        st.warning("Първо трябва да създадеш пътуване.")
        if st.button("✈️ Създай пътуване", key="expense_create_trip"):
            st.session_state.page = "new_trip"
            st.rerun()
    else:
        trip_ids = list(st.session_state.trips.keys())
        default_trip = st.session_state.expense_trip
        default_index = trip_ids.index(default_trip) if default_trip in trip_ids else 0

        selected_trip = st.selectbox(
            "Към кое пътуване?",
            trip_ids,
            index=default_index,
            format_func=lambda x: st.session_state.trips[x]["destination"],
            key="expense_trip_select",
        )

        amount = st.number_input("Сума (€)", min_value=0.0, step=1.0, key="expense_amount")
        category = st.selectbox(
            "Категория",
            ["🍔 Храна", "🏨 Нощувка", "🚗 Транспорт", "🎟️ Забавления", "🛍️ Покупки", "📱 Други"],
            key="expense_category",
        )
        expense_date = st.date_input("Дата", value=date.today(), key="expense_date")
        note = st.text_input("Описание", placeholder="Например: Вечеря, бензин, зареждане", key="expense_note")

        fuel_expense = is_fuel_expense(note)
        fuel_liters = 0.0
        fuel_odometer = 0.0
        fuel_full_tank = False

        if fuel_expense:
            st.info("⛽ Разпознат е разход за гориво.")
            fuel_liters = st.number_input("Литри гориво (л)", min_value=0.0, step=0.1, format="%.2f", key="fuel_liters")
            fuel_odometer = st.number_input("Километраж при зареждане (км)", min_value=0.0, step=1.0, format="%.0f", key="fuel_odometer")
            fuel_full_tank = st.checkbox("Пълен резервоар", value=False, key="fuel_full_tank")

        st.write("")

        if st.button("Добави разход", type="primary", use_container_width=True, key="save_expense"):
            if amount <= 0:
                st.error("Моля, въведи сума по-голяма от 0.")
            else:
                st.session_state.trips[selected_trip]["expenses"].append(
                    {
                        "amount": amount,
                        "category": category,
                        "date": expense_date,
                        "note": note,
                        "is_fuel": fuel_expense,
                        "fuel_liters": fuel_liters if fuel_expense else 0.0,
                        "fuel_odometer": fuel_odometer if fuel_expense else 0.0,
                        "fuel_full_tank": fuel_full_tank if fuel_expense else False,
                    }
                )
                save_trips()
                st.session_state.selected_trip = selected_trip
                st.session_state.expense_trip = None
                st.session_state.page = "trip"
                st.rerun()


# --- LIST ALL TRIPS PAGE ---
elif st.session_state.page == "trips":
    st.title("✈️ Моите пътувания")

    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("← Начало", key="trips_home"):
            go_home()
    with c2:
        if st.button("＋ Ново пътуване", type="primary", key="trips_new"):
            st.session_state.page = "new_trip"
            st.rerun()

    st.divider()

    if not st.session_state.trips:
        st.info("Все още нямаш създадени пътувания.")
    else:
        for trip_id, trip in st.session_state.trips.items():
            spent = trip_expenses(trip)
            trip_budget = trip["budget"]
            progress = min(spent / trip_budget, 1.0) if trip_budget > 0 else 0.0

            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"✈️ {trip['destination']}")
                    st.caption(f"{trip['start_date'].strftime('%d.%m.%Y')} – {trip['end_date'].strftime('%d.%m.%Y')}")
                    st.progress(progress)
                    st.caption(f"€{spent:.2f} от €{trip_budget:.2f}")
                with col2:
                    st.write("")
                    if st.button("Отвори →", key=f"trips_open_{trip_id}", use_container_width=True):
                        open_trip(trip_id)


# --- SINGLE TRIP DETAILS PAGE ---
elif st.session_state.page == "trip":
    trip_id = st.session_state.selected_trip
    if not trip_id or trip_id not in st.session_state.trips:
        go_home()

    trip = st.session_state.trips[trip_id]
    spent = trip_expenses(trip)
    remaining = trip["budget"] - spent

    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("← Назад", key="trip_detail_back"):
            st.session_state.page = "trips"
            st.rerun()
    with c2:
        st.title(f"✈️ {trip['destination']}")

    st.caption(f"Период: {trip['start_date'].strftime('%d.%m.%Y')} – {trip['end_date'].strftime('%d.%m.%Y')}")
    st.divider()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Бюджет", f"€{trip['budget']:.2f}")
    with m2:
        st.metric("Похарчени", f"€{spent:.2f}")
    with m3:
        st.metric("Остават", f"€{remaining:.2f}")

    st.write("")
    if st.button("＋ Добави разход към това пътуване", type="primary", use_container_width=True, key="trip_add_exp"):
        open_add_expense(trip_id)

    st.divider()
    st.subheader("Разходи")

    if not trip["expenses"]:
        st.info("Все още няма записани разходи за това пътуване.")
    else:
        for idx, exp in enumerate(trip["expenses"]):
            with st.container(border=True):
                ec1, ec2, ec3 = st.columns([3, 2, 1])
                with ec1:
                    st.markdown(f"**{exp['category']}** — €{exp['amount']:.2f}")
                    if exp["note"]:
                        st.caption(exp["note"])
                with ec2:
                    st.caption(f"Дата: {exp['date'].strftime('%d.%m.%Y')}")
                    if exp.get("is_fuel"):
                        st.caption(f"⛽ {exp['fuel_liters']}л | {exp['fuel_odometer']}км")
                with ec3:
                    if st.button("🗑️", key=f"del_{trip_id}_{idx}"):
                        delete_expense(trip_id, idx)
                        st.rerun()


# --- OTHER PLACEHOLDER PAGES ---
elif st.session_state.page in ["analytics", "history", "comparison", "settings"]:
    st.title(f"⚙️ {st.session_state.page.capitalize()}")
    if st.button("← Начало", key="placeholder_back"):
        go_home()
    st.info("Тази страница е в процес на разработка.")
