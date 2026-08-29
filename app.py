import streamlit as st
import pandas as pd
import datetime

# 1. СТИЛИЗИРАНЕ (Като в твоето травел кодче)
st.markdown("""
    <style>
    .tm-home-trips-title {
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 15px;
        padding-bottom: 5px;
        border-bottom: 2px solid #E5E7EB;
    }
    .finance-card {
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        background-color: #F9FAFB;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Имитация на твоята функция за вземане на настройки (за целите на примера ползваме session_state)
if "finance_records" not in st.session_state:
    st.session_state.finance_records = []

def get_month_settings(record_id):
    # Връща настройките на записа - по аналогия с твоя get_trip_settings
    return next((r for r in st.session_state.finance_records if r["id"] == record_id), {})

# 2. sidebar ФОРМА ЗА ВЪВЕЖДАНЕ
st.sidebar.header("➕ Нов запис")
t_date = st.sidebar.date_input("Дата", datetime.date.today())
t_type = st.sidebar.selectbox("Тип", ["Разход", "Доход"])
categories = ["Храна", "Сметки", "Транспорт", "Заплата", "Други"]
t_category = st.sidebar.selectbox("Категория", categories)
t_amount = st.sidebar.number_input("Сума (лв.)", min_value=0.01, step=1.0)
t_desc = st.sidebar.text_input("Описание")

if st.sidebar.button("Добави към бюджета"):
    new_id = len(st.session_state.finance_records) + 1
    st.session_state.finance_records.append({
        "id": str(new_id),
        "date": t_date.strftime("%d.%m.%Y"),
        "type": t_type,
        "category": t_category,
        "amount": t_amount,
        "description": t_desc
    })
    st.rerun()

# 3. ЛОГИКА ЗА СОРТИРАНЕ И СТАТУСИ (Идентична на твоята)
def _finance_sort_key(rid):
    stg = get_month_settings(str(rid))
    date_str = str(stg.get("date", "") or "").strip()
    try:
        d = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
    except Exception:
        d = datetime.date.max
    # Сортиране по дата в обратен ред (най-новите най-отгоре)
    return -d.toordinal() if d != datetime.date.max else 0

existing_records = [r["id"] for r in st.session_state.finance_records]
existing_records = sorted(existing_records, key=_finance_sort_key)

# 4. ВИЗУАЛИЗАЦИЯ С ЕДНАКЪВ ДИЗАЙН
if existing_records:
    # Използваме твоя CSS клас за заглавието
    st.markdown("<div class='tm-home-trips-title'>Финансова История</div>", unsafe_allow_html=True)

    for _rec_id in existing_records:
        _settings = get_month_settings(_rec_id)
        _date = str(_settings.get("date", "") or "").strip()
        _type = _settings.get("type", "Разход")
        _amount = _settings.get("amount", 0.0)
        _category = _settings.get("category", "")
        _desc = _settings.get("description", "")

        # ЛОГИКА ЗА ЦВЕТНИТЕ ТОЧКИ (Спрямо типа транзакция)
        # Зелена точка за Доход, Червена за по-голям Разход, Жълта за малък Разход под 20 лв.
        if _type == "Доход":
            _status_dot = "🟢"
            _status_text = f"+{_amount:.2f} лв. (Доход)"
        else:
            if _amount > 20.0:
                _status_dot = "🔴"
                _status_text = f"-{_amount:.2f} лв. (Голям разход)"
            else:
                _status_dot = "🟡"
                _status_text = f"-{_amount:.2f} лв. (Дребен разход)"

        # Визуализиране на реда в стила на травел приложението
        with st.container():
            st.markdown(f"""
            <div class='finance-card'>
                <strong>{_status_dot} {_status_text}</strong> | Категория: {_category} <br>
                <small style='color: gray;'>Дата: {_date} | Описание: {_desc}</small>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Няма регистрирани транзакции. Добави първата от менюто вляво.")
