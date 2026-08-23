import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

# Configuration and basic setup
st.set_page_config(page_title="PixelApp", page_icon="🐾", layout="centered")
# (Custom CSS styling remains same)

KATEGORII = ["Храна и напитки", "Транспорт", "Куче", "Други", "Нощувки/Хотел", "Депозит/Резервация"]
DATA_FILE, SETTINGS_FILE = "budget_data_2026.csv", "trip_settings_2026.csv"

# Functions for data handling (get_trip_data, save_trip_settings, add_expense)
# ... (File initialization and function definitions)

# =====================================================================
# СРАВНИТЕЛЕН ПАНЕЛ (Comparison Panel) - Optimized Structure
# =====================================================================
if "show_comparison_screen" not in st.session_state: st.session_state["show_comparison_screen"] = False

if st.session_state["show_comparison_screen"]:
    st.header("📊 Глобален сравнителен панел")
    
    # Toggle to switch back
    if not st.toggle("Сравнителен панел", value=True):
        st.session_state["show_comparison_screen"] = False
        st.rerun()
        
    chosen_criteria = st.segmented_control("Критерий:", ["Цена за 1 км", "Обща Стойност", "Изминати км", "Нощувки и Депозити"], default="Цена за 1 км")
    
    # Data aggregation and logic
    # ... (Logic to calculate metrics from CSV files)

    if all_trips_computed:
        df_plot = pd.DataFrame(all_trips_computed)
        # Visuals using Plotly
        fig = px.bar(df_plot.sort_values(by=chosen_criteria, ascending="Изминати" in chosen_criteria), 
                     x=chosen_criteria, y="Пътуване", orientation='h', color=chosen_criteria)
        # ... (Plot formatting)
        st.plotly_chart(fig, use_container_width=True)

    if st.button("❌ Затвори"):
        st.session_state["show_comparison_screen"] = False
        st.rerun()
    st.stop() # Stops execution here for the panel

# =====================================================================
# ГЛАВЕН ЕКРАН (Main Screen) - Standard flow
# =====================================================================
# ... (Main application flow)
