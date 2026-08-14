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

# Функция за генериране на PDF с вградена кирилица (Cp1251)
def generate_pdf(trip_name, total_site, deposit, categories_totals, rows_data):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import CIDFont

    # Използваме стандартния вграден Helvetica с кодиране за Източна Европа (Кирилица)
    font_name = 'Helvetica'
    enc = 'Cp1251'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"Budget_{trip_name}")
    styles = getSampleStyleSheet()
    
    # Специфични стилове с енкодинг
    title_style = ParagraphStyle('TitleStyle', fontName=font_name, fontSize=24, leading=28, spaceAfter=20, textColor=colors.HexColor('#1f77b4'), encoding=enc)
    heading_style = ParagraphStyle('HeadingStyle', fontName=font_name, fontSize=16, leading=20, spaceAfter=10, spaceBefore=15, textColor=colors.HexColor('#2c3e50'), encoding=enc)
    text_style = ParagraphStyle('TextStyle', fontName=font_name, fontSize=11, leading=15, spaceAfter=6, encoding=enc)

    story = []
    story.append(Paragraph(f"Финансов отчет: {trip_name.upper().replace('_', ' ')}", title_style))
    story.append(Paragraph(f"Дата на генериране: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", text_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Обща статистика", heading_style))
    story.append(Paragraph(f"Платен депозит за хотел: {deposit:.2f} лв.", text_style))
    story.append(Paragraph(f"Общо похарчени на място: {total_site:.2f} лв.", text_style))
    story.append(Paragraph(f"ОБЩО РАЗХОДИ ЗА ПОЧИВКАТА: {deposit + total_site:.2f} лв.", text_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Разходи по категории", heading_style))
    
    cat_data = [[Paragraph("Категория", text_style), Paragraph("Сума (лв.)", text_style), Paragraph("Процент", text_style)]]
    for kat, s_value in categories_totals.items():
        percentage = (s_value / total_site * 100) if total_site > 0 else 0.0
        cat_data.append([
            Paragraph(str(kat), text_style), 
            Paragraph(f"{s_value:.2f} лв.", text_style), 
            Paragraph(f"{percentage:.1f}%", text_style)
        ])
    
    t_cat = Table(cat_data, colWidths=[200, 150, 100])
    t_cat.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f2f2')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 20))
    story.append(Paragraph("Пълна хронология на плащанията", heading_style))
    chrono_data = [[Paragraph("Дата/Час", text_style), Paragraph("Сума", text_style), Paragraph("Категория", text_style), Paragraph("Описание", text_style)]]
    
    for row in reversed(rows_data):
        chrono_data.append([
            Paragraph(str(row[0]), text_style), 
            Paragraph(f"{row[1]:.2f} лв.", text_style), 
            Paragraph(str(row[2]), text_style), 
            Paragraph(str(row[3]), text_style)
        ])
        
    t_chrono = Table(chrono_data, colWidths=[100, 80, 120, 150])
    t_chrono.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_name),
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
                    continue 

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

    # 5. ПРИКЛЮЧВАНЕ НА ПОЧИВКА И ЕКСПОРТ
    st.markdown("---")
    st.subheader("🏁 Приключване на почивката")
    st.write("Свалете официален PDF отчет с пълна хронология на разходите преди затваряне.")
    
    pdf_buffer = generate_pdf(trip_id, total_on_site, depozit_hotel, categories_totals, rows_data)
    
    st.download_button(
        label="📥 ИЗТЕГЛИ PDF ОТЧЕТ",
        data=pdf_buffer,
        file_name=f"otchet_{trip_id}_2026.pdf",
        mime="application/pdf",
        use_container_width=True
    )

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
