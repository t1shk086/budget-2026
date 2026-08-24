import streamlit as st
from datetime import date


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Travel Manager",
    page_icon="✈️",
    layout="wide"
)


# =========================================================
# SESSION STATE
# =========================================================

if "trips" not in st.session_state:
    st.session_state.trips = {}

if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_trip" not in st.session_state:
    st.session_state.selected_trip = None

if "expense_trip" not in st.session_state:
    st.session_state.expense_trip = None


# =========================================================
# DATA
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

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
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
        color: #ffffff;
    }

    div[data-testid="stMetric"] {
        background: #0d1a26;
        border: 1px solid #1c3041;
        border-radius: 16px;
        padding: 14px 16px;
    }

    div[data-testid="stMetricLabel"] {
        color: #8fa1b2;
    }

    div[data-testid="stMetricValue"] {
        color: #f4f8fb;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background: #0d1925;
        border-color: #22374a;
        border-radius: 10px;
    }

    hr {
        border-color: #1a2a39;
    }

    details {
        background: #0d1925;
        border: 1px solid #1b2d3e;
        border-radius: 14px;
    }

    .tm-header {
        padding: 8px 0 18px 0;
    }

    .tm-brand {
        font-size: clamp(1.8rem, 4vw, 2.7rem);
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #f4f8fb;
        margin: 0;
    }

    .tm-subtitle {
        color: #8fa1b2;
        margin-top: 4px;
        font-size: 0.98rem;
    }

    .tm-card {
        background: linear-gradient(145deg, #102130, #0c1823);
        border: 1px solid #203446;
        border-radius: 20px;
        padding: 20px;
        min-height: 118px;
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
        margin-bottom: 5px;
    }

    .tm-card-text {
        color: #8fa1b2;
        font-size: .9rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px;
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }

        .tm-card {
            min-height: auto;
            padding: 17px;
        }

        div[data-testid="stMetric"] {
            padding: 11px 12px;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.35rem;
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
        st.session_state.page = "trips"
        st.rerun()

    if st.button(
        "＋  Добави разход",
        use_container_width=True,
        key="nav_expense"
    ):
        open_add_expense()

    st.divider()

    st.caption("Планиране")

    if st.button(
        "📊  Анализи",
        use_container_width=True,
        key="nav_analysis"
    ):
        st.session_state.page = "analytics"
        st.rerun()

    if st.button(
        "🕘  История",
        use_container_width=True,
        key="nav_history"
    ):
        st.session_state.page = "history"
        st.rerun()

    if st.button(
        "⇄  Сравнение",
        use_container_width=True,
        key="nav_comparison"
    ):
        st.session_state.page = "comparison"
        st.rerun()

    if st.button(
        "⚙️  Настройки",
        use_container_width=True,
        key="nav_settings"
    ):
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
            <div class="tm-subtitle">
                Всичко за твоите пътувания и разходи на едно място.
            </div>
        </div>
        """,
        unsafe_allow_html=True
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
            len(st.session_state.trips)
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

    # -----------------------------------------------------
    # QUICK ACTIONS
    # -----------------------------------------------------

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

        if st.button(
            "Добави разход →",
            use_container_width=True,
            type="primary",
            key="quick_add"
        ):
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

        if st.button(
            "Създай пътуване →",
            use_container_width=True,
            key="quick_trip"
        ):
            st.session_state.page = "new_trip"
            st.rerun()

    st.write("")
    st.divider()

    # -----------------------------------------------------
    # MY TRIPS
    # -----------------------------------------------------

    st.subheader("Моите пътувания")

    if not st.session_state.trips:

        st.info(
            "Все още нямаш пътувания. "
            "Създай първото си пътуване от бутона по-горе."
        )

    else:

        for trip_id, trip in st.session_state.trips.items():

            spent = trip_expenses(trip)
            trip_budget = trip["budget"]

            if trip_budget > 0:
                progress = min(
                    spent / trip_budget,
                    1.0
                )
            else:
                progress = 0

            with st.container(border=True):

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
                        f"€{spent:.2f} "
                        f"от €{trip_budget:.2f}"
                    )

                with c2:

                    st.write("")

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

    if st.button(
        "← Назад",
        key="new_trip_back"
    ):
        go_home()

    st.divider()

    destination = st.text_input(
        "Дестинация",
        placeholder="Например: Париж"
    )

    c1, c2 = st.columns(2)

    with c1:

        start_date = st.date_input(
            "Начална дата",
            value=date.today()
        )

    with c2:

        end_date = st.date_input(
            "Крайна дата",
            value=date.today()
        )

    budget = st.number_input(
        "Бюджет (€)",
        min_value=0.0,
        step=50.0
    )

    st.write("")

    if st.button(
        "Създай пътуването",
        type="primary",
        use_container_width=True,
        key="create_trip"
    ):

        if not destination.strip():

            st.error(
                "Моля, въведи дестинация."
            )

        elif end_date < start_date:

            st.error(
                "Крайната дата не може да бъде "
                "преди началната."
            )

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

            st.session_state.selected_trip = trip_id
            st.session_state.page = "trip"

            st.rerun()


# =========================================================
# ADD EXPENSE
# =========================================================

elif st.session_state.page == "add_expense":

    st.title("➕ Добави разход")

    if st.button(
        "← Назад",
        key="expense_back"
    ):

        if st.session_state.expense_trip:

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
            key="expense_create_trip"
        ):

            st.session_state.page = "new_trip"
            st.rerun()

    else:

        trip_ids = list(
            st.session_state.trips.keys()
        )

        default_trip = st.session_state.expense_trip

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
                st.session_state.trips[x]["destination"],
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
            "Бележка",
            placeholder="Например: Вечеря",
            key="expense_note"
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
                        "amount": amount,
                        "category": category,
                        "date": expense_date,
                        "note": note
                    }
                )

                st.session_state.selected_trip = selected_trip
                st.session_state.expense_trip = None
                st.session_state.page = "trip"

                st.rerun()


# =========================================================
# TRIPS
# =========================================================

elif st.session_state.page == "trips":

    st.title("✈️ Моите пътувания")

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
            st.session_state.page = "new_trip"
            st.rerun()

    st.divider()

    if not st.session_state.trips:

        st.info(
            "Все още нямаш създадени пътувания."
        )

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

                st.write(
                    f"Похарчено: €{spent:.2f} "
                    f"/ "
                    f"€{trip['budget']:.2f}"
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

    if (
        trip_id is None
        or trip_id not in st.session_state.trips
    ):
        go_home()

    trip = st.session_state.trips[trip_id]

    if st.button(
        "← Моите пътувания",
        key="trip_back"
    ):

        st.session_state.page = "trips"
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
    remaining = trip["budget"] - spent

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

    st.subheader("Разходи")

    if not trip["expenses"]:

        st.info(
            "Все още няма добавени разходи."
        )

    else:

        expenses = sorted(
            trip["expenses"],
            key=lambda x: x["date"],
            reverse=True
        )

        for index, expense in enumerate(expenses):

            with st.container(border=True):

                c1, c2 = st.columns(
                    [4, 1]
                )

                with c1:

                    st.write(
                        f"**{expense['category']}**"
                    )

                    if expense["note"]:

                        st.write(
                            expense["note"]
                        )

                    st.caption(
                        expense["date"].strftime(
                            "%d.%m.%Y"
                        )
                    )

                with c2:

                    st.metric(
                        "Сума",
                        f"€{expense['amount']:.2f}"
                    )


# =========================================================
# PLACEHOLDER PAGES
# =========================================================

elif st.session_state.page == "analytics":

    st.title("📊 Анализи")

    st.info(
        "Тук ще изградим анализа на разходите."
    )

    if st.button(
        "← Начало",
        key="analytics_home"
    ):
        go_home()


elif st.session_state.page == "history":

    st.title("🕘 История")

    st.info(
        "Тук ще изградим историята на разходите."
    )

    if st.button(
        "← Начало",
        key="history_home"
    ):
        go_home()


elif st.session_state.page == "comparison":

    st.title("⇄ Сравнение")

    st.info(
        "Тук ще изградим сравнението между пътуванията."
    )

    if st.button(
        "← Начало",
        key="comparison_home"
    ):
        go_home()


elif st.session_state.page == "settings":

    st.title("⚙️ Настройки")

    st.info(
        "Тук ще изградим настройките."
    )

    if st.button(
        "← Начало",
        key="settings_home"
    ):
        go_home()
