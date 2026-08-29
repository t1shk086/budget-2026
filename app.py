
import streamlit as st
import pandas as pd
import sqlite3
import datetime

# 1. НАСТРОЙКА НА БАЗАТА ДАННИ
def init_db():
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            category TEXT,
            amount REAL,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_transaction(date, t_type, category, amount, description):
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("INSERT INTO transactions (date, type, category, amount, description) VALUES (?, ?, ?, ?, ?)",
              (date.strftime("%Y-%m-%d"), t_type, category, amount, description))
    conn.commit()
    conn.close()

def get_transactions():
    conn = sqlite3.connect("budget.db")
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    return df

# Инициализиране
init_db()

# 2. ИНТЕРФЕЙС НА СТРИМЛИТ
st.set_page_config(page_title="Бюджетен Помощник", page_icon="💰", layout="wide")
st.title("💰 Моят Месечен Бюджет")

# Странична лента (Sidebar) за въвеждане на данни
st.sidebar.header("➕ Добави нов запис")
t_date = st.sidebar.date_input("Дата", datetime.date.today())
t_type = st.sidebar.selectbox("Тип", ["Разход", "Доход"])

# Динамични категории според типа
if t_type == "Разход":
    categories = ["Храна", "Сметки/Наем", "Транспорт/Гориво", "Забавления", "Здраве", "Други"]
else:
    categories = ["Заплата", "Фриланс/Бизнес", "Инвестиции", "Подарък", "Други"]

t_category = st.sidebar.selectbox("Категория", categories)
t_amount = st.sidebar.number_input("Сума (лв.)", min_value=0.01, step=1.0, format="%.2f")
t_desc = st.sidebar.text_input("Описание (опционално)")

if st.sidebar.button("Запази записа"):
    add_transaction(t_date, t_type, t_category, t_amount, t_desc)
    st.sidebar.success("Записът е добавен успешно!")
    st.rerun()

# 3. ЛОГИКА ЗА ИЗЧИСЛЕНИЯ И ГРАФИКИ
df = get_transactions()

if not df.empty:
    # Изчисляване на общи суми
    total_income = df[df["type"] == "Доход"]["amount"].sum()
    total_expense = df[df["type"] == "Разход"]["amount"].sum()
    balance = total_income - total_expense

    # Показване на KPI карти
    col1, col2, col3 = st.columns(3)
    col1.metric("📈 Общо Доходи", f"{total_income:.2f} лв.")
    col2.metric("📉 Общо Разходи", f"{total_expense:.2f} лв.")
    
    # Цвят на баланса в зависимост от стойността
    if balance >= 0:
        col3.metric("💳 Текущ Баланс", f"{balance:.2f} лв.", delta=f"+{balance:.2f} лв.")
    else:
        col3.metric("💳 Текущ Баланс", f"{balance:.2f} лв.", delta=f"{balance:.2f} лв.", delta_color="inverse")

    st.markdown("---")

    # Секция с графики
    col_graph1, col_graph2 = st.columns(2)

    with col_graph1:
        st.subheader("📊 Разходи по категории")
        df_expenses = df[df["type"] == "Разход"]
        if not df_expenses.empty:
            category_totals = df_expenses.groupby("category")["amount"].sum()
            st.bar_chart(category_totals)
        else:
            st.info("Няма регистрирани разходи все още.")

    with col_graph2:
        st.subheader("📈 Тренд на доходи vs разходи")
        df_trend = df.groupby(["date", "type"])["amount"].sum().unstack().fillna(0)
        st.line_chart(df_trend)

    st.markdown("---")

    # Таблица с история на транзакциите
    st.subheader("📜 История на записите")
    # Красиво форматиране на таблицата
    df_display = df.copy()
    df_display.columns = ["ID", "Дата", "Тип", "Категория", "Сума (лв.)", "Описание"]
    st.dataframe(df_display.drop(columns=["ID"]), use_container_width=True)

else:
    st.info("Все още нямаш въведени доходи или разходи. Използвай менюто вляво, за да добавиш първия!")
