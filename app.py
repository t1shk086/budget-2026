else:
    trip_id = st.session_state["current_trip"]
    if st.button("⬅️ НАЗАД КЪМ НАЧАЛОТО", use_container_width=True):
        st.session_state["current_trip"] = None
        st.rerun()
    st.markdown(f"<h2 style='text-align: center; color: #00f2fe;'>🌴 {trip_id.upper().replace('_', ' ')}</h2>", unsafe_allow_html=True)
    
    current_settings = get_trip_settings(trip_id)
    car_index = 0 if current_settings["car_trip"] == "Не" else 1
    car_choice = st.selectbox("Пътувате ли със собствен автомобил?", ["Не", "Да"], index=car_index)
    track_fuel_choice = "Не"
    start_km_val, end_km_val, manual_fuel_val = 0.0, 0.0, 0.0
    if car_choice == "Да":
        track_index = 0 if current_settings["track_fuel"] == "Да" else 1
        track_fuel_choice = st.selectbox("Искате ли изчисляване на разход на гориво?", ["Да", "Добави впоследствие"], index=track_index)
        if track_fuel_choice == "Да":
            start_km_val = st.number_input("Начални км", value=float(current_settings["start_km"]))
            end_km_val = st.number_input("Крайни км", value=float(current_settings["end_km"]))
    save_trip_settings(trip_id, car_choice, track_fuel_choice, start_km_val, end_km_val, manual_fuel_val)

    v_id = st.session_state["form_version"]
    col1, col2 = st.columns(2)
    with col1: s_input = st.number_input("СУМА (EUR)", min_value=0.0, step=1.0, key=f"s_{v_id}")
    with col2: o_input = st.text_input("Описание", key=f"o_{v_id}")

    @st.dialog("⛽ Зареждане на гориво")
    def fuel_modal(amount, category, description):
        liters = st.number_input("Литри", min_value=0.0, step=0.1)
        if st.button("💾 Запиши гориво", use_container_width=True, type="primary"):
            if add_expense(trip_id, amount, category, f"[ГОРИВО] {description}", liters=liters):
                st.session_state["form_version"] += 1
                st.rerun()

    grid = st.columns(3)
    for i, kat in enumerate(KATEGORII):
        with grid[i % 3]:
            if st.button(kat, use_container_width=True, key=f"b_{i}"):
                if s_input and s_input > 0:
                    desc = o_input.strip() if o_input else "Без описание"
                    if kat == "Транспорт" and car_choice == "Да" and track_fuel_choice == "Да" and any(k in desc.lower() for k in ["гориво", "зареждане", "бензин", "дизел"]):
                        fuel_modal(s_input, kat, desc)
                    else:
                        if add_expense(trip_id, s_input, kat, desc):
                            st.session_state["form_version"] += 1
                            st.rerun()

    df_trip = get_trip_data(trip_id)
    df_expenses = df_trip[df_trip["type"] == "expense"]
    total_on_site = float(df_expenses["amount"].sum())
    categories_totals = {k: 0.0 for k in KATEGORII if k != "Депозит/Резервация"}
    total_liters_sum = 0.0
    for _, row in df_expenses.iterrows():
        if row["category"] in categories_totals: categories_totals[row["category"]] += float(row["amount"])
        if row["category"] == "Транспорт": total_liters_sum += float(row.get("liters", 0.0))

    st.subheader("📊 Анализ")
    for kat, s_value in categories_totals.items():
        st.write(f"{get_emoji(kat)} {kat}: **{s_value:.2f} EUR**")

    if car_choice == "Да" and track_fuel_choice == "Да":
        dist = end_km_val - start_km_val
        if dist > 0:
            st.info(f"⛽ Среден разход: **{(total_liters_sum / dist * 100):.1f} л / 100 км** (Изминати: {dist:.1f} км)")

    if not df_trip.empty:
        st.subheader("📋 Хронология")
        for _, r in df_expenses.iterrows():
            st.text(f"{r['date']} - {r['category']}: {r['amount']} EUR ({r['description']})")
