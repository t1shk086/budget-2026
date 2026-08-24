import streamlit as st


st.set_page_config(
    page_title="Travel Manager",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ Travel Manager")
st.subheader("Управлявай своите пътувания и разходи")

st.write("Добре дошъл в Travel Manager!")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Пътувания", "0")

with col2:
    st.metric("Общо разходи", "€0.00")

with col3:
    st.metric("Оставащ бюджет", "€0.00")
