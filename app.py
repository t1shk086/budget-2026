import streamlit as st
import pandas as pd
import datetime
import os
import glob
import io
import base64

# Настройка на страницата (Тъмна тема и оптимизиран мобилен изглед)
st.set_page_config(page_title="Бюджет 2026", page_icon="💰", layout="centered")

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]

# Функция за определяне на емоджи според категорията за мобилния изглед
def get_emoji(category):
    mapping = {
        "Храна и напитки": "🍔",
        "Транспорт": "🚗",
        "Куче": "🐾",
        "Нощувки/Хотел": "🏨",
        "Депозит/Резервация": "📌",
        "Други": "🪙"
    }
    return mapping.get(category, "💳")

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

# Функция за генериране на HTML отчет за разпечатване на кирилица в Евро
def generate_html_pdf(trip_name, total_site, deposit, categories_totals, rows_data):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Отчет_{trip_name}</title>
        <style>
            body {{ font-family: 'Arial', sans-serif; color: #2c3e50; padding: 30px; }}
            h1 {{ color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 10px; margin-bottom: 5px; }}
            h2 {{ color: #2c3e50; margin-top: 25px; font-size: 18px; border-left: 4px solid #1f77b4; padding-left: 10px; }}
            .stats {{ background: #f8f9fa; padding: 15px; border-radius: 6px; margin-top: 15px; border: 1px solid #e2e8f0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; }}
            th {{ background-color: #f1f5f9; color: #334155; font-weight: bold; }}
            .chrono-th {{ background-color: #e2e8f0; color: #1e293b; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
        </style>
    </head>
    <body>
        <h1>Финансов отчет: {trip_name.upper().replace('_', ' ')}</h1>
        <p style="color: #64748b; font-size: 13px;"><b>Дата на генериране:</b> {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        
        <div class="stats">
            <p style="margin: 5px 0;"><b>Платен депозит за хотел:</b> {deposit:.2f} EUR</p>
            <p style="margin: 5px 0;"><b>Общо похарчени на място:</b> {total_site:.2f} EUR</p>
            <p style="margin: 5px 0; font-size: 16px; color: #1e3a8a;"><b>ОБЩО РАЗХОДИ ЗА ПОЧИВКАТА:</b> {deposit + total_site:.2f} EUR</p>
        </div>

        <h2>Разходи по категории</h2>
        <table>
            <tr>
                <th>Категория</th>
                <th>Сума (EUR)</th>
                <th>Процент</th>
            </tr>
    """
    
    for kat, s_value in categories_totals.items():
        percentage = (s_value / total_site * 100) if total_site > 0 else 0.0
        html_content += f"""
            <tr>
                <td><b>{kat}</b></td>
                <td>{s_value:.2f} EUR</td>
                <td>{percentage:.1f}%</td>
            </tr>
        """
        
    html_content += """
        </table>
        <h2>Пълна хронология на плащанията</h2>
        <table>
            <tr>
                <th class="chrono-th">Дата/Час</th>
                <th class="chrono-th">Сума</th>
                <th class="chrono-th">Категория</th>
                <th class="chrono-th">Описание</th>
            </tr>
    """
    
    for row in reversed(rows_data):
        pdf_date, pdf_suma, pdf_kat, pdf_opis = row
        html_content += f"""
            <tr>
                <td>{pdf_date}</td>
                <td><b>{pdf_suma:.2f} EUR</b></td>
                <td>{pdf_kat}</td>
                <td>{pdf_opis}</td>
            </tr>
        """
        
    html_content += """
        </table>
        <script>
            window.onload = function() {
                window.print();
            }
        </script>
    </body>
    </html>
    """
    return html_content.encode('utf-8')
# Инициализация на състоянията на полетата, ако все още не съществуват
if "vavedena_suma" not in st.session_state:
    st.session_state.vavedena_suma = 0.0
if "vavedeno_opisanie" not in st.session_state:
    st.session_state.vavedeno_opisanie = ""

# 1. СТАРТОВ ЕКРАН (Избор на пътуване)
st.title("💰 Бюджет 2026")

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

    # 2. ВЪВЕЖДАНЕ НА ДАННИ (Обвързани със st.session_state)
    col1, col2 = st.columns(2)
    with col1:
        suma_vavedena = st.number_input("СУМА (EUR)", min_value=0.0, step=1.0, format="%.2f", key="vavedena_suma")
    with col2:
        opisanie = st.text_input("Описание", placeholder="Без описание", key="vavedeno_opisanie")

    st.write("Изберете категория за запис:")
    grid = st.columns(3)
    
    selected_category = None
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"btn_{i}"):
                selected_category = kat

    # Обработка на записа и автоматично нулиране на полетата
    if selected_category and suma_vavedena > 0:
        чисто_описание = opisanie.replace("|", "-").strip() if opisanie else "Без описание"
        
        if selected_category == "Депозит/Резервация":
            nov_depozit = depozit_hotel + suma_vavedena
            with open(ime_fail_depozit, "w", encoding="utf-8") as f: 
                f.write(str(nov_depozit))
            st.success(f"Записан депозит: {suma_vavedena:.2f} EUR")
        else:
            data_chas = datetime.datetime.now().strftime("%d.%m %H:%M")
            with open(ime_fail_razhodi, "a", encoding="utf-8") as f:
                f.write(f"{data_chas}|{suma_vavedena}|{suma_vavedena}|{selected_category}|{чисто_описание}|обикновен\n")
            st.success(f"Успешно записан разход за {selected_category}!")
        
        # МАГИЯТА ТУК: Изпразваме стойностите в session_state веднага след запис
        st.session_state.vavedena_suma = 0.0
        st.session_state.vavedeno_opisanie = ""
        st.rerun()
    # 3. СТАТИСТИКА И МОБИЛНА ХРОНОЛОГИЯ
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
                    continue 

    # Прогрес барове
    for kat, s_value in categories_totals.items():
        percentage = (s_value / total_on_site) if total_on_site > 0 else 0.0
        st.write(f"**{kat}**: {s_value:.2f} EUR ({percentage * 100:.1f}%)")
        st.progress(float(percentage))

    st.markdown("---")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric("🏨 ПЛАТЕН ДЕПОЗИТ", f"{depozit_hotel:.2f} EUR")
    with col_stat2:
        st.metric("💰 ОБЩО НА МЯСТО", f"{total_on_site:.2f} EUR")

    # Хронология, напълно оптимизирана за мобилни екрани (Samsung S24)
    if rows_data:
        st.markdown("---")
        st.subheader("📋 Хронология на плащанията")
        
        for idx, row in reversed(list(enumerate(rows_data))):
            r_date, r_suma, r_kat, r_opis = row
            icon = get_emoji(r_kat)
            
            c_text, c_button = st.columns([4, 1])
            
            with c_text:
                st.markdown(f"{icon} **{r_kat}** — <span style='color:#ff4b4b; font-weight:bold;'>{r_suma:.2f} EUR</span>", unsafe_allow_html=True)
                st.markdown(f"<small style='color:#888;'>📅 {r_date} | 📝 {r_opis}</small>", unsafe_allow_html=True)
            
            with c_button:
                st.write("")
                if st.button("❌", key=f"del_btn_{idx}"):
                    del original_lines[idx]
                    with open(ime_fail_razhodi, "w", encoding="utf-8") as f:
                        for remaining_line in original_lines:
                            f.write(remaining_line + "\n")
                    st.success("Разходът беше изтрит!")
                    st.rerun()
            
            st.markdown('<hr style="border: 0; height: 1px; background: #333; margin: 12px 0; opacity: 0.15;">', unsafe_allow_html=True)

    # 5. ПРИКЛЮЧВАНЕ НА ПОЧИВКА
    st.markdown("---")
    st.subheader("🏁 Приключване на почивката")
    st.write("Свалете официалния отчет. Документът ще се отвори в браузъра и сам ще предложи запис като PDF.")
    
    html_buffer = generate_html_pdf(trip_id, total_on_site, depozit_hotel, categories_totals, rows_data)
    b64_html = base64.b64encode(html_buffer).decode()
    
    custom_css_button = f"""
        <a href="data:text/html;base64,{b64_html}" download="otchet_{trip_id}_2026.html" style="text-decoration: none;">
            <button style="
                width: 100%;
                background-color: #ff4b4b;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: background-color 0.3s ease;
            ">
                📥 ПРИКЛЮЧИ ПОЧИВКАТА И СВАЛИ PDF
            </button>
        </a>
    """
    st.markdown(custom_css_button, unsafe_allow_html=True)

    # 6. ИЗТРИВАНЕ НА ЦЯЛО ПЪТУВАНЕ
    st.markdown("---")
    st.subheader("🚨 Изтриване на цялото пътуване")
    
    име_за_показване = trip_id.upper().replace('_', ' ')
    st.warning(f"Внимание: Това ще изтрие перманентно всички файлове, разходи и депозити за '{име_за_показване}'!")
    potvurditel = st.checkbox(f"Потвърждавам, че искам да изтрия '{име_за_показване}' завинаги.")
    
    if st.button("🗑️ ИЗТРИЙ ЦЯЛОТО ПЪТУВАНЕ", type="primary", use_container_width=True, disabled=not potvurditel):
        if os.path.exists(ime_fail_razhodi):
            os.remove(ime_fail_razhodi)
        if os.path.exists(ime_fail_depozit):
            os.remove(ime_fail_depozit)
            
        depozit_hotel = 0.0
        st.success(f"Пътуването '{име_за_показване}' и неговите файлове бяха изтрити!")
        st.rerun()
