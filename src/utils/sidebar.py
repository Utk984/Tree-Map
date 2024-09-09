def sidebar_components(states_df, cities_df, st, map_types):
    center_lat, center_lon, zoom = 20.5937, 78.9629, 4
    location = ""

    st.sidebar.title("Map Options")

    selected_state = st.sidebar.selectbox(
        "Select State",
        [""] + list(states_df[states_df["country_name"] == "India"]["name"].unique()),
    )

    selected_city = ""
    if selected_state:
        selected_city = st.sidebar.selectbox(
            "Select City",
            [""]
            + list(
                cities_df[cities_df["state_name"] == selected_state]["name"].unique()
            ),
        )

    selected_map_type = st.sidebar.selectbox("Select Map Type", list(map_types.keys()))

    if selected_city:
        city_data = cities_df[cities_df["name"] == selected_city].iloc[0]
        center_lat, center_lon, zoom = city_data["latitude"], city_data["longitude"], 11
        location = selected_city
    elif selected_state:
        state_data = states_df[states_df["name"] == selected_state].iloc[0]
        center_lat, center_lon, zoom = (
            state_data["latitude"],
            state_data["longitude"],
            7,
        )
        location = selected_state

    return center_lat, center_lon, zoom, location, selected_map_type
