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
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return {}


def save_trips():
    serializable = {}
    for trip_id, trip in st.session_state.trips.items():
        serializable[trip_id] = {
            "destination": trip["destination"],
            "start_date": trip["start_date"].isoformat(),
            "end_date": trip["end_date"].isoformat(),
            "budget": float(trip["budget"]),
            "expenses": []
        }
        for expense in trip.get("expenses", []):
            serializable[trip_id]["expenses"].append({
                "amount": float(expense.get("amount", 0)),
                "category": expense.get("category", "📱 Други"),
                "date": expense["date"].isoformat(),
                "note": expense.get("note", ""),
                "is_fuel": expense.get("is_fuel", False),
                "fuel_liters": float(expense.get("fuel_liters", 0.0)),
                "fuel_odometer": float(expense.get("fuel_odometer", 0.0)),
                "fuel_full_tank": expense.get("fuel_full_tank", False),
            })
    try:
        DATA_FILE.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
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
    return sum(float(trip.get("budget", 0)) for trip in st.session_state.trips.values())


def trip_expenses(trip):
    return sum(float(expense.get("amount", 0)) for expense in trip.get("expenses", []))


# =========================================================
# NAVIGATION (Поправено с премахване на st.rerun от тук)
# =========================================================

def go_home():
    st.session_state.page = "home"
    st.session_state.selected_trip = None
    st.session_state.expense_trip = None

def open_trip(trip_id):
    st.session_state.selected_trip = trip_id
    st.session_state.expense_trip = trip_id
    st.session_state.page = "trip"

def open_add_expense(trip_id=None):
    st.session_state.expense_trip = trip_id
    st.session_state.page = "add_expense"

def open_new_trip():
    st.session_state.page = "new_trip"

def open_page(page):
    st.session_state.page = page


# =========================================================
# CSS (Поправен и затворен блок)
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, .stApp, button, input, textarea, select {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    .stApp {
        background: radial-gradient(circle, #ffffff 0%, #f0f2f6 100%);
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# UI ИНТЕРФЕЙС (Нова секция, за да работи приложението)
# =========================================================

# Странично меню за навигация
st.sidebar.title("📌 Навигация")
if st.sidebar.button("🏠 Начало", on_click=go_home): pass
if st.sidebar.button("➕ Нова екскурзия", on_click=open_new_trip): pass

# Рендиране на страници в зависимост от състоянието
if st.session_state.page == "home":
    st.title("✈️ Добре дошли в Travel Manager")
    
    col1, col2 = st.columns(2)
    col1.metric("Общ Бюджет", f"{total_budget():.2f} лв.")
    col2.metric("Общи Разходи", f"{total_expenses():.2f} лв.")
    
    st.write("Вашите екскурзии ще се покажат тук.")

elif st.session_state.page == "new_trip":
    st.title("➕ Създай нова екскурзия")
    # Тук можете да добавите формата за създаване на екскурзия

elif st.session_state.page == "trip":
    st.title(f"🗺️ Преглед на екскурзия: {st.session_state.selected_trip}")

elif st.session_state.page == "add_expense":
    st.title("💰 Добави разход")



# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        "## ✈️ Travel Manager"
    )

    st.caption(
        "Пътувания и разходи"
    )

    st.divider()

    if st.button(
        "⌂  Начало",
        use_container_width=True,
        key="nav_home"
    ):

        go_home()

    if st.button(
        "✈️  Пътувания",
        use_container_width=True,
        key="nav_trips"
    ):

        open_page("trips")

    if st.button(
        "＋  Добави разход",
        use_container_width=True,
        key="nav_expense"
    ):

        open_add_expense()

    st.divider()

    st.caption(
        "Планиране"
    )

    if st.button(
        "📊  Анализи",
        use_container_width=True,
        key="nav_analysis"
    ):

        open_page("analytics")

    if st.button(
        "🕘  История",
        use_container_width=True,
        key="nav_history"
    ):

        open_page("history")

    if st.button(
        "⇄  Сравнение",
        use_container_width=True,
        key="nav_comparison"
    ):

        open_page("comparison")

    if st.button(
        "⚙️  Настройки",
        use_container_width=True,
        key="nav_settings"
    ):

        open_page("settings")


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "home":

    # =====================================================
    # HEADER
    # =====================================================

    st.header(
        "✈️ Travel Manager"
    )

    st.caption(
        "Всичко за твоите пътувания и разходи "
        "на едно място."
    )

    st.write("")

    # =====================================================
    # DASHBOARD
    # =====================================================

    expenses = total_expenses()

    budget = total_budget()

    remaining = (
        budget
        - expenses
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "✈️ Пътувания",
            len(
                st.session_state.trips
            )
        )

    with c2:

        st.metric(
            "💳 Общо разходи",
            f"€{expenses:.2f}"
        )

    with c3:

        st.metric(
            "💰 Оставащ бюджет",
            f"€{remaining:.2f}"
        )

    st.write("")

    # =====================================================
    # QUICK ACTIONS
    # =====================================================

    st.subheader(
        "Бързи действия"
    )

    q1, q2 = st.columns(2)

    with q1:

        st.markdown(
            """
            <div class="tm-card tm-card-primary">

                <div class="tm-card-title">
                    ➕ Добави разход
                </div>

                <div class="tm-card-text">
                    Бързо добавяне на разход
                    към избрано пътуване.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Добави разход →",
            type="primary",
            use_container_width=True,
            key="quick_add"
        ):

            open_add_expense()

    with q2:

        st.markdown(
            """
            <div class="tm-card">

                <div class="tm-card-title">
                    ✈️ Ново пътуване
                </div>

                <div class="tm-card-text">
                    Създай ново пътуване
                    и задай неговия бюджет.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Създай пътуване →",
            use_container_width=True,
            key="quick_trip"
        ):

            open_new_trip()

    st.write("")

    st.divider()

    # =====================================================
    # MY TRIPS
    # =====================================================

    st.subheader(
        "Моите пътувания"
    )

    if not st.session_state.trips:

        st.info(
            "Все още нямаш пътувания. "
            "Създай първото си пътуване "
            "от бутона „Създай пътуване“."
        )

    else:

        for trip_id, trip in (
            st.session_state.trips.items()
        ):

            spent = trip_expenses(
                trip
            )

            trip_budget = float(
                trip.get(
                    "budget",
                    0
                )
            )

            if trip_budget > 0:

                progress = min(
                    spent / trip_budget,
                    1.0
                )

            else:

                progress = 0.0

            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [4, 1]
                )

                with c1:

                    st.subheader(
                        f"✈️ {trip['destination']}"
                    )

                    st.caption(
                        f"{trip['start_date'].strftime('%d.%m.%Y')}"
                        f" – "
                        f"{trip['end_date'].strftime('%d.%m.%Y')}"
                    )

                    st.progress(
                        progress
                    )

                    st.caption(
                        f"€{spent:.2f}"
                        f" от "
                        f"€{trip_budget:.2f}"
                    )

                with c2:

                    st.write("")

                    if st.button(
                        "Отвори →",
                        use_container_width=True,
                        key=f"home_open_{trip_id}"
                    ):

                        open_trip(
                            trip_id
                        )


# =========================================================
# NEW TRIP
# =========================================================

elif st.session_state.page == "new_trip":

    st.title(
        "✈️ Ново пътуване"
    )

    if st.button(
        "← Назад",
        key="new_trip_back"
    ):

        go_home()

    st.divider()

    destination = st.text_input(
        "Дестинация",
        placeholder="Например: Париж",
        key="new_destination"
    )

    c1, c2 = st.columns(2)

    with c1:

        start_date = st.date_input(
            "Начална дата",
            value=date.today(),
            key="new_start_date"
        )

    with c2:

        end_date = st.date_input(
            "Крайна дата",
            value=date.today(),
            key="new_end_date"
        )

    budget = st.number_input(
        "Бюджет (€)",
        min_value=0.0,
        step=50.0,
        key="new_budget"
    )

    st.write("")

    if st.button(
        "Създай пътуването",
        type="primary",
        use_container_width=True,
        key="create_trip"
    ):

        destination = (
            destination.strip()
        )

        if not destination:

            st.error(
                "Моля, въведи дестинация."
            )

        elif end_date < start_date:

            st.error(
                "Крайната дата не може да бъде "
                "преди началната."
            )

        else:

            base_id = (
                destination
                + "_"
                + start_date.strftime(
                    "%Y%m%d"
                )
            )

            trip_id = base_id

            counter = 2

            while trip_id in (
                st.session_state.trips
            ):

                trip_id = (
                    f"{base_id}_{counter}"
                )

                counter += 1

            st.session_state.trips[
                trip_id
            ] = {

                "destination":
                    destination,

                "start_date":
                    start_date,

                "end_date":
                    end_date,

                "budget":
                    float(budget),

                "expenses":
                    []
            }

            save_trips()

            st.session_state.selected_trip = (
                trip_id
            )

            st.session_state.expense_trip = (
                trip_id
            )

            st.session_state.page = (
                "trip"
            )

            st.rerun()


# =========================================================
# ADD EXPENSE
# =========================================================

elif st.session_state.page == "add_expense":

    st.title(
        "➕ Добави разход"
    )

    if st.button(
        "← Назад",
        key="expense_back"
    ):

        if (
            st.session_state.expense_trip
            and
            st.session_state.expense_trip
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
            key="expense_create_trip"
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

            default_index = (
                trip_ids.index(
                    default_trip
                )
            )

        else:

            default_index = 0

        selected_trip = st.selectbox(
            "Към кое пътуване?",
            trip_ids,
            index=default_index,
            format_func=lambda x:
                st.session_state.trips[
                    x
                ]["destination"],
            key="expense_trip_select"
        )

        amount = st.number_input(
            "Сума (€)",
            min_value=0.0,
            step=1.0,
            key="expense_amount"
        )

        category = st.selectbox(
            "Категория",
            [
                "🍔 Храна",
                "🏨 Нощувка",
                "🚗 Транспорт",
                "🎟️ Забавления",
                "🛍️ Покупки",
                "📱 Други"
            ],
            key="expense_category"
        )

        expense_date = st.date_input(
            "Дата",
            value=date.today(),
            key="expense_date"
        )

        note = st.text_input(
            "Описание",
            placeholder=(
                "Например: Вечеря, бензин, зареждане"
            ),
            key="expense_note"
        )

        fuel_expense = (
            is_fuel_expense(
                note
            )
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
                key="fuel_liters"
            )

            fuel_odometer = st.number_input(
                "Километраж при зареждане (км)",
                min_value=0.0,
                step=1.0,
                format="%.0f",
                key="fuel_odometer"
            )

            fuel_full_tank = st.checkbox(
                "Пълен резервоар",
                key="fuel_full_tank"
            )

        st.write("")

        if st.button(
            "Добави разход",
            type="primary",
            use_container_width=True,
            key="save_expense"
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

                        "amount":
                            float(amount),

                        "category":
                            category,

                        "date":
                            expense_date,

                        "note":
                            note,

                        "is_fuel":
                            fuel_expense,

                        "fuel_liters":
                            (
                                fuel_liters
                                if fuel_expense
                                else 0.0
                            ),

                        "fuel_odometer":
                            (
                                fuel_odometer
                                if fuel_expense
                                else 0.0
                            ),

                        "fuel_full_tank":
                            (
                                fuel_full_tank
                                if fuel_expense
                                else False
                            )
                    }
                )

                save_trips()

                st.session_state.selected_trip = (
                    selected_trip
                )

                st.session_state.expense_trip = (
                    selected_trip
                )

                st.session_state.page = (
                    "trip"
                )

                st.rerun()


# =========================================================
# TRIPS
# =========================================================

elif st.session_state.page == "trips":

    st.title(
        "✈️ Моите пътувания"
    )

    c1, c2 = st.columns(
        [1, 4]
    )

    with c1:

        if st.button(
            "← Начало",
            key="trips_home"
        ):

            go_home()

    with c2:

        if st.button(
            "＋ Ново пътуване",
            type="primary",
            key="trips_new"
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
            key="empty_create_trip"
        ):

            open_new_trip()

    else:

        for trip_id, trip in (
            st.session_state.trips.items()
        ):

            spent = trip_expenses(
                trip
            )

            with st.container(
                border=True
            ):

                st.subheader(
                    f"✈️ {trip['destination']}"
                )

                st.caption(
                    f"{trip['start_date'].strftime('%d.%m.%Y')}"
                    f" – "
                    f"{trip['end_date'].strftime('%d.%m.%Y')}"
                )

                if trip["budget"] > 0:

                    st.progress(
                        min(
                            spent
                            / trip["budget"],
                            1.0
                        )
                    )

                st.write(
                    f"Похарчено: "
                    f"€{spent:.2f} / "
                    f"€{trip['budget']:.2f}"
                )

                if st.button(
                    "Отвори",
                    key=f"trips_open_{trip_id}",
                    use_container_width=True
                ):

                    open_trip(
                        trip_id
                    )


# =========================================================
# TRIP
# =========================================================

elif st.session_state.page == "trip":

    trip_id = (
        st.session_state.selected_trip
    )

    if (
        trip_id is None
        or trip_id
        not in st.session_state.trips
    ):

        go_home()

    trip = (
        st.session_state.trips[
            trip_id
        ]
    )

    if st.button(
        "← Моите пътувания",
        key="trip_back"
    ):

        st.session_state.page = (
            "trips"
        )

        st.session_state.expense_trip = (
            None
        )

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

    spent = trip_expenses(
        trip
    )

    remaining = (
        float(
            trip["budget"]
        )
        - spent
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "💰 Бюджет",
            f"€{trip['budget']:.2f}"
        )

    with c2:

        st.metric(
            "💳 Похарчено",
            f"€{spent:.2f}"
        )

    with c3:

        st.metric(
            "✓ Остава",
            f"€{remaining:.2f}"
        )

    st.write("")

    if st.button(
        "➕ Добави разход",
        type="primary",
        use_container_width=True,
        key="trip_add_expense"
    ):

        open_add_expense(
            trip_id
        )

    st.divider()

    # =====================================================
    # FUEL
    # =====================================================

    fuel_expenses = [

        expense

        for expense
        in trip["expenses"]

        if expense.get(
            "is_fuel",
            False
        )
    ]

    if fuel_expenses:

        st.subheader(
            "⛽ Гориво"
        )

        total_fuel_liters = sum(

            expense.get(
                "fuel_liters",
                0.0
            )

            for expense
            in fuel_expenses
        )

        total_fuel_cost = sum(

            expense.get(
                "amount",
                0.0
            )

            for expense
            in fuel_expenses
        )

        fuel_with_km = [

            expense

            for expense
            in fuel_expenses

            if expense.get(
                "fuel_odometer",
                0.0
            ) > 0

            and expense.get(
                "fuel_liters",
                0.0
            ) > 0
        ]

        fuel_with_km.sort(

            key=lambda expense:
                expense.get(
                    "fuel_odometer",
                    0
                )
        )

        avg_price_per_liter = (

            total_fuel_cost
            / total_fuel_liters

            if total_fuel_liters > 0

            else None
        )

        overall_consumption = None

        if len(
            fuel_with_km
        ) >= 2:

            first_odometer = (
                fuel_with_km[
                    0
                ].get(
                    "fuel_odometer",
                    0
                )
            )

            last_odometer = (
                fuel_with_km[
                    -1
                ].get(
                    "fuel_odometer",
                    0
                )
            )

            known_km = (
                last_odometer
                - first_odometer
            )

            if (
                known_km > 0
                and total_fuel_liters > 0
            ):

                overall_consumption = (
                    total_fuel_liters
                    / known_km
                    * 100
                )

        full_tank_positions = [

            index

            for index, expense
            in enumerate(
                fuel_with_km
            )

            if expense.get(
                "fuel_full_tank",
                False
            )
        ]

        real_consumption_values = []

        for position in range(
            1,
            len(
                full_tank_positions
            )
        ):

            start_index = (
                full_tank_positions[
                    position - 1
                ]
            )

            end_index = (
                full_tank_positions[
                    position
                ]
            )

            start = (
                fuel_with_km[
                    start_index
                ]
            )

            end = (
                fuel_with_km[
                    end_index
                ]
            )

            km = (
                end[
                    "fuel_odometer"
                ]
                -
                start[
                    "fuel_odometer"
                ]
            )

            liters_between = sum(

                expense.get(
                    "fuel_liters",
                    0.0
                )

                for expense
                in fuel_with_km[
                    start_index + 1:
                    end_index + 1
                ]
            )

            if (
                km > 0
                and liters_between > 0
            ):

                real_consumption_values.append(

                    liters_between
                    / km
                    * 100
                )

        real_consumption = (

            sum(
                real_consumption_values
            )
            / len(
                real_consumption_values
            )

            if real_consumption_values

            else None
        )

        fc1, fc2, fc3 = st.columns(3)

        with fc1:

            st.metric(
                "Зареждания",
                len(
                    fuel_expenses
                )
            )

        with fc2:

            st.metric(
                "Общо литри",
                f"{total_fuel_liters:.2f} л"
            )

        with fc3:

            st.metric(
                "Разход за гориво",
                f"€{total_fuel_cost:.2f}"
            )

        fc4, fc5 = st.columns(2)

        with fc4:

            if avg_price_per_liter is not None:

                st.metric(
                    "Средна цена",
                    f"€{avg_price_per_liter:.2f}/л"
                )

        with fc5:

            if overall_consumption is not None:

                st.metric(
                    "Среден разход",
                    f"{overall_consumption:.2f} л/100 км"
                )

            else:

                st.caption(
                    "За среден разход са нужни "
                    "поне 2 зареждания с известен "
                    "километраж."
                )

        if real_consumption is not None:

            st.metric(
                "Реален разход",
                f"{real_consumption:.2f} л/100 км"
            )

        else:

            st.caption(
                "Реален разход: нужни са поне 2 "
                "зареждания с отбелязан пълен "
                "резервоар."
            )

        st.divider()

    # =====================================================
    # CATEGORIES
    # =====================================================

    selected_category = "Всички"

    if trip["expenses"]:

        st.subheader(
            "📊 Разходи по категории"
        )

        category_totals = {}

        for expense in trip["expenses"]:

            category = expense.get(
                "category",
                "📱 Други"
            )

            category_totals[
                category
            ] = (

                category_totals.get(
                    category,
                    0.0
                )

                +
                expense.get(
                    "amount",
                    0.0
                )
            )

        category_totals = dict(
            sorted(
                category_totals.items(),
                key=lambda item:
                    item[1],
                reverse=True
            )
        )

        total_category_expenses = sum(
            category_totals.values()
        )

        selected_category = st.selectbox(
            "Покажи категория",
            [
                "Всички"
            ]
            +
            list(
                category_totals.keys()
            ),
            key=f"category_filter_{trip_id}"
        )

        cards = []

        for (
            category,
            category_amount
        ) in category_totals.items():

            percentage = (

                category_amount
                /
                total_category_expenses
                *
                100

                if total_category_expenses > 0

                else 0
            )

            cards.append(

                f"""
                <div class="tm-cat-card">

                    <div class="tm-cat-top">

                        <div class="tm-cat-name">
                            {category}
                        </div>

                        <div class="tm-cat-pct">
                            {percentage:.1f}%
                        </div>

                    </div>

                    <div class="tm-cat-amount">
                        €{category_amount:.2f}
                    </div>

                    <div class="tm-cat-bar">

                        <div
                            class="tm-cat-fill"
                            style="
                                width:
                                {min(
                                    percentage,
                                    100
                                ):.2f}%;
                            "
                        ></div>

                    </div>

                    <div class="tm-cat-label">
                        от общо
                        €{total_category_expenses:.2f}
                    </div>

                </div>
                """
            )

        st.markdown(

            '<div class="tm-cat-grid">'
            +
            "".join(cards)
            +
            "</div>",

            unsafe_allow_html=True
        )

        # =================================================
        # DONUT
        # =================================================

        st.subheader(
            "🍩 Разпределение на разходите"
        )

        try:

            import plotly.graph_objects as go

            labels = list(
                category_totals.keys()
            )

            values = list(
                category_totals.values()
            )

            fig = go.Figure(

                data=[

                    go.Pie(

                        labels=labels,

                        values=values,

                        hole=0.62,

                        textinfo="none",

                        hovertemplate=(
                            "<b>%{label}</b><br>"
                            "Сума: €%{value:.2f}<br>"
                            "Дял: %{percent}"
                            "<extra></extra>"
                        ),

                        marker=dict(

                            line=dict(

                                color="#08111a",

                                width=2
                            )
                        )
                    )
                ]
            )

            fig.update_layout(

                height=430,

                margin=dict(
                    l=10,
                    r=10,
                    t=15,
                    b=15
                ),

                showlegend=True,

                legend=dict(

                    orientation="h",

                    yanchor="bottom",

                    y=-0.08,

                    xanchor="center",

                    x=0.5
                ),

                paper_bgcolor=(
                    "rgba(0,0,0,0)"
                ),

                plot_bgcolor=(
                    "rgba(0,0,0,0)"
                ),

                font=dict(
                    color="#eef5f9",
                    family="Inter"
                )
            )

            fig.add_annotation(

                text=(
                    f"<b>"
                    f"€{total_category_expenses:.2f}"
                    f"</b>"
                    "<br>"
                    "<span style="
                    "'font-size:12px'>"
                    "Общо"
                    "</span>"
                ),

                x=0.5,

                y=0.5,

                xref="paper",

                yref="paper",

                showarrow=False,

                font=dict(
                    size=20,
                    color="#f4f8fb",
                    family="Inter"
                )
            )

            st.plotly_chart(

                fig,

                use_container_width=True,

                config={
                    "displayModeBar": False,
                    "responsive": True
                },

                key=f"donut_chart_{trip_id}"
            )

        except ImportError:

            st.warning(
                "Plotly не е инсталиран."
            )

        st.divider()

    # =====================================================
    # EXPENSES
    # =====================================================

    st.subheader(
        "💳 Разходи"
    )

    if not trip["expenses"]:

        st.info(
            "Все още няма добавени разходи."
        )

    else:

        expenses = sorted(

            enumerate(
                trip["expenses"]
            ),

            key=lambda item:
                item[1]["date"],

            reverse=True
        )

        if selected_category != "Всички":

            expenses = [

                item

                for item in expenses

                if item[1].get(
                    "category",
                    "📱 Други"
                )
                ==
                selected_category
            ]

        for (
            original_index,
            expense
        ) in expenses:

            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [4, 1]
                )

                with c1:

                    st.write(
                        f"**{expense['category']}**"
                    )

                    if expense.get(
                        "note"
                    ):

                        st.write(
                            expense["note"]
                        )

                    if expense.get(
                        "is_fuel",
                        False
                    ):

                        liters = expense.get(
                            "fuel_liters",
                            0.0
                        )

                        odometer = expense.get(
                            "fuel_odometer",
                            0.0
                        )

                        caption = (
                            f"⛽ "
                            f"{liters:.2f} л"
                        )

                        if liters > 0:

                            caption += (
                                f" · "
                                f"€"
                                f"{expense['amount'] / liters:.2f}"
                                f"/л"
                            )

                        if odometer > 0:

                            caption += (
                                f" · "
                                f"{odometer:.0f} км"
                            )

                        if expense.get(
                            "fuel_full_tank",
                            False
                        ):

                            caption += (
                                " · ✓ пълен"
                            )

                        st.caption(
                            caption
                        )

                    st.caption(
                        expense[
                            "date"
                        ].strftime(
                            "%d.%m.%Y"
                        )
                    )

                with c2:

                    st.metric(
                        "Сума",
                        f"€{expense['amount']:.2f}"
                    )

                confirm_key = (
                    f"confirm_delete_"
                    f"{trip_id}_"
                    f"{original_index}"
                )

                if not st.session_state.get(
                    confirm_key,
                    False
                ):

                    if st.button(
                        "🗑️ Изтрий",
                        use_container_width=True,
                        key=(
                            f"delete_"
                            f"{trip_id}_"
                            f"{original_index}"
                        )
                    ):

                        st.session_state[
                            confirm_key
                        ] = True

                        st.rerun()

                else:

                    st.warning(
                        "Сигурен ли си, че искаш "
                        "да изтриеш този разход?"
                    )

                    d1, d2 = st.columns(2)

                    with d1:

                        if st.button(
                            "Да, изтрий",
                            type="primary",
                            use_container_width=True,
                            key=(
                                f"confirm_yes_"
                                f"{trip_id}_"
                                f"{original_index}"
                            )
                        ):

                            del trip[
                                "expenses"
                            ][
                                original_index
                            ]

                            save_trips()

                            st.session_state.pop(
                                confirm_key,
                                None
                            )

                            st.rerun()

                    with d2:

                        if st.button(
                            "Отказ",
                            use_container_width=True,
                            key=(
                                f"confirm_no_"
                                f"{trip_id}_"
                                f"{original_index}"
                            )
                        ):

                            st.session_state.pop(
                                confirm_key,
                                None
                            )

                            st.rerun()


# =========================================================
# ANALYTICS
# =========================================================

elif st.session_state.page == "analytics":

    st.title(
        "📊 Анализи"
    )

    if st.button(
        "← Начало",
        key="analytics_home"
    ):

        go_home()

    st.divider()

    expenses = total_expenses()

    budget = total_budget()

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Пътувания",
            len(
                st.session_state.trips
            )
        )

    with c2:

        st.metric(
            "Общ бюджет",
            f"€{budget:.2f}"
        )

    with c3:

        st.metric(
            "Общо разходи",
            f"€{expenses:.2f}"
        )

    if st.session_state.trips:

        st.subheader(
            "Разходи по пътувания"
        )

        for (
            trip_id,
            trip
        ) in st.session_state.trips.items():

            spent = trip_expenses(
                trip
            )

            st.write(
                f"**✈️ {trip['destination']}**"
            )

            if trip["budget"] > 0:

                st.progress(
                    min(
                        spent
                        /
                        trip["budget"],
                        1.0
                    )
                )

            st.caption(
                f"€{spent:.2f}"
                f" от "
                f"€{trip['budget']:.2f}"
            )


# =========================================================
# HISTORY
# =========================================================

elif st.session_state.page == "history":

    st.title(
        "🕘 История"
    )

    if st.button(
        "← Начало",
        key="history_home"
    ):

        go_home()

    st.divider()

    all_expenses = []

    for (
        trip_id,
        trip
    ) in st.session_state.trips.items():

        for (
            index,
            expense
        ) in enumerate(
            trip.get(
                "expenses",
                []
            )
        ):

            all_expenses.append(
                (
                    trip,
                    expense,
                    index
                )
            )

    all_expenses.sort(

        key=lambda item:
            item[1]["date"],

        reverse=True
    )

    if not all_expenses:

        st.info(
            "Все още няма въведени разходи."
        )

    else:

        for (
            trip,
            expense,
            index
        ) in all_expenses:

            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [4, 1]
                )

                with c1:

                    st.write(
                        f"**{expense['category']}**"
                    )

                    st.caption(
                        f"✈️ "
                        f"{trip['destination']} "
                        f"· "
                        f"{expense['date'].strftime('%d.%m.%Y')}"
                    )

                    if expense.get(
                        "note"
                    ):

                        st.write(
                            expense["note"]
                        )

                with c2:

                    st.metric(
                        "Сума",
                        f"€{expense['amount']:.2f}"
                    )


# =========================================================
# COMPARISON
# =========================================================

elif st.session_state.page == "comparison":

    st.title(
        "⇄ Сравнение"
    )

    if st.button(
        "← Начало",
        key="comparison_home"
    ):

        go_home()

    st.divider()

    if not st.session_state.trips:

        st.info(
            "Няма пътувания за сравнение."
        )

    else:

        for (
            trip_id,
            trip
        ) in st.session_state.trips.items():

            spent = trip_expenses(
                trip
            )

            remaining = (
                trip["budget"]
                -
                spent
            )

            with st.container(
                border=True
            ):

                st.subheader(
                    f"✈️ {trip['destination']}"
                )

                c1, c2, c3 = st.columns(3)

                with c1:

                    st.metric(
                        "Бюджет",
                        f"€{trip['budget']:.2f}"
                    )

                with c2:

                    st.metric(
                        "Разходи",
                        f"€{spent:.2f}"
                    )

                with c3:

                    st.metric(
                        "Остава",
                        f"€{remaining:.2f}"
                    )


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "settings":

    st.title(
        "⚙️ Настройки"
    )

    if st.button(
        "← Начало",
        key="settings_home"
    ):

        go_home()

    st.divider()

    st.subheader(
        "💾 Данни"
    )

    st.write(
        f"Файл с данни: "
        f"`{DATA_FILE.name}`"
    )

    st.write(
        f"Брой пътувания: "
        f"**{len(st.session_state.trips)}**"
    )

    if st.button(
        "💾 Запази данните",
        use_container_width=True,
        key="settings_save"
    ):

        save_trips()

        st.success(
            "Данните са записани успешно."
        )

    st.divider()

    st.subheader(
        "ℹ️ Travel Manager"
    )

    st.caption(
        "Управление на пътувания, бюджети, "
        "разходи и гориво."
    )
