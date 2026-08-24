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
# SESSION STATE
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

            trip["start_date"] = date.fromisoformat(
                trip["start_date"]
            )

            trip["end_date"] = date.fromisoformat(
                trip["end_date"]
            )

            for expense in trip.get("expenses", []):

                expense["date"] = date.fromisoformat(
                    expense["date"]
                )

                expense["is_fuel"] = expense.get(
                    "is_fuel", False
                )

                expense["fuel_liters"] = expense.get(
                    "fuel_liters", 0.0
                )

                expense["fuel_odometer"] = expense.get(
                    "fuel_odometer", 0.0
                )

                expense["fuel_full_tank"] = expense.get(
                    "fuel_full_tank", False
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

    text = (text or "").lower()

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

    expenses = st.session_state.trips[
        trip_id
    ]["expenses"]

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
# IMPORTANT:
# EVERYTHING IS INSIDE ONE PYTHON STRING
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
.stApp,
.stApp *,
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
        1.8rem;

    padding-bottom:
        4rem;
}


/* =====================================================
   SIDEBAR
   ===================================================== */

section[data-testid="stSidebar"] {

    background:
        #09141f;

    border-right:
        1px solid #1a2b3a;
}


section[data-testid="stSidebar"] .block-container {

    padding-top:
        1.5rem;
}


/* =====================================================
   STANDARD BUTTONS
   ===================================================== */

.stButton > button {

    width:
        100%;

    min-height:
        44px;

    border-radius:
        12px;

    border:
        1px solid #263c4f;

    background:
        #101e2a;

    color:
        #eef5f9;

    font-family:
        'Inter',
        sans-serif !important;

    font-weight:
        650;

    transition:
        background .18s ease,
        border-color .18s ease,
        transform .18s ease;
}


.stButton > button:hover {

    background:
        #15283a;

    border-color:
        #2b9cff;

    color:
        #ffffff;

    transform:
        translateY(-1px);
}


/* =====================================================
   PRIMARY BUTTON
   ===================================================== */

.stButton > button[kind="primary"] {

    background:
        linear-gradient(
            135deg,
            #147bd1,
            #239de5
        ) !important;

    border:
        1px solid #2aa9f0 !important;

    color:
        #ffffff !important;

    box-shadow:
        0 8px 22px rgba(20,123,209,.22);
}


.stButton > button[kind="primary"]:hover {

    background:
        linear-gradient(
            135deg,
            #1889e5,
            #2aaaf0
        ) !important;

    border-color:
        #48b9f5 !important;

    color:
        #ffffff !important;
}


/* =====================================================
   METRICS
   ===================================================== */

div[data-testid="stMetric"] {

    background:
        #0d1a26;

    border:
        1px solid #1c3041;

    border-radius:
        16px;

    padding:
        14px 16px;
}


div[data-testid="stMetricLabel"] {

    color:
        #8fa1b2;
}


div[data-testid="stMetricValue"] {

    color:
        #f4f8fb;
}


/* =====================================================
   INPUTS
   ===================================================== */

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {

    background:
        #0d1925;

    border:
        1px solid #22374a;

    border-radius:
        10px;
}


div[data-baseweb="input"] input {

    color:
        #f4f8fb !important;
}


div[data-baseweb="select"] * {

    color:
        #f4f8fb !important;
}


/* =====================================================
   HEADER
   ===================================================== */

.tm-header {

    padding:
        8px 0 22px 0;
}


.tm-brand {

    display:
        block;

    font-family:
        'Inter',
        sans-serif !important;

    font-size:
        clamp(
            2rem,
            4vw,
            2.8rem
        );

    font-weight:
        800;

    letter-spacing:
        -0.055em;

    line-height:
        1.08;

    color:
        #f4f8fb;

    margin:
        0;
}


.tm-subtitle {

    display:
        block;

    color:
        #8fa1b2;

    margin-top:
        9px;

    font-size:
        .98rem;

    font-weight:
        500;

    line-height:
        1.5;

    letter-spacing:
        -.015em;
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

    border:
        1px solid #203446;

    border-radius:
        20px;

    padding:
        20px;

    min-height:
        116px;

    box-shadow:
        0 10px 28px rgba(0,0,0,.18);

    box-sizing:
        border-box;
}


.tm-card-primary {

    border-color:
        #235d83;

    background:
        linear-gradient(
            145deg,
            #12314a,
            #0c1c29
        );
}


.tm-card-title {

    color:
        #f5f8fb;

    font-size:
        1.12rem;

    font-weight:
        750;

    margin-bottom:
        6px;
}


.tm-card-text {

    color:
        #8fa1b2;

    font-size:
        .9rem;

    line-height:
        1.45;
}


/* =====================================================
   CONTAINERS
   ===================================================== */

div[data-testid="stVerticalBlockBorderWrapper"] {

    border-radius:
        18px;
}


/* =====================================================
   DIVIDER
   ===================================================== */

hr {

    border-color:
        #1a2a39;
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 700px) {

    .block-container {

        padding-left:
            1rem;

        padding-right:
            1rem;

        padding-top:
            1rem;
    }


    .tm-brand {

        font-size:
            2rem;
    }


    .tm-subtitle {

        font-size:
            .92rem;
    }


    .tm-card {

        min-height:
            auto;

        padding:
            17px;
    }


    div[data-testid="stMetric"] {

        padding:
            11px 12px;
    }


    div[data-testid="stMetricValue"] {

        font-size:
            1.35rem;
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
            font-family:Inter,sans-serif;
            font-size:1.35rem;
            font-weight:800;
            letter-spacing:-.04em;
            color:#f4f8fb;
            line-height:1.15;
        ">
            ✈️ Travel Manager
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption("Пътувания и разходи")

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

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    st.markdown(
        """
        <div style="
            width:100%;
            padding:10px 0 24px 0;
            display:block;
            visibility:visible;
            opacity:1;
        ">

            <div style="
                display:block;
                visibility:visible;
                opacity:1;
                color:#f4f8fb;
                font-family:Inter, sans-serif;
                font-size:clamp(32px, 5vw, 46px);
                font-weight:800;
                line-height:1.1;
                letter-spacing:-1.8px;
                margin:0;
                padding:0;
            ">
                ✈️ Travel Manager
            </div>

            <div style="
                display:block;
                visibility:visible;
                opacity:1;
                color:#9aaaba;
                font-family:Inter, sans-serif;
                font-size:16px;
                font-weight:500;
                line-height:1.5;
                margin-top:10px;
            ">
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

    st.markdown(
        """
        <div style="
            display:block;
            visibility:visible;
            opacity:1;
            color:#f4f8fb;
            font-family:Inter, sans-serif;
            font-size:24px;
            font-weight:750;
            line-height:1.3;
            margin:8px 0 16px 0;
        ">
            Бързи действия
        </div>
        """,
        unsafe_allow_html=True
    )

    q1, q2 = st.columns(2)

    with q1:

        st.markdown(
            """
            <div style="
                display:block;
                background:linear-gradient(
                    145deg,
                    #12314a,
                    #0c1c29
                );
                border:1px solid #235d83;
                border-radius:20px;
                padding:20px;
                margin-bottom:10px;
                min-height:110px;
                box-sizing:border-box;
            ">

                <div style="
                    color:#f5f8fb;
                    font-family:Inter,sans-serif;
                    font-size:18px;
                    font-weight:750;
                    margin-bottom:7px;
                ">
                    ➕ Добави разход
                </div>

                <div style="
                    color:#9aaaba;
                    font-family:Inter,sans-serif;
                    font-size:14px;
                    line-height:1.5;
                ">
                    Бързо добавяне на разход към
                    избрано пътуване.
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
            <div style="
                display:block;
                background:linear-gradient(
                    145deg,
                    #102130,
                    #0c1823
                );
                border:1px solid #203446;
                border-radius:20px;
                padding:20px;
                margin-bottom:10px;
                min-height:110px;
                box-sizing:border-box;
            ">

                <div style="
                    color:#f5f8fb;
                    font-family:Inter,sans-serif;
                    font-size:18px;
                    font-weight:750;
                    margin-bottom:7px;
                ">
                    ✈️ Ново пътуване
                </div>

                <div style="
                    color:#9aaaba;
                    font-family:Inter,sans-serif;
                    font-size:14px;
                    line-height:1.5;
                ">
                    Създай ново пътуване и задай
                    неговия бюджет.
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

    st.markdown(
        """
        <div style="
            display:block;
            visibility:visible;
            opacity:1;
            color:#f4f8fb;
            font-family:Inter,sans-serif;
            font-size:24px;
            font-weight:750;
            line-height:1.3;
            margin:8px 0 16px 0;
        ">
            Моите пътувания
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

                c1, c2 = st.columns([4, 1])

                with c1:

                    st.subheader(
                        f"✈️ {trip['destination']}"
                    )

                    st.caption(
                        f"{trip['start_date'].strftime('%d.%m.%Y')}"
                        f" – "
                        f"{trip['end_date'].strftime('%d.%m.%Y')}"
                    )

                    st.progress(progress)

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
                        open_trip(trip_id)


    # =====================================================
    # QUICK ACTIONS
    # =====================================================

    st.markdown(
        """
        <div style="
            font-family:Inter,sans-serif;
            font-size:1.45rem;
            font-weight:750;
            color:#f4f8fb;
            margin:8px 0 14px 0;
        ">
            Бързи действия
        </div>
        """,
        unsafe_allow_html=True
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
                    Бързо добавяне на разход към
                    избрано пътуване.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

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

                <div class="tm-card-title">
                    ✈️ Ново пътуване
                </div>

                <div class="tm-card-text">
                    Създай ново пътуване и задай
                    неговия бюджет.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        if st.button(
            "Създай пътуване →",
            use_container_width=True,
            key="quick_trip"
        ):

            st.session_state.page = "new_trip"
            st.rerun()


    st.write("")
    st.divider()


    # =====================================================
    # MY TRIPS
    # =====================================================

    st.subheader("Моите пътувания")


    if not st.session_state.trips:

        st.info(
            "Все още нямаш пътувания. "
            "Създай първото си пътуване "
            "от бутона по-горе."
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

                c1, c2 = st.columns([4, 1])


                with c1:

                    st.subheader(
                        f"✈️ {trip['destination']}"
                    )

                    st.caption(
                        f"{trip['start_date'].strftime('%d.%m.%Y')}"
                        f" – "
                        f"{trip['end_date'].strftime('%d.%m.%Y')}"
                    )

                    st.progress(progress)

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
            "Описание",
            placeholder=(
                "Например: Вечеря, бензин, зареждане"
            ),
            key="expense_note"
        )


        fuel_expense = is_fuel_expense(note)

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
                ]["expenses"].append({

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

        open_add_expense(trip_id)


    st.divider()


    # =====================================================
    # FUEL STATISTICS
    # =====================================================

    fuel_expenses = [

        expense

        for expense in trip["expenses"]

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

        for expense in fuel_expenses
    )


    total_fuel_cost = sum(

        expense["amount"]

        for expense in fuel_expenses
    )


    if fuel_expenses:

        st.subheader("⛽ Гориво")


        fuel_with_km = [

            expense

            for expense in fuel_expenses

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


        if len(fuel_with_km) >= 2:

            first_odometer = (
                fuel_with_km[0]["fuel_odometer"]
            )

            last_odometer = (
                fuel_with_km[-1]["fuel_odometer"]
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
            in enumerate(fuel_with_km)

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

            start_index = full_indices[
                position - 1
            ]

            end_index = full_indices[
                position
            ]

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

            sum(real_consumption_values)
            / len(real_consumption_values)

            if real_consumption_values
            else None
        )


        fc1, fc2, fc3 = st.columns(3)


        with fc1:

            st.metric(
                "Зареждания",
                len(fuel_expenses)
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


            category_totals[category] = (

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

            ["Всички"]
            + list(category_totals.keys()),

            key=f"category_filter_{trip_id}"
        )


        # =================================================
        # CATEGORY CARDS
        # =================================================

        cards = []


        for category, category_amount in category_totals.items():

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


        category_html = (
            """
            <style>

            .tm-cat-grid {

                display:
                    grid;

                grid-template-columns:
                    repeat(
                        3,
                        minmax(0, 1fr)
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

                min-height:
                    128px;

                box-sizing:
                    border-box;
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
                            minmax(0, 1fr)
                        );
                }
            }


            @media (max-width: 600px) {

                .tm-cat-grid {

                    grid-template-columns:
                        1fr;
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

            <div class="tm-cat-grid">
            """
            + "".join(cards)
            +
            """
            </div>
            """
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

                paper_bgcolor="rgba(0,0,0,0)",

                plot_bgcolor="rgba(0,0,0,0)",

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

    st.subheader("Разходи")


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


        for original_index, expense in expenses:

            with st.container(border=True):

                c1, c2 = st.columns([4, 1])


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
                        expense["date"].strftime(
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

    st.title("📊 Анализи")


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

    st.title("🕘 История")


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

    st.title("⇄ Сравнение")


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

    st.title("⚙️ Настройки")


    st.info(
        "Тук ще изградим настройките."
    )


    if st.button(
        "← Начало",
        key="settings_home"
    ):

        go_home()
