import streamlit as st
import pandas as pd
import datetime
import os
import glob

# Настройка на страницата (Тъмна тема и заглавие)
st.set_page_config(page_title="Бюджет 2026", page_icon="💰", layout="centered")

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]

# Функция за зареждане на депозит
def load_deposit(trip_name):
    filename = f"depozit_{trip_name}_2026.txt"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f: 
                return float(f.read().strip())
        except: 
            return 0.0
    return 0.0

# 1. СТАРТОВ ЕКРАН (Избор на пътуване)
st.title("💰 Бюджет 2026")

# Търсене на съществуващи почивки
all_files = glob.glob("vsichki_razhodi_*.txt")
existing_trips = []
for file_path in all_files:
    file_name = os.path.basename(file_path).replace("vsichki_razhodi_", "")
    parts = file_name.split("_")
    if len(parts) > 1:
        pure_name = " ".join(parts[:-1])
        if pure_name and pure_name not in existing_trips:
            existing_trips.append(pure_name)

menu_options = existing_trips + ["➕ СЪЗДАЙ НОВО ПЪТУВАНЕ"]
user_choice = st.selectbox("Изберете или създайте почивка:", menu_options)

trip_id = ""
if user_choice == "➕ СЪЗДАЙ НОВО ПЪТУВАНЕ":
    input_text = st.text_input("Въведете име на новата дестинация:").strip()
    if input_text:
        trip_id = input_text.replace(" ", "_")
else:
    trip_id = user_choice.replace(" ", "_")

if trip_id:
    st.markdown("---")
    st.subheader(f"🌴 Дестинация: {trip_id.upper().replace('_', ' ')}")
    
    ime_fail_razhodi = f"vsichki_razhodi_{trip_id}_2026.txt"
    ime_fail_depozit = f"depozit_{trip_id}_2026.txt"
    depozit_hotel = load_deposit(trip_id)

    # 2. ВЪВЕЖДАНЕ НА ДАННИ
    col1, col2 = st.columns(2)
    with col1:
        suma_vavedena = st.number_input("СУМА (лв.)", min_value=0.0, step=1.0, format="%.2f", key="suma_input")
    with col2:
        # Защита: премахваме символа "|" за да не чупи структурата на текстовия файл
        opisanie = st.text_input("Описание", placeholder="Без описание", key="opis_input").replace("|", "-")

    # Бутони за категории
    st.write("Изберете категория за запис:")
    grid = st.columns(3)
    
    selected_category = None
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"btn_{i}"):
                selected_category = kat

    if selected_category and suma_vavedena > 0:
        if selected_category == "Депозит/Резервация":
            # Натрупване на новия депозит към вече съществуващия
            nov_depozit = depozit_hotel + suma_vavedena
            with open(ime_fail_depozit, "w", encoding="utf-8") as f: 
                f.write(str(nov_depozit))
            st.success(f"Записан депозит: {suma_vavedena:.2f} лв. (Общо до момента: {nov_depozit:.2f} лв.)")
            st.rerun()
        else:
            data_chas = datetime.datetime.now().strftime("%d.%m %H:%M")
            with open(ime_fail_razhodi, "a", encoding="utf-8") as f:
                f.write(f"{data_chas}|{suma_vavedena}|{suma_vavedena}|{selected_category}|{opisanie if opisanie else 'Без описание'}|обикновен\n")
            st.success(f"Успешно записан разход за {selected_category}!")
            st.rerun()

    # 3. СТАТИСТИКА И ХРОНОЛОГИЯ
    st.markdown("---")
    st.subheader("📊 Екранна статистика")

    total_on_site = 0.0
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    rows_data = []
    original_lines = []

    if os.path.exists(ime_fail_razhodi) and os.path.getsize(ime_fail_razhodi) > 0:
        with open(ime_fail_razhodi, "r", encoding="utf-8") as f:
            for line in f:
                stripped_line = line.strip()
                if not stripped_line: 
                    continue
                original_lines.append(stripped_line)
                try:
                    c_date, c_zapis, c_vavedena, c_kat, c_opis, c_tip = stripped_line.split("|")
                    val_vavedena = float(c_vavedena)
                    total_on_site += val_vavedena
                    if c_kat in categories_totals: 
                        categories_totals[c_kat] += val_vavedena
                    rows_data.append([c_date, val_vavedena, c_kat, c_opis])
                except ValueError:
                    continue # Пропускане на евентуално повредени редове

    for kat, s_value in categories_totals.items():
        percentage = (s_value / total_on_site) if total_on_site > 0 else 0.0
        st.write(f"**{kat}**: {s_value:.2f} лв. ({percentage * 100:.1f}%)")
        st.progress(float(percentage))

    st.markdown("---")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("🏨 ПЛАТЕН ДЕПОЗИТ", f"{depozit_hotel:.2f} лв.")
    with col_stat2:
        st.metric("💰 ОБЩО НА МЯСТО", f"{total_on_site:.2f} лв.")

    # Таблица с хронология
    if rows_data:
        st.markdown("---")
        st.subheader("📋 Хронология на плащанията")
        df = pd.DataFrame(rows_data, columns=["Дата/Час", "Сума (лв.)", "Категория", "Описание"])
        st.dataframe(df.iloc[::-1], use_container_width=True)

        # 4. УПРАВЛЕНИЕ И ИЗТРИВАНЕ НА РАЗХОДИ
        st.markdown("---")
        st.subheader("🗑️ Управление и изтриване на отделни разходи")
        
        delete_options = []
        for index, row in enumerate(rows_data):
            option_text = f"[{row[0]}] {row[2]} | {row[1]:.2f} лв. ({row[3]})"
            delete_options.append((index, option_text))
        
        selected_to_delete = st.selectbox(
            "Изберете кой разход искате да изтриете:", 
            options=delete_options, 
            format_func=lambda x: x[1]
        )
        
        if st.button("❌ Изтрий избрания разход", type="primary", use_container_width=True):
            index_to_remove = selected_to_delete[0]
            del original_lines[index_to_remove]
            
            with open(ime_fail_razhodi, "w", encoding="utf-8") as f:
                for remaining_line in original_lines:
                    f.write(remaining_line + "\n")
            
            st.success("Разходът беше изтрит успешно!")
            st.rerun()

    # 5. ИЗТРИВАНЕ НА ЦЯЛО ПЪТУВАНЕ
    st.markdown("---")
    st.subheader("🚨 Изтриване на цялото пътуване")
    
    име_за_показване = trip_id.upper().replace('_', ' ')
    st.warning(f"Внимание: Това ще изтрие перманентно всички файлове, разходи и депозити за '{име_за_показване}'!")
    
    # Чекбокс за защита от инцидентно изтриване
    potvurditel = st.checkbox(f"Потвърждавам, че искам да изтрия '{име_за_показване}' завинаги.")
    
    if st.button("🗑️ ИЗТРИЙ ЦЯЛОТО ПЪТУВАНЕ", type="primary", use_container_width=True, disabled=not potvurditel):
        # Премахване на разходите
        if os.path.exists(ime_fail_razhodi):
            os.remove(ime_fail_razhodi)
        
        # Премахване на депозита
        if os.path.exists(ime_fail_depozit):
            os.remove(ime_fail_depozit)
            
        st.success(f"Пътуването '{име_за_показване}' и неговите файлове бяха изтрити!")
        st.rerun()
