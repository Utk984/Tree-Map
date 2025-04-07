import os

import folium
import geopandas as gpd
import leafmap.foliumap as leafmap
import numpy as np
import pandas as pd
from folium.plugins import MarkerCluster
from shapely.geometry import Point
from tqdm import tqdm


def load_tree_data():
    """
    Load tree data from CSV and convert to a GeoDataFrame
    """
    df = pd.read_csv("./tree_data.csv")
    df["id"] = range(1, len(df) + 1)

    df = df[["id", "tree_lat", "tree_lng", "image_path", "conf"]]
    df = df.dropna(subset=["tree_lat", "tree_lng"])
    df["tree_lat"] = df["tree_lat"].astype(float)
    df["tree_lng"] = df["tree_lng"].astype(float)

    geometry = [Point(xy) for xy in zip(df["tree_lng"], df["tree_lat"])]
    return gpd.GeoDataFrame(df, geometry=geometry)


def load_streetview_data():
    """
    Load street view data from CSV and convert to a GeoDataFrame
    """
    df = pd.read_csv("./csvs/delhi_streets.csv")
    df = df.dropna(subset=["lat", "lon"])
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)

    geometry = [Point(xy) for xy in zip(df["lon"], df["lat"])]
    return gpd.GeoDataFrame(df, geometry=geometry)


def add_tree_markers(map_object, tree_gdf, min_distance=0.0):
    """
    Add clustered tree markers with popup images to the map.
    """
    buffer_distance = min_distance / 111320
    coords = np.array([(geom.x, geom.y) for geom in tree_gdf.geometry])
    cell_size = buffer_distance * 2
    min_x, min_y = np.min(coords, axis=0)
    grid_indices = np.floor((coords - [min_x, min_y]) / cell_size).astype(int)

    grid_cells = {}
    for i, (gx, gy) in enumerate(grid_indices):
        grid_cells.setdefault((gx, gy), []).append(i)

    selected_indices = []
    total_points = len(tree_gdf)

    with tqdm(total=total_points, desc="Filtering trees") as pbar:
        for cell_idx, point_indices in grid_cells.items():
            for idx in point_indices:
                if idx in selected_indices:
                    continue

                x, y = coords[idx]
                too_close = False
                gx, gy = cell_idx

                for dx, dy in [
                    (-1, -1),
                    (-1, 0),
                    (-1, 1),
                    (0, -1),
                    (0, 0),
                    (0, 1),
                    (1, -1),
                    (1, 0),
                    (1, 1),
                ]:
                    neigh_cell = (gx + dx, gy + dy)
                    if neigh_cell in grid_cells:
                        for neigh_idx in grid_cells[neigh_cell]:
                            if neigh_idx in selected_indices:
                                nx, ny = coords[neigh_idx]
                                if ((x - nx) ** 2 + (y - ny) ** 2) < buffer_distance**2:
                                    too_close = True
                                    break
                    if too_close:
                        break

                if not too_close:
                    selected_indices.append(idx)
                pbar.update(1)

    filtered_gdf = tree_gdf.iloc[selected_indices].copy().reset_index(drop=True)
    feature_group = folium.FeatureGroup(name="Trees")

    for idx, tree in filtered_gdf.iterrows():
        lat, lon = tree.geometry.y, tree.geometry.x
        img_url = f"http://localhost:8000/views/{tree['image_path'].split('/')[-1]}"
        popup_content = f"""
            <div style='width: 250px;'>
                <h4>Tree {idx}</h4>
                <img src='{img_url}' width='100%'>
                <p><strong>Coordinates:</strong> {lat:.6f}, {lon:.6f}</p>
                <p><strong>Confidence:</strong> {tree['conf']:.2f}</p>
            </div>
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color="darkgreen",
            fill=True,
            fill_color="lightgreen",
            fill_opacity=0.8,
            weight=2,
            popup=popup_content,
        ).add_to(feature_group)

    feature_group.add_to(map_object)
    return map_object, filtered_gdf


def add_streetview_markers(map_object, streetview_gdf):
    """
    Add street view panorama markers with popup images.
    """
    feature_group = folium.FeatureGroup(name="Street View")

    for _, pano in streetview_gdf.iterrows():
        lat, lon = pano.geometry.y, pano.geometry.x
        img_url = f"http://localhost:8000/full/{pano['pano_id']}.jpg"
        popup_content = f"""
            <div style='width: 250px;'>
                <h4>Street View</h4>
                <img src='{img_url}' width='100%'>
                <p><strong>Coordinates:</strong> {lat:.6f}, {lon:.6f}</p>
            </div>
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color="blue",
            fill=True,
            fill_color="cyan",
            fill_opacity=0.7,
            weight=2,
            popup=popup_content,
        ).add_to(feature_group)

    feature_group.add_to(map_object)
    return map_object


def main():
    """
    Main function to create and display the map
    """
    print("Loading data...")
    tree_gdf = load_tree_data()
    streetview_gdf = load_streetview_data()

    m = leafmap.Map(center=[28.6139, 77.2090], zoom_start=12, max_zoom=25)
    m.add_basemap("CartoDB.Positron")
    m.add_tile_layer(
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Esri World Imagery",
        attribution="Esri",
        max_native_zoom=19,
        max_zoom=25,
    )

    m, _ = add_tree_markers(m, tree_gdf)
    m = add_streetview_markers(m, streetview_gdf)
    folium.LayerControl().add_to(m)

    output_path = "tree_streetview_map.html"
    m.to_html(output_path)
    print(f"Map saved to {output_path}")

    import webbrowser

    webbrowser.open(f"file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
