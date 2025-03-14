import os

import folium
import geopandas as gpd
import leafmap.foliumap as leafmap
import numpy as np
import pandas as pd
from folium.plugins import MarkerCluster
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon
from tqdm import tqdm


def load_data_from_csv():
    """
    Load tree data from CSV and convert to a GeoDataFrame
    """
    df = pd.read_csv("./data/delhi_trees.csv")
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


def add_tree_markers(map_object, tree_gdf, min_distance=1.0):
    """
    Add tree markers to the map using efficient spatial filtering

    Args:
        map_object: The leafmap map object
        tree_gdf: GeoDataFrame of tree data
        min_distance: Minimum distance between markers in meters

    Returns:
        Updated map object with markers, filtered GeoDataFrame
    """
    # Convert min_distance (meters) to degrees (approximate)
    buffer_distance = min_distance / 111320

    print(f"Filtering {len(tree_gdf)} trees with grid-based approach...")

    # Extract coordinates and create a coordinate-to-index mapping
    coords = np.array([(geom.x, geom.y) for geom in tree_gdf.geometry])

    # Create a spatial grid for efficient filtering
    # Determine grid cell size based on min_distance
    cell_size = buffer_distance * 2  # Cell size slightly larger than search radius

    # Compute grid indices for each point
    min_x, min_y = np.min(coords, axis=0)
    grid_indices = np.floor((coords - [min_x, min_y]) / cell_size).astype(int)

    # Create dictionary mapping grid cells to points
    grid_cells = {}
    for i, (gx, gy) in enumerate(grid_indices):
        key = (gx, gy)
        if key not in grid_cells:
            grid_cells[key] = []
        grid_cells[key].append(i)

    # Initialize array to track selected points
    selected_indices = []

    # Process grid cells in order (this introduces a consistent bias, but is fast)
    # Add a progress bar to show progress for the entire filtering process
    total_points = len(tree_gdf)
    with tqdm(total=total_points, desc="Filtering trees") as pbar:
        for cell_idx, point_indices in grid_cells.items():
            # Within each cell, process points one by one
            for idx in point_indices:
                # Skip if this point was already rejected
                if idx in selected_indices:
                    continue

                # Get this point's coordinates
                x, y = coords[idx]

                # Check if this point is too close to any already selected point
                too_close = False

                # Get neighboring cells to check (including this cell)
                gx, gy = cell_idx
                neighboring_cells = [
                    (gx + dx, gy + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]
                ]

                # Check against points in neighboring cells
                for neigh_cell in neighboring_cells:
                    if neigh_cell not in grid_cells:
                        continue

                    for neigh_idx in grid_cells[neigh_cell]:
                        if (
                            neigh_idx in selected_indices
                        ):  # Only check against selected points
                            nx, ny = coords[neigh_idx]
                            # Check Euclidean distance
                            if ((x - nx) ** 2 + (y - ny) ** 2) < buffer_distance**2:
                                too_close = True
                                break

                    if too_close:
                        break

                if not too_close:
                    selected_indices.append(idx)

                # Update progress bar
                pbar.update(1)

    print(f"Selected {len(selected_indices)} trees after spatial filtering")

    # Get filtered GeoDataFrame using selected indices
    filtered_gdf = tree_gdf.iloc[selected_indices].copy()

    # Reset index of filtered GeoDataFrame to avoid potential issues with non-sequential indices
    filtered_gdf = filtered_gdf.reset_index(drop=True)

    # Add markers for the filtered trees with progress bar
    print("Adding tree markers to map...")
    cluster = MarkerCluster(
        options={
            "disableClusteringAtZoom": 17,
            "spiderfyOnMaxZoom": False,
        }
    )

    for idx, tree in tqdm(
        filtered_gdf.iterrows(), total=len(filtered_gdf), desc="Adding markers"
    ):
        lat, lon = tree.geometry.y, tree.geometry.x
        img_path = tree["image_path"]
        conf = tree["conf"]
        i = tree["id"]

        # Get just the filename without the path for use in URL
        image_filename = img_path.split("/")[-1]

        # For cross-origin compatibility, use an iframe to load the image
        # This will ensure the image loads regardless of how the HTML is viewed\
        image_url = f"http://localhost:8000/{image_filename}"
        image_html = f'<img src="{image_url}" width="100%">'
        coords_html = f'<p style="margin: 2px 0;"><strong>Coordinates:</strong> {lat:.6f}, {lon:.6f}</p>'
        conf_html = (
            f'<p style="margin: 2px 0;"><strong>Confidence:</strong> {conf:.2f}</p>'
        )

        address_html = (
            f'<p style="margin: 2px 0;"><strong>Address:</strong> {image_url}</p>'
        )
        popup_content = f"""
            <div style="width: 250px; line-height: 1.2; margin: 0;">
                <h4 style="margin: 0; padding-bottom: 4px;">Tree {idx}</h4>
                {image_html}
                {coords_html}
                {conf_html}
            </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=250),
            icon=folium.Icon(
                icon="tree",
                prefix="fa",
                color="green",
                icon_color="#ffffff",
            ),
        ).add_to(cluster)

    cluster.add_to(map_object)
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
    m = leafmap.Map(center=[28.6139, 77.2090], zoom_start=12)  # Default to Delhi

    # Add basemaps
    m.add_basemap("HYBRID")
    m.add_basemap("Esri.WorldImagery")

    # Add labels to basemap
    m.add_basemap("CartoDB.PositronOnlyLabels")

    # Add South Delhi boundary as a layer
    print("Adding South Delhi boundary...")
    south_delhi_geojson = "./data/South Delhi.geojson"

    # Add GeoJSON to map with styling
    m.add_geojson(
        south_delhi_geojson,
        layer_name="South Delhi Boundary",
        style={
            "color": "#3388ff",
            "weight": 3,
            "fillColor": "#3388ff",
            "fillOpacity": 0.1,
        },
        info_mode="on_hover",
        zoom_to_layer=False,
    )

    # Add tree markers efficiently
    m, filtered_gdf = add_tree_markers(m, filtered_gdf)

    # Add layer control - using folium's method
    folium.LayerControl().add_to(m)

    print(f"Total trees shown: {len(filtered_gdf)}")

    # Save the map to an HTML file
    output_path = "tree_map.html"
    m.to_html(output_path)
    print(f"Map saved to {output_path}")

    # Add instructions for viewing the map
    print("\nTo view the map with images correctly:")
    print("1. Make sure your image server is running: python -m http.server 8000")
    print("2. Open the saved map in a web browser while the server is running")
    print(
        f"3. If you want to share the map, you'll need to host both the HTML and images on a web server"
    )

    # Optional: Open the map in a web browser
    import webbrowser

    webbrowser.open(f"file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
