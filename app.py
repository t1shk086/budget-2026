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
    initial_sidebar_state="expanded"
)


# =========================================================
# SESSION STATE
# =========================================================

DATA_FILE = Path("trips.json")


def load_trips():

    if not DATA_FILE.exists():
        return {}

    try:

        raw = json.loads(
            DATA_FILE.read_text(
                encoding="utf-8"
            )
        )

        for trip in raw.values():

            trip["start_date"] = date.fromisoformat(
                trip["start_date"]
            )

            trip["end_date"] = date.fromisoformat(
                trip["end_date"]
            )

            for expense in trip.get(
                "expenses",
                []
            ):

                expense["date"] = date.fromisoformat(
                    expense["date"]
                )

                expense["is_fuel"] = expense.get(
                    "is_fuel",
                    False
                )

                expense["fuel_liters"] = expense.get(
                    "fuel_liters",
                    0.0
                )

                expense["fuel_odometer"] = expense.get(
                    "fuel_odometer",
                    0.0
                )

                expense["fuel_full_tank"] = expense.get(
                    "fuel_full_tank",
                    False
                )

        return raw

    except (
        json.JSONDecodeError,
        OSError,
        ValueError
    ):

        return {}


def save_trips():

    serializable = {}

    for trip_id, trip in st.session_state.trips.items():

        serializable[trip_id] = {

            "destination":
                trip["destination"],

            "start_date":
                trip["start_date"].isoformat(),

            "end_date":
                trip["end_date"].isoformat(),

            "budget":
                trip["budget"],

            "expenses": [

                {
                    "amount":
                        expense["amount"],

                    "category":
                        expense["category"],

                    "date":
                        expense["date"].isoformat(),

                    "note":
                        expense["note"],

                    "is_fuel":
                        expense.get(
                            "is_fuel",
                            False
                        ),

                    "fuel_liters":
                        expense.get(
                            "fuel_liters",
                            0.0
                        ),

                    "fuel_odometer":
                        expense.get(
                            "fuel_odometer",
                            0.0
                        ),

                    "fuel_full_tank":
                        expense.get(
                            "fuel_full_tank",
                            False
                        )
                }

                for expense
                in trip["expenses"]
            ]
        }

    DATA_FILE.write_text(
        json.dumps(
            serializable,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


FUEL_KEYWORDS = (
    "газ",
    "гориво",
    "зареждане",
    "бензин",
    "дизел",
)


def is_fuel_expense(text):

    text = (
        text or ""
    ).lower()

    return any(
        keyword in text
        for keyword in FUEL_KEYWORDS
    )


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
        for trip
        in st.session_state.trips.values()
        for expense
        in trip["expenses"]
    )


def total_budget():

    return sum(
        trip["budget"]
        for trip
        in st.session_state.trips.values()
    )


def trip_expenses(trip):

    return sum(
        expense["amount"]
        for expense
        in trip["expenses"]
    )


def delete_expense(
    trip_id,
    expense_index
):

    expenses = st.session_state.trips[
        trip_id
    ]["expenses"]

    if 0 <= expense_index < len(expenses):

        del expenses[
            expense_index
        ]

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


def open_add_expense(
    trip_id=None
):

    st.session_state.expense_trip = trip_id

    st.session_state.page = "add_expense"

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


/* =========================================================
   GLOBAL
   ========================================================= */

html,
body,
.stApp,
[class*="css"],
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
        #08111a;
}


.block-container {

    max-width:
        1080px;

    padding-top:
        1.4rem;

    padding-bottom:
        4rem;
}


/* =========================================================
   HIDE STREAMLIT DEFAULT ELEMENTS
   ========================================================= */

#MainMenu {

    visibility:
        hidden;
}


footer {

    visibility:
        hidden;
}


header {

    background:
        transparent !important;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

section[data-testid="stSidebar"] {

    background:
        #09141f;

    border-right:
        1px solid #1a2b3a;
}


section[data-testid="stSidebar"]
.block-container {

    padding-top:
        1.2rem;
}


/* =========================================================
   BUTTONS
   ========================================================= */

.stButton > button {

    border-radius:
        12px;

    min-height:
        44px;

    font-weight:
        650;

    border:
        1px solid #263c4f;

    background:
        #101e2a;

    color:
        #eef5f9;

    transition:
        all .18s ease;
}


.stButton > button:hover {

    border-color:
        #2b9cff;

    background:
        #15283a;

    color:
        #ffffff;

    transform:
        translateY(-1px);
}


.stButton > button:active {

    transform:
        translateY(0);
}


.stButton > button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            #1f8fff,
            #1673d4
        ) !important;

    border:
        1px solid #2b9cff !important;

    color:
        white !important;
}


/* =========================================================
   METRICS
   ========================================================= */

div[data-testid="stMetric"] {

    background:
        linear-gradient(
            145deg,
            #0e1c29,
            #0b1722
        );

    border:
        1px solid #1c3041;

    border-radius:
        16px;

    padding:
        14px 16px;

    box-shadow:
        0 8px 24px rgba(
            0,
            0,
            0,
            .14
        );
}


div[data-testid="stMetricLabel"] {

    color:
        #8fa1b2;
}


div[data-testid="stMetricValue"] {

    color:
        #f4f8fb;
}


/* =========================================================
   INPUTS
   ========================================================= */

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {

    background:
        #0d1925;

    border-color:
        #22374a;

    border-radius:
        10px;
}


/* =========================================================
   DIVIDER
   ========================================================= */

hr {

    border-color:
        #1a2a39;
}


/* =========================================================
   CONTAINERS
   ========================================================= */

div[data-testid="stVerticalBlockBorderWrapper"] {

    border-radius:
        18px;

    border-color:
        #1c3041;
}


/* =========================================================
   HOME HERO
   ========================================================= */

.tm-header {

    position:
        relative;

    padding:
        10px 0 24px 0;

    overflow:
        hidden;
}


.tm-header::before {

    content:
        "";

    position:
        absolute;

    width:
        190px;

    height:
        190px;

    right:
        -70px;

    top:
        -100px;

    border-radius:
        50%;

    background:
        radial-gradient(
            circle,
            rgba(
                43,
                156,
                255,
                .16
            ),
            transparent 70%
        );

    pointer-events:
        none;
}


.tm-brand-row {

    display:
        flex;

    align-items:
        center;

    gap:
        12px;
}


.tm-logo {

    width:
        48px;

    height:
        48px;

    min-width:
        48px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        15px;

    background:
        linear-gradient(
            145deg,
            #173c5c,
            #0e2538
        );

    border:
        1px solid #285878;

    box-shadow:
        0 8px 24px rgba(
            0,
            0,
            0,
            .20
        );
}


.tm-logo svg {

    width:
        29px;

    height:
        29px;

    display:
        block;
}


.tm-brand {

    font-size:
        clamp(
            2rem,
            4vw,
            2.75rem
        );

    font-weight:
        800;

    letter-spacing:
        -.055em;

    line-height:
        1;

    color:
        #f4f8fb;

    margin:
        0;
}


.tm-brand-accent {

    color:
        #45b2ff;
}


.tm-subtitle {

    color:
        #8fa1b2;

    margin:
        10px 0 0 60px;

    font-size:
        .96rem;

    font-weight:
        500;

    letter-spacing:
        -.015em;

    line-height:
        1.5;

    max-width:
        500px;
}


/* =========================================================
   SECTION TITLE
   ========================================================= */

.tm-section {

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    margin:
        25px 0 14px 0;
}


.tm-section-title {

    font-size:
        1.25rem;

    font-weight:
        750;

    color:
        #f4f8fb;

    letter-spacing:
        -.025em;
}


.tm-section-subtitle {

    color:
        #738697;

    font-size:
        .78rem;
}


/* =========================================================
   QUICK ACTIONS
   ========================================================= */

.tm-quick-grid {

    display:
        grid;

    grid-template-columns:
        repeat(
            2,
            minmax(
                0,
                1fr
            )
        );

    gap:
        14px;

    margin:
        0 0 28px 0;
}


.tm-quick-card {

    position:
        relative;

    min-height:
        150px;

    padding:
        20px;

    border-radius:
        20px;

    border:
        1px solid #203446;

    background:
        linear-gradient(
            145deg,
            #102130,
            #0c1823
        );

    overflow:
        hidden;

    box-shadow:
        0 10px 28px rgba(
            0,
            0,
            0,
            .15
        );
}


.tm-quick-card.primary {

    border-color:
        #235d83;

    background:
        linear-gradient(
            145deg,
            #12314a,
            #0c1c29
        );
}


.tm-quick-icon {

    width:
        42px;

    height:
        42px;

    border-radius:
        13px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    font-size:
        21px;

    background:
        rgba(
            255,
            255,
            255,
            .06
        );

    border:
        1px solid rgba(
            255,
            255,
            255,
            .08
        );

    margin-bottom:
        14px;
}


.tm-quick-title {

    color:
        #f5f8fb;

    font-size:
        1.08rem;

    font-weight:
        750;

    margin-bottom:
        5px;
}


.tm-quick-text {

    color:
        #8fa1b2;

    font-size:
        .86rem;

    line-height:
        1.45;
}


/* =========================================================
   TRIP CARD
   ========================================================= */

.tm-trip-title {

    font-size:
        1.15rem;

    font-weight:
        750;

    color:
        #f4f8fb;
}


.tm-trip-date {

    color:
        #7f91a1;

    font-size:
        .82rem;
}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 700px) {

    .block-container {

        padding-left:
            1rem;

        padding-right:
            1rem;

        padding-top:
            .9rem;

        padding-bottom:
            3rem;
    }


    .tm-brand-row {

        gap:
            10px;
    }


    .tm-logo {

        width:
            43px;

        height:
            43px;

        min-width:
            43px;

        border-radius:
            13px;
    }


    .tm-logo svg {

        width:
            26px;

        height:
            26px;
    }


    .tm-brand {

        font-size:
            2rem;
    }


    .tm-subtitle {

        margin-left:
            53px;

        font-size:
            .88rem;
    }


    .tm-quick-grid {

        grid-template-columns:
            1fr;

        gap:
            11px;
    }


    .tm-quick-card {

        min-height:
            132px;

        padding:
            17px;
    }


    div[data-testid="stMetric"] {

        padding:
            11px 12px;
    }


    div[data-testid="stMetricValue"] {

        font-size:
            1.3rem;
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
        """
        <div style="
            display:flex;
            align-items:center;
            gap:10px;
            font-family:Inter,sans-serif;
            font-size:1.25rem;
            font-weight:800;
            letter-spacing:-.04em;
            color:#f4f8fb;
        ">
            <span style="font-size:1.35rem;">✈️</span>
            <span>Travel Manager</span>
        </div>
        """,
        unsafe_allow_html=True
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

    st.caption(
        "Планиране"
    )


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

    # -----------------------------------------------------
    # HERO
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="tm-header">

            <div class="tm-brand-row">

                <div class="tm-logo">

                    <svg
                        viewBox="0 0 64 64"
                        xmlns="http://www.w3.org/2000/svg"
                        aria-hidden="true"
                    >

                        <path
                            d="M9 42
                               C17 40 23 37 29 31
                               L40 20
                               C44 16 49 15 55 17
                               L46 26
                               L53 32
                               C54 33 54 35 52 36
                               L44 36
                               L35 45
                               C32 48 28 49 24 47
                               L29 41
                               L20 39
                               C16 40 12 41 9 42Z"
                            fill="#45b2ff"
                        />

                        <path
                            d="M14 46
                               C25 44 34 39 42 31"
                            fill="none"
                            stroke="#eef8ff"
                            stroke-width="3"
                            stroke-linecap="round"
                            opacity=".9"
                        />

                    </svg>

                </div>

                <div class="tm-brand">
                    Travel <span class="tm-brand-accent">Manager</span>
                </div>

            </div>

            <div class="tm-subtitle">
                Всичко за твоите пътувания и разходи
                на едно място.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # QUICK ACTIONS HEADER
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="tm-section">

            <div class="tm-section-title">
                Бързи действия
            </div>

            <div class="tm-section-subtitle">
                Най-често използваните функции
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # QUICK ACTION CARDS
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="tm-quick-grid">

            <div class="tm-quick-card primary">

                <div class="tm-quick-icon">
                    ＋
                </div>

                <div class="tm-quick-title">
                    Добави разход
                </div>

                <div class="tm-quick-text">
                    Бързо добавяне на разход към
                    избрано пътуване.
                </div>

            </div>


            <div class="tm-quick-card">

                <div class="tm-quick-icon">
                    ✈️
                </div>

                <div class="tm-quick-title">
                    Ново пътуване
                </div>

                <div class="tm-quick-text">
                    Създай ново пътуване и задай
                    неговия бюджет.
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    q1, q2 = st.columns(2)


    with q1:

        if st.button(
            "＋  Добави разход →",
            use_container_width=True,
            type="primary",
            key="quick_add"
        ):

            open_add_expense()


    with q2:

        if st.button(
            "✈️  Създай пътуване →",
            use_container_width=True,
            key="quick_trip"
        ):

            st.session_state.page = (
                "new_trip"
            )

            st.rerun()


    st.write("")


    # -----------------------------------------------------
    # MY TRIPS
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="tm-section">

            <div class="tm-section-title">
                Моите пътувания
            </div>

            <div class="tm-section-subtitle">
                Твоите активни пътувания
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    if not st.session_state.trips:

        st.info(
            "Все още нямаш пътувания. "
            "Създай първото си пътуване "
            "от бутона по-горе."
        )

    else:

        for trip_id, trip in (
            st.session_state.trips.items()
        ):

            spent = trip_expenses(
                trip
            )

            trip_budget = trip[
                "budget"
            ]


            if trip_budget > 0:

                progress = min(
                    spent / trip_budget,
                    1.0
                )

            else:

                progress = 0


            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [4, 1]
                )


                with c1:

                    st.markdown(
                        f"""
                        <div class="tm-trip-title">
                            ✈️ {trip['destination']}
                        </div>

                        <div class="tm-trip-date">
                            {trip['start_date'].strftime('%d.%m.%Y')}
                            –
                            {trip['end_date'].strftime('%d.%m.%Y')}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                    st.progress(
                        progress
                    )


                    st.caption(
                        f"€{spent:.2f} "
                        f"от "
                        f"€{trip_budget:.2f}"
                    )


                with c2:

                    st.write("")


                    if st.button(
                        "Отвори →",
                        key=f"home_open_{trip_id}",
                        use_container_width=True
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
                + start_date.strftime(
                    "%Y%m%d"
                )
            )


            st.session_state.trips[
                trip_id
            ] = {

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


            save_trips()


            st.session_state.selected_trip = (
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

            st.session_state.page = (
                "new_trip"
            )

            st.rerun()


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
                value=False,
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
                            amount,

                        "category":
                            category,

                        "date":
                            expense_date,

                        "note":
                            note,

                        "is_fuel":
                            fuel_expense,

                        "fuel_liters":
                            fuel_liters
                            if fuel_expense
                            else 0.0,

                        "fuel_odometer":
                            fuel_odometer
                            if fuel_expense
                            else 0.0,

                        "fuel_full_tank":
                            fuel_full_tank
                            if fuel_expense
                            else False
                    }
                )


                save_trips()


                st.session_state.selected_trip = (
                    selected_trip
                )


                st.session_state.expense_trip = (
                    None
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

            st.session_state.page = (
                "new_trip"
            )

            st.rerun()


    st.divider()


    if not st.session_state.trips:

        st.info(
            "Все още нямаш създадени пътувания."
        )

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


    trip = st.session_state.trips[
        trip_id
    ]


    if st.button(
        "← Моите пътувания",
        key="trip_back"
    ):

        st.session_state.page = (
            "trips"
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
        trip["budget"]
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
    # FUEL STATISTICS
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


    total_fuel_liters = sum(

        expense.get(
            "fuel_liters",
            0.0
        )

        for expense
        in fuel_expenses
    )


    total_fuel_cost = sum(

        expense["amount"]

        for expense
        in fuel_expenses
    )


    if fuel_expenses:

        st.subheader(
            "⛽ Гориво"
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
                expense["fuel_odometer"]
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
                fuel_with_km[0][
                    "fuel_odometer"
                ]
            )


            last_odometer = (
                fuel_with_km[-1][
                    "fuel_odometer"
                ]
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


        full_indices = [

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
            len(full_indices)
        ):

            start_index = (
                full_indices[
                    position - 1
                ]
            )


            end_index = (
                full_indices[
                    position
                ]
            )


            start = fuel_with_km[
                start_index
            ]


            end = fuel_with_km[
                end_index
            ]


            km = (
                end["fuel_odometer"]
                - start["fuel_odometer"]
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
                    "За среден разход са нужни поне "
                    "2 зареждания с известен километраж."
                )


        if real_consumption is not None:

            st.metric(
                "Реален разход",
                f"{real_consumption:.2f} л/100 км"
            )

        else:

            st.caption(
                "Реален разход: нужни са поне 2 "
                "зареждания с отбелязан пълен резервоар."
            )


    # =====================================================
    # EXPENSES BY CATEGORY
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

                + expense["amount"]
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
            + list(
                category_totals.keys()
            ),

            key=f"category_filter_{trip_id}"
        )


        # =================================================
        # CATEGORY CARDS
        # =================================================

        st.markdown(
            """
<style>

.tm-cat-grid {

    display:
        grid;

    grid-template-columns:
        repeat(
            3,
            minmax(
                0,
                1fr
            )
        );

    gap:
        12px;

    margin:
        10px 0 18px 0;
}


.tm-cat-card {

    border:
        1px solid
        rgba(
            120,
            120,
            140,
            .18
        );

    border-radius:
        18px;

    padding:
        16px;

    background:
        linear-gradient(
            145deg,
            rgba(
                255,
                255,
                255,
                .055
            ),
            rgba(
                255,
                255,
                255,
                .018
            )
        );

    box-shadow:
        0 6px 22px
        rgba(
            0,
            0,
            0,
            .06
        );

    min-height:
        128px;
}


.tm-cat-top {

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    gap:
        8px;
}


.tm-cat-name {

    font-size:
        14px;

    font-weight:
        650;

    opacity:
        .86;

    overflow:
        hidden;

    text-overflow:
        ellipsis;

    white-space:
        nowrap;
}


.tm-cat-pct {

    font-size:
        12px;

    font-weight:
        700;

    opacity:
        .65;
}


.tm-cat-amount {

    font-size:
        24px;

    font-weight:
        800;

    letter-spacing:
        -.5px;

    margin-top:
        13px;
}


.tm-cat-bar {

    height:
        6px;

    border-radius:
        99px;

    background:
        rgba(
            128,
            128,
            128,
            .18
        );

    overflow:
        hidden;

    margin-top:
        13px;
}


.tm-cat-fill {

    height:
        100%;

    border-radius:
        99px;

    background:
        linear-gradient(
            90deg,
            #7c5cff,
            #35c7ff
        );
}


.tm-cat-label {

    margin-top:
        7px;

    font-size:
        11px;

    opacity:
        .55;
}


@media (max-width: 900px) {

    .tm-cat-grid {

        grid-template-columns:
            repeat(
                2,
                minmax(
                    0,
                    1fr
                )
            );
    }

}


@media (max-width: 600px) {

    .tm-cat-grid {

        grid-template-columns:
            1fr;

        gap:
            10px;
    }


    .tm-cat-card {

        min-height:
            112px;

        padding:
            14px;
    }


    .tm-cat-amount {

        font-size:
            22px;
    }

}

</style>
""",
            unsafe_allow_html=True
        )


        cards = []


        for (
            category,
            category_amount
        ) in category_totals.items():

            percentage = (

                category_amount
                / total_category_expenses
                * 100

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
            style="width:{min(percentage, 100):.2f}%"
        ></div>

    </div>

    <div class="tm-cat-label">
        от общо €{total_category_expenses:.2f}
    </div>

</div>
"""
            )


        category_html = (
            '<div class="tm-cat-grid">'
            + "".join(cards)
            + "</div>"
        )


        st.markdown(
            category_html,
            unsafe_allow_html=True
        )


        # =================================================
        # DONUT CHART
        # =================================================

        st.write("")


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
                "За интерактивната графика е необходима "
                "библиотеката Plotly."
            )


        st.divider()


    # =====================================================
    # EXPENSE LIST
    # =====================================================

    st.subheader(
        "Разходи"
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
                == selected_category
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


                    if expense["note"]:

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


                        fuel_caption = (
                            f"⛽ {liters:.2f} л"
                        )


                        if liters > 0:

                            fuel_caption += (
                                f" · "
                                f"€{expense['amount'] / liters:.2f}/л"
                            )


                        if odometer > 0:

                            fuel_caption += (
                                f" · "
                                f"{odometer:.0f} км"
                            )


                        if expense.get(
                            "fuel_full_tank",
                            False
                        ):

                            fuel_caption += (
                                " · ✓ пълен"
                            )


                        st.caption(
                            fuel_caption
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
                        key=(
                            f"delete_"
                            f"{trip_id}_"
                            f"{original_index}"
                        ),
                        use_container_width=True
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
                            key=(
                                f"confirm_yes_"
                                f"{trip_id}_"
                                f"{original_index}"
                            ),
                            type="primary",
                            use_container_width=True
                        ):

                            delete_expense(
                                trip_id,
                                original_index
                            )


                            st.session_state.pop(
                                confirm_key,
                                None
                            )


                            st.rerun()


                    with d2:

                        if st.button(
                            "Отказ",
                            key=(
                                f"confirm_no_"
                                f"{trip_id}_"
                                f"{original_index}"
                            ),
                            use_container_width=True
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


    st.info(
        "Тук ще изградим анализа на разходите."
    )


    if st.button(
        "← Начало",
        key="analytics_home"
    ):

        go_home()


# =========================================================
# HISTORY
# =========================================================

elif st.session_state.page == "history":

    st.title(
        "🕘 История"
    )


    st.info(
        "Тук ще изградим историята на разходите."
    )


    if st.button(
        "← Начало",
        key="history_home"
    ):

        go_home()


# =========================================================
# COMPARISON
# =========================================================

elif st.session_state.page == "comparison":

    st.title(
        "⇄ Сравнение"
    )


    st.info(
        "Тук ще изградим сравнението "
        "между пътуванията."
    )


    if st.button(
        "← Начало",
        key="comparison_home"
    ):

        go_home()


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "settings":

    st.title(
        "⚙️ Настройки"
    )


    st.info(
        "Тук ще изградим настройките."
    )


    if st.button(
        "← Начало",
        key="settings_home"
    ):

        go_home()
