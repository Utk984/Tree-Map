import os

import folium
import geopandas as gpd
import leafmap.foliumap as leafmap
import numpy as np
import pandas as pd
from folium.plugins import MarkerCluster
from shapely.geometry import Point
from tqdm import tqdm


def load_data_from_csv():
    """
    Load tree data from CSV and convert to a GeoDataFrame
    """
    df = pd.read_csv("./tree_data.csv")
    df["id"] = range(1, len(df) + 1)

    # Select necessary columns
    df = df[
        [
            "id",
            "tree_lat",
            "tree_lng",
            "image_path",
            "conf",
        ]
    ]

    # Convert to float and drop NaN values
    df["tree_lat"] = df["tree_lat"].astype(float)
    df["tree_lng"] = df["tree_lng"].astype(float)
    df = df.dropna(subset=["tree_lat", "tree_lng"])

    # Create geometry column - note that Point takes (x, y) which is (longitude, latitude)
    geometry = [Point(xy) for xy in zip(df["tree_lng"], df["tree_lat"])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    return gdf


def add_tree_markers(map_object, tree_gdf, min_distance=2.0):
    """
    Add clustered light green circle markers with a border to the map.

    Args:
        map_object: The leafmap map object.
        tree_gdf: GeoDataFrame of tree data.
        min_distance: Minimum distance between markers in meters.

    Returns:
        Updated map object with markers, filtered GeoDataFrame.
    """
    buffer_distance = min_distance / 111320

    coords = np.array([(geom.x, geom.y) for geom in tree_gdf.geometry])
    cell_size = buffer_distance * 2
    min_x, min_y = np.min(coords, axis=0)
    grid_indices = np.floor((coords - [min_x, min_y]) / cell_size).astype(int)

    grid_cells = {}
    for i, (gx, gy) in enumerate(grid_indices):
        key = (gx, gy)
        if key not in grid_cells:
            grid_cells[key] = []
        grid_cells[key].append(i)

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
                neighboring_cells = [
                    (gx + dx, gy + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]
                ]

                for neigh_cell in neighboring_cells:
                    if neigh_cell not in grid_cells:
                        continue

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

    filtered_gdf = tree_gdf.iloc[selected_indices].copy()
    filtered_gdf = filtered_gdf.reset_index(drop=True)

    feature_group = folium.FeatureGroup(name="Trees")

    for idx, tree in tqdm(
        filtered_gdf.iterrows(), total=len(filtered_gdf), desc="Adding circles"
    ):
        lat, lon = tree.geometry.y, tree.geometry.x
        img_path = tree["image_path"]
        conf = tree["conf"]
        i = tree["id"]

        # Get just the filename without the path for use in URL
        image_filename = img_path.split("/")[-1]

        image_url = f"http://localhost:8000/{image_filename}"
        image_html = f'<img src="{image_url}" width="100%">'
        coords_html = f'<p style="margin: 2px 0;"><strong>Coordinates:</strong> {lat:.6f}, {lon:.6f}</p>'
        conf_html = (
            f'<p style="margin: 2px 0;"><strong>Confidence:</strong> {conf:.2f}</p>'
        )

        popup_content = f"""
            <div style="width: 250px; line-height: 1.2; margin: 0;">
                <h4 style="margin: 0; padding-bottom: 4px;">Tree {idx}</h4>
                {image_html}
                {coords_html}
                {conf_html}
            </div>
        """

        circle = folium.CircleMarker(
            location=[lat, lon],
            radius=8,  # Adjust size of circle
            color="darkgreen",  # Border color
            fill=True,
            fill_color="lightgreen",  # Fill color
            fill_opacity=0.8,  # Transparency of fill
            weight=2,  # Border thickness
            popup=popup_content,
        )

        circle.add_to(feature_group)

    # feature_group.add_to(cluster)
    feature_group.add_to(map_object)

    return map_object, filtered_gdf


def main():
    """
    Main function to create and display the map
    """
    # Load tree data using GeoPandas
    print("Loading tree data...")
    tree_gdf = load_data_from_csv()
    filtered_gdf = tree_gdf

    # Create a leafmap Map instance
    m = leafmap.Map(center=[28.6139, 77.2090], zoom_start=12, max_zoom=25)

    m.add_tile_layer(
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Esri World Imagery",
        attribution="Esri",
        max_native_zoom=19,
        max_zoom=25,
    )

    # Add labels to basemap
    m.add_basemap("CartoDB.PositronOnlyLabels")

    # Add tree markers efficiently
    m, filtered_gdf = add_tree_markers(m, filtered_gdf)

    # Add layer control - using folium's method
    folium.LayerControl().add_to(m)

    print(f"Total trees shown: {len(filtered_gdf)}")

    # Save the map to an HTML file
    output_path = "tree_map.html"
    m.to_html(output_path)
    print(f"Map saved to {output_path}")

    import webbrowser

    webbrowser.open(f"file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
