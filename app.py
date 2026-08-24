import json
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(page_title="Travel Manager", page_icon="✈️", layout="wide")


# =========================================================
# SESSION STATE & PERSISTENCE
# =========================================================

DATA_FILE = Path("trips.json")


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

  except (json.JSONDecodeError, OSError, ValueError):
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
                "fuel_full_tank": expense.get("fuel_full_tank", False),
            }
            for expense in trip["expenses"]
        ],
    }

  DATA_FILE.write_text(
      json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8"
  )


FUEL_KEYWORDS = ("газ", "гориво", "зареждане", "бензин", "дизел")


def is_fuel_expense(text):
  text = (text or "").lower()
  return any(keyword in text for keyword in FUEL_KEYWORDS)


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
  return sum(trip["budget"] for trip in st.session_state.trips.values())


def trip_expenses(trip):
  return sum(expense["amount"] for expense in trip["expenses"])


def delete_expense(trip_id, expense_index):
  expenses = st.session_state.trips[trip_id]["expenses"]
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
# =========================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stApp *, button, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.stApp {
    background: #08111a;
}

.block-container {
    max-width: 1080px;
    padding-top: 1.8rem;
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
    width: 100%;
    min-height: 44px;
    border-radius: 12px;
    border: 1px solid #263c4f;
    background: #101e2a;
    color: #eef5f9;
    font-weight: 650;
    transition: background .18s ease, border-color .18s ease, transform .18s ease;
}

.stButton > button:hover {
    background: #15283a;
    border-color: #2b9cff;
    color: #ffffff;
    transform: translateY(-1px);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #147bd1, #239de5) !important;
    border: 1px solid #2aa9f0 !important;
    color: #ffffff !important;
    box-shadow: 0 8px 22px rgba(20,123,209,.22);
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1889e5, #2aaaf0) !important;
    border-color: #48b9f5 !important;
}

div[data-testid="stMetric"] {
    background: #0d1a26;
    border: 1px solid #1c3041;
    border-radius: 16px;
    padding: 14px 16px;
}

div[data-testid="stMetricLabel"] { color: #8fa1b2; }
div[data-testid="stMetricValue"] { color: #f4f8fb; }

div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
    background: #0d1925;
    border: 1px solid #22374a;
    border-radius: 10px;
}

div[data-baseweb="input"] input, div[data-baseweb="select"] * {
    color: #f4f8fb !important;
}

.tm-header { padding: 8px 0 22px 0; }
.tm-brand {
    font-size: clamp(2rem, 4vw, 2.8rem);
    font-weight: 800;
    letter-spacing: -0.055em;
    color: #f4f8fb;
    margin: 0;
}
.tm-subtitle {
    color: #8fa1b2;
    margin-top: 9px;
    font-size: .98rem;
    font-weight: 500;
}

.tm-card {
    background: linear-gradient(145deg, #102130, #0c1823);
    border: 1px solid #203446;
    border-radius: 20px;
    padding: 20px;
    min-height: 116px;
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
    margin-bottom: 6px;
}

.tm-card-text {
    color: #8fa1b2;
    font-size: .9rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px; }
hr { border-color: #1a2a39; }

@media (max-width: 700px) {
    .block-container { padding: 1rem; }
    .tm-brand { font-size: 2rem; }
    .tm-card { min-height: auto; padding: 17px; }
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
  st.markdown(
      """
        <div style="font-family:Inter,sans-serif; font-size:1.35rem; font-weight:800; color:#f4f8fb;">
            ✈️ Travel Manager
        </div>
        """,
      unsafe_allow_html=True,
  )
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

  if st.button("⚙️  Настройки", use_container_width=True, key="nav_settings"):
    st.session_state.page = "settings"
    st.rerun()

  st.divider()
  st.markdown(
      f"""
    <div style="padding:10px 12px; background:#0d1a26; border-radius:12px; border:1px solid #1c3041;">
        <div style="font-size:0.75rem; color:#8fa1b2; font-weight:600;">ОБЩО ПЪТУВАНИЯ</div>
        <div style="font-size:1.3rem; color:#f4f8fb; font-weight:800; margin-top:2px;">{len(st.session_state.trips)}</div>
    </div>
    """,
      unsafe_allow_html=True,
  )


# =========================================================
# PAGES
# =========================================================

# --- HOME PAGE ---
if st.session_state.page == "home":
  st.markdown(
      """
        <div class="tm-header">
            <h1 class="tm-brand">Табло</h1>
            <div class="tm-subtitle">Бърз преглед на бюджета и активните пътувания</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

  c1, c2, c3 = st.columns(3)
  with c1:
    st.metric("Пътувания", len(st.session_state.trips))
  with c2:
    st.metric("Общ Бюджет", f"{total_budget():.2f} лв.")
  with c3:
    st.metric("Общо Разходи", f"{total_expenses():.2f} лв.")

  st.write("")
  st.write("")

  c_btn1, c_btn2, _ = st.columns([1, 1, 2])
  with c_btn1:
    if st.button("＋ Ново пътуване", type="primary"):
      st.session_state.page = "add_trip"
      st.rerun()
  with c_btn2:
    if st.button("＋ Добави разход"):
      open_add_expense()

  st.write("")
  st.subheader("Предстоящи и активни пътувания")

  if not st.session_state.trips:
    st.info("Все още нямаш добавени пътувания.")
  else:
    cols = st.columns(2)
    for index, (trip_id, trip) in enumerate(st.session_state.trips.items()):
      spent = trip_expenses(trip)
      progress = min(spent / trip["budget"], 1.0) if trip["budget"] > 0 else 0

      with cols[index % 2]:
        card_class = (
            "tm-card tm-card-primary" if index == 0 else "tm-card"
        )
        st.markdown(
            f"""
                <div class="{card_class}">
                    <div class="tm-card-title">📍 {trip['destination']}</div>
                    <div class="tm-card-text">📅 {trip['start_date'].strftime('%d.%m.%Y')} — {trip['end_date'].strftime('%d.%m.%Y')}</div>
                    <div class="tm-card-text" style="margin-top: 10px; color: #f4f8fb; font-weight: 600;">
                        Изхарчени: {spent:.2f} / {trip['budget']:.2f} лв.
                    </div>
                </div>
                """,
            unsafe_allow_html=True,
        )
        st.progress(progress)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
          if st.button("Детайли", key=f"det_{trip_id}"):
            open_trip(trip_id)
        with col_b2:
          if st.button("＋ Разход", key=f"exp_{trip_id}"):
            open_add_expense(trip_id)

        st.write("")


# --- LIST ALL TRIPS ---
elif st.session_state.page == "trips":
  st.title("Всички пътувания")

  if st.button("＋ Ново пътуване", type="primary"):
    st.session_state.page = "add_trip"
    st.rerun()

  st.write("")

  if not st.session_state.trips:
    st.info("Няма налични пътувания.")
  else:
    for trip_id, trip in st.session_state.trips.items():
      spent = trip_expenses(trip)
      with st.expander(f"📍 {trip['destination']}"):
        st.write(
            f"**Дати:** {trip['start_date'].strftime('%d.%m.%Y')} -"
            f" {trip['end_date'].strftime('%d.%m.%Y')}"
        )
        st.write(f"**Бюджет:** {trip['budget']:.2f} лв.")
        st.write(f"**Изхарчени:** {spent:.2f} лв.")

        c1, c2 = st.columns([1, 4])
        with c1:
          if st.button("Преглед", key=f"all_{trip_id}"):
            open_trip(trip_id)


# --- ADD TRIP ---
elif st.session_state.page == "add_trip":
  st.title("Ново пътуване")

  with st.form("new_trip_form"):
    destination = st.text_input("Дестинация")
    col1, col2 = st.columns(2)
    with col1:
      start_date = st.date_input("Начална дата", value=date.today())
    with col2:
      end_date = st.date_input("Крайна дата", value=date.today())

    budget = st.number_input("Бюджет (лв.)", min_value=0.0, value=500.0)
    submitted = st.form_submit_button("Запази пътуването", type="primary")

    if submitted:
      if not destination:
        st.error("Моля, въведи дестинация.")
      else:
        new_id = f"trip_{len(st.session_state.trips) + 1}"
        st.session_state.trips[new_id] = {
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget,
            "expenses": [],
        }
        save_trips()
        st.success("Пътуването е добавено успешно!")
        go_home()


# --- SINGLE TRIP DETAILS (С КРЪГОВА ГРАФИКА) ---
elif st.session_state.page == "trip":
  trip_id = st.session_state.selected_trip
  if not trip_id or trip_id not in st.session_state.trips:
    go_home()

  trip = st.session_state.trips[trip_id]
  spent = trip_expenses(trip)

  st.title(f"📍 {trip['destination']}")
  st.caption(
      f"{trip['start_date'].strftime('%d.%m.%Y')} —"
      f" {trip['end_date'].strftime('%d.%m.%Y')}"
  )

  c1, c2 = st.columns(2)
  with c1:
    st.metric("Бюджет", f"{trip['budget']:.2f} лв.")
  with c2:
    st.metric("Изразходвани", f"{spent:.2f} лв.")

  st.write("")
  if st.button("＋ Добави разход към това пътуване", type="primary"):
    open_add_expense(trip_id)

  st.divider()
  st.subheader("Разходи по категории")

  if not trip["expenses"]:
    st.info("Все още няма добавени разходи за това пътуване.")
  else:
    # ГРУПИРАНЕ ПО КАТЕГОРИИ
    categories = {}
    for exp in trip["expenses"]:
      cat = exp["category"]
      categories[cat] = categories.get(cat, 0.0) + exp["amount"]

    # КРЪГОВА ГРАФИКА (DONUT / PIE CHART)
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("#08111a")  # Съвпада с фона на приложението
    ax.set_facecolor("#08111a")

    labels = list(categories.keys())
    values = list(categories.values())

    # Цветова палитра, съобразена с тъмната тема
    colors = [
        "#147bd1",
        "#239de5",
        "#48b9f5",
        "#2aa9f0",
        "#1889e5",
        "#0d5995",
        "#62c2f8",
    ]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[: len(values)],
        wedgeprops=dict(width=0.4, edgecolor="#08111a", linewidth=2),
    )

    # Стилизиране на текста вътре в графиката
    for text in texts:
      text.set_color("#f4f8fb")
      text.set_fontsize(10)
      text.set_fontweight("bold")
    for autotext in autotexts:
      autotext.set_color("#ffffff")
      autotext.set_fontsize(9)
      autotext.set_fontweight("bold")

    st.pyplot(fig)

    st.divider()
    st.subheader("Списък с разходи")

    for i, exp in enumerate(trip["expenses"]):
      fuel_badge = " ⛽" if exp.get("is_fuel") else ""
      col_e1, col_e2, col_e3 = st.columns([3, 2, 1])

      with col_e1:
        st.write(
            f"**{exp['category']}**{fuel_badge} — {exp['note'] or 'Без описание'}"
        )
      with col_e2:
        st.write(
            f"{exp['amount']:.2f} лв.  *({exp['date'].strftime('%d.%m')})*"
        )
      with col_e3:
        if st.button("Изтрий", key=f"del_{trip_id}_{i}"):
          delete_expense(trip_id, i)
          st.rerun()


# --- ADD EXPENSE ---
elif st.session_state.page == "add_expense":
  st.title("Добави нов разход")

  if not st.session_state.trips:
    st.warning("Първо трябва да създадеш пътуване.")
  else:
    trip_options = {
        tid: t["destination"] for tid, t in st.session_state.trips.items()
    }
    default_index = 0

    if st.session_state.expense_trip in trip_options:
      default_index = list(trip_options.keys()).index(
          st.session_state.expense_trip
      )

    selected_trip_id = st.selectbox(
        "Избери пътуване",
        options=list(trip_options.keys()),
        format_func=lambda x: trip_options[x],
        index=default_index,
    )

    with st.form("new_expense_form"):
      category = st.selectbox(
          "Категория",
          ["Храна", "Гориво", "Настаняване", "Транспорт", "Забавления", "Други"],
      )
      amount = st.number_input("Сума (лв.)", min_value=0.01, value=10.0)
      expense_date = st.date_input("Дата", value=date.today())
      note = st.text_input("Описание / Бележка")

      is_fuel_auto = is_fuel_expense(category) or is_fuel_expense(note)

      st.markdown("---")
      st.markdown("#### ⛽ Гориво (по избор)")

      is_fuel = st.checkbox("Това е разход за гориво", value=is_fuel_auto)

      fuel_liters = st.number_input(
          "Литри гориво", min_value=0.0, value=0.0, step=0.1
      )
      fuel_odometer = st.number_input(
          "Километраж (км)", min_value=0.0, value=0.0, step=1.0
      )
      fuel_full_tank = st.checkbox("Пълен резервоар", value=True)

      submitted = st.form_submit_button("Запази разхода", type="primary")

      if submitted:
        new_expense = {
            "amount": amount,
            "category": category,
            "date": expense_date,
            "note": note,
            "is_fuel": is_fuel,
            "fuel_liters": fuel_liters if is_fuel else 0.0,
            "fuel_odometer": fuel_odometer if is_fuel else 0.0,
            "fuel_full_tank": fuel_full_tank if is_fuel else False,
        }
        st.session_state.trips[selected_trip_id]["expenses"].append(new_expense)
        save_trips()
        st.success("Разходът е добавен!")
        open_trip(selected_trip_id)


# --- ANALYTICS PAGE ---
elif st.session_state.page == "analytics":
  st.title("📊 Анализи и статистика")
  st.write("Тук можеш да следиш разходите по категории за всички пътувания.")

  all_categories = {}
  for trip in st.session_state.trips.values():
    for exp in trip["expenses"]:
      cat = exp["category"]
      all_categories[cat] = all_categories.get(cat, 0.0) + exp["amount"]

  if all_categories:
    st.bar_chart(all_categories)
  else:
    st.info("Няма данни за показване.")


# --- SETTINGS PAGE ---
elif st.session_state.page == "settings":
  st.title("⚙️ Настройки")
  st.write("Настройки на приложението.")

  if st.button("Изчисти всички данни", type="primary"):
    st.session_state.trips = {}
    save_trips()
    st.success("Данните са изтрити.")
    st.rerun()
