import streamlit as st
import json
import os
from datetime import date, datetime

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="My Budget",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

DATA_FILE = "budget_data.json"


# ============================================================
# DATA
# ============================================================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "monthly": {},
            "trips": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.setdefault("monthly", {})
        data.setdefault("trips", {})
        return data

    except Exception:
        return {
            "monthly": {},
            "trips": {}
        }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()


# ============================================================
# HELPERS
# ============================================================

def current_month():
    return date.today().strftime("%Y-%m")


def month_name(month_key):
    try:
        d = datetime.strptime(month_key, "%Y-%m")
        return d.strftime("%B %Y")
    except Exception:
        return month_key


def get_month(month_key):
    if month_key not in data["monthly"]:
        data["monthly"][month_key] = {
            "starting_amount": 0.0,
            "salary": 0.0,
            "credit_card_start": 0.0,
            "expenses": []
        }

    month = data["monthly"][month_key]

    month.setdefault("starting_amount", 0.0)
    month.setdefault("salary", 0.0)
    month.setdefault("credit_card_start", 0.0)
    month.setdefault("expenses", [])

    return month


def money(value):
    return f"€{value:,.2f}"


def calculate_month(month):
    debit = 0.0
    cash = 0.0
    credit = 0.0
    credit_repayment = 0.0

    for expense in month["expenses"]:
        amount = float(expense.get("amount", 0))

        payment = expense.get("payment_method", "")

        if payment == "Дебитна карта":
            debit += amount

        elif payment == "В брой":
            cash += amount

        elif payment == "Кредитна карта":
            credit += amount

        elif payment == "Възстановяване по кредитна карта":
            credit_repayment += amount

    total_real_expenses = debit + cash + credit_repayment

    available_money = (
        float(month["starting_amount"])
        + float(month["salary"])
        - total_real_expenses
    )

    credit_card_balance = (
        float(month["credit_card_start"])
        + credit
        - credit_repayment
    )

    total_recorded = debit + cash + credit

    return {
        "debit": debit,
        "cash": cash,
        "credit": credit,
        "credit_repayment": credit_repayment,
        "total_real_expenses": total_real_expenses,
        "total_recorded": total_recorded,
        "available_money": available_money,
        "credit_card_balance": credit_card_balance,
    }


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .app-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }

    .app-subtitle {
        text-align: center;
        color: #777;
        margin-bottom: 2rem;
    }

    .big-button {
        width: 100%;
        min-height: 90px;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        border-radius: 18px !important;
        margin-bottom: 10px !important;
    }

    .money-card {
        padding: 18px;
        border-radius: 18px;
        background: rgba(128,128,128,0.08);
        margin-bottom: 12px;
    }

    .money-label {
        color: #777;
        font-size: 0.9rem;
    }

    .money-value {
        font-size: 1.45rem;
        font-weight: 800;
    }

    .section-title {
        font-size: 1.45rem;
        font-weight: 800;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "quick_target" not in st.session_state:
    st.session_state.quick_target = None


# ============================================================
# HEADER
# ============================================================

def show_header():
    st.markdown(
        '<div class="app-title">💰 My Budget</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="app-subtitle">Личен бюджет и пътувания</div>',
        unsafe_allow_html=True
    )


# ============================================================
# HOME
# ============================================================

def home_page():

    show_header()

    st.markdown("### Какво искаш да направиш?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💸\n\nБЪРЗ РАЗХОД",
            use_container_width=True,
            key="quick_expense",
        ):
            st.session_state.page = "quick"
            st.rerun()

    with col2:
        if st.button(
            "📅\n\nМЕСЕЧНИ РАЗХОДИ",
            use_container_width=True,
            key="monthly_expenses",
        ):
            st.session_state.page = "monthly"
            st.rerun()

    st.write("")

    if st.button(
        "✈️\n\nПЪТУВАНИЯ",
        use_container_width=True,
        key="trips",
    ):
        st.session_state.page = "trips"
        st.rerun()

    # --------------------------------------------------------
    # Current month summary
    # --------------------------------------------------------

    month_key = current_month()
    month = get_month(month_key)
    calc = calculate_month(month)

    st.write("")
    st.markdown("### 📊 Този месец")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"""
            <div class="money-card">
                <div class="money-label">Налични средства</div>
                <div class="money-value">{money(calc["available_money"])}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="money-card">
                <div class="money-label">Кредитна карта</div>
                <div class="money-value">{money(calc["credit_card_balance"])}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# QUICK EXPENSE
# ============================================================

def quick_expense_page():

    if st.button("← Назад"):
        st.session_state.page = "home"
        st.session_state.quick_target = None
        st.rerun()

    st.markdown("## 💸 Бърз разход")

    # --------------------------------------------------------
    # Choose destination
    # --------------------------------------------------------

    if st.session_state.quick_target is None:

        st.markdown("### Към какво е разходът?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "📅\n\nМЕСЕЧЕН БЮДЖЕТ",
                use_container_width=True,
            ):
                st.session_state.quick_target = "monthly"
                st.rerun()

        with col2:
            if st.button(
                "✈️\n\nПЪТУВАНЕ",
                use_container_width=True,
            ):
                st.session_state.quick_target = "trip"
                st.rerun()

        return

    # --------------------------------------------------------
    # Monthly expense
    # --------------------------------------------------------

    if st.session_state.quick_target == "monthly":

        st.markdown("### 📅 Разход към месечния бюджет")

        month_key = st.selectbox(
            "Месец",
            options=list(
                dict.fromkeys(
                    [current_month()] + list(data["monthly"].keys())
                )
            ),
            format_func=month_name,
        )

        month = get_month(month_key)

        amount = st.number_input(
            "Сума (€)",
            min_value=0.01,
            step=1.00,
            format="%.2f",
        )

        category = st.text_input(
            "Категория",
            placeholder="Напр. Храна, Гориво, Сметки..."
        )

        payment_method = st.selectbox(
            "Начин на плащане",
            [
                "Дебитна карта",
                "В брой",
                "Кредитна карта",
                "Възстановяване по кредитна карта",
            ]
        )

        expense_date = st.date_input(
            "Дата",
            value=date.today(),
        )

        note = st.text_input(
            "Бележка",
            placeholder="По желание"
        )

        if payment_method == "Възстановяване по кредитна карта":
            st.info(
                "Тази сума ще намали задължението по кредитната карта "
                "и ще бъде извадена от наличните ти средства."
            )

        if st.button(
            "➕ ДОБАВИ РАЗХОД",
            use_container_width=True,
            type="primary",
        ):

            if amount <= 0:
                st.error("Въведи сума.")
                return

            if not category and payment_method != "Възстановяване по кредитна карта":
                st.error("Въведи категория.")
                return

            if payment_method == "Възстановяване по кредитна карта":
                category = "Плащане на кредитна карта"

            month["expenses"].append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "amount": float(amount),
                "category": category,
                "payment_method": payment_method,
                "date": str(expense_date),
                "note": note,
            })

            save_data(data)

            st.success("Разходът е добавен.")
            st.session_state.page = "monthly"
            st.session_state.quick_target = None
            st.rerun()

        return

    # --------------------------------------------------------
    # Trip expense
    # --------------------------------------------------------

    if st.session_state.quick_target == "trip":

        st.markdown("### ✈️ Разход към пътуване")

        if not data["trips"]:
            st.warning("Все още няма създадени пътувания.")

            if st.button("➕ Създай пътуване"):
                st.session_state.page = "trips"
                st.session_state.quick_target = None
                st.rerun()

            return

        trip_id = st.selectbox(
            "Избери пътуване",
            list(data["trips"].keys())
        )

        trip = data["trips"][trip_id]

        amount = st.number_input(
            "Сума (€)",
            min_value=0.01,
            step=1.00,
            format="%.2f",
        )

        category = st.text_input(
            "Категория",
            placeholder="Напр. Хотел, Гориво, Храна..."
        )

        expense_date = st.date_input(
            "Дата",
            value=date.today(),
        )

        note = st.text_input(
            "Бележка",
            placeholder="По желание"
        )

        if st.button(
            "➕ ДОБАВИ КЪМ ПЪТУВАНЕТО",
            use_container_width=True,
            type="primary",
        ):

            if amount <= 0:
                st.error("Въведи сума.")
                return

            if not category:
                st.error("Въведи категория.")
                return

            trip.setdefault("expenses", [])

            trip["expenses"].append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "amount": float(amount),
                "category": category,
                "date": str(expense_date),
                "note": note,
            })

            save_data(data)

            st.success("Разходът е добавен към пътуването.")

            st.session_state.page = "trips"
            st.session_state.quick_target = None
            st.rerun()


# ============================================================
# MONTHLY PAGE
# ============================================================

def monthly_page():

    if st.button("← Начало"):
        st.session_state.page = "home"
        st.rerun()

    st.markdown("## 📅 Месечни разходи")

    month_key = st.selectbox(
        "Избери месец",
        options=list(
            dict.fromkeys(
                [current_month()] + list(data["monthly"].keys())
            )
        ),
        format_func=month_name,
    )

    month = get_month(month_key)

    # --------------------------------------------------------
    # BASIC MONTH DATA
    # --------------------------------------------------------

    st.markdown("### 💰 Основни суми")

    col1, col2 = st.columns(2)

    with col1:
        starting_amount = st.number_input(
            "Начална сума (€)",
            min_value=0.0,
            value=float(month["starting_amount"]),
            step=50.0,
            format="%.2f",
            key=f"start_{month_key}",
        )

    with col2:
        salary = st.number_input(
            "Получена заплата (€)",
            min_value=0.0,
            value=float(month["salary"]),
            step=50.0,
            format="%.2f",
            key=f"salary_{month_key}",
        )

    credit_start = st.number_input(
        "Кредитна карта — начално задължение (€)",
        min_value=0.0,
        value=float(month["credit_card_start"]),
        step=50.0,
        format="%.2f",
        key=f"credit_start_{month_key}",
    )

    if st.button(
        "💾 ЗАПАЗИ СУМИТЕ",
        use_container_width=True,
    ):

        month["starting_amount"] = float(starting_amount)
        month["salary"] = float(salary)
        month["credit_card_start"] = float(credit_start)

        save_data(data)

        st.success("Сумите са запазени.")
        st.rerun()

    # --------------------------------------------------------
    # CALCULATIONS
    # --------------------------------------------------------

    calc = calculate_month(month)

    st.markdown("### 📊 Обобщение")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"""
            <div class="money-card">
                <div class="money-label">Налични средства</div>
                <div class="money-value">
                    {money(calc["available_money"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="money-card">
                <div class="money-label">Кредитна карта</div>
                <div class="money-value">
                    {money(calc["credit_card_balance"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Дебитна карта",
            money(calc["debit"])
        )

    with c2:
        st.metric(
            "В брой",
            money(calc["cash"])
        )

    with c3:
        st.metric(
            "Кредитна карта",
            money(calc["credit"])
        )

    st.metric(
        "Плащания по кредитната карта",
        money(calc["credit_repayment"])
    )

    st.metric(
        "Общо реално изразходвани",
        money(calc["total_real_expenses"])
    )

    # --------------------------------------------------------
    # EXPENSE LIST
    # --------------------------------------------------------

    st.markdown("### 🧾 Разходи")

    if not month["expenses"]:
        st.info("Все още няма разходи за този месец.")

    else:

        for index, expense in reversed(
            list(enumerate(month["expenses"]))
        ):

            amount = float(expense.get("amount", 0))
            category = expense.get("category", "")
            payment = expense.get("payment_method", "")
            expense_date = expense.get("date", "")
            note = expense.get("note", "")

            with st.container(border=True):

                col1, col2 = st.columns([4, 1])

                with col1:

                    st.markdown(
                        f"**{category}**  \n"
                        f"{payment} · {expense_date}"
                    )

                    if note:
                        st.caption(note)

                with col2:

                    st.markdown(
                        f"### {money(amount)}"
                    )

                    if st.button(
                        "🗑️",
                        key=f"delete_{month_key}_{index}",
                    ):

                        month["expenses"].pop(index)
                        save_data(data)
                        st.rerun()


# ============================================================
# TRIPS PAGE
# ============================================================

def trips_page():

    if st.button("← Начало"):
        st.session_state.page = "home"
        st.rerun()

    st.markdown("## ✈️ Пътувания")

    # --------------------------------------------------------
    # CREATE TRIP
    # --------------------------------------------------------

    with st.expander("➕ Ново пътуване"):

        trip_name = st.text_input(
            "Име на пътуването",
            placeholder="Напр. Ливиньо 2026"
        )

        trip_budget = st.number_input(
            "Бюджет (€)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
        )

        if st.button(
            "СЪЗДАЙ ПЪТУВАНЕ",
            use_container_width=True,
        ):

            if not trip_name.strip():
                st.error("Въведи име на пътуването.")
                return

            if trip_name in data["trips"]:
                st.error("Вече има пътуване с това име.")
                return

            data["trips"][trip_name] = {
                "budget": float(trip_budget),
                "expenses": []
            }

            save_data(data)

            st.success("Пътуването е създадено.")
            st.rerun()

    # --------------------------------------------------------
    # TRIP LIST
    # --------------------------------------------------------

    if not data["trips"]:
        st.info("Все още няма създадени пътувания.")
        return

    for trip_name, trip in data["trips"].items():

        expenses = trip.get("expenses", [])

        total_spent = sum(
            float(x.get("amount", 0))
            for x in expenses
        )

        budget = float(trip.get("budget", 0))

        remaining = budget - total_spent

        if budget > 0:
            percentage = min(
                100,
                max(
                    0,
                    (total_spent / budget) * 100
                )
            )
        else:
            percentage = 0

        with st.container(border=True):

            st.markdown(f"### ✈️ {trip_name}")

            c1, c2 = st.columns(2)

            with c1:
                st.metric(
                    "Похарчено",
                    money(total_spent)
                )

            with c2:
                st.metric(
                    "Остава",
                    money(remaining)
                )

            if budget > 0:
                st.progress(
                    percentage / 100
                )

                st.caption(
                    f"{money(total_spent)} / "
                    f"{money(budget)} · "
                    f"{percentage:.0f}%"
                )

            if st.button(
                "Отвори",
                key=f"open_trip_{trip_name}",
                use_container_width=True,
            ):

                st.session_state.selected_trip = trip_name
                st.session_state.page = "trip_detail"
                st.rerun()


# ============================================================
# TRIP DETAIL
# ============================================================

def trip_detail_page():

    trip_name = st.session_state.get("selected_trip")

    if not trip_name or trip_name not in data["trips"]:
        st.session_state.page = "trips"
        st.rerun()

    trip = data["trips"][trip_name]

    if st.button("← Пътувания"):
        st.session_state.page = "trips"
        st.rerun()

    st.markdown(f"## ✈️ {trip_name}")

    budget = float(trip.get("budget", 0))

    expenses = trip.get("expenses", [])

    total_spent = sum(
        float(x.get("amount", 0))
        for x in expenses
    )

    remaining = budget - total_spent

    st.metric(
        "Бюджет",
        money(budget)
    )

    st.metric(
        "Похарчено",
        money(total_spent)
    )

    st.metric(
        "Остава",
        money(remaining)
    )

    if budget > 0:
        percentage = min(
            100,
            max(
                0,
                total_spent / budget
            )
        )

        st.progress(percentage)

    st.markdown("### 🧾 Разходи")

    if not expenses:
        st.info("Все още няма разходи.")

    for expense in reversed(expenses):

        st.markdown(
            f"""
            <div class="money-card">
                <b>{expense.get("category", "")}</b><br>
                {expense.get("date", "")}<br>
                {expense.get("note", "")}
                <div style="font-size:1.3rem;font-weight:800;">
                    {money(float(expense.get("amount", 0)))}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# ROUTER
# ============================================================

if st.session_state.page == "home":
    home_page()

elif st.session_state.page == "quick":
    quick_expense_page()

elif st.session_state.page == "monthly":
    monthly_page()

elif st.session_state.page == "trips":
    trips_page()

elif st.session_state.page == "trip_detail":
    trip_detail_page()

else:
    st.session_state.page = "home"
    st.rerun()
