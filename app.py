import json
from datetime import date
from pathlib import Path
import streamlit as st

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Travel Manager",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATA
# =========================================================

DATA_FILE = Path("trips.json")

FUEL_KEYWORDS = (
    "газ",
    "гориво",
    "зареждане",
    "бензин",
    "дизел",
)


def load_trips():
    if not DATA_FILE.exists():
        return {}

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))

        for trip in raw.values():
            if isinstance(trip.get("start_date"), str):
                trip["start_date"] = date.fromisoformat(trip["start_date"])

            if isinstance(trip.get("end_date"), str):
                trip["end_date"] = date.fromisoformat(trip["end_date"])

            trip.setdefault("destination", "")
            trip.setdefault("budget", 0.0)
            trip.setdefault("expenses", [])

            for expense in trip["expenses"]:
                if isinstance(expense.get("date"), str):
                    expense["date"] = date.fromisoformat(expense["date"])

                expense.setdefault("amount", 0.0)
                expense.setdefault("category", "📱 Други")
                expense.setdefault("note", "")
                expense.setdefault("is_fuel", False)
                expense.setdefault("fuel_liters", 0.0)
                expense.setdefault("fuel_odometer", 0.0)
                expense.setdefault("fuel_full_tank", False)

        return raw

    except (
        json.JSONDecodeError,
        OSError,
        ValueError,
        TypeError,
    ):
        return {}


def save_trips():
    serializable = {}

    for trip_id, trip in st.session_state.trips.items():
        serializable[trip_id] = {
            "destination": trip["destination"],
            "start_date": trip["start_date"].isoformat(),
            "end_date": trip["end_date"].isoformat(),
            "budget": float(trip["budget"]),
            "expenses": [],
        }

        for expense in trip.get("expenses", []):
            serializable[trip_id]["expenses"].append(
                {
                    "amount": float(expense.get("amount", 0)),
                    "category": expense.get(
                        "category",
                        "📱 Други",
                    ),
                    "date": expense["date"].isoformat(),
                    "note": expense.get("note", ""),
                    "is_fuel": expense.get(
                        "is_fuel",
                        False,
                    ),
                    "fuel_liters": float(
                        expense.get(
                            "fuel_liters",
                            0.0,
                        )
                    ),
                    "fuel_odometer": float(
                        expense.get(
                            "fuel_odometer",
                            0.0,
                        )
                    ),
                    "fuel_full_tank": expense.get(
                        "fuel_full_tank",
                        False,
                    ),
                }
            )

    try:
        DATA_FILE.write_text(
            json.dumps(
                serializable,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError as error:
        st.error(f"Неуспешно записване на данните: {error}")


def is_fuel_expense(text):
    text = (text or "").lower()

    return any(keyword in text for keyword in FUEL_KEYWORDS)


# =========================================================
# SESSION STATE
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
# CALCULATIONS
# =========================================================


def total_expenses():
    return sum(
        float(expense.get("amount", 0))
        for trip in st.session_state.trips.values()
        for expense in trip.get("expenses", [])
    )


def total_budget():
    return sum(
        float(trip.get("budget", 0))
        for trip in st.session_state.trips.values()
    )


def trip_expenses(trip):
    return sum(
        float(expense.get("amount", 0))
        for expense in trip.get("expenses", [])
    )
def category_breakdown(trip):
    categories = {}

    for expense in trip.get("expenses", []):
        category = expense.get("category", "📱 Други")
        amount = float(expense.get("amount", 0))

        categories[category] = categories.get(category, 0) + amount

    total = sum(categories.values())

    result = []

    for category, amount in sorted(
        categories.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        percentage = (
            (amount / total) * 100
            if total > 0
            else 0
        )

        result.append(
            {
                "category": category,
                "amount": amount,
                "percentage": percentage,
            }
        )

    return result

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
    st.session_state.expense_trip = trip_id
    st.session_state.page = "trip"
    st.rerun()


def open_add_expense(trip_id=None):
    st.session_state.expense_trip = trip_id
    st.session_state.page = "add_expense"
    st.rerun()


def open_new_trip():
    st.session_state.page = "new_trip"
    st.rerun()


def open_page(page):
    st.session_state.page = page
    st.rerun()


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown(
    """
<style>

@import url(
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
);


/* =====================================================
   GLOBAL
   ===================================================== */

html,
body,
[class*="css"],
.stApp,
button,
input,
textarea,
select {
    font-family:
        'Inter',
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        sans-serif !important;
}

.stApp {
    background:
        radial-gradient(
            circle at top right,
            rgba(22,135,217,.08),
            transparent 32%
        ),
        #08111a;
}

.block-container {
    max-width: 1080px;
    padding-top: 2rem;
    padding-bottom: 5rem;
}


/* =====================================================
   SIDEBAR
   ===================================================== */

section[data-testid="stSidebar"] {
    background: #09141f;
    border-right: 1px solid #1a2b3a;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.4rem;
}

.tm-sidebar-logo {
    font-size: 1.35rem;
    font-weight: 800;
    color: #f4f8fb;
    letter-spacing: -.04em;
    margin-bottom: 2px;
}

.tm-sidebar-sub {
    color: #7890a3;
    font-size: .82rem;
}


/* =====================================================
   STREAMLIT BUTTONS
   ===================================================== */

.stButton > button {
    min-height: 44px;
    border-radius: 12px;
    border: 1px solid #263c4f;
    background: #101e2a;
    color: #eef5f9;
    font-weight: 650;
    transition:
        background .15s ease,
        border-color .15s ease,
        transform .15s ease;
}

.stButton > button:hover {
    background: #152b3d;
    border-color: #2b9cff;
    color: white;
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0);
}


/* PRIMARY */

.stButton > button[kind="primary"] {
    background: #1687d9;
    border-color: #1687d9;
    color: white;
}

.stButton > button[kind="primary"]:hover {
    background: #2199ec;
    border-color: #2199ec;
}


/* =====================================================
   INPUTS
   ===================================================== */

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {
    background: #0d1925 !important;
    border-color: #22374a !important;
    border-radius: 10px !important;
}

textarea,
input {
    color: #eef5f9 !important;
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {
    background:
        linear-gradient(
            145deg,
            #10202e,
            #0c1823
        );
    border: 1px solid #1d3447;
    border-radius: 17px;
    padding: 15px 17px;
}

div[data-testid="stMetricLabel"] {
    color: #8fa1b2 !important;
}

div[data-testid="stMetricValue"] {
    color: #f4f8fb !important;
}


/* =====================================================
   HOME HEADER
   ===================================================== */

.tm-header {
    width: 100%;
    padding: 8px 0 8px 0;
}

.tm-brand {
    color: #f4f8fb !important;
    font-size: clamp(
        2rem,
        5vw,
        3rem
    );
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -.055em;
    margin: 0;
}

.tm-subtitle {
    color: #8fa1b2 !important;
    font-size: 1rem;
    font-weight: 500;
    line-height: 1.5;
    margin-top: 9px;
}


/* =====================================================
   SECTION TITLE
   ===================================================== */

.tm-section-title {
    color: #f4f8fb !important;
    font-size: 1.4rem;
    font-weight: 750;
    line-height: 1.3;
    margin: 12px 0 15px 0;
}


/* =====================================================
   QUICK ACTION CARDS
   ===================================================== */

.tm-card {
    background:
        linear-gradient(
            145deg,
            #102130,
            #0c1823
        );
    border: 1px solid #203446;
    border-radius: 20px;
    padding: 20px;
    min-height: 118px;
    box-shadow:
        0 10px 28px
        rgba(0,0,0,.18);
    margin-bottom: 10px;
}

.tm-card-primary {
    border-color: #235d83;
    background:
        linear-gradient(
            145deg,
            #12314a,
            #0c1c29
        );
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


/* =====================================================
   TRIP CARD
   ===================================================== */

.tm-trip-card {
    background:
        linear-gradient(
            145deg,
            #0f1f2c,
            #0b1721
        );
    border: 1px solid #1d3446;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 12px;
}

.tm-trip-title {
    color: #f4f8fb;
    font-size: 1.1rem;
    font-weight: 750;
}

.tm-trip-date {
    color: #8196a8;
    font-size: .84rem;
    margin-top: 4px;
}

.tm-trip-money {
    color: #b7c6d2;
    font-size: .88rem;
    margin-top: 7px;
}


/* =====================================================
   CATEGORY CARDS
   ===================================================== */

.tm-cat-grid {
    display: grid;
    grid-template-columns:
        repeat(
            3,
            minmax(0, 1fr)
        );
    gap: 12px;
    margin: 10px 0 20px 0;
}

.tm-cat-card {
    border: 1px solid rgba(120,120,140,.18);
    border-radius: 18px;
    padding: 16px;
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.055),
            rgba(255,255,255,.018)
        );
    min-height: 128px;
}

.tm-cat-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.tm-cat-name {
    font-size: 14px;
    font-weight: 650;
    opacity: .86;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.tm-cat-pct {
    font-size: 12px;
    font-weight: 700;
    opacity: .65;
}

.tm-cat-amount {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -.5px;
    margin-top: 13px;
}

.tm-cat-bar {
    height: 6px;
    border-radius: 99px;
    background: rgba(128,128,128,.18);
    overflow: hidden;
    margin-top: 13px;
}

.tm-cat-fill {
    height: 100%;
    border-radius: 99px;
    background:
        linear-gradient(
            90deg,
            #7c5cff,
            #35c7ff
        );
}

.tm-cat-label {
    margin-top: 7px;
    font-size: 11px;
    opacity: .55;
}


/* =====================================================
   INFO / WARNING
   ===================================================== */

div[data-testid="stAlert"] {
    border-radius: 14px;
}

/* =====================================================
   TRIP CATEGORY ANALYSIS
   ===================================================== */

.tm-trip-analysis {
    margin-top: 16px;
    padding-top: 15px;
    border-top: 1px solid rgba(255,255,255,.07);
}

.tm-trip-analysis-title {
    color: #dce7ef;
    font-size: .88rem;
    font-weight: 700;
    margin-bottom: 12px;
}

.tm-category-row {
    margin-bottom: 12px;
}

.tm-category-row-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 6px;
}

.tm-category-name {
    color: #cbd8e2;
    font-size: .78rem;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.tm-category-value {
    color: #91a5b5;
    font-size: .75rem;
    font-weight: 600;
    white-space: nowrap;
}

.tm-roundbar {
    width: 100%;
    height: 8px;
    background: rgba(255,255,255,.07);
    border-radius: 999px;
    overflow: hidden;
}

.tm-roundbar-fill {
    height: 100%;
    min-width: 2px;
    border-radius: 999px;
    background:
        linear-gradient(
            90deg,
            #1687d9,
            #35c7ff
        );
    transition: width .3s ease;
}

.tm-category-percent {
    margin-top: 4px;
    color: #71889a;
    font-size: .68rem;
    text-align: right;
}


/* =====================================================
   TRIP ANALYSIS MOBILE
   ===================================================== */

@media (max-width: 700px) {

    .tm-trip-analysis {
        margin-top: 14px;
        padding-top: 13px;
    }

    .tm-trip-analysis-title {
        font-size: .84rem;
    }

    .tm-category-row {
        margin-bottom: 10px;
    }

    .tm-category-name {
        font-size: .74rem;
    }

    .tm-category-value {
        font-size: .72rem;
    }

    .tm-roundbar {
        height: 7px;
    }
}
/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 900px) {

    .tm-cat-grid {
        grid-template-columns:
            repeat(
                2,
                minmax(0, 1fr)
            );
    }
}

@media (max-width: 700px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
    }

    .tm-brand {
        font-size: 2.05rem;
    }

    .tm-subtitle {
        font-size: .92rem;
    }

    div[data-testid="stMetric"] {
        padding: 11px 12px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.3rem;
    }

    .tm-card {
        padding: 17px;
    }
}

@media (max-width: 600px) {

    .tm-cat-grid {
        grid-template-columns: 1fr;
        gap: 10px;
    }

    .tm-cat-card {
        min-height: 112px;
        padding: 14px;
    }

    .tm-cat-amount {
        font-size: 22px;
    }
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
<div class="tm-sidebar-logo">✈️ Travel Manager</div>
<div class="tm-sidebar-sub">Пътувания и разходи</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        "⌂  Начало",
        use_container_width=True,
        key="nav_home",
    ):
        go_home()

    if st.button(
        "✈️  Пътувания",
        use_container_width=True,
        key="nav_trips",
    ):
        open_page("trips")

    if st.button(
        "＋  Добави разход",
        use_container_width=True,
        key="nav_expense",
    ):
        open_add_expense()

    st.divider()

    st.caption("Планиране")

    if st.button(
        "📊  Анализи",
        use_container_width=True,
        key="nav_analysis",
    ):
        open_page("analytics")

    if st.button(
        "🕘  История",
        use_container_width=True,
        key="nav_history",
    ):
        open_page("history")

    if st.button(
        "⇄  Сравнение",
        use_container_width=True,
        key="nav_comparison",
    ):
        open_page("comparison")

    if st.button(
        "⚙️  Настройки",
        use_container_width=True,
        key="nav_settings",
    ):
        open_page("settings")


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "home":

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    st.markdown(
        """
<div class="tm-header">
    <div class="tm-brand">✈️ Travel Manager</div>
    <div class="tm-subtitle">Всичко за твоите пътувания и разходи на едно място.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.write("")

    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    expenses = total_expenses()
    budget = total_budget()
    remaining = budget - expenses

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "✈️ Пътувания",
            len(st.session_state.trips),
        )

    with c2:
        st.metric(
            "💳 Общо разходи",
            f"€{expenses:.2f}",
        )

    with c3:
        st.metric(
            "💰 Оставащ бюджет",
            f"€{remaining:.2f}",
        )

    st.write("")

    # -----------------------------------------------------
    # QUICK ACTIONS
    # -----------------------------------------------------

    st.markdown(
        '<div class="tm-section-title">Бързи действия</div>',
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

        if st.button(
            "Добави разход →",
            use_container_width=True,
            type="primary",
            key="quick_add",
        ):
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

        if st.button(
            "Създай пътуване →",
            use_container_width=True,
            key="quick_trip",
        ):
            open_new_trip()

    st.write("")
    st.divider()

    # -----------------------------------------------------
    # MY TRIPS
    # -----------------------------------------------------

    st.markdown(
        '<div class="tm-section-title">Моите пътувания</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.trips:

        st.info(
            "Все още нямаш пътувания. "
            "Създай първото си пътуване от "
            "бутона „Създай пътуване“."
        )

    else:

        for trip_id, trip in st.session_state.trips.items():

            spent = trip_expenses(trip)
            trip_budget = float(trip.get("budget", 0))

            if trip_budget > 0:
                progress = min(
                    spent / trip_budget,
                    1.0,
                )
            else:
                progress = 0.0

            st.markdown(
                '<div class="tm-trip-card">',
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns([4, 1])

            with c1:

                st.markdown(
                    f"""
<div class="tm-trip-title">✈️ {trip['destination']}</div>
<div class="tm-trip-date">{trip['start_date'].strftime('%d.%m.%Y')} – {trip['end_date'].strftime('%d.%m.%Y')}</div>
""",
                    unsafe_allow_html=True,
                )

                st.progress(progress)

                st.markdown(
                    f"""
<div class="tm-trip-money">€{spent:.2f} от €{trip_budget:.2f}</div>
""",
                    unsafe_allow_html=True,
                )

            with c2:

                st.write("")

                if st.button(
                    "Отвори →",
                    use_container_width=True,
                    key=f"home_open_{trip_id}",
                ):
                    open_trip(trip_id)

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )


# =========================================================
# NEW TRIP
# =========================================================

elif st.session_state.page == "new_trip":

    st.title("✈️ Ново пътуване")

    if st.button(
        "← Назад",
        key="new_trip_back",
    ):
        go_home()

    st.divider()

    destination = st.text_input(
        "Дестинация",
        placeholder="Например: Париж",
        key="new_destination",
    )

    c1, c2 = st.columns(2)

    with c1:

        start_date = st.date_input(
            "Начална дата",
            value=date.today(),
            key="new_start_date",
        )

    with c2:

        end_date = st.date_input(
            "Крайна дата",
            value=date.today(),
            key="new_end_date",
        )

    budget = st.number_input(
        "Бюджет (€)",
        min_value=0.0,
        step=50.0,
        key="new_budget",
    )

    st.write("")

    if st.button(
        "Създай пътуването",
        type="primary",
        use_container_width=True,
        key="create_trip",
    ):

        destination = destination.strip()

        if not destination:

            st.error(
                "Моля, въведи дестинация."
            )

        elif end_date < start_date:

            st.error(
                "Крайната дата не може да бъде преди началната."
            )

        else:

            base_id = (
                destination
                + "_"
                + start_date.strftime("%Y%m%d")
            )

            trip_id = base_id
            counter = 2

            while trip_id in st.session_state.trips:

                trip_id = f"{base_id}_{counter}"

                counter += 1

            st.session_state.trips[trip_id] = {
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "budget": float(budget),
                "expenses": [],
            }

            save_trips()

            st.session_state.selected_trip = trip_id
            st.session_state.expense_trip = trip_id
            st.session_state.page = "trip"

            st.rerun()


# =========================================================
# ADD EXPENSE
# =========================================================

elif st.session_state.page == "add_expense":

    st.title("➕ Добави разход")

    if st.button(
        "← Назад",
        key="expense_back",
    ):

        if (
            st.session_state.expense_trip
            and st.session_state.expense_trip
            in st.session_state.trips
        ):

            open_trip(
                st.session_state.expense_trip
            )

        else:

            go_home()

    st.divider()

    if not st.session_state.trips:

        st.warning(
            "Първо трябва да създадеш пътуване."
        )

        if st.button(
            "✈️ Създай пътуване",
            type="primary",
            key="expense_create_trip",
        ):
            open_new_trip()

    else:

        trip_ids = list(
            st.session_state.trips.keys()
        )

        default_trip = (
            st.session_state.expense_trip
        )

        if default_trip in trip_ids:

            default_index = trip_ids.index(
                default_trip
            )

        else:

            default_index = 0

        selected_trip = st.selectbox(
            "Към кое пътуване?",
            trip_ids,
            index=default_index,
            format_func=lambda x:
                st.session_state.trips[x][
                    "destination"
                ],
            key="expense_trip_select",
        )

        amount = st.number_input(
            "Сума (€)",
            min_value=0.0,
            step=1.0,
            key="expense_amount",
        )

        category = st.selectbox(
            "Категория",
            [
                "🍔 Храна",
                "🏨 Нощувка",
                "🚗 Транспорт",
                "🎟️ Забавления",
                "🛍️ Покупки",
                "📱 Други",
            ],
            key="expense_category",
        )

        expense_date = st.date_input(
            "Дата",
            value=date.today(),
            key="expense_date",
        )

        note = st.text_input(
            "Описание",
            placeholder="Например: Вечеря, бензин, зареждане",
            key="expense_note",
        )

        fuel_expense = is_fuel_expense(
            note
        )

        fuel_liters = 0.0
        fuel_odometer = 0.0
        fuel_full_tank = False

        if fuel_expense:

            st.info(
                "⛽ Разпознат е разход за гориво."
            )

            fuel_liters = st.number_input(
                "Литри гориво (л)",
                min_value=0.0,
                step=0.1,
                format="%.2f",
                key="fuel_liters",
            )

            fuel_odometer = st.number_input(
                "Километраж при зареждане (км)",
                min_value=0.0,
                step=1.0,
                format="%.0f",
                key="fuel_odometer",
            )

            fuel_full_tank = st.checkbox(
                "Пълен резервоар",
                key="fuel_full_tank",
            )

        st.write("")

        if st.button(
            "Добави разход",
            type="primary",
            use_container_width=True,
            key="save_expense",
        ):

            if amount <= 0:

                st.error(
                    "Моля, въведи сума по-голяма от 0."
                )

            else:

                st.session_state.trips[
                    selected_trip
                ]["expenses"].append(
                    {
                        "amount": float(amount),
                        "category": category,
                        "date": expense_date,
                        "note": note,
                        "is_fuel": fuel_expense,
                        "fuel_liters": (
                            fuel_liters
                            if fuel_expense
                            else 0.0
                        ),
                        "fuel_odometer": (
                            fuel_odometer
                            if fuel_expense
                            else 0.0
                        ),
                        "fuel_full_tank": (
                            fuel_full_tank
                            if fuel_expense
                            else False
                        ),
                    }
                )

                save_trips()

                st.session_state.selected_trip = (
                    selected_trip
                )

                st.session_state.expense_trip = (
                    selected_trip
                )

                st.session_state.page = "trip"

                st.rerun()


# =========================================================
# TRIPS
# =========================================================

elif st.session_state.page == "trips":

    st.title("✈️ Моите пътувания")

    c1, c2 = st.columns([1, 4])

    with c1:

        if st.button(
            "← Начало",
            key="trips_home",
        ):
            go_home()

    with c2:

        if st.button(
            "＋ Ново пътуване",
            type="primary",
            key="trips_new",
        ):
            open_new_trip()

    st.divider()

    if not st.session_state.trips:

        st.info(
            "Все още нямаш създадени пътувания."
        )

        if st.button(
            "Създай първото пътуване",
            type="primary",
            key="empty_create_trip",
        ):
            open_new_trip()

    else:

        for trip_id, trip in st.session_state.trips.items():

            spent = trip_expenses(trip)

            with st.container(border=True):

                st.subheader(
                    f"✈️ {trip['destination']}"
                )

                st.caption(
                    f"{trip['start_date'].strftime('%d.%m.%Y')}"
                    f" – "
                    f"{trip['end_date'].strftime('%d.%m.%Y')}"
                )

                st.progress(
                    min(
                        spent / trip["budget"],
                        1.0,
                    )
                    if trip["budget"] > 0
                    else 0.0
                )

                st.write(
                    f"Похарчено: €{spent:.2f} / "
                    f"€{trip['budget']:.2f}"
                )

                if st.button(
                    "Отвори",
                    key=f"trips_open_{trip_id}",
                    use_container_width=True,
                ):
                    open_trip(trip_id)


# =========================================================
# TRIP
# =========================================================

elif st.session_state.page == "trip":

    trip_id = (
        st.session_state.selected_trip
    )

    if (
        trip_id is None
        or trip_id not in st.session_state.trips
    ):
        go_home()

    trip = st.session_state.trips[
        trip_id
    ]

    if st.button(
        "← Моите пътувания",
        key="trip_back",
    ):

        st.session_state.page = "trips"
        st.session_state.expense_trip = None
        st.rerun()

    st.title(
        f"✈️ {trip['destination']}"
    )

    st.caption(
        f"{trip['start_date'].strftime('%d.%m.%Y')}"
        f" – "
        f"{trip['end_date'].strftime('%d.%m.%Y')}"
    )

    st.divider()

    spent = trip_expenses(trip)

    remaining = (
        float(trip["budget"])
        - spent
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "💰 Бюджет",
            f"€{trip['budget']:.2f}",
        )

    with c2:

        st.metric(
            "💳 Похарчено",
            f"€{spent:.2f}",
        )

    with c3:

        st.metric(
            "✓ Остава",
            f"€{remaining:.2f}",
        )

    st.write("")

    if st.button(
        "➕ Добави разход",
        type="primary",
        use_container_width=True,
        key="trip_add_expense",
    ):
        open_add_expense(trip_id)

    st.divider()

    # =====================================================
    # FUEL
    # =====================================================

    fuel_expenses = [
        expense
        for expense in trip["expenses"]
        if expense.get(
            "is_fuel",
            False,
        )
    ]

    if fuel_expenses:

        st.subheader(
            "⛽ Гориво"
        )

        total_fuel_liters = sum(
            expense.get(
                "fuel_liters",
                0.0,
            )
            for expense in fuel_expenses
        )

        total_fuel_cost = sum(
            expense.get(
                "amount",
                0.0,
            )
            for expense in fuel_expenses
        )

        fuel_with_km = [
            expense
            for expense in fuel_expenses
            if expense.get(
                "fuel_odometer",
                0.0,
            ) > 0
            and expense.get(
                "fuel_liters",
                0.0,
            ) > 0
        ]

        fuel_with_km.sort(
            key=lambda expense:
                expense.get(
                    "fuel_odometer",
                    0,
                )
        )

        avg_price_per_liter = (
            total_fuel_cost
            / total_fuel_liters
            if total_fuel_liters > 0
            else None
        )

        overall_consumption = None

        if len(fuel_with_km) >= 2:

            first_odometer = (
                fuel_with_km[0].get(
                    "fuel_odometer",
                    0,
                )
            )

            last_odometer = (
                fuel_with_km[-1].get(
                    "fuel_odometer",
                    0,
                )
            )

            total_km = (
                last_odometer
                - first_odometer
            )

            # Exclude liters from the first fueling
            # as they were consumed during previous km
            liters_consumed = sum(
                e.get(
                    "fuel_liters",
                    0.0,
                )
                for e in fuel_with_km[1:]
            )

            if total_km > 0:

                overall_consumption = (
                    liters_consumed
                    / total_km
                ) * 100

        fc1, fc2, fc3 = st.columns(3)

        with fc1:

            st.metric(
                "⛽ Заредени литри",
                f"{total_fuel_liters:.2f} л",
            )

        with fc2:

            st.metric(
                "💶 Ср. цена / liter",
                (
                    f"€{avg_price_per_liter:.2f}"
                    if avg_price_per_liter
                    else "N/A"
                ),
            )

        with fc3:

            st.metric(
                "🏎️ Разход",
                (
                    f"{overall_consumption:.2f} л/100км"
                    if overall_consumption
                    else "N/A"
                ),
            )

        st.write("")

    # =====================================================
    # ALL EXPENSES LIST
    # =====================================================

    st.subheader(
        "📜 Списък с разходи"
    )

    if not trip["expenses"]:

        st.info(
            "Няма добавени разходи за това пътуване."
        )

    else:

        for idx, expense in enumerate(
            reversed(
                trip["expenses"]
            )
        ):

            with st.container(border=True):

                ec1, ec2 = st.columns(
                    [3, 1]
                )

                with ec1:

                    st.markdown(
                        f"**{expense['category']}** – "
                        f"€{expense['amount']:.2f}"
                    )

                    st.caption(
                        f"Дата: "
                        f"{expense['date'].strftime('%d.%m.%Y')}"
                        f" | "
                        f"{expense.get('note', '')}"
                    )

                    if expense.get(
                        "is_fuel",
                        False,
                    ):

                        st.caption(
                            f"⛽ "
                            f"{expense.get('fuel_liters', 0.0)} л @ "
                            f"{expense.get('fuel_odometer', 0.0)} км "
                            f"({'Пълен' if expense.get('fuel_full_tank') else 'Частичен'})"
                        )

                with ec2:

                    # Calculate actual original index
                    # for deletion from reversed list

                    real_idx = (
                        len(
                            trip["expenses"]
                        )
                        - 1
                        - idx
                    )

                    if st.button(
                        "🗑️ Изтрий",
                        key=(
                            f"del_exp_"
                            f"{trip_id}_"
                            f"{real_idx}"
                        ),
                    ):

                        trip["expenses"].pop(
                            real_idx
                        )

                        save_trips()

                        st.rerun()


# =========================================================
# OTHER PAGES
# =========================================================

elif st.session_state.page in [
    "analytics",
    "history",
    "comparison",
    "settings",
]:

    pages_title = {
        "analytics": "📊 Анализи",
        "history": "🕘 История",
        "comparison": "⇄ Сравнение",
        "settings": "⚙️ Настройки",
    }

    st.title(
        pages_title[
            st.session_state.page
        ]
    )

    if st.button(
        "← Начало",
        key="placeholder_back",
    ):
        go_home()

    st.divider()

    st.info(
        "Тази страница е в процес на разработка."
    )
