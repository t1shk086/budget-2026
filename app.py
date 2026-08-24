import streamlit as st
from datetime import date


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

if "trips" not in st.session_state:
    st.session_state.trips = {}

if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_trip" not in st.session_state:
    st.session_state.selected_trip = None

if "show_new_trip" not in st.session_state:
    st.session_state.show_new_trip = False

if "show_expense" not in st.session_state:
    st.session_state.show_expense = False


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 0%, rgba(25, 115, 255, 0.10), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(0, 220, 170, 0.07), transparent 25%),
        #070d14;
    color: #f4f7fb;
}

/* Hide Streamlit chrome */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    background: transparent !important;
}


/* Main width */

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 6rem;
}


/* Sidebar */

section[data-testid="stSidebar"] {
    background: #09111b;
    border-right: 1px solid #182637;
}

section[data-testid="stSidebar"] > div {
    padding-top: 2rem;
}

.sidebar-logo {
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 30px;
}

.sidebar-logo span {
    color: #20a7ff;
}


/* Headings */

h1 {
    font-weight: 800 !important;
    letter-spacing: -1px;
}

h2, h3 {
    font-weight: 700 !important;
}


/* Cards */

.tm-card {
    background:
        linear-gradient(
            145deg,
            rgba(18, 31, 46, 0.96),
            rgba(10, 19, 29, 0.96)
        );
    border: 1px solid #1c3045;
    border-radius: 18px;
    padding: 22px;
    box-shadow:
        0 10px 30px rgba(0,0,0,0.20),
        inset 0 1px 0 rgba(255,255,255,0.02);
}

.metric-card {
    min-height: 145px;
}

.metric-label {
    color: #8ea0b5;
    font-size: 14px;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -1px;
}

.metric-sub {
    color: #788ba0;
    font-size: 12px;
    margin-top: 7px;
}


/* Accent cards */

.quick-expense {
    background:
        linear-gradient(
            135deg,
            #0bbd92,
            #0b8fbd
        );
    border: none;
    border-radius: 18px;
    padding: 25px;
    min-height: 120px;
}

.quick-trip {
    background:
        linear-gradient(
            135deg,
            #176ce0,
            #164eb7
        );
    border: none;
    border-radius: 18px;
    padding: 25px;
    min-height: 120px;
}

.quick-title {
    font-size: 22px;
    font-weight: 800;
}

.quick-sub {
    opacity: 0.82;
    font-size: 13px;
    margin-top: 5px;
}


/* Trip cards */

.trip-card {
    background:
        linear-gradient(
            145deg,
            #101d2b,
            #0a131e
        );
    border: 1px solid #1d3044;
    border-radius: 17px;
    padding: 18px;
    margin-bottom: 12px;
}

.trip-title {
    font-size: 18px;
    font-weight: 700;
}

.trip-date {
    color: #8295aa;
    font-size: 12px;
    margin-top: 4px;
}

.trip-money {
    font-size: 14px;
    color: #dce6f1;
    margin-top: 12px;
}

.progress-bg {
    background: #1b2939;
    height: 7px;
    border-radius: 10px;
    overflow: hidden;
    margin-top: 10px;
}

.progress-fill {
    height: 100%;
    border-radius: 10px;
    background: linear-gradient(90deg, #20d5a3, #20a7ff);
}


/* Section title */

.section-title {
    font-size: 20px;
    font-weight: 800;
    margin-top: 12px;
    margin-bottom: 15px;
}


/* Buttons */

.stButton > button {
    border-radius: 12px !important;
    border: 1px solid #24384d !important;
    background: #101c29 !important;
    color: #eaf2fa !important;
    min-height: 44px;
    font-weight: 600;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    border-color: #238cff !important;
    background: #142437 !important;
    color: white !important;
}

button[kind="primary"] {
    background: linear-gradient(
        135deg,
        #1688ff,
        #0b63d7
    ) !important;
    border: none !important;
}


/* Inputs */

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
textarea {
    background: #0c1723 !important;
    border-color: #21364b !important;
    border-radius: 10px !important;
}


/* Progress */

div[data-testid="stProgress"] > div {
    background: #172638;
}

div[data-testid="stProgress"] > div > div {
    background: linear-gradient(
        90deg,
        #20d5a3,
        #1ca6ff
    );
}


/* Mobile bottom navigation */

.mobile-nav {
    display: none;
}

@media (max-width: 768px) {

    .block-container {
        padding-top: 1rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
        padding-bottom: 6rem;
    }

    section[data-testid="stSidebar"] {
        display: none;
    }

    h1 {
        font-size: 27px !important;
    }

    .metric-card {
        min-height: 120px;
    }

    .metric-value {
        font-size: 24px;
    }

    .quick-expense,
    .quick-trip {
        min-height: 105px;
        padding: 18px;
    }

    .quick-title {
        font-size: 18px;
    }

    .mobile-nav {
        display: block;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background: rgba(7, 13, 20, 0.97);
        border-top: 1px solid #1c3044;
        padding: 8px 8px 10px;
        backdrop-filter: blur(15px);
    }
}


/* Remove excessive spacing */

div[data-testid="stVerticalBlock"] > div {
    gap: 0.45rem;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPERS
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


def open_trip(trip_id):
    st.session_state.selected_trip = trip_id
    st.session_state.page = "trip"
    st.session_state.show_new_trip = False
    st.session_state.show_expense = False
    st.rerun()


def go_home():
    st.session_state.page = "home"
    st.session_state.selected_trip = None
    st.session_state.show_new_trip = False
    st.session_state.show_expense = False
    st.rerun()


def money(value):
    return f"€{value:,.2f}"


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-logo">🐾 <span>Pixel</span>App</div>',
        unsafe_allow_html=True
    )

    if st.button("⌂  Начало", use_container_width=True):
        go_home()

    if st.button("▤  Пътувания", use_container_width=True):
        go_home()

    if st.button("＋  Добави разход", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.show_expense = True
        st.rerun()

    if st.button("⌁  Анализи", use_container_width=True):
        st.info("Анализите ще бъдат добавени в следващия етап.")

    if st.button("◈  История + Класации", use_container_width=True):
        st.info("Историята ще бъде добавена в следващия етап.")

    if st.button("▣  Сравнение", use_container_width=True):
        st.info("Сравнението ще бъде добавено в следващия етап.")

    if st.button("⚙  Настройки", use_container_width=True):
        st.info("Настройките ще бъдат добавени в следващия етап.")

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.caption("Travel Manager")
    st.caption("Вашият бюджет. Вашите пътувания.")


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "home":

    st.markdown(
        "## 👋 Добре дошъл в Travel Manager"
    )

    st.markdown(
        '<div style="color:#8295aa;margin-bottom:25px;">'
        'Всичко за твоите пътувания и разходи на едно място.'
        '</div>',
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    expenses = total_expenses()
    budget = total_budget()
    remaining = budget - expenses

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="tm-card metric-card">
                <div class="metric-label">✈️ Пътувания</div>
                <div class="metric-value">{len(st.session_state.trips)}</div>
                <div class="metric-sub">активни и завършени</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="tm-card metric-card">
                <div class="metric-label">💳 Общо разходи</div>
                <div class="metric-value">{money(expenses)}</div>
                <div class="metric-sub">за всички пътувания</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class="tm-card metric-card">
                <div class="metric-label">◷ Общ бюджет</div>
                <div class="metric-value">{money(budget)}</div>
                <div class="metric-sub">планиран</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""
            <div class="tm-card metric-card">
                <div class="metric-label">✓ Оставащ бюджет</div>
                <div class="metric-value">{money(remaining)}</div>
                <div class="metric-sub">наличен</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # QUICK ACTIONS
    # -----------------------------------------------------

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="quick-expense">
                <div style="font-size:28px;">＋</div>
                <div class="quick-title">Добави разход</div>
                <div class="quick-sub">
                    Бързо добави нов разход към пътуване
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Добави разход →",
            key="quick_expense",
            use_container_width=True
        ):
            st.session_state.show_expense = True
            st.session_state.show_new_trip = False
            st.rerun()

    with c2:

        st.markdown(
            """
            <div class="quick-trip">
                <div style="font-size:28px;">✈️</div>
                <div class="quick-title">Ново пътуване</div>
                <div class="quick-sub">
                    Създай ново пътуване и задай бюджет
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "Създай пътуване →",
            key="quick_trip",
            use_container_width=True
        ):
            st.session_state.show_new_trip = True
            st.session_state.show_expense = False
            st.rerun()

    # -----------------------------------------------------
    # NEW TRIP FORM
    # -----------------------------------------------------

    if st.session_state.show_new_trip:

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):

            st.subheader("✈️ Ново пътуване")

            with st.form("new_trip"):

                destination = st.text_input(
                    "Дестинация",
                    placeholder="Например: Гърция"
                )

                c1, c2 = st.columns(2)

                with c1:
                    start = st.date_input(
                        "Начална дата",
                        date.today()
                    )

                with c2:
                    end = st.date_input(
                        "Крайна дата",
                        date.today()
                    )

                budget_value = st.number_input(
                    "Бюджет (€)",
                    min_value=0.0,
                    step=50.0
                )

                submitted = st.form_submit_button(
                    "Създай пътуването",
                    type="primary",
                    use_container_width=True
                )

                if submitted:

                    if not destination.strip():
                        st.error("Въведи дестинация.")

                    elif end < start:
                        st.error(
                            "Крайната дата не може да е преди началната."
                        )

                    else:

                        trip_id = (
                            f"{destination.strip()} "
                            f"{start.strftime('%d.%m.%Y')}"
                        )

                        st.session_state.trips[trip_id] = {
                            "destination": destination.strip(),
                            "start_date": start,
                            "end_date": end,
                            "budget": budget_value,
                            "expenses": []
                        }

                        st.session_state.show_new_trip = False

                        st.success(
                            f"Пътуването „{destination.strip()}“ е създадено."
                        )

                        st.rerun()

    # -----------------------------------------------------
    # QUICK EXPENSE FORM
    # -----------------------------------------------------

    if st.session_state.show_expense:

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):

            st.subheader("＋ Бързо добавяне на разход")

            if not st.session_state.trips:

                st.info(
                    "Първо създай поне едно пътуване."
                )

            else:

                trip_ids = list(
                    st.session_state.trips.keys()
                )

                with st.form("quick_expense_form"):

                    selected_trip = st.selectbox(
                        "Пътуване",
                        trip_ids
                    )

                    c1, c2 = st.columns(2)

                    with c1:
                        amount = st.number_input(
                            "Сума (€)",
                            min_value=0.0,
                            step=1.0
                        )

                    with c2:
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

                    submitted = st.form_submit_button(
                        "Добави разход",
                        type="primary",
                        use_container_width=True
                    )

                    if submitted:

                        if amount <= 0:
                            st.error(
                                "Въведи сума по-голяма от 0."
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

                            st.session_state.show_expense = False

                            st.success(
                                "Разходът е добавен успешно."
                            )

                            st.rerun()

    # -----------------------------------------------------
    # TRIPS
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">Моите пътувания</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.trips:

        st.markdown(
            """
            <div class="tm-card">
                <div style="font-size:18px;font-weight:700;">
                    Все още нямаш пътувания
                </div>
                <div style="color:#8295aa;margin-top:5px;">
                    Създай първото си пътуване от бутона по-горе.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        for trip_id, trip in st.session_state.trips.items():

            spent = trip_expenses(trip)

            progress = 0

            if trip["budget"] > 0:
                progress = min(
                    spent / trip["budget"],
                    1
                )

            percent = int(progress * 100)

            c1, c2 = st.columns([5, 1])

            with c1:

                st.markdown(
                    f"""
                    <div class="trip-card">

                        <div class="trip-title">
                            ✈️ {trip["destination"]}
                        </div>

                        <div class="trip-date">
                            {trip["start_date"].strftime("%d.%m.%Y")}
                            –
                            {trip["end_date"].strftime("%d.%m.%Y")}
                        </div>

                        <div class="trip-money">
                            Похарчено
                            <b>{money(spent)}</b>
                            &nbsp; / &nbsp;
                            Бюджет
                            <b>{money(trip["budget"])}</b>
                        </div>

                        <div class="progress-bg">
                            <div
                                class="progress-fill"
                                style="width:{percent}%"
                            ></div>
                        </div>

                        <div style="
                            color:#71859b;
                            font-size:11px;
                            margin-top:6px;
                        ">
                            {percent}% използван бюджет
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with c2:

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button(
                    "Отвори →",
                    key=f"open_{trip_id}",
                    use_container_width=True
                ):
                    open_trip(trip_id)


# =========================================================
# TRIP PAGE
# =========================================================

elif st.session_state.page == "trip":

    trip_id = st.session_state.selected_trip

    if trip_id not in st.session_state.trips:
        go_home()

    trip = st.session_state.trips[trip_id]

    if st.button("← Моите пътувания"):
        go_home()

    st.markdown("<br>", unsafe_allow_html=True)

    spent = trip_expenses(trip)
    remaining = trip["budget"] - spent

    st.title(f"✈️ {trip['destination']}")

    st.caption(
        f"{trip['start_date'].strftime('%d.%m.%Y')} "
        f"– "
        f"{trip['end_date'].strftime('%d.%m.%Y')}"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
            <div class="tm-card metric-card">
                <div class="metric-label">Бюджет</div>
                <div class="metric-value">{money(trip["budget"])}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="tm-card metric-card">
                <div class="metric-label">Похарчено</div>
                <div class="metric-value">{money(spent)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""
            <div class="tm-card metric-card">
                <div class="metric-label">Остава</div>
                <div class="metric-value">{money(remaining)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "＋  Добави разход",
        type="primary",
        use_container_width=True
    ):
        st.session_state.show_expense = True
        st.rerun()

    if st.session_state.show_expense:

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):

            st.subheader("Нов разход")

            with st.form("trip_expense"):

                c1, c2 = st.columns(2)

                with c1:
                    amount = st.number_input(
                        "Сума (€)",
                        min_value=0.0,
                        step=1.0
                    )

                with c2:
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
                    "Бележка"
                )

                submitted = st.form_submit_button(
                    "Добави",
                    type="primary",
                    use_container_width=True
                )

                if submitted:

                    if amount <= 0:

                        st.error(
                            "Въведи сума по-голяма от 0."
                        )

                    else:

                        trip["expenses"].append(
                            {
                                "amount": amount,
                                "category": category,
                                "date": expense_date,
                                "note": note
                            }
                        )

                        st.session_state.show_expense = False

                        st.rerun()

    # -----------------------------------------------------
    # EXPENSE HISTORY
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">Разходи</div>',
        unsafe_allow_html=True
    )

    if not trip["expenses"]:

        st.markdown(
            """
            <div class="tm-card">
                Все още няма добавени разходи.
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        for i, expense in enumerate(
            sorted(
                trip["expenses"],
                key=lambda x: x["date"],
                reverse=True
            )
        ):

            with st.container(border=True):

                c1, c2 = st.columns([4, 1])

                with c1:

                    st.markdown(
                        f"**{expense['category']}**"
                    )

                    if expense["note"]:
                        st.write(expense["note"])

                    st.caption(
                        expense["date"].strftime(
                            "%d.%m.%Y"
                        )
                    )

                with c2:

                    st.metric(
                        "Сума",
                        money(expense["amount"])
                    )


# =========================================================
# MOBILE NAVIGATION
# =========================================================

st.markdown(
    """
    <div class="mobile-nav">
    </div>
    """,
    unsafe_allow_html=True
)
