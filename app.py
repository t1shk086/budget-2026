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


def format_money(value):
    return f"€{value:,.2f}"


def budget_percent(trip):
    if trip["budget"] <= 0:
        return 0

    return min(
        trip_expenses(trip) / trip["budget"],
        1
    )


# =========================================================
# NAVIGATION
# =========================================================

def navigate(page):
    st.session_state.page = page
    st.rerun()


def open_trip(trip_id):
    st.session_state.selected_trip = trip_id
    st.session_state.page = "trip"
    st.rerun()


def open_add_expense(trip_id=None):

    st.session_state.expense_trip = trip_id
    st.session_state.page = "add_expense"
    st.rerun()


def go_home():

    st.session_state.page = "home"
    st.session_state.selected_trip = None
    st.session_state.expense_trip = None
    st.rerun()


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 10% 0%,
                rgba(20,120,255,.12),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 10%,
                rgba(0,210,160,.07),
                transparent 25%
            ),
            #070d14;
        color: #f5f8fc;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* SIDEBAR */

    section[data-testid="stSidebar"] {
        background: #09111b;
        border-right: 1px solid #18293a;
    }

    .logo {
        font-size: 23px;
        font-weight: 800;
        margin-bottom: 25px;
    }

    .logo-blue {
        color: #29a7ff;
    }

    .logo-sub {
        color: #687c91;
        font-size: 11px;
        margin-top: -20px;
        margin-left: 30px;
        margin-bottom: 25px;
    }

    /* CARDS */

    .card {
        background:
            linear-gradient(
                145deg,
                #111f2e,
                #0b151f
            );
        border: 1px solid #1c3044;
        border-radius: 18px;
        padding: 20px;
        box-shadow:
            0 12px 30px rgba(0,0,0,.18);
    }

    .metric {
        min-height: 130px;
    }

    .metric-label {
        color: #8498ad;
        font-size: 13px;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .metric-small {
        color: #71869c;
        font-size: 11px;
        margin-top: 8px;
    }

    /* QUICK ACTIONS */

    .quick-card {
        min-height: 115px;
        border-radius: 18px;
        padding: 22px;
        color: white;
    }

    .quick-green {
        background:
            linear-gradient(
                135deg,
                #11bd91,
                #098eaa
            );
    }

    .quick-blue {
        background:
            linear-gradient(
                135deg,
                #167cff,
                #174bb8
            );
    }

    .quick-icon {
        font-size: 28px;
    }

    .quick-title {
        font-size: 20px;
        font-weight: 800;
    }

    .quick-sub {
        font-size: 12px;
        opacity: .82;
        margin-top: 4px;
    }

    /* TRIP */

    .trip-card {
        background:
            linear-gradient(
                145deg,
                #101d2b,
                #0b151f
            );
        border: 1px solid #1b3044;
        border-radius: 17px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .trip-name {
        font-size: 18px;
        font-weight: 700;
    }

    .trip-date {
        color: #7e93a8;
        font-size: 12px;
        margin-top: 4px;
    }

    .trip-amount {
        color: #dce6ef;
        font-size: 13px;
        margin-top: 12px;
    }

    .progress-background {
        height: 7px;
        background: #1a2939;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 10px;
    }

    .progress-value {
        height: 100%;
        background:
            linear-gradient(
                90deg,
                #19d6a0,
                #1ca6ff
            );
        border-radius: 10px;
    }

    /* EXPENSE */

    .expense-card {
        background: #0d1925;
        border: 1px solid #1b2d40;
        border-radius: 14px;
        padding: 15px;
        margin-bottom: 8px;
    }

    /* BUTTONS */

    .stButton > button {
        border-radius: 11px !important;
        border: 1px solid #24384d !important;
        background: #101c29 !important;
        color: #eef5fb !important;
        min-height: 43px;
        font-weight: 600;
    }

    .stButton > button:hover {
        border-color: #238cff !important;
        background: #142638 !important;
    }

    /* INPUTS */

    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    textarea {
        background: #0b1723 !important;
        border-color: #20364a !important;
        border-radius: 10px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="logo">
            🐾 <span class="logo-blue">Pixel</span>App
        </div>

        <div class="logo-sub">
            TRAVEL MANAGER
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "⌂  Начало",
        use_container_width=True
    ):
        navigate("home")

    if st.button(
        "▤  Пътувания",
        use_container_width=True
    ):
        navigate("trips")

    if st.button(
        "＋  Добави разход",
        use_container_width=True
    ):
        open_add_expense()

    st.markdown("<br>", unsafe_allow_html=True)

    st.caption("Още")

    if st.button(
        "◈  Анализи",
        use_container_width=True
    ):
        navigate("analytics")

    if st.button(
        "◉  История + Класации",
        use_container_width=True
    ):
        navigate("history")

    if st.button(
        "⇄  Сравнение",
        use_container_width=True
    ):
        navigate("comparison")

    if st.button(
        "⚙  Настройки",
        use_container_width=True
    ):
        navigate("settings")


# =========================================================
# HOME
# =========================================================

def render_home():

    st.title("👋 Добре дошъл в Travel Manager")

    st.markdown(
        """
        <div style="
            color:#8195aa;
            margin-bottom:25px;
        ">
            Всичко за твоите пътувания и разходи на едно място.
        </div>
        """,
        unsafe_allow_html=True
    )

    expenses = total_expenses()
    budget = total_budget()
    remaining = budget - expenses

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        (
            "✈️ Пътувания",
            str(len(st.session_state.trips)),
            "активни и завършени"
        ),
        (
            "💳 Общо разходи",
            format_money(expenses),
            "за всички пътувания"
        ),
        (
            "◷ Общ бюджет",
            format_money(budget),
            "планиран"
        ),
        (
            "✓ Оставащ бюджет",
            format_money(remaining),
            "наличен"
        )
    ]

    for column, data in zip(
        [c1, c2, c3, c4],
        metrics
    ):

        with column:

            st.markdown(
                f"""
                <div class="card metric">

                    <div class="metric-label">
                        {data[0]}
                    </div>

                    <div class="metric-value">
                        {data[1]}
                    </div>

                    <div class="metric-small">
                        {data[2]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # QUICK ACTIONS
    # -----------------------------------------------------

    st.markdown(
        "### Бързи действия"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="quick-card quick-green">

                <div class="quick-icon">＋</div>

                <div class="quick-title">
                    Добави разход
                </div>

                <div class="quick-sub">
                    Бързо добавяне към пътуване
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Добави разход →",
            key="home_add_expense",
            use_container_width=True
        ):
            open_add_expense()

    with c2:

        st.markdown(
            """
            <div class="quick-card quick-blue">

                <div class="quick-icon">✈️</div>

                <div class="quick-title">
                    Ново пътуване
                </div>

                <div class="quick-sub">
                    Създай пътуване и задай бюджет
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Създай пътуване →",
            key="home_new_trip",
            use_container_width=True
        ):
            navigate("new_trip")

    # -----------------------------------------------------
    # TRIPS
    # -----------------------------------------------------

    st.markdown(
        "### Моите пътувания"
    )

    if not st.session_state.trips:

        st.markdown(
            """
            <div class="card">

                <div style="
                    font-size:18px;
                    font-weight:700;
                ">
                    Все още нямаш пътувания
                </div>

                <div style="
                    color:#8195aa;
                    margin-top:6px;
                ">
                    Създай първото си пътуване
                    от бутона „Ново пътуване“.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        for trip_id, trip in st.session_state.trips.items():

            render_trip_card(
                trip_id,
                trip
            )


# =========================================================
# TRIP CARD
# =========================================================

def render_trip_card(
    trip_id,
    trip
):

    spent = trip_expenses(trip)
    percent = budget_percent(trip)
    percent_display = int(percent * 100)

    c1, c2 = st.columns(
        [5, 1]
    )

    with c1:

        st.markdown(
            f"""
            <div class="trip-card">

                <div class="trip-name">
                    ✈️ {trip["destination"]}
                </div>

                <div class="trip-date">
                    {trip["start_date"].strftime("%d.%m.%Y")}
                    –
                    {trip["end_date"].strftime("%d.%m.%Y")}
                </div>

                <div class="trip-amount">
                    Похарчено:
                    <b>{format_money(spent)}</b>
                    &nbsp; / &nbsp;
                    Бюджет:
                    <b>{format_money(trip["budget"])}</b>
                </div>

                <div class="progress-background">

                    <div
                        class="progress-value"
                        style="width:{percent_display}%"
                    ></div>

                </div>

                <div style="
                    color:#71869b;
                    font-size:11px;
                    margin-top:6px;
                ">
                    {percent_display}% използван бюджет
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Отвори →",
            key=f"trip_open_{trip_id}",
            use_container_width=True
        ):
            open_trip(trip_id)


# =========================================================
# TRIPS PAGE
# =========================================================

def render_trips():

    st.title("✈️ Моите пътувания")

    if st.button(
        "＋ Ново пътуване",
        type="primary"
    ):
        navigate("new_trip")

    st.divider()

    if not st.session_state.trips:

        st.info(
            "Все още няма създадени пътувания."
        )

    else:

        for trip_id, trip in st.session_state.trips.items():

            render_trip_card(
                trip_id,
                trip
            )


# =========================================================
# NEW TRIP PAGE
# =========================================================

def render_new_trip():

    st.title("✈️ Ново пътуване")

    if st.button("← Назад"):
        go_home()

    st.divider()

    with st.container(border=True):

        destination = st.text_input(
            "Дестинация",
            placeholder="Например: Гърция"
        )

        c1, c2 = st.columns(2)

        with c1:

            start_date = st.date_input(
                "Начална дата",
                date.today()
            )

        with c2:

            end_date = st.date_input(
                "Крайна дата",
                date.today()
            )

        budget = st.number_input(
            "Бюджет (€)",
            min_value=0.0,
            step=50.0
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Създай пътуването",
            type="primary",
            use_container_width=True
        ):

            if not destination.strip():

                st.error(
                    "Моля, въведи дестинация."
                )

            elif end_date < start_date:

                st.error(
                    "Крайната дата не може да е "
                    "преди началната."
                )

            else:

                trip_id = (
                    f"{destination.strip()} "
                    f"{start_date.strftime('%d.%m.%Y')}"
                )

                st.session_state.trips[trip_id] = {

                    "destination":
                        destination.strip(),

                    "start_date":
                        start_date,

                    "end_date":
                        end_date,

                    "budget":
                        budget,

                    "expenses":
                        []
                }

                st.session_state.selected_trip = trip_id

                st.session_state.page = "trip"

                st.rerun()


# =========================================================
# ADD EXPENSE PAGE
# =========================================================

def render_add_expense():

    st.title("＋ Добави разход")

    if st.button("← Назад"):

        if st.session_state.expense_trip:
            open_trip(
                st.session_state.expense_trip
            )
        else:
            go_home()

    st.divider()

    if not st.session_state.trips:

        st.info(
            "Първо трябва да създадеш пътуване."
        )

        if st.button(
            "✈️ Създай пътуване",
            type="primary"
        ):
            navigate("new_trip")

        return

    # -----------------------------------------------------
    # TRIP SELECTION
    # -----------------------------------------------------

    trip_ids = list(
        st.session_state.trips.keys()
    )

    selected_trip_id = st.session_state.expense_trip

    if selected_trip_id not in trip_ids:

        selected_trip_id = st.selectbox(
            "Пътуване",
            trip_ids
        )

    else:

        selected_trip_id = st.selectbox(
            "Пътуване",
            trip_ids,
            index=trip_ids.index(
                selected_trip_id
            )
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # FORM
    # -----------------------------------------------------

    with st.container(border=True):

        amount = st.number_input(
            "Сума (€)",
            min_value=0.0,
            step=1.0
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
            ]
        )

        expense_date = st.date_input(
            "Дата",
            date.today()
        )

        note = st.text_input(
            "Бележка",
            placeholder="Например: Вечеря"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Добави разход",
            type="primary",
            use_container_width=True
        ):

            if amount <= 0:

                st.error(
                    "Моля, въведи сума по-голяма от 0."
                )

            else:

                st.session_state.trips[
                    selected_trip_id
                ]["expenses"].append(
                    {
                        "amount": amount,
                        "category": category,
                        "date": expense_date,
                        "note": note
                    }
                )

                # След добавяне отиваме
                # директно към пътуването

                open_trip(
                    selected_trip_id
                )


# =========================================================
# TRIP PAGE
# =========================================================

def render_trip():

    trip_id = st.session_state.selected_trip

    if (
        not trip_id
        or trip_id not in st.session_state.trips
    ):
        go_home()

    trip = st.session_state.trips[trip_id]

    if st.button(
        "← Моите пътувания"
    ):
        navigate("trips")

    st.title(
        f"✈️ {trip['destination']}"
    )

    st.caption(
        f"{trip['start_date'].strftime('%d.%m.%Y')} "
        f"– "
        f"{trip['end_date'].strftime('%d.%m.%Y')}"
    )

    spent = trip_expenses(trip)

    remaining = (
        trip["budget"] - spent
    )

    st.divider()

    # -----------------------------------------------------
    # TRIP METRICS
    # -----------------------------------------------------

    c1, c2, c3 = st.columns(3)

    values = [
        (
            "Бюджет",
            format_money(trip["budget"])
        ),
        (
            "Похарчено",
            format_money(spent)
        ),
        (
            "Остава",
            format_money(remaining)
        )
    ]

    for column, value in zip(
        [c1, c2, c3],
        values
    ):

        with column:

            st.markdown(
                f"""
                <div class="card metric">

                    <div class="metric-label">
                        {value[0]}
                    </div>

                    <div class="metric-value">
                        {value[1]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # ADD EXPENSE
    # -----------------------------------------------------

    if st.button(
        "＋ Добави разход",
        type="primary",
        use_container_width=True
    ):

        open_add_expense(
            trip_id
        )

    # -----------------------------------------------------
    # EXPENSES
    # -----------------------------------------------------

    st.markdown(
        "### Разходи"
    )

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

        for expense in expenses:

            c1, c2 = st.columns(
                [4, 1]
            )

            with c1:

                st.markdown(
                    f"""
                    <div class="expense-card">

                        <b>
                            {expense["category"]}
                        </b>

                        <div style="
                            color:#d5e0eb;
                            margin-top:5px;
                        ">
                            {expense["note"]
                            if expense["note"]
                            else "Без бележка"}
                        </div>

                        <div style="
                            color:#71869b;
                            font-size:11px;
                            margin-top:5px;
                        ">
                            {expense["date"].strftime("%d.%m.%Y")}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c2:

                st.metric(
                    "Сума",
                    format_money(
                        expense["amount"]
                    )
                )


# =========================================================
# PLACEHOLDER PAGES
# =========================================================

def render_placeholder(
    title,
    description
):

    st.title(title)

    st.markdown(
        f"""
        <div class="card">

            <div style="
                font-size:18px;
                font-weight:700;
            ">
                {title}
            </div>

            <div style="
                color:#8195aa;
                margin-top:8px;
            ">
                {description}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("← Начало"):
        go_home()


# =========================================================
# ROUTER
# =========================================================

page = st.session_state.page

if page == "home":

    render_home()

elif page == "trips":

    render_trips()

elif page == "new_trip":

    render_new_trip()

elif page == "add_expense":

    render_add_expense()

elif page == "trip":

    render_trip()

elif page == "analytics":

    render_placeholder(
        "📊 Анализи",
        "Тук ще изградим анализа на разходите."
    )

elif page == "history":

    render_placeholder(
        "🏆 История + Класации",
        "Тук ще изградим историята и класациите."
    )

elif page == "comparison":

    render_placeholder(
        "⇄ Сравнение",
        "Тук ще изградим сравнението между пътуванията."
    )

elif page == "settings":

    render_placeholder(
        "⚙️ Настройки",
        "Тук ще изградим настройките на приложението."
    )

else:

    go_home()
