import geopandas as gpd

from utils.boundaries import get_sector_boundary


def sidebar_components(states_df, cities_df, st):
    center_lat, center_lon, zoom = 20.5937, 78.9629, 5
    location = ""

    st.sidebar.title("Map Options")

    selected_state = st.sidebar.selectbox(
        "Select State",
        [""] + list(states_df[states_df["country_name"] == "India"]["name"].unique()),
    )

    selected_city, selected_sector = "", ""
    if selected_state:
        state_data = states_df[states_df["name"] == selected_state].iloc[0]
        center_lat, center_lon, zoom = (
            state_data["latitude"],
            state_data["longitude"],
            8,
        )
        location = selected_state
        if selected_state == "Chandigarh":
            gdf = gpd.read_file("Chandigarh_Sectors.geojson")
            sector_names = gdf["Sector_nam"].unique()
            selected_sector = st.sidebar.selectbox(
                "Select Sector", [""] + list(sector_names)
            )
        else:
            selected_city = st.sidebar.selectbox(
                "Select City",
                [""]
                + list(
                    cities_df[cities_df["state_name"] == selected_state][
                        "name"
                    ].unique()
                ),
            )

    if selected_city:
        city_data = cities_df[cities_df["name"] == selected_city].iloc[0]
        center_lat, center_lon, zoom = city_data["latitude"], city_data["longitude"], 13
        location = selected_city
    elif selected_sector:
        coords = get_sector_boundary(selected_sector)
        center_lat, center_lon = coords[0][0], coords[0][1]
        location = "Sector:" + selected_sector
        zoom = 15

    return center_lat, center_lon, zoom, location
