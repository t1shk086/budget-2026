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

DATA_FILE = Path("trips.json")
SETTINGS_FILE = Path("travel_manager_settings.json")

DEFAULT_TRIP_LAYOUT = ["expenses", "categories", "fuel"]

# =========================================================
# DATA
# =========================================================

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
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return {}


def save_trips():
    serializable = {}

    for trip_id, trip in st.session_state.trips.items():
        serializable[trip_id] = {
            "destination": trip["destination"],
            "start_date": trip["start_date"].isoformat(),
            "end_date": trip["end_date"].isoformat(),
            "budget": float(trip.get("budget", 0.0)),
            "expenses": [
                {
                    "amount": float(expense.get("amount", 0.0)),
                    "category": expense.get("category", "📱 Други"),
                    "date": expense["date"].isoformat(),
                    "note": expense.get("note", ""),
                    "is_fuel": expense.get("is_fuel", False),
                    "fuel_liters": float(expense.get("fuel_liters", 0.0)),
                    "fuel_odometer": float(expense.get("fuel_odometer", 0.0)),
                    "fuel_full_tank": expense.get("fuel_full_tank", False)
                }
                for expense in trip.get("expenses", [])
            ]
        }

    DATA_FILE.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def load_settings():
    defaults = {"trip_layout": DEFAULT_TRIP_LAYOUT.copy()}

    if not SETTINGS_FILE.exists():
        return defaults

    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        allowed = DEFAULT_TRIP_LAYOUT.copy()
        layout = raw.get("trip_layout", allowed.copy())

        if not isinstance(layout, list):
            layout = allowed.copy()

        clean = [item for item in layout if item in allowed]

        for item in allowed:
            if item not in clean:
                clean.append(item)

        return {"trip_layout": clean}

    except (json.JSONDecodeError, OSError, TypeError):
        return defaults


def save_settings():
    payload = {
        "trip_layout": list(
            st.session_state.get(
                "trip_layout",
                DEFAULT_TRIP_LAYOUT
            )
        )
    }

    try:
        SETTINGS_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except OSError as error:
        st.error(f"Неуспешно записване на настройките: {error}")


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

if "trip_layout" not in st.session_state:
    st.session_state.trip_layout = load_settings().get(
        "trip_layout",
        DEFAULT_TRIP_LAYOUT.copy()
    )


# =========================================================
# HELPERS
# =========================================================

FUEL_KEYWORDS = (
    "газ", "гориво", "зареждане", "бензин", "дизел"
)

CATEGORIES = [
    "🍔 Храна",
    "🏨 Нощувка",
    "🚗 Транспорт",
    "🎟️ Забавления",
    "🛍️ Покупки",
    "📱 Други"
]


def is_fuel_expense(text):
    text = (text or "").lower()
    return any(keyword in text for keyword in FUEL_KEYWORDS)


def total_expenses():
    return sum(
        float(e.get("amount", 0.0))
        for trip in st.session_state.trips.values()
        for e in trip.get("expenses", [])
    )


def total_budget():
    return sum(
        float(trip.get("budget", 0.0))
        for trip in st.session_state.trips.values()
    )


def trip_expenses(trip):
    return sum(
        float(e.get("amount", 0.0))
        for e in trip.get("expenses", [])
    )


def category_breakdown(trip):
    categories = {}

    for expense in trip.get("expenses", []):
        category = expense.get("category", "📱 Други")
        amount = float(expense.get("amount", 0.0))
        categories[category] = categories.get(category, 0.0) + amount

    total = sum(categories.values())

    result = []
    for category, amount in sorted(
        categories.items(),
        key=lambda item: item[1],
        reverse=True
    ):
        percentage = amount / total * 100 if total else 0
        result.append({
            "category": category,
            "amount": amount,
            "percentage": percentage
        })

    return result


def delete_expense(trip_id, index):
    expenses = st.session_state.trips[trip_id]["expenses"]

    if 0 <= index < len(expenses):
        del expenses[index]
        save_trips()


def update_trip_budget(trip_id, new_budget):
    if trip_id in st.session_state.trips:
        st.session_state.trips[trip_id]["budget"] = float(new_budget)
        save_trips()


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
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #08111a;
    }

    .block-container {
        max-width: 1080px;
        padding-top: 1.6rem;
        padding-bottom: 4rem;
    }

    section[data-testid="stSidebar"] {
        background: #09141f;
        border-right: 1px solid #1a2b3a;
    }

    .stButton > button {
        border-radius: 12px;
        min-height: 44px;
        font-weight: 650;
        border: 1px solid #263c4f;
        background: #101e2a;
        color: #eef5f9;
    }

    .stButton > button:hover {
        border-color: #2b9cff;
        background: #15283a;
    }

    div[data-testid="stMetric"] {
        background: #0d1a26;
        border: 1px solid #1c3041;
        border-radius: 16px;
        padding: 14px 16px;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background: #0d1925;
        border-color: #22374a;
        border-radius: 10px;
    }

    .tm-brand {
        font-size: clamp(1.8rem, 4vw, 2.7rem);
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #f4f8fb;
    }

    .tm-subtitle {
        color: #8fa1b2;
        margin-top: 4px;
    }

    .tm-card {
        background: linear-gradient(145deg, #102130, #0c1823);
        border: 1px solid #203446;
        border-radius: 20px;
        padding: 20px;
        min-height: 118px;
    }

    .tm-card-primary {
        border-color: #235d83;
        background: linear-gradient(145deg, #12314a, #0c1c29);
    }

    .tm-card-title {
        color: #f5f8fb;
        font-size: 1.12rem;
        font-weight: 750;
        margin-bottom: 5px;
    }

    .tm-card-text {
        color: #8fa1b2;
        font-size: .9rem;
    }

    .tm-category-row {
        margin-bottom: 13px;
    }

    .tm-category-row-top {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 6px;
    }

    .tm-category-name {
        color: #cbd8e2;
        font-size: .82rem;
        font-weight: 650;
    }

    .tm-category-value {
        color: #91a5b5;
        font-size: .78rem;
        font-weight: 650;
    }

    .tm-roundbar {
        width: 100%;
        height: 9px;
        background: rgba(255,255,255,.07);
        border-radius: 999px;
        overflow: hidden;
    }

    .tm-roundbar-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg,#1687d9,#35c7ff);
    }

    .tm-category-percent {
        margin-top: 4px;
        color: #71889a;
        font-size: .7rem;
        text-align: right;
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .tm-card {
            padding: 17px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## ✈️ Travel Manager")
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
        <div>
            <div class="tm-brand">✈️ Travel Manager</div>
            <div class="tm-subtitle">
                Всичко за твоите пътувания и разходи на едно място.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    expenses = total_expenses()
    budget = total_budget()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("✈️ Пътувания", len(st.session_state.trips))

    with c2:
        st.metric("💳 Общо разходи", f"€{expenses:.2f}")

    with c3:
        st.metric("💰 Оставащ бюджет", f"€{budget-expenses:.2f}")

    st.write("")
    st.subheader("Бързи действия")

    q1, q2 = st.columns(2)

    with q1:
        st.markdown(
            """
            <div class="tm-card tm-card-primary">
                <div class="tm-card-title">➕ Добави разход</div>
                <div class="tm-card-text">
                    Бързо добавяне на разход към избрано пътуване.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("Добави разход →", use_container_width=True, type="primary"):
            open_add_expense()

    with q2:
        st.markdown(
            """
            <div class="tm-card">
                <div class="tm-card-title">✈️ Ново пътуване</div>
                <div class="tm-card-text">
                    Създай ново пътуване и задай неговия бюджет.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("Създай пътуване →", use_container_width=True):
            st.session_state.page = "new_trip"
            st.rerun()

    st.divider()
    st.subheader("Моите пътувания")

    if not st.session_state.trips:
        st.info("Все още нямаш пътувания.")
    else:
        for trip_id, trip in st.session_state.trips.items():
            spent = trip_expenses(trip)
            trip_budget = float(trip.get("budget", 0))
            progress = min(spent / trip_budget, 1) if trip_budget else 0

            with st.container(border=True):
                c1, c2 = st.columns([4, 1])

                with c1:
                    st.subheader(f"✈️ {trip['destination']}")
                    st.caption(
                        f"{trip['start_date'].strftime('%d.%m.%Y')} – "
                        f"{trip['end_date'].strftime('%d.%m.%Y')}"
                    )
                    st.progress(progress)

                with c2:
                    if st.button(
                        "Отвори →",
                        key=f"home_open_{trip_id}",
                        use_container_width=True
                    ):
                        open_trip(trip_id)


# =========================================================
# NEW TRIP
# =========================================================

elif st.session_state.page == "new_trip":

    st.title("✈️ Ново пътуване")

    if st.button("← Назад"):
        go_home()

    st.divider()

    destination = st.text_input(
        "Дестинация",
        placeholder="Например: Париж"
    )

    c1, c2 = st.columns(2)

    with c1:
        start_date = st.date_input("Начална дата", value=date.today())

    with c2:
        end_date = st.date_input("Крайна дата", value=date.today())

    budget = st.number_input(
        "Бюджет (€)",
        min_value=0.0,
        step=50.0
    )

    if st.button(
        "Създай пътуването",
        type="primary",
        use_container_width=True
    ):
        if not destination.strip():
            st.error("Моля, въведи дестинация.")
        elif end_date < start_date:
            st.error("Крайната дата не може да бъде преди началната.")
        else:
            trip_id = (
                destination.strip()
                + "_"
                + start_date.strftime("%Y%m%d")
            )

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

    if st.button("← Назад"):
        if st.session_state.expense_trip:
            open_trip(st.session_state.expense_trip)
        else:
            go_home()

    st.divider()

    if not st.session_state.trips:
        st.warning("Първо трябва да създадеш пътуване.")
    else:
        trip_ids = list(st.session_state.trips.keys())
        default_trip = st.session_state.expense_trip
        default_index = trip_ids.index(default_trip) if default_trip in trip_ids else 0

        selected_trip = st.selectbox(
            "Към кое пътуване?",
            trip_ids,
            index=default_index,
            format_func=lambda x: st.session_state.trips[x]["destination"]
        )

        amount = st.number_input(
            "Сума (€)",
            min_value=0.0,
            step=1.0
        )

        category = st.selectbox("Категория", CATEGORIES)

        expense_date = st.date_input("Дата", value=date.today())

        note = st.text_input(
            "Описание",
            placeholder="Например: Вечеря, бензин, зареждане"
        )

        fuel_expense = is_fuel_expense(note)

        fuel_liters = 0.0
        fuel_odometer = 0.0
        fuel_full_tank = False

        if fuel_expense:
            st.info("⛽ Разпознат е разход за гориво.")

            fuel_liters = st.number_input(
                "Литри гориво (л)",
                min_value=0.0,
                step=0.1,
                format="%.2f"
            )

            fuel_odometer = st.number_input(
                "Километраж при зареждане (км)",
                min_value=0.0,
                step=1.0
            )

            fuel_full_tank = st.checkbox("Пълен резервоар")

        if st.button(
            "Добави разход",
            type="primary",
            use_container_width=True
        ):
            if amount <= 0:
                st.error("Моля, въведи сума по-голяма от 0.")
            else:
                st.session_state.trips[selected_trip]["expenses"].append({
                    "amount": amount,
                    "category": category,
                    "date": expense_date,
                    "note": note,
                    "is_fuel": fuel_expense,
                    "fuel_liters": fuel_liters if fuel_expense else 0,
                    "fuel_odometer": fuel_odometer if fuel_expense else 0,
                    "fuel_full_tank": fuel_full_tank if fuel_expense else False
                })

                save_trips()

                st.session_state.selected_trip = selected_trip
                st.session_state.expense_trip = None
                st.session_state.page = "trip"
                st.rerun()


# =========================================================
# TRIPS
# =========================================================

elif st.session_state.page == "trips":

    st.title("✈️ Моите пътувания")

    c1, c2 = st.columns([1, 4])

    with c1:
        if st.button("← Начало"):
            go_home()

    with c2:
        if st.button("＋ Ново пътуване", type="primary"):
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
                st.caption(
                    f"{trip['start_date'].strftime('%d.%m.%Y')} – "
                    f"{trip['end_date'].strftime('%d.%m.%Y')}"
                )
                st.write(
                    f"Похарчено: €{spent:.2f} / €{trip['budget']:.2f}"
                )

                if st.button(
                    "Отвори",
                    key=f"trips_open_{trip_id}",
                    use_container_width=True
                ):
                    open_trip(trip_id)


# =========================================================
# TRIP
# =========================================================

elif st.session_state.page == "trip":

    trip_id = st.session_state.selected_trip

    if trip_id is None or trip_id not in st.session_state.trips:
        go_home()

    trip = st.session_state.trips[trip_id]

    if st.button("← Моите пътувания"):
        st.session_state.page = "trips"
        st.rerun()

    st.title(f"✈️ {trip['destination']}")

    st.caption(
        f"{trip['start_date'].strftime('%d.%m.%Y')} – "
        f"{trip['end_date'].strftime('%d.%m.%Y')}"
    )

    st.divider()

    spent = trip_expenses(trip)
    remaining = float(trip.get("budget", 0)) - spent

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("💰 Бюджет", f"€{trip['budget']:.2f}")

    with c2:
        st.metric("💳 Похарчено", f"€{spent:.2f}")

    with c3:
        st.metric("✓ Остава", f"€{remaining:.2f}")

    # -----------------------------------------------------
    # BUDGET
    # -----------------------------------------------------

    with st.expander("💰 Управление на бюджета"):

        budget_value = st.number_input(
            "Бюджет на пътуването (€)",
            min_value=0.0,
            value=float(trip.get("budget", 0)),
            step=50.0,
            format="%.2f",
            key=f"budget_{trip_id}"
        )

        categories = category_breakdown(trip)

        st.markdown("### Бюджет по категории")

        if categories:
            for item in categories:
                st.caption(item["category"])

                category_budget_key = (
                    f"category_budget_{trip_id}_"
                    + item["category"]
                )

                st.number_input(
                    "Лимит (€)",
                    min_value=0.0,
                    value=float(
                        trip.get(
                            "category_budgets",
                            {}
                        ).get(
                            item["category"],
                            0.0
                        )
                    ),
                    step=10.0,
                    key=category_budget_key
                )

        if st.button(
            "💾 Запази бюджета",
            type="primary",
            use_container_width=True
        ):
            trip["budget"] = float(budget_value)

            if "category_budgets" not in trip:
                trip["category_budgets"] = {}

            for item in categories:
                key = (
                    f"category_budget_{trip_id}_"
                    + item["category"]
                )

                if key in st.session_state:
                    trip["category_budgets"][item["category"]] = float(
                        st.session_state[key]
                    )

            save_trips()
            st.success("Бюджетът е запазен.")
            st.rerun()

    if st.button(
        "➕ Добави разход",
        type="primary",
        use_container_width=True
    ):
        open_add_expense(trip_id)

    st.divider()

    # -----------------------------------------------------
    # FUEL DATA
    # -----------------------------------------------------

    fuel_expenses = [
        e for e in trip.get("expenses", [])
        if e.get("is_fuel", False)
    ]

    total_fuel_liters = sum(
        e.get("fuel_liters", 0.0)
        for e in fuel_expenses
    )

    total_fuel_cost = sum(
        e.get("amount", 0.0)
        for e in fuel_expenses
    )

    fuel_with_km = [
        e for e in fuel_expenses
        if e.get("fuel_odometer", 0) > 0
        and e.get("fuel_liters", 0) > 0
    ]

    fuel_with_km.sort(
        key=lambda e: e.get("fuel_odometer", 0)
    )

    avg_price_per_liter = (
        total_fuel_cost / total_fuel_liters
        if total_fuel_liters > 0 else None
    )

    total_distance = 0

    if len(fuel_with_km) >= 2:
        first_odometer = fuel_with_km[0]["fuel_odometer"]
        last_odometer = fuel_with_km[-1]["fuel_odometer"]
        total_distance = max(
            last_odometer - first_odometer,
            0
        )

        overall_consumption = (
            total_fuel_liters / total_distance * 100
            if total_distance > 0 else None
        )
    else:
        first_odometer = None
        last_odometer = None
        overall_consumption = None

    # =====================================================
    # USER SELECTED TRIP LAYOUT
    # =====================================================

    for section in st.session_state.trip_layout:

        # -------------------------------------------------
        # EXPENSES
        # -------------------------------------------------

        if section == "expenses":

            st.subheader(
                f"💳 Разходи ({len(trip.get('expenses', []))})"
            )

            expenses = trip.get("expenses", [])

            if not expenses:
                st.info("Все още няма добавени разходи.")
            else:
                st.caption(
                    f"{len(expenses)} разхода · "
                    f"€{sum(e.get('amount', 0) for e in expenses):.2f}"
                )

                ordered = sorted(
                    enumerate(expenses),
                    key=lambda x: x[1].get("date", date.min),
                    reverse=True
                )

                current_day = None

                for original_index, expense in ordered:

                    expense_date = expense.get("date")

                    if expense_date != current_day:
                        current_day = expense_date
                        st.markdown(
                            f"**{expense_date.strftime('%d.%m.%Y') if expense_date else 'Без дата'}**"
                        )

                    category = expense.get(
                        "category",
                        "📱 Други"
                    )

                    note = (
                        expense.get("note")
                        or "Без описание"
                    ).strip()

                    amount = float(
                        expense.get(
                            "amount",
                            0
                        )
                    )

                    short_note = (
                        note
                        if len(note) <= 38
                        else note[:35] + "..."
                    )

                    expanded_key = (
                        f"expanded_{trip_id}"
                    )

                    if expanded_key not in st.session_state:
                        st.session_state[expanded_key] = None

                    expanded = (
                        st.session_state[expanded_key]
                        == original_index
                    )

                    r1, r2 = st.columns([5, 1.2])

                    with r1:
                        if st.button(
                            f"{category} · {short_note}",
                            key=f"expense_{trip_id}_{original_index}",
                            use_container_width=True
                        ):
                            st.session_state[expanded_key] = (
                                None
                                if expanded
                                else original_index
                            )
                            st.rerun()

                    with r2:
                        st.markdown(
                            f"""
                            <div style="
                                text-align:right;
                                padding-top:9px;
                                font-weight:800;
                                white-space:nowrap;">
                                €{amount:.2f}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    if expanded:

                        with st.container(border=True):

                            if expense.get("note"):
                                st.write(
                                    expense["note"]
                                )

                            if expense.get(
                                "is_fuel",
                                False
                            ):
                                liters = float(
                                    expense.get(
                                        "fuel_liters",
                                        0
                                    )
                                )

                                odo = float(
                                    expense.get(
                                        "fuel_odometer",
                                        0
                                    )
                                )

                                info = []

                                if liters > 0:
                                    info.append(
                                        f"{liters:.2f} л"
                                    )
                                    info.append(
                                        f"€{amount/liters:.2f}/л"
                                    )

                                if odo > 0:
                                    info.append(
                                        f"{odo:.0f} км"
                                    )

                                if expense.get(
                                    "fuel_full_tank",
                                    False
                                ):
                                    info.append(
                                        "✓ Пълен резервоар"
                                    )

                                if info:
                                    st.caption(
                                        "⛽ "
                                        + " · ".join(info)
                                    )

                            b1, b2 = st.columns(2)

                            with b1:
                                if st.button(
                                    "🗑️ Изтрий",
                                    key=f"delete_{trip_id}_{original_index}",
                                    use_container_width=True
                                ):
                                    delete_expense(
                                        trip_id,
                                        original_index
                                    )

                                    st.session_state[
                                        expanded_key
                                    ] = None

                                    st.rerun()

                    st.divider()

        # -------------------------------------------------
        # CATEGORIES
        # -------------------------------------------------

        elif section == "categories":

            st.subheader(
                "📊 Интерактивен анализ по категории"
            )

            categories = category_breakdown(trip)

            if not categories:
                st.info(
                    "Все още няма разходи по категории."
                )
            else:

                names = [
                    item["category"]
                    for item in categories
                ]

                selected = st.selectbox(
                    "Избери категория",
                    ["Всички"] + names,
                    key=f"category_filter_{trip_id}"
                )

                total_trip = trip_expenses(trip)

                if selected == "Всички":
                    visible = trip.get(
                        "expenses",
                        []
                    )

                    selected_total = total_trip

                else:
                    visible = [
                        e for e in trip.get(
                            "expenses",
                            []
                        )
                        if e.get(
                            "category",
                            "📱 Други"
                        ) == selected
                    ]

                    selected_total = sum(
                        float(e.get("amount", 0))
                        for e in visible
                    )

                percentage = (
                    selected_total / total_trip * 100
                    if total_trip > 0 else 0
                )

                a1, a2, a3 = st.columns(3)

                with a1:
                    st.metric(
                        "💶 Общо",
                        f"€{selected_total:.2f}"
                    )

                with a2:
                    st.metric(
                        "🧾 Разходи",
                        len(visible)
                    )

                with a3:
                    st.metric(
                        "📈 Дял",
                        f"{percentage:.1f}%"
                    )

                st.write("")

                for item in categories:

                    if (
                        selected != "Всички"
                        and item["category"] != selected
                    ):
                        continue

                    st.markdown(
                        f"""
                        <div class="tm-category-row">
                            <div class="tm-category-row-top">
                                <div class="tm-category-name">
                                    {item["category"]}
                                </div>
                                <div class="tm-category-value">
                                    €{item["amount"]:.2f}
                                </div>
                            </div>

                            <div class="tm-roundbar">
                                <div class="tm-roundbar-fill"
                                     style="width:{min(item["percentage"],100):.1f}%">
                                </div>
                            </div>

                            <div class="tm-category-percent">
                                {item["percentage"]:.1f}%
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # -------------------------------------------------
        # FUEL
        # -------------------------------------------------

        elif section == "fuel":

            st.subheader(
                "🚗 Гориво и километраж"
            )

            if not fuel_expenses:

                st.info(
                    "Все още няма отчетени разходи за гориво."
                )

            else:

                f1, f2, f3 = st.columns(3)

                with f1:
                    st.metric(
                        "Зареждания",
                        len(fuel_expenses)
                    )

                with f2:
                    st.metric(
                        "Общо литри",
                        f"{total_fuel_liters:.2f} л"
                    )

                with f3:
                    st.metric(
                        "Разход за гориво",
                        f"€{total_fuel_cost:.2f}"
                    )

                f4, f5 = st.columns(2)

                with f4:
                    if avg_price_per_liter is not None:
                        st.metric(
                            "Средна цена",
                            f"€{avg_price_per_liter:.2f}/л"
                        )

                with f5:
                    if overall_consumption is not None:
                        st.metric(
                            "Среден разход",
                            f"{overall_consumption:.2f} л/100 км"
                        )

                if total_distance > 0:

                    st.markdown(
                        f"""
                        <div style="
                            padding:16px;
                            border:1px solid rgba(120,120,140,.18);
                            border-radius:16px;
                            background:rgba(255,255,255,.035);
                            margin-top:15px;">

                            <div style="
                                display:flex;
                                justify-content:space-between;
                                gap:10px;">

                                <div>
                                    <div style="font-size:11px;opacity:.55">
                                        Начален
                                    </div>
                                    <b>
                                        {first_odometer:,.0f} км
                                    </b>
                                </div>

                                <div style="text-align:center">
                                    <div style="font-size:11px;opacity:.55">
                                        Пробег
                                    </div>
                                    <div style="
                                        font-size:24px;
                                        font-weight:800;">
                                        {total_distance:,.0f} км
                                    </div>
                                </div>

                                <div style="text-align:right">
                                    <div style="font-size:11px;opacity:.55">
                                        Последен
                                    </div>
                                    <b>
                                        {last_odometer:,.0f} км
                                    </b>
                                </div>

                            </div>

                            <div style="
                                height:9px;
                                border-radius:999px;
                                background:rgba(128,128,128,.18);
                                overflow:hidden;
                                margin-top:14px;">

                                <div style="
                                    height:100%;
                                    width:100%;
                                    border-radius:999px;
                                    background:linear-gradient(
                                        90deg,
                                        #7c5cff,
                                        #35c7ff
                                    );">
                                </div>

                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


# =========================================================
# ANALYTICS
# =========================================================

elif st.session_state.page == "analytics":

    st.title("📊 Анализи")

    if not st.session_state.trips:
        st.info("Няма налични пътувания.")
    else:

        trip_ids = list(
            st.session_state.trips.keys()
        )

        selected = st.selectbox(
            "Пътуване",
            trip_ids,
            format_func=lambda x:
                st.session_state.trips[x]["destination"]
        )

        trip = st.session_state.trips[selected]
        categories = category_breakdown(trip)

        if not categories:
            st.info("Няма разходи.")
        else:
            for item in categories:
                st.markdown(
                    f"""
                    <div class="tm-category-row">
                        <div class="tm-category-row-top">
                            <span class="tm-category-name">
                                {item["category"]}
                            </span>
                            <span class="tm-category-value">
                                €{item["amount"]:.2f}
                            </span>
                        </div>
                        <div class="tm-roundbar">
                            <div class="tm-roundbar-fill"
                                 style="width:{min(item["percentage"],100):.1f}%">
                            </div>
                        </div>
                        <div class="tm-category-percent">
                            {item["percentage"]:.1f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    if st.button("← Начало"):
        go_home()


# =========================================================
# HISTORY
# =========================================================

elif st.session_state.page == "history":

    st.title("🕘 История")

    if not st.session_state.trips:
        st.info("Няма история.")
    else:
        for trip in st.session_state.trips.values():
            for expense in sorted(
                trip.get("expenses", []),
                key=lambda e: e.get("date", date.min),
                reverse=True
            ):
                st.write(
                    f"**{trip['destination']}** · "
                    f"{expense.get('category','📱 Други')} · "
                    f"€{float(expense.get('amount',0)):.2f}"
                )

    if st.button("← Начало"):
        go_home()


# =========================================================
# COMPARISON
# =========================================================

elif st.session_state.page == "comparison":

    st.title("⇄ Сравнение")

    if len(st.session_state.trips) < 2:
        st.info(
            "Необходими са поне две пътувания."
        )
    else:
        for trip in st.session_state.trips.values():
            st.metric(
                trip["destination"],
                f"€{trip_expenses(trip):.2f}"
            )

    if st.button("← Начало"):
        go_home()


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "settings":

    st.title("⚙️ Настройки")

    if st.button("← Начало"):
        go_home()

    st.divider()

    st.subheader(
        "🎨 Как искате да се визуализира пътуването ви?"
    )

    st.caption(
        "Изберете секциите и ги подредете в желания ред."
    )

    labels = {
        "expenses": "📜 Разходи",
        "categories": "📊 Разходи по категории",
        "fuel": "🚗 Гориво и километраж"
    }

    enabled = {}

    for key, label in labels.items():
        enabled[key] = st.checkbox(
            label,
            value=key in st.session_state.trip_layout,
            key=f"enabled_{key}"
        )

    ordered = [
        key
        for key in st.session_state.trip_layout
        if enabled.get(key, False)
    ]

    for key in labels:
        if enabled[key] and key not in ordered:
            ordered.append(key)

    st.markdown("### Подредба")

    for i, key in enumerate(ordered):

        c1, c2, c3 = st.columns(
            [0.6, 4, 2]
        )

        with c1:
            st.write(f"**{i+1}.**")

        with c2:
            st.write(labels[key])

        with c3:

            up, down = st.columns(2)

            with up:
                if st.button(
                    "↑",
                    key=f"up_{key}",
                    disabled=i == 0,
                    use_container_width=True
                ):
                    ordered[i-1], ordered[i] = (
                        ordered[i],
                        ordered[i-1]
                    )

                    st.session_state.trip_layout = ordered
                    save_settings()
                    st.rerun()

            with down:
                if st.button(
                    "↓",
                    key=f"down_{key}",
                    disabled=i == len(ordered)-1,
                    use_container_width=True
                ):
                    ordered[i+1], ordered[i] = (
                        ordered[i],
                        ordered[i+1]
                    )

                    st.session_state.trip_layout = ordered
                    save_settings()
                    st.rerun()

    if st.button(
        "💾 Запази настройките",
        type="primary",
        use_container_width=True
    ):

        if not ordered:
            st.error(
                "Избери поне една секция."
            )
        else:
            st.session_state.trip_layout = ordered.copy()
            save_settings()

            st.success(
                "Настройките са запазени постоянно."
            )
