import streamlit as st
from datetime import date


# =========================================================
# PAGE CONFIG
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


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def total_expenses():
    total = 0

    for trip in st.session_state.trips.values():
        for expense in trip["expenses"]:
            total += expense["amount"]

    return total


def total_budget():
    total = 0

    for trip in st.session_state.trips.values():
        total += trip["budget"]

    return total


def trip_expenses(trip):
    total = 0

    for expense in trip["expenses"]:
        total += expense["amount"]

    return total


def go_home():
    st.session_state.page = "home"
    st.session_state.selected_trip = None
    st.rerun()


def open_trip(trip_id):
    st.session_state.selected_trip = trip_id
    st.session_state.page = "trip"
    st.rerun()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("✈️ Travel Manager")

if st.sidebar.button(
    "Начало",
    use_container_width=True
):
    go_home()

if st.sidebar.button(
    "Пътувания",
    use_container_width=True
):
    st.session_state.page = "trips"
    st.rerun()

if st.sidebar.button(
    "Добави разход",
    use_container_width=True
):
    st.session_state.page = "add_expense"
    st.rerun()


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "home":

    st.title("✈️ Travel Manager")

    st.subheader(
        "Управлявай своите пътувания и разходи"
    )

    st.write(
        "Добре дошъл в Travel Manager!"
    )

    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    expenses = total_expenses()
    budget = total_budget()
    remaining = budget - expenses

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Пътувания",
            len(st.session_state.trips)
        )

    with col2:
        st.metric(
            "Общо разходи",
            f"€{expenses:.2f}"
        )

    with col3:
        st.metric(
            "Оставащ бюджет",
            f"€{remaining:.2f}"
        )

    st.divider()

    # -----------------------------------------------------
    # ACTIONS
    # -----------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "➕ Добави разход",
            use_container_width=True
        ):

            st.session_state.page = "add_expense"
            st.rerun()

    with col2:

        if st.button(
            "✈️ Ново пътуване",
            use_container_width=True
        ):

            st.session_state.page = "new_trip"
            st.rerun()

    # -----------------------------------------------------
    # MY TRIPS
    # -----------------------------------------------------

    st.divider()

    st.subheader("Моите пътувания")

    if len(st.session_state.trips) == 0:

        st.info(
            "Все още нямаш създадени пътувания."
        )

    else:

        for trip_id, trip in st.session_state.trips.items():

            spent = trip_expenses(trip)
            remaining_trip = (
                trip["budget"] - spent
            )

            with st.container(border=True):

                st.subheader(
                    f"✈️ {trip['destination']}"
                )

                st.write(
                    f"{trip['start_date'].strftime('%d.%m.%Y')}"
                    f" – "
                    f"{trip['end_date'].strftime('%d.%m.%Y')}"
                )

                st.write(
                    f"Похарчено: €{spent:.2f}"
                )

                st.write(
                    f"Бюджет: €{trip['budget']:.2f}"
                )

                st.write(
                    f"Остава: €{remaining_trip:.2f}"
                )

                if st.button(
                    "Отвори пътуването",
                    key=f"open_{trip_id}",
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

    col1, col2 = st.columns(2)

    with col1:

        start_date = st.date_input(
            "Начална дата",
            value=date.today()
        )

    with col2:

        end_date = st.date_input(
            "Крайна дата",
            value=date.today()
        )

    budget = st.number_input(
        "Бюджет (€)",
        min_value=0.0,
        step=50.0
    )

    st.divider()

    if st.button(
        "Създай пътуването",
        use_container_width=True
    ):

        if destination.strip() == "":

            st.error(
                "Моля, въведи дестинация."
            )

        elif end_date < start_date:

            st.error(
                "Крайната дата не може да бъде "
                "преди началната дата."
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

            st.session_state.selected_trip = trip_id
            st.session_state.page = "trip"

            st.rerun()


# =========================================================
# ADD EXPENSE
# =========================================================

elif st.session_state.page == "add_expense":

    st.title("➕ Добави разход")

    if st.button("← Назад"):

        go_home()

    st.divider()

    if len(st.session_state.trips) == 0:

        st.warning(
            "Нямаш създадени пътувания."
        )

        if st.button(
            "Създай пътуване"
        ):

            st.session_state.page = "new_trip"
            st.rerun()

    else:

        trip_ids = list(
            st.session_state.trips.keys()
        )

        selected_trip = st.selectbox(
            "Към кое пътуване?",
            trip_ids,
            format_func=lambda x:
                st.session_state.trips[x]["destination"]
        )

        amount = st.number_input(
            "Сума (€)",
            min_value=0.0,
            step=1.0
        )

        category = st.selectbox(
            "Категория",
            [
                "Храна",
                "Нощувка",
                "Транспорт",
                "Забавления",
                "Покупки",
                "Други"
            ]
        )

        expense_date = st.date_input(
            "Дата",
            value=date.today()
        )

        note = st.text_input(
            "Бележка",
            placeholder="Например: Вечеря"
        )

        st.divider()

        if st.button(
            "Добави разход",
            use_container_width=True
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
                st.session_state.page = "trip"

                st.rerun()


# =========================================================
# TRIPS
# =========================================================

elif st.session_state.page == "trips":

    st.title("✈️ Моите пътувания")

    if st.button(
        "← Начало"
    ):

        go_home()

    st.divider()

    if len(st.session_state.trips) == 0:

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

                st.write(
                    f"Период: "
                    f"{trip['start_date'].strftime('%d.%m.%Y')}"
                    f" – "
                    f"{trip['end_date'].strftime('%d.%m.%Y')}"
                )

                st.write(
                    f"Бюджет: €{trip['budget']:.2f}"
                )

                st.write(
                    f"Похарчено: €{spent:.2f}"
                )

                if st.button(
                    "Отвори",
                    key=f"trips_open_{trip_id}",
                    use_container_width=True
                ):

                    open_trip(trip_id)


# =========================================================
# TRIP DETAILS
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
        "← Моите пътувания"
    ):

        st.session_state.page = "trips"
        st.rerun()

    st.title(
        f"✈️ {trip['destination']}"
    )

    st.write(
        f"{trip['start_date'].strftime('%d.%m.%Y')}"
        f" – "
        f"{trip['end_date'].strftime('%d.%m.%Y')}"
    )

    st.divider()

    spent = trip_expenses(trip)
    remaining = trip["budget"] - spent

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Бюджет",
            f"€{trip['budget']:.2f}"
        )

    with col2:

        st.metric(
            "Похарчено",
            f"€{spent:.2f}"
        )

    with col3:

        st.metric(
            "Остава",
            f"€{remaining:.2f}"
        )

    st.divider()

    if st.button(
        "➕ Добави разход",
        use_container_width=True
    ):

        st.session_state.page = "add_expense"

        # Запомняме текущото пътуване
        # за да бъде избрано автоматично

        st.session_state.expense_trip = trip_id

        st.rerun()

    st.subheader("Разходи")

    if len(trip["expenses"]) == 0:

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

            with st.container(border=True):

                col1, col2 = st.columns(
                    [3, 1]
                )

                with col1:

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

                with col2:

                    st.metric(
                        "Сума",
                        f"€{expense['amount']:.2f}"
                    )
