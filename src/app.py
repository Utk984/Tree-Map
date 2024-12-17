import os

import folium
import folium.plugins
import numpy as np
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from OSMPythonTools.overpass import Overpass
from scipy.spatial import ConvexHull, Delaunay
from streamlit_folium import folium_static

from utils.boundaries import get_osm_data, get_sector_boundary
from utils.sidebar import sidebar_components

load_dotenv()

DB_URL = os.getenv("DB_URL")
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGE_DIR = os.path.join(project_root, "static", "streetview_images")
os.makedirs(IMAGE_DIR, exist_ok=True)

overpass = Overpass()

st.set_page_config(layout="wide", page_title="Tree Inventory of India")
# st.html("<style> .main {overflow: hidden} </style>")


@st.cache_data(ttl=60)
def load_data():
    # Load state and city data
    states = pd.read_csv("./locations/states.csv")
    cities = pd.read_csv("./locations/cities.csv")

    # Load coordinates from the database
    coordinates = []
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                t.tree_id,
                t.lat,
                t.lng,
                t.lat_offset,
                t.lng_offset,
                t.species,
                t.common_name,
                t.description,
                t.img_path,
                i.address
            FROM tree_details t JOIN streetview_images i ON t.image_id = i.image_id;
            """
        )
        coordinates = cursor.fetchall()
        print(f"Loaded {len(coordinates)} coordinates from the database.")
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Error loading data from database: {e}")

    return states, cities, coordinates


def get_address_geopy(lat, lng):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.reverse((lat, lng), language="en")
    if location:
        return location.address
    else:
        return None


def add_boundary_to_map(boundary_coords, map_object, coordinates):
    points_array = np.array(boundary_coords)
    hull = ConvexHull(points_array)
    boundary_points = points_array[hull.vertices]
    folium.Polygon(
        locations=boundary_points, color="blue", weight=1, fill=True, fill_opacity=0.05
    ).add_to(map_object)

    delaunay = Delaunay(boundary_coords)
    filtered_coords = [
        (
            tree_id,
            lat,
            lon,
            lat_offset,
            lng_offset,
            species,
            common_name,
            description,
            img_path,
            address,
        )
        for tree_id, lat, lon, lat_offset, lng_offset, species, common_name, description, img_path, address in coordinates
        if delaunay.find_simplex([lat, lon]) >= 0
    ]

    return filtered_coords


def add_tree_markers(map_object, coordinates):
    cluster = MarkerCluster(
        # Disable clustering at zoom level 17
        options={
            "disableClusteringAtZoom": 17,
            "spiderfyOnMaxZoom": False,
        }
    )

    for (
        tree_id,
        lat,
        lon,
        lat_offset,
        lng_offset,
        species,
        common_name,
        description,
        img_path,
        address,
    ) in coordinates:
        lat += lat_offset / 1113200
        lon += lng_offset / 1113200

        image_path = os.path.join(
            "http://127.0.0.1:8000/", f"{img_path.split('/')[-1]}"
        )
        image_html = f'<img src="{image_path}" width="100%">'

        # address = None
        if address:
            address_html = (
                f'<p style="margin: 2px 0;"><strong>Address:</strong> {address}</p>'
            )
        else:
            address_html = f'<p style="margin: 2px 0;"><strong>Address:</strong> {lat:.8f}, {lon:.8f}</p>'

        popup_content = f"""
        <div style="width: 250px; line-height: 1.2; margin: 0;">
            <h4 style="margin: 0; padding-bottom: 4px;">Tree {tree_id}</h4>
            {image_html}
            {address_html}
            <p style="margin: 2px 0;"><strong>Species:</strong> {species}</p>
            <p style="margin: 2px 0;"><strong>Common Name:</strong> {common_name}</p>
            <p style="margin: 2px 0;"><strong>Description:</strong> {description}</p>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(icon="tree", prefix="fa", color="green"),
        ).add_to(cluster)

        # marker.add_to(map_object)
    cluster.add_to(map_object)

    return map_object


def main():
    st.markdown(
        """
        <style>
        .stApp {
            margin: 0;
            padding: 0;
        }
        iframe {
            width: 100% !important;
            height: calc(100vh - 200px) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🌳 Tree Inventory 🌳")

    # Load data
    states_df, cities_df, coordinates = load_data()
    filtered_coordinates = coordinates

    # Sidebar components
    center_lat, center_lon, zoom, location = sidebar_components(
        states_df, cities_df, st
    )

    m = folium.Map(
        location=[center_lat, center_lon], zoom_start=zoom, max_zoom=23, tiles=None
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
    ).add_to(m)

    if location:
        if location.startswith("Sector:"):
            boundary_data = get_sector_boundary(location.split(":")[1])
        else:
            boundary_data = get_osm_data(location)
        filtered_coordinates = add_boundary_to_map(boundary_data, m, coordinates)

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

    # Display the map
    folium_static(m)


if __name__ == "__main__":
    main()
