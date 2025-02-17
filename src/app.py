import os

import folium
import folium.plugins
import numpy as np
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv
from folium.plugins import MarkerCluster
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from OSMPythonTools.overpass import Overpass
from scipy.spatial import ConvexHull, Delaunay
from streamlit_folium import folium_static, st_folium
from tqdm import tqdm

from utils.boundaries import get_osm_data, get_sector_boundary
from utils.sidebar import sidebar_components

load_dotenv()

DB_URL = os.getenv("DB_URL")
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGE_DIR = os.path.join(project_root, "static", "streetview_images")
os.makedirs(IMAGE_DIR, exist_ok=True)

overpass = Overpass()

st.set_page_config(layout="wide", page_title="Tree Inventory of India")
st.html("<style> .main {overflow: hidden} </style>")


def load_data_fromcsv():
    df = pd.read_csv("./all_trees.csv")
    df["id"] = range(1, len(df) + 1)
    # df["conf"] = df["conf"].apply(
    #     lambda x: float(re.search(r"([\d.]+)", str(x)).group())
    # )
    # df = df[df["conf"] >= 0.1]
    # df = df[df["image_path"].str.contains("view0|view2")]

    df = df[
        [
            "id",
            "tree_lat",
            "tree_lng",
            "lat_offset",
            "lng_offset",
            "gpt_species",
            "gpt_common_name",
            "gpt_description",
            "image_path",
            "address",
        ]
    ]

    df["lat_offset"] = df["lat_offset"].astype(float)
    df["lng_offset"] = df["lng_offset"].astype(float)
    df["tree_lat"] = df["tree_lat"].astype(float)
    df["tree_lng"] = df["tree_lng"].astype(float)

    df = df.dropna(subset=["tree_lat", "tree_lng"])

    coordinates = df.values.tolist()
    species = df["gpt_common_name"].value_counts()
    # remove "Unknown" from value counts
    species = species[species.index != "Unknown Tree Species"]
    species = species[species.index != "Unknown"]

    return coordinates, species


@st.cache_data(ttl=60)
def load_data_fromdb():
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
        cursor.close()
        conn.close()

        print(f"Loaded {len(coordinates)} coordinates from the database.")
    except Exception as e:
        st.error(f"Error loading data from database: {e}")

    return coordinates


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
        locations=boundary_points, color="blue", weight=2, fill=True, fill_opacity=0.2
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


def add_tree_markers(map_object, coordinates, min_distance=1.0):
    """
    Add tree markers to the map while maintaining a minimum distance between trees.

    :param map_object: The folium map object
    :param coordinates: List of tree data
    :param min_distance: Minimum distance in meters between trees
    """
    cluster = MarkerCluster(
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
    ) in tqdm(coordinates):
        # Apply offsets
        lat += lat_offset / 1113200
        lon += lng_offset / 1113200

        image_path = os.path.join(
            "http://127.0.0.1:8000/", f"{img_path.split('/')[-1]}"
        )
        image_html = f'<img src="{image_path}" width="100%">'

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

        # Add marker to the cluster
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(icon="tree", prefix="fa", color="green"),
        ).add_to(cluster)

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
        .main {
            padding: 0.5rem 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        iframe {
            width: 100% !important;
            height: 80vh !important;
            margin: 0 auto;
        }
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0rem;
            max-width: 100% !important;
        }
        h1 {
            text-align: center;
            padding: 0.5rem 1rem;
            font-size: 1.8em;
            margin: 10;
            width: 100%;
            color: white;
        }
        .stMarkdown {
            width: 100%;
        }
        div[data-testid="stVerticalBlock"] {
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("🌳 Tree Inventory 🌳")

    # Load data
    states_df = pd.read_csv("./locations/states.csv")
    cities_df = pd.read_csv("./locations/cities.csv")
    coordinates, species = load_data_fromcsv()
    filtered_coordinates = coordinates

    # Sidebar components
    center_lat, center_lon, zoom, location = sidebar_components(
        states_df, cities_df, st
    )

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)

    if location:
        if location.startswith("Sector:"):
            boundary_data = get_sector_boundary(location.split(":")[1])
        else:
            boundary_data = get_osm_data(location)
        filtered_coordinates = add_boundary_to_map(boundary_data, m, coordinates)

    st.sidebar.markdown(
        f"""
        <div style="background-color:#f0f0f5; padding: 10px; border-radius: 10px; margin-top: 20px; text-align: center;">
            <h2 style="color: #000000;">Total Trees 🌳 : {len(filtered_coordinates)}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    species_count = species.head(5)
    st.sidebar.markdown(
        f"""
    <div style="
        background-color: #f0f0f5;
        padding: 10px; 
        border-radius: 10px; 
        margin-top: 20px; 
    ">
        <h2 style="color: #000000; text-align: center;">Top 5 species</h2>
        <ul style="list-style-type: none; padding: 0; font-size: 18px; color: #000;">
            <li style="padding: 5px 0;"><b>{species_count.index[0]}</b>: {species_count[0]}</li>
            <li style="padding: 5px 0;"><b>{species_count.index[1]}</b>: {species_count[1]}</li>
            <li style="padding: 5px 0;"><b>{species_count.index[2]}</b>: {species_count[2]}</li>
            <li style="padding: 5px 0;"><b>{species_count.index[3]}</b>: {species_count[3]}</li>
            <li style="padding: 5px 0;"><b>{species_count.index[4]}</b>: {species_count[4]}</li>
        </ul>
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
