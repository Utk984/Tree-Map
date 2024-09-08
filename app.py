import folium
import numpy as np
import pandas as pd
import streamlit as st
from OSMPythonTools.overpass import Overpass
from scipy.spatial import ConvexHull, Delaunay
from streamlit_folium import folium_static

from boundaries import get_osm_data

overpass = Overpass()

# Streamlit app configuration
st.set_page_config(layout="wide", page_title="Tree Inventory of India")


# Map type configuration
map_types = {
    "OpenStreetMap": {
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        "name": "OpenStreetMap",
    },
    "Esri Satellite": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attribution": "Esri",
        "name": "Esri Satellite",
    },
    "Esri Labels": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        "attribution": "Esri",
        "name": "Esri Labels",
    },
}

# Tree coordinates
coordinates = [
    (20.5937, 78.9629),
    (19.0760, 72.8777),
    (28.6139, 77.2090),
    (22.5726, 88.3639),
    (13.0827, 80.2707),
    (12.9716, 77.5946),
    (17.3850, 78.4867),
    (25.2950, 82.9876),
    (23.8103, 90.4125),
    (21.1702, 72.8311),
]


@st.cache_data
def load_data():
    states = pd.read_csv("./locations/states.csv")
    cities = pd.read_csv("./locations/cities.csv")
    return states, cities


def sidebar_components(states_df, cities_df):
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

    return selected_state, selected_city, selected_map_type


def add_boundary_to_map(result, map_object):
    boundary_coords = [
        (element["lat"], element["lon"])
        for element in result
        if "lat" in element and "lon" in element
    ]
    if len(boundary_coords) < 3:
        return coordinates

    points_array = np.array(boundary_coords)
    hull = ConvexHull(points_array)
    boundary_points = points_array[hull.vertices]
    folium.Polygon(
        locations=boundary_points, color="blue", weight=1, fill=True, fill_opacity=0.1
    ).add_to(map_object)

    delaunay = Delaunay(boundary_coords)
    filtered_coords = [
        (lat, lon) for lat, lon in coordinates if delaunay.find_simplex([lat, lon]) >= 0
    ]

    return filtered_coords


# Build the folium map
def create_map(center_lat, center_lon, zoom, selected_map_type):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles=None)

    for layer_name, layer_data in map_types.items():
        folium.TileLayer(
            tiles=layer_data["url"],
            attr=layer_data["attribution"],
            name=layer_data["name"],
            overlay=False,
        ).add_to(m)

    folium.TileLayer(
        tiles=map_types[selected_map_type]["url"],
        attr=map_types[selected_map_type]["attribution"],
    ).add_to(m)

    return m


# Add markers for each location
def add_tree_markers(map_object, coordinates):
    for lat, lon in coordinates:
        popup_content = f"""
        <div style="width: 200px">
            <h4>Location Information</h4>
            <p><strong>Latitude:</strong> {lat:.8f}</p>
            <p><strong>Longitude:</strong> {lon:.8f}</p>
            <p>Add any additional information here.</p>
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(icon="leaf", color="green"),
        ).add_to(map_object)


def main():
    st.title("🌳 Tree Inventory of India")
    st.markdown(
        "### Explore tree data and boundaries within India using interactive maps."
    )

    states_df, cities_df = load_data()

    selected_state, selected_city, selected_map_type = sidebar_components(
        states_df, cities_df
    )

    center_lat, center_lon, zoom = 20.5937, 78.9629, 4
    location = ""

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

    m = create_map(center_lat, center_lon, zoom, selected_map_type)

    if location:
        boundary_data = get_osm_data(location)
        filtered_coordinates = add_boundary_to_map(boundary_data, m)
    else:
        filtered_coordinates = coordinates

    st.sidebar.markdown(
        f"""
        <div style="background-color:#f0f0f5; padding: 10px; border-radius: 10px; margin-top: 20px;">
            <h2 style="color: #000000;">Total Trees 🌳 : {len(filtered_coordinates)}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    add_tree_markers(m, filtered_coordinates)

    folium.plugins.Fullscreen(
        position="topright",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(m)

    folium_static(m)


if __name__ == "__main__":
    main()
