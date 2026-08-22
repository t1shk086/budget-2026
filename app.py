import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import io
import datetime
import requests
import re

# === КОНСТАНТИ И НАСТРОЙКИ ЗА ФАЙЛОВЕТЕ ===
DATA_FILE = "budget_data_2026.csv"
SETTINGS_FILE = "trip_settings_2026.csv"
MAP_FILE = "trip_map_points_2026.csv"

KATEGORII = ["Транспорт", "Храна и напитки", "Нощувки/Хотел", "Куче", "Други"]

# Инициализация на сесиите
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = None
if "form_version" not in st.session_state:
    st.session_state["form_version"] = 0
if "show_comparison_graphic" not in st.session_state:
    st.session_state["show_comparison_graphic"] = False

# === СИГУРНИ ПОДРАВНЕНИ ФУНКЦИИ ===
def get_trip_data(trip_id):
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["trip_id", "date", "category", "description", "current_km", "amount", "type"])
    df = pd.read_csv(DATA_FILE, encoding="utf-8")
    return df[df["trip_id"] == trip_id]

def add_expense(trip_id, amount, category, description, is_deposit=False):
    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    new_row = {
        "trip_id": trip_id,
        "date": now_str,
        "category": category,
        "description": description,
        "current_km": 0.0,
        "amount": float(amount),
        "type": "deposit" if is_deposit else "expense"
    }
    df = pd.DataFrame([new_row])
    if os.path.exists(DATA_FILE):
        df_old = pd.read_csv(DATA_FILE, encoding="utf-8")
        df = pd.concat([df_old, df], ignore_index=True)
    df.to_csv(DATA_FILE, index=False, encoding="utf-8")
    return True

def analyze_receipt_text(image_file):
    try:
        payload = {"language": "bul", "isOverlayRequired": False, "ocrEngine": "2"}
        files = {"filename": (image_file.name, image_file.getvalue(), image_file.type)}
        response = requests.post("https://ocr.space", data=payload, files=files, headers={"apikey": "helloworld"})
        
        result_json = response.json()
        parsed_results = result_json.get("ParsedResults", [{}])
        if not parsed_results:
            return None, 0.0
            
        parsed_text = parsed_results[0].get("ParsedText", "").lower()
        
        ai_kat = None
        if any(w in parsed_text for w in ["lukoil", "shell", "omv", "petrol", "бензин", "дизел", "газ", "гориво", "еко", "eko", "gaz"]):
            ai_kat = "Транспорт"
        elif any(w in parsed_text for w in ["lidl", "billa", "kaufland", "метро", "ресторант", "механа", "кафе", "храна", "pizz", "супермаркет"]):
            ai_kat = "Храна и напитки"
        elif any(w in parsed_text for w in ["хотел", "hotel", "нощувка", "booking", "airbnb"]):
            ai_kat = "Нощувки/Хотел"
        elif any(w in parsed_text for w in ["ветеринар", "зоо", "куче", "дог", "dog"]):
            ai_kat = "Куче"
        
        amounts = re.findall(r'\d+[\.,]\d{2}', parsed_text)
        amounts = [float(a.replace(',', '.')) for a in amounts]
        ai_amount = max(amounts) if amounts else 0.0
        
        return ai_kat, ai_amount
    except:
        return None, 0.0

# === ИНТЕГРИРАНА МУЛТИФУНКЦИОНАЛНА ДИАЛОГОВА СИСТЕМА ===
@st.dialog("💾 Действия с отчети и анализи", width="large")
def download_and_compare_dialog():
    st.markdown("#### 📥 Изтегляне на текущото пътуване")
    trip_id = st.session_state["current_trip"]
    df_trip = get_trip_data(trip_id)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📄 Свали Отчет за Печат (HTML)",
            data="<h1>Отчет за пътуване</h1>",
            file_name=f"Otchet_{trip_id}_2026.html",
            mime="text/html",
            use_container_width=True
        )
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_trip.to_excel(writer, index=False, sheet_name='Разходи')
        st.download_button(
            label="📊 Свали Таблица с разходи (Excel)",
            data=buffer.getvalue(),
            file_name=f"Razhodi_{trip_id}_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    st.markdown("---")
    st.markdown("#### 🔄 Глобални анализи на бранда")
    
    show_comparison = st.checkbox("📈 Сравни всички записани пътувания", value=st.session_state.show_comparison_graphic, key="stable_comparison_toggle")
    st.session_state.show_comparison_graphic = show_comparison
        
    if show_comparison:
        st.markdown("<br>", unsafe_allow_html=True)
        chosen_criteria = st.segmented_control(
            label="Изберете критерий за сравнение:",
            options=["Цена за 1 км", "Пари на Ден", "Обща Стойност"],
            default="Цена за 1 км",
            key="popup_segmented_metric_selector"
        )
        
        all_trips_computed = []
        try:
            df_all_data = pd.read_csv(DATA_FILE, encoding="utf-8")
            unique_trips = df_all_data["trip_id"].dropna().unique()
            for t in unique_trips:
                df_t = df_all_data[df_all_data["trip_id"] == t]
                t_total = float(df_t["amount"].sum())
                all_trips_computed.append({
                    "Пътуване": str(t).replace("_", " ").upper(),
                    "Обща Стойност (EUR)": t_total,
                    "Цена за 1 км (EUR)": t_total / 100.0,
                    "Пари на Ден (EUR)": t_total / 5.0,
                    "DistValid": True
                })
        except:
            pass
            
        if all_trips_computed:
            df_pixel = pd.DataFrame(all_trips_computed)
            
            if chosen_criteria == "Цена за 1 км":
                x_col = "Цена за 1 км (EUR)"
                t_format = "%{text:.2f} EUR/км"
                graph_title = "💰 ЕФЕКТИВНОСТ НА КИЛОМЕТЪР"
            elif chosen_criteria == "Обща Стойност":
                x_col = "Обща Стойност (EUR)"
                t_format = "%{text:,.2f} EUR"
                graph_title = "💸 ТОТАЛЕН ИЗХАРЧЕН БЮДЖЕТ"
            else:
                x_col = "Пари на Ден (EUR)"
                t_format = "%{text:.2f} EUR/ден"
                graph_title = "📅 СРЕДЕН РАЗХОД НА ДЕН"
                
            df_sorted = df_pixel.sort_values(by=x_col, ascending=True)
            fig_pixel = px.bar(df_sorted, x=x_col, y="Пътуване", orientation='h', text=x_col)
            fig_pixel.update_traces(
                marker=dict(
                    color=df_sorted[x_col],
                    colorscale=[[0, '#00f2fe'], [1, '#4facfe']],
                    line=dict(width=0),
                    cornerradius=15
                ),
                texttemplate=f"<b>{t_format}</b>",
                textposition='outside',
                cliponaxis=False
            )
            fig_pixel.update_layout(
                title=dict(text=graph_title),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, showline=False, showticklabels=False, title=""),
                yaxis=dict(showgrid=False, showline=False, title=""),
                height=240,
                bargap=0.35
            )
            st.plotly_chart(fig_pixel, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("❌ Затвори прозореца", use_container_width=True, type="primary", key="close_entire_popup_dialog_btn"):
        st.rerun()

# === ИЗОЛИРАН ДИАЛОГ ЗА АВТОМАТИЧНО СКАНИРАНЕ НА БЕЛЕЖКИ ===
@st.dialog("📸 Автоматичен скенер на бележки", width="large")
def scan_receipt_popup_dialog():
    st.markdown("<p style='color: #aaa; margin-bottom: 15px;'>Снимайте касовата бележка на живо от телефона си. AI автоматично ще извлече сумата и категорията.</p>", unsafe_allow_html=True)
    
    uploaded_receipt = st.file_uploader(
        label="📸 СНИМКА НА ЖИВО (Натиснете тук за камера)", 
        type=["jpg", "jpeg", "png"], 
        key="popup_receipt_camera_uploader"
    )

    if uploaded_receipt is not None:
        with st.spinner("🔄 AI анализира текста..."):
            ai_kat, ai_amount = analyze_receipt_text(uploaded_receipt)
        
        st.markdown("---")
        st.markdown("#### 📝 Преглед на извлечените данни:")
        
        final_amount = st.number_input("Разпозната сума (EUR):", value=float(ai_amount), min_value=0.0, step=0.01, format="%.2f")
        final_desc = st.text_input("Описание / Обект:", value="Разход от сканирана бележка")
        
        st.markdown("<small>Изберете категория (AI маркира автоматично, ако я открие):</small>", unsafe_allow_html=True)
        final_cat = st.segmented_control(
            label="Избор на категория от бутони:",
            options=KATEGORII,
            default=ai_kat if ai_kat in KATEGORII else None,
            label_visibility="collapsed",
            key="popup_scanned_cat_clicker"
        )
        
        if st.button("💾 ЗАПИШИ РАЗХОДА ТУК", use_container_width=True, type="primary"):
            if not final_cat:
                st.error("Грешка: Трябва да кликнете върху категория!")
            elif final_amount <= 0:
                st.error("Грешка: Въведете валидна сума!")
            else:
                is_deposit = (final_cat == "Депозит/Резервация")
                if add_expense(st.session_state["current_trip"], final_amount, final_cat, final_desc, is_deposit):
                    st.success("✅ Разходът е записан успешно!")
                    st.session_state["form_version"] += 1
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("❌ Отказ и затваряне", use_container_width=True, key="close_ocr_popup_dialog_btn"):
        st.rerun()

# === ГЛАВЕН ЕКРАН НА ПРИЛОЖЕНИЕТО ===
st.title("🐾 PixelApp Budget Tracker 2026")

# Зареждане на базовото меню
# === БЕЗОПАСЕН УЕБ СКЕНЕР ЗА БЕЛЕЖКИ ===
def analyze_receipt_text(image_file):
    import re
    import requests
    try:
        payload = {"language": "bul", "isOverlayRequired": False, "ocrEngine": "2"}
        files = {"filename": (image_file.name, image_file.getvalue(), image_file.type)}
        response = requests.post("https://ocr.space", data=payload, files=files, headers={"apikey": "helloworld"})
        
        result_json = response.json()
        parsed_results = result_json.get("ParsedResults", [{}])
        if not parsed_results:
            return None, 0.0
            
        parsed_text = parsed_results[0].get("ParsedText", "").lower()
        
        ai_kat = None
        if any(w in parsed_text for w in ["lukoil", "shell", "omv", "petrol", "бензин", "дизел", "газ", "гориво", "еко", "eko", "gaz"]):
            ai_kat = "Транспорт"
        elif any(w in parsed_text for w in ["lidl", "billa", "kaufland", "метро", "ресторант", "механа", "кафе", "храна", "pizz", "супермаркет", "донер"]):
            ai_kat = "Храна и напитки"
        elif any(w in parsed_text for w in ["хотел", "hotel", "нощувка", "booking", "airbnb"]):
            ai_kat = "Нощувки/Хотел"
        elif any(w in parsed_text for w in ["ветеринар", "зоо", "куче", "дог", "dog"]):
            ai_kat = "Куче"
        
        amounts = re.findall(r'\d+[\.,]\d{2}', parsed_text)
        amounts = [float(a.replace(',', '.')) for a in amounts]
        ai_amount = max(amounts) if amounts else 0.0
        
        return ai_kat, ai_amount
    except:
        return None, 0.0

@st.dialog("📸 Автоматичен скенер на бележки", width="large")
def scan_receipt_popup_dialog():
    st.markdown("<p style='color: #aaa; margin-bottom: 15px;'>Снимайте касовата бележка на живо от телефона си. AI автоматично ще извлече сумата и категорията.</p>", unsafe_allow_html=True)
    
    uploaded_receipt = st.file_uploader(
        label="📸 СНИМКА НА ЖИВО (Натиснете тук за камера)", 
        type=["jpg", "jpeg", "png"], 
        key="popup_receipt_camera_uploader"
    )

    if uploaded_receipt is not None:
        with st.spinner("🔄 AI анализира текста..."):
            ai_kat, ai_amount = analyze_receipt_text(uploaded_receipt)
        
        st.markdown("---")
        st.markdown("#### 📝 Преглед на извлечените данни:")
        
        final_amount = st.number_input("Разпозната сума (EUR):", value=float(ai_amount), min_value=0.0, step=0.01, format="%.2f")
        final_desc = st.text_input("Описание / Обект:", value="Разход от сканирана бележка")
        
        st.markdown("<small>Изберете категория (AI маркира автоматично, ако я открие):</small>", unsafe_allow_html=True)
        final_cat = st.segmented_control(
            label="Избор на категория от бутони:",
            options=KATEGORII,
            default=ai_kat if ai_kat in KATEGORII else None,
            label_visibility="collapsed",
            key="popup_scanned_cat_clicker"
        )
        
        if st.button("💾 ЗАПИШИ РАЗХОДА ТУК", use_container_width=True, type="primary"):
            if not final_cat:
                st.error("Грешка: Трябва да кликнете върху категория!")
            elif final_amount <= 0:
                st.error("Грешка: Въведете валидна сума!")
            else:
                is_deposit = (final_cat == "Депозит/Резервация")
                if add_expense(st.session_state["current_trip"], final_amount, final_cat, final_desc, is_deposit):
                    st.success("✅ Разходът е записан успешно!")
                    st.session_state["form_version"] += 1
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("❌ Отказ и затваряне", use_container_width=True, key="close_ocr_popup_dialog_btn"):
        st.rerun()
    # Бутон за активиране на скенера директно в страничното меню
    st.markdown("---")
    st.markdown("### 📸 Скенер в движение")
    if st.session_state["current_trip"] is not None:
        if st.button("📸 Сканирай бележка на живо", use_container_width=True, key="sidebar_camera_ocr_trigger", type="secondary"):
            scan_receipt_popup_dialog()
    else:
        st.caption("ℹ️ Заредете пътуване, за да отключите скенера на бележки.")
