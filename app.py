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

if "show_expense" not in st.session_state:
    st.session_state.show_expense = False

if "show_new_trip" not in st.session_state:
    st.session_state.show_new_trip = False


# =========================================================
# FUNCTIONS
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
    st.session_state.show_expense = False
    st.session_state.show_new_trip = False
    st.rerun()


def go_home():

    st.session_state.page = "home"
    st.session_state.selected_trip = None
    st.session_state.show_expense = False
    st.session_state.show_new_trip = False
    st.rerun()


# =========================================================
# HOME PAGE
# =========================================================

if st.session_state.page == "home":

    st.title("✈️ Travel Manager")
    st.subheader("Управлявай своите пътувания и разходи")

    st.write("Добре дошъл в Travel Manager!")

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
    # QUICK ACTIONS
    # -----------------------------------------------------

    st.subheader("Бързи действия")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "➕  Добави разход",
            use_container_width=True
        ):

            st.session_state.show_expense = True
            st.session_state.show_new_trip = False
            st.rerun()

    with col2:

        if st.button(
            "✈️  Ново пътуване",
            use_container_width=True
        ):

            st.session_state.show_new_trip = True
            st.session_state.show_expense = False
            st.rerun()

    # -----------------------------------------------------
    # NEW TRIP
    # -----------------------------------------------------

    if st.session_state.show_new_trip:

        st.divider()

        st.subheader("✈️ Ново пътуване")

        with st.form("new_trip_form"):

            destination = st.text_input(
                "Дестинация",
                placeholder="Например: Рим"
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

            budget_value = st.number_input(
                "Бюджет (€)",
                min_value=0.0,
                step=50.0
            )

            create_trip = st.form_submit_button(
                "Създай пътуването",
                use_container_width=True
            )

            if create_trip:

                if not destination.strip():

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
                        f"{destination.strip()} "
                        f"{start_date.strftime('%d.%m.%Y')}"
                    )

                    st.session_state.trips[trip_id] = {
                        "destination": destination.strip(),
                        "start_date": start_date,
                        "end_date": end_date,
                        "budget": budget_value,
                        "expenses": []
                    }

                    st.session_state.show_new_trip = False

                    st.success(
                        f"Пътуването „{destination.strip()}“ "
                        "е създадено!"
                    )

                    st.rerun()

    # -----------------------------------------------------
    # QUICK EXPENSE
    # -----------------------------------------------------

    if st.session_state.show_expense:

        st.divider()

        st.subheader("➕ Бързо добавяне на разход")

        if not st.session_state.trips:

            st.info(
                "Първо създай поне едно пътуване."
            )

        else:

            trip_options = list(
                st.session_state.trips.keys()
            )

            with st.form("home_expense_form"):

                selected_trip = st.selectbox(
                    "Пътуване",
                    trip_options
                )

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
                    value=date.today()
                )

                note = st.text_input(
                    "Бележка",
                    placeholder="Например: Вечеря"
                )

                add_expense = st.form_submit_button(
                    "Добави разход",
                    use_container_width=True
                )

                if add_expense:

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

                        st.session_state.show_expense = False

                        st.success(
                            "Разходът беше добавен успешно!"
                        )

                        st.rerun()

    # -----------------------------------------------------
    # MY TRIPS
    # -----------------------------------------------------

    st.divider()

    st.subheader("Моите пътувания")

    if not st.session_state.trips:

        st.info(
            "Все още нямаш създадени пътувания."
        )

    else:

        for trip_id, trip in st.session_state.trips.items():

            spent = trip_expenses(trip)
            remaining_trip = trip["budget"] - spent

            with st.container(border=True):

                col1, col2 = st.columns([3, 1])

                with col1:

                    st.markdown(
                        f"### ✈️ {trip['destination']}"
                    )

                    st.write(
                        f"{trip['start_date'].strftime('%d.%m.%Y')} "
                        f"– "
                        f"{trip['end_date'].strftime('%d.%m.%Y')}"
                    )

                    st.write(
                        f"Похарчено: **€{spent:.2f}** "
                        f"/ Бюджет: **€{trip['budget']:.2f}**"
                    )

                with col2:

                    st.metric(
                        "Остава",
                        f"€{remaining_trip:.2f}"
                    )

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

    # -----------------------------------------------------
    # BACK
    # -----------------------------------------------------

    if st.button("← Моите пътувания"):

        go_home()

    st.divider()

    # -----------------------------------------------------
    # TRIP HEADER
    # -----------------------------------------------------

    st.title(
        f"✈️ {trip['destination']}"
    )

    st.write(
        f"{trip['start_date'].strftime('%d.%m.%Y')} "
        f"– "
        f"{trip['end_date'].strftime('%d.%m.%Y')}"
    )

    # -----------------------------------------------------
    # TRIP STATS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ADD EXPENSE
    # -----------------------------------------------------

    if st.button(
        "➕  Добави разход",
        use_container_width=True
    ):

        st.session_state.show_expense = True
        st.rerun()

    if st.session_state.show_expense:

        st.divider()

        st.subheader("Нов разход")

        with st.form("trip_expense_form"):

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
                value=date.today()
            )

            note = st.text_input(
                "Бележка",
                placeholder="Например: Вечеря"
            )

            add_expense = st.form_submit_button(
                "Добави",
                use_container_width=True
            )

            if add_expense:

                if amount <= 0:

                    st.error(
                        "Моля, въведи сума по-голяма от 0."
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

                    st.success(
                        "Разходът беше добавен."
                    )

                    st.rerun()

    # -----------------------------------------------------
    # EXPENSE HISTORY
    # -----------------------------------------------------

    st.divider()

    st.subheader("Разходи")

    if not trip["expenses"]:

        st.info(
            "Все още няма добавени разходи."
        )

    else:

        expenses_sorted = sorted(
            trip["expenses"],
            key=lambda x: x["date"],
            reverse=True
        )

        for expense in expenses_sorted:

            with st.container(border=True):

                col1, col2 = st.columns([3, 1])

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
