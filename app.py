# Изтеглете файла от линка по-горе или копирайте целия код отдолу:
import streamlit as st
import pandas as pd
import datetime
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import base64

# 1. Конфигуриране на страницата (Задължително на първо място)
st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")

# 2. Прочитане на логото и превръщането му в чист уеб елемент
logo_html_tag = ""
logo_filename = "logo.png"

if os.path.exists(logo_filename):
    with open(logo_filename, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    # Генерираме чист HTML код за логото с мека неонова сянка, съвпадаща с приложението
    logo_html_tag = f'''
    <div style="text-align: center; width: 100%; margin-top: 15px; margin-bottom: 5px;">
        <img src="data:image/png;base64,{encoded_string}" style="width: 250px; height: auto; display: inline-block; filter: drop-shadow(0 0 15px rgba(0, 242, 254, 0.2));">
    </div>
    '''
else:
    logo_html_tag = "<h1 style='text-align: center; color: #00f2fe; margin-top: 15px;'>PixelApp 🐾</h1>"

# 3. МОДЕРНИЗИРАН PREMIUM CSS ДИЗАЙН (СЪЩАТА СТРУКТУРА, НО ПО-КРАСИВА)
st.markdown(f'''
<style>
    /* Луксозен дълбок фон на приложението */
    html, body, [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, #07090c 0%, #0f131a 50%, #0a0d12 100%) !important;
        background-attachment: fixed !important;
    }}
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.1) !important;
        z-index: -1;
        pointer-events: none;
    }}
    
    /* Модернизирани входни полета с по-чист стъклен ефект */
    div.stSelectbox, div.stNumberInput, div.stTextInput, div.stFileUploader {{
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important; 
        padding: 8px 14px !important;
        box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(8px) !important;
        margin-bottom: 16px !important;
        transition: border-color 0.25s ease !important;
    }}
    
    /* Ефект при избиране или писане в поле (светва в синьо като логото) */
    div.stSelectbox:focus-within, div.stNumberInput:focus-within, div.stTextInput:focus-within {{
        border-color: rgba(0, 242, 254, 0.3) !important;
    }}
    
    /* Ултрамодерни системни бутони с деликатна неонова рамка */
    button[data-testid="stBaseButton-secondary"], 
    button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, #1c202a, #11141a) !important; 
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important; 
        border-radius: 14px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; 
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        width: 100% !important;
        padding: 10px 20px !important;
    }}
    
    /* Плавен неонов блясък при докосване на бутон */
    button[data-testid="stBaseButton-secondary"]:hover, 
    button[data-testid="stBaseButton-primary"]:hover {{
        background: linear-gradient(135deg, #242936, #151922) !important;
        transform: translateY(-1px) !important; 
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.25) !important;
        border-color: rgba(0, 242, 254, 0.4) !important;
    }}
    
    button[data-testid="stBaseButton-secondary"]:active, 
    button[data-testid="stBaseButton-primary"]:active {{
        transform: translateY(0px) !important;
    }}
    
    small {{ color: #8a90a1 !important; font-weight: 500 !important; }}
</style>

{logo_html_tag}
<hr style="border: 0; border-top: 1px solid rgba(255,255,255,0.06); margin-bottom: 25px; margin-top: 15px;">
''', unsafe_allow_html=True)
