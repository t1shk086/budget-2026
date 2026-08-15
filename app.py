import streamlit as st
import pandas as pd
import datetime
import os
import glob
import io
import base64

# Настройка на страницата за мобилен и десктоп изглед
st.set_page_config(page_title="Бюджет 2026", page_icon="💰", layout="centered")

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE = "budget_data_2026.csv"

# Функция за емоджи според категорията
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

# Инициализиране на централната база данни (CSV), ако не съществува
if not os.path.exists(DATA_FILE):
    try:
        df_init = pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type"])
        df_init.to_csv(DATA_FILE, index=False, encoding="utf-8")
    except:
        pass

# Сигурно зареждане на данни за конкретно пътуване
def get_trip_data(trip_id):
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type"])
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        return df[df["trip_id"] == trip_id]
    except:
        return pd.DataFrame(columns=["trip_id", "date", "amount", "category", "description", "type"])

# Сигурен запис на нов ред в базата
def add_expense(trip_id, amount, category, description, is_deposit=False):
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8") if os.path.exists(DATA_FILE) else pd.DataFrame()
        new_row = {
            "trip_id": trip_id,
            "date": datetime.datetime.now().strftime("%d.%m %H:%M"),
            "amount": float(amount),
            "category": category,
            "description": description if description else "Без описание",
            "type": "deposit" if is_deposit else "expense"
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False, encoding="utf-8")
        return True
    except:
        return False

# Функция за генериране на чист HTML/PDF отчет за разпечатване
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
            <tr><th>Категория</th><th>Сума (EUR)</th><th>Процент</th></tr>
    """
    for kat, s_value in categories_totals.items():
        percentage = (s_value / total_site * 100) if total_site > 0 else 0.0
        html_content += f"<tr><td><b>{kat}</b></td><td>{s_value:.2f} EUR</td><td>{percentage:.1f}%</td></tr>"
    
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
        html_content += f"<tr><td>{row[0]}</td><td><b>{row[1]:.2f} EUR</b></td><td>{row[2]}</td><td>{row[3]}</td></tr>"
        
    html_content += "</table><script>window.onload = function() { window.print(); }</script></body></html>"
    return html_content.encode('utf-8')
if "form_version" not in st.session_state:
    st.session_state["form_version"] = 0

st.title("💰 Бюджет 2026")

# Динамично извличане на съществуващи пътувания от базата данни
existing_trips = []
if os.path.exists(DATA_FILE):
    try:
        df_all = pd.read_csv(DATA_FILE, encoding="utf-8")
        existing_trips = list(df_all["trip_id"].unique())
    except:
        pass

menu_options = [t.replace("_", " ") for t in existing_trips] + ["➕ СЪЗДАЙ НОВО ПЪТУВАНЕ"]
user_choice = st.selectbox("Изберете или създайте почивка:", menu_options)

trip_id = ""
if user_choice == "➕ СЪЗДАЙ НОВО ПЪТУВАНЕ":
    input_text = st.text_input("Въведете име на новата дестинация:").strip()
    if input_text:
        trip_id = input_text.replace(" ", "_")
else:
    trip_id = user_choice.replace(" ", "_")

# Показваме формата само при заредено име на дестинация
if trip_id:
    st.markdown("---")
    st.subheader(f"🌴 Дестинация: {trip_id.upper().replace('_', ' ')}")
    
    papka_snimki = f"snimki_{trip_id}_2026"
    
    # Зареждане на актуалните данни от DataFrame
    df_trip = get_trip_data(trip_id)
    depozit_hotel = float(df_trip[df_trip["type"] == "deposit"]["amount"].sum())
    
    v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1:
        s_input = st.number_input("СУМА (EUR)", min_value=0.0, step=1.0, format="%.2f", key=f"suma_{v_id}")
    with col2:
        o_input = st.text_input("Описание", placeholder="Без описание", key=f"opis_{v_id}")

    st.write("Изберете категория за запис:")
    grid = st.columns(3)
    
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"btn_{i}"):
                if s_input > 0:
                    clean_desc = o_input.replace("|", "-").strip() if o_input else "Без описание"
                    is_dep = (kat == "Депозит/Резервация")
                    
                    if add_expense(trip_id, s_input, kat, clean_desc, is_deposit=is_dep):
                        st.session_state["form_version"] += 1
                        st.success("Записано успешно!")
                        st.rerun()
    # Изчисляване на екранна статистика от DataFrame
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    rows_data = []
    
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals:
            categories_totals[row["category"]] += float(row["amount"])
        rows_data.append([row["date"], float(row["amount"]), row["category"], row["description"]])

    st.markdown("---")
    st.subheader("📊 Екранна статистика")
    
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

    # Хронология в лек HTML формат
    if not df_trip.empty:
        st.markdown("---")
        st.subheader("📋 Хронология на плащанията")
        
        try:
            df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8")
            trip_indices = df_all_data[df_all_data["trip_id"] == trip_id].index.tolist()
            
            for idx in reversed(trip_indices):
                r_row = df_all_data.loc[idx]
                icon = get_emoji(r_row["category"])
                
                st.markdown(f"""
                <div style="background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-bottom: 5px;">
                    <span style="font-size: 18px;">{icon}</span> <b>{r_row["category"]}</b> — 
                    <span style="color:#ff4b4b; font-weight:bold;">{r_row["amount"]:.2f} EUR</span><br>
                    <small style="color:#888;">📅 {r_row["date"]} | 📝 {r_row["description"]}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🗑️ Изтрий този разход", key=f"del_{idx}", use_container_width=True):
                    df_all_data = df_all_data.drop(idx)
                    df_all_data.to_csv(DATA_FILE, index=False, encoding="utf-8")
                    st.success("Разходът е изтрит!")
                    st.rerun()
        except:
            pass

    # Бутон за PDF/HTML отчет
    st.markdown("---")
    st.subheader("🏁 Приключване на почивката")
    html_buffer = generate_html_pdf(trip_id, total_on_site, depozit_hotel, categories_totals, rows_data)
    b64_html = base64.b64encode(html_buffer).decode()
    
    custom_css_button = f"""
        <a href="data:text/html;base64,{b64_html}" download="otchet_{trip_id}_2026.html" style="text-decoration: none;">
            <button style="width: 100%; background-color: #ff4b4b; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                📥 ПРИКЛЮЧИ ПОЧИВКАТА И СВАЛИ PDF
            </button>
        </a>
    """
    st.markdown(custom_css_button, unsafe_allow_html=True)

    # 📸 ВГРАДЕН АЛБУМ БЕЗ РИСК ОТ БЛОКИРАНЕ НА БРАУЗЪРА
    st.markdown("---")
    with st.expander("📸 Снимки и спомени от почивката (Дискретно)"):
        if not os.path.exists(papka_snimki):
            try: os.makedirs(papka_snimki)
            except: pass
            
        uploaded_files = st.file_uploader("Качете снимки за спомен:", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"uploader_{trip_id}")
        if uploaded_files:
            for file in uploaded_files:
                path_to_save = os.path.join(papka_snimki, file.name)
                if not os.path.exists(path_to_save):
                    with open(path_to_save, "wb") as f:
                        f.write(file.getbuffer())
            st.success("Снимките са запазени!")
            st.rerun()
            
        saved_photos = glob.glob(os.path.join(papka_snimki, "*"))
        if saved_photos:
            st.write(f"Запазени спомени: {len(saved_photos)}")
            
            # Избор на снимка за преглед на цял екран вътре в самото приложение
            снимки_имена = [os.path.basename(p) for p in saved_photos]
            избрана_снимка = st.selectbox("👁️ Изберете снимка за преглед в голям размер:", ["-- Изберете снимка --"] + снимки_имена)
            
            if избрана_снимка != "-- Изберете снимка --":
                път_към_голяма = os.path.join(papka_snimki, избрана_снимка)
                st.image(път_към_голяма, use_container_width=True, caption=избрана_снимка)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("📂 Галерия с бутони за премахване:")
            
            img_grid = st.columns(3)
            for idx, img_path in enumerate(saved_photos):
                with img_grid[idx % 3]:
                    st.image(img_path, use_container_width=True)
                    if st.button("❌ Изтрий", key=f"del_img_{idx}", use_container_width=True):
                        os.remove(img_path)
                        st.success("Снимката е премахната!")
                        st.rerun()
        else:
            st.info("Все още няма качени снимки.")

    # Изтриване на цяло пътуване
    st.markdown("---")
    st.subheader("🚨 Изтриване на цялото пътуване")
    име_за_показване = trip_id.upper().replace('_', ' ')
    st.warning(f"Внимание: Това ще изтрие перманентно всички разходи за '{име_за_показване}'!")
    potvurditel = st.checkbox(f"Потвърждавам изтриването на '{име_за_показване}'.")
    
    if st.button("🗑️ ИЗТРИЙ ЦЯЛОТО ПЪТУВАНЕ", type="primary", use_container_width=True, disabled=not potvurditel):
        try:
            df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8")
            df_all_data = df_all_data[df_all_data["trip_id"] != trip_id]
            df_all_data.to_csv(DATA_FILE, index=False, encoding="utf-8")
            if os.path.exists(papka_snimki):
                for img_path in glob.glob(os.path.join(papka_snimki, "*")):
                    os.remove(img_path)
                os.rmdir(papka_snimki)
            st.success(f"Пътуването беше изтрито!")
            st.rerun()
        except:
            pass
else:
    st.info("👋 Добре дошли! Моля, изберете съществуващо пътуване от менюто горе или натиснете '➕ СЪЗДАЙ НОВО ПЪТУВАНЕ', за да започнете.")
