import streamlit as st
import pandas as pd
import datetime
import os
import glob
import io

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

# Функция за генериране на PDF на български език
def generate_pdf(trip_name, total_site, deposit, categories_totals, rows_data):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        font_name = 'DejaVuSans'
    except:
        try:
            pdfmetrics.registerFont(TTFont('LiberationSans', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
            font_name = 'LiberationSans'
        except:
            font_name = 'Helvetica'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Budget_{trip_name}")
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=font_name, fontSize=24, leading=28, spaceAfter=20, textColor=colors.HexColor('#1f77b4'))
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontName=font_name, fontSize=16, leading=20, spaceAfter=10, spaceBefore=15, textColor=colors.HexColor('#2c3e50'))
    text_style = ParagraphStyle('TextStyle', parent=styles['Normal'], fontName=font_name, fontSize=11, leading=15, spaceAfter=6)

    story = []
    story.append(Paragraph(f"Финансов отчет: {trip_name.upper().replace('_', ' ')}", title_style))
    story.append(Paragraph(f"Дата на генериране: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", text_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Обща статистика", heading_style))
    story.append(Paragraph(f"<b>Платен депозит за хотел:</b> {deposit:.2f} лв.", text_style))
    story.append(Paragraph(f"<b>Общо похарчени на място:</b> {total_site:.2f} лв.", text_style))
    story.append(Paragraph(f"<b>ОБЩО РАЗХОДИ ЗА ПОЧИВКАТА:</b> {deposit + total_site:.2f} лв.", text_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Разходи по категории", heading_style))
    cat_data = [[Paragraph("<b>Категория</b>", text_style), Paragraph("<b>Сума (лв.)</b>", text_style), Paragraph("<b>Процент</b>", text_style)]]
    for kat, s_value in categories_totals.items():
        percentage = (s_value / total_site * 100) if total_site > 0 else 0.0
        cat_data.append([Paragraph(kat, text_style), Paragraph(f"{s_value:.2f} лв.", text_style), Paragraph(f"{percentage:.1f}%", text_style)])
    
    t_cat = Table(cat_data, colWidths=[200, 150, 100])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f2f2')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Пълна хронология на плащанията", heading_style))
    chrono_data = [[Paragraph("<b>Дата/Час</b>", text_style), Paragraph("<b>Сума</b>", text_style), Paragraph("<b>Категория</b>", text_style), Paragraph("<b>Описание</b>", text_style)]]
    
    for row in reversed(rows_data):
        chrono_data.append([Paragraph(str(row[0]), text_style), Paragraph(f"{row[1]:.2f} лв.", text_style), Paragraph(str(row[2]), text_style), Paragraph(str(row[3]), text_style)])
        
    t_chrono = Table(chrono_data, colWidths=[90, 80, 130, 170])
    t_chrono.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e6f2ff')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_chrono)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
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

    # 2. ВЪВЕЖДАНЕ НА ДАННИ
    col1, col2 = st.columns(2)
    with col1:
        suma_vavedena = st.number_input("СУМА (лв.)", min_value=0.0, step=1.0, format="%.2f", key="suma_input")
    with col2:
        opisanie = st.text_input("Описание", placeholder="Без описание", key="opis_input").replace("|", "-")

    st.write("Изберете категория за запис:")
    grid = st.columns(3)
    
    selected_category = None
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"btn_{i}"):
                selected_category = kat

    if selected_category and suma_vavedena > 0:
        if selected_category == "Депозит/Резервация":
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
streamlit
pandas
reportlab
