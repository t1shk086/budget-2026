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
        raw = json.loads(
            DATA_FILE.read_text(encoding="utf-8")
        )

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
                    "fuel_full_tank": expense.get("fuel_full_tank", False)
                }
                for expense in trip["expenses"]
            ]
        }

    DATA_FILE.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8"
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
# DATA FUNCTIONS
# =========================================================

def total_expenses():
    return sum(
        expense["amount"]
        for trip in st.session_state.trips.values()
        for expense in trip["expenses"]
    )


def total_budget():
    return sum(
        trip["budget"]
        for trip in st.session_state.trips.values()
    )


def trip_expenses(trip):
    return sum(
        expense["amount"]
        for expense in trip["expenses"]
    )


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

html, body, .stApp, .stApp *, button, input, textarea, select {
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

.tm-header { padding: 8px 0 22px 0; }
.tm-brand {
    font-size: clamp(2rem, 4vw, 2.8rem);
    font-weight: 800;
    letter-spacing: -0.055em;
    color: #f4f8fb;
    margin: 0;
}
.tm-subtitle {
    color: #8fa1b2;
    margin-top: 9px;
    font-size: .98rem;
    font-weight: 500;
}

.tm-card {
    background: linear-gradient(145deg, #102130, #0c1823);
    border: 1px solid #203446;
    border-radius: 20px;
    padding: 20px;
    min-height: 116px;
    box-shadow: 0 10px 28px rgba(0,0,0,.18);
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
}

div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px; }
hr { border-color: #1a2a39; }

@media (max-width: 700px) {
    .block-container { padding: 1rem; }
    .tm-brand { font-size: 2rem; }
    .tm-card { min-height: auto; padding: 17px; }
}
</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div style="font-family:Inter,sans-serif; font-size:1.35rem; font-weight:800; color:#f4f8fb;">
            ✈️ Travel Manager
        </div>
        """,
        unsafe_allow_html=True
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
# HOME
# =========================================================

if st.session_state.page == "home":
    st.markdown(
        """
        <div class="tm-header">
            <div class="tm-brand">✈️ Travel Manager</div>
            <div class="tm-subtitle">Всичко за твоите пътувания и разходи на едно място.</div>
        </div>
        """,
        unsafe_allow_html=True
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
        '<div style="font-size:1.45rem; font-weight:750; color:#f4f8fb; margin:8px 0 14px 0;">Бързи действия</div>',
        unsafe_allow_html=True
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
            unsafe_allow_html=True
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
            unsafe_allow_html=True
        )
        st.write("")
        if st.button("Създай пътуване →", use_container_width=True, key="quick_trip"):
            st.session_state.page = "new_trip"
            st.rerun()

    st.write("")
    st.divider()

    st.subheader("Моите пътувания")
    if not st.session_state.trips:
        st.info("Все още нямаш пътувания. Създай първото си пътуване от бутона по-горе.")
    else:
        for trip_id, trip in st.session_state.trips.items():
            spent = trip_expenses(trip)
            trip_budget = trip["budget"]
            progress = min(spent / trip_budget, 1.0) if trip_budget > 0 else 0.0

            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.subheader(f"✈️ {trip['destination']}")
                    st.caption(f"{trip['start_date'].strftime('%d.%m.%Y')} – {trip['end_date'].strftime('%d.%m.%Y')}")
                    st.progress(progress)
                    st.caption(f"€{spent:.2f} от €{trip_budget:.2f}")
                with c2:
                    st.write("")
                    if st.button("Отвори →", key=f"home_open_{trip_id}", use_container_width=True):
                        open_trip(trip_id)


# =========================================================
# NEW TRIP
# =========================================================

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
                "expenses": []
            }
            save_trips()
            st.session_state.selected_trip = trip_id
            st.session_state.page = "trip"
            st.rerun()


# =========================================================
# ADD EXPENSE
# =========================================================

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
            key="expense_trip_select"
        )

        amount = st.number_input("Сума (€)", min_value=0.0, step=1.0, key="expense_amount")
        category = st.selectbox(
            "Категория",
            ["🍔 Храна", "🏨 Нощувка", "🚗 Транспорт", "🎟️ Забавления", "🛍️ Покупки", "📱 Други"],
            key="expense_category"
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
                st.session_state.trips[selected_trip]["expenses"].append({
                    "amount": amount,
                    "category": category,
                    "date": expense_date,
                    "note": note,
                    "is_fuel": fuel_expense,
                    "fuel_liters": fuel_liters if fuel_expense else 0.0,
                    "fuel_odometer": fuel_odometer if fuel_expense else 0.0,
                    "fuel_full_tank": fuel_full_tank if fuel_expense else False
                })
                save_trips()
                st.session_state.selected_trip = selected_trip
                st.session_state.expense_trip = None
                st.session_state.page = "trip"
                st.rerun()


# =========================================================
# TRIPS LIST
# =========================================================

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
            with st.container(border=True):
                st.subheader(f"✈️ {trip['destination']}")
                st.caption(f"{trip['start_date'].strftime('%d.%m.%Y')} – {trip['end_date'].strftime('%d.%m.%Y')}")
                st.write(f"Похарчено: €{spent:.2f} / €{trip['budget']:.2f}")
                if st.button("Отвори", key=f"trips_open_{trip_id}", use_container_width=True):
                    open_trip(trip_id)


# =========================================================
# TRIP DETAILS
# =========================================================

elif st.session_state.page == "trip":
    trip_id = st.session_state.selected_trip
    if trip_id is None or trip_id not in st.session_state.trips:
        go_home()

    trip = st.session_state.trips[trip_id]

    if st.button("← Моите пътувания", key="trip_back"):
        st.session_state.page = "trips"
        st.rerun()

    st.title(f"✈️ {trip['destination']}")
    st.caption(f"{trip['start_date'].strftime('%d.%m.%Y')} – {trip['end_date'].strftime('%d.%m.%Y')}")
    st.divider()

    spent = trip_expenses(trip)
    remaining = trip["budget"] - spent

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("💰 Бюджет", f"€{trip['budget']:.2f}")
    with c2:
        st.metric("💳 Похарчено", f"€{spent:.2f}")
    with c3:
        st.metric("✓ Остава", f"€{remaining:.2f}")

    st.write("")
    if st.button("➕ Добави разход", type="primary", use_container_width=True, key="trip_add_expense"):
        open_add_expense(trip_id)

    st.divider()

    # FUEL STATISTICS
    fuel_expenses = [e for e in trip["expenses"] if e.get("is_fuel", False)]
    total_fuel_liters = sum(e.get("fuel_liters", 0.0) for e in fuel_expenses)
    total_fuel_cost = sum(e["amount"] for e in fuel_expenses)

    if fuel_expenses:
        st.subheader("⛽ Гориво")
        fuel_with_km = sorted(
            [e for e in fuel_expenses if e.get("fuel_odometer", 0.0) > 0 and e.get("fuel_liters", 0.0) > 0],
            key=lambda x: x["fuel_odometer"]
        )

        avg_price_per_liter = total_fuel_cost / total_fuel_liters if total_fuel_liters > 0 else None
        overall_consumption = None

        if len(fuel_with_km) >= 2:
            known_km = fuel_with_km[-1]["fuel_odometer"] - fuel_with_km[0]["fuel_odometer"]
            if known_km > 0 and total_fuel_liters > 0:
                overall_consumption = (total_fuel_liters / known_km) * 100

        full_indices = [i for i, e in enumerate(fuel_with_km) if e.get("fuel_full_tank", False)]
        real_consumption_values = []

        for pos in range(1, len(full_indices)):
            start = fuel_with_km[full_indices[pos - 1]]
            end = fuel_with_km[full_indices[pos]]
            km = end["fuel_odometer"] - start["fuel_odometer"]
            liters_between = sum(e.get("fuel_liters", 0.0) for e in fuel_with_km[full_indices[pos - 1] + 1 : full_indices[pos] + 1])
            if km > 0 and liters_between > 0:
                real_consumption_values.append((liters_between / km) * 100)

        real_consumption = sum(real_consumption_values) / len(real_consumption_values) if real_consumption_values else None

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            st.metric("Зареждания", len(fuel_expenses))
        with fc2:
            st.metric("Общо литри", f"{total_fuel_liters:.2f} л")
        with fc3:
            st.metric("Разход за гориво", f"€{total_fuel_cost:.2f}")

        fc4, fc5 = st.columns(2)
        with fc4:
            if avg_price_per_liter:
                st.metric("Средна цена", f"€{avg_price_per_liter:.2f}/л")
        with fc5:
            if overall_consumption:
                st.metric("Среден разход", f"{overall_consumption:.2f} л/100 км")
            else:
                st.caption("За среден разход са нужни поне 2 зареждания с известен километраж.")

        if real_consumption:
            st.metric("Реален разход", f"{real_consumption:.2f} л/100 км")

        st.divider()

    # EXPENSES LIST & CATEGORY BREAKDOWN
    if trip["expenses"]:
        st.subheader("📊 Разходи по категории")
        category_totals = {}
        for exp in trip["expenses"]:
            cat = exp["category"]
            category_totals[cat] = category_totals.get(cat, 0.0) + exp["amount"]

        for cat, amt in category_totals.items():
            st.write(f"**{cat}**: €{amt:.2f}")

        st.divider()
        st.subheader("📋 Всички разходи")

        for idx, exp in enumerate(reversed(trip["expenses"])):
            real_idx = len(trip["expenses"]) - 1 - idx
            with st.container(border=True):
                ec1, ec2, ec3 = st.columns([3, 2, 1])
                with ec1:
                    st.write(f"**{exp['category']}** - €{exp['amount']:.2f}")
                    if exp['note']:
                        st.caption(exp['note'])
                with ec2:
                    st.caption(f"Дата: {exp['date'].strftime('%d.%m.%Y')}")
                    if exp.get("is_fuel", False):
                        st.caption(f"⛽ {exp.get('fuel_liters', 0)}л | {exp.get('fuel_odometer', 0)}км")
                with ec3:
                    if st.button("🗑️", key=f"del_{trip_id}_{real_idx}"):
                        delete_expense(trip_id, real_idx)
                        st.rerun()
    else:
        st.info("Все още няма добавени разходи за това пътуване.")


# =========================================================
# ANALYTICS
# =========================================================

elif st.session_state.page == "analytics":
    st.title("📊 Анализи")
    if st.button("← Начало", key="analytics_home"):
        go_home()
    st.divider()

    if not st.session_state.trips:
        st.info("Няма налични данни за анализ.")
    else:
        all_expenses = [e for t in st.session_state.trips.values() for e in t["expenses"]]
        if not all_expenses:
            st.info("Добави разходи, за да видиш графики и статистики.")
        else:
            cat_totals = {}
            for e in all_expenses:
                cat_totals[e["category"]] = cat_totals.get(e["category"], 0.0) + e["amount"]

            st.subheader("Разходи по категории (Общо)")
            st.bar_chart(cat_totals)


# =========================================================
# HISTORY
# =========================================================

elif st.session_state.page == "history":
    st.title("🕘 История")
    if st.button("← Начало", key="history_home"):
        go_home()
    st.divider()

    all_expenses_flat = []
    for t_id, t in st.session_state.trips.items():
        for e in t["expenses"]:
            all_expenses_flat.append({**e, "destination": t["destination"]})

    all_expenses_flat.sort(key=lambda x: x["date"], reverse=True)

    if not all_expenses_flat:
        st.info("Няма регистрирана история на разходите.")
    else:
        for exp in all_expenses_flat:
            with st.container(border=True):
                st.write(f"**{exp['destination']}** | {exp['category']} - €{exp['amount']:.2f}")
                st.caption(f"Дата: {exp['date'].strftime('%d.%m.%Y')} | {exp['note']}")


# =========================================================
# COMPARISON
# =========================================================

elif st.session_state.page == "comparison":
    st.title("⇄ Сравнение на пътувания")
    if st.button("← Начало", key="comp_home"):
        go_home()
    st.divider()

    if len(st.session_state.trips) < 2:
        st.info("Трябват ти поне 2 пътувания, за да ги сравниш.")
    else:
        comp_data = []
        for t_id, t in st.session_state.trips.items():
            spent = trip_expenses(t)
            comp_data.append({
                "Дестинация": t["destination"],
                "Бюджет (€)": t["budget"],
                "Похарчено (€)": spent,
                "Разлика (€)": t["budget"] - spent
            })
        st.dataframe(comp_data, use_container_width=True)


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "settings":
    st.title("⚙️ Настройки")
    if st.button("← Начало", key="settings_home"):
        go_home()
    st.divider()

    st.subheader("Управление на данните")
    st.caption("Данните се съхраняват локално във файла `trips.json`.")

    if st.button("⚠️ Изчисти всички данни", type="primary"):
        st.session_state.trips = {}
        save_trips()
        st.success("Всички данни бяха изтрити успешно!")
        st.rerun()
