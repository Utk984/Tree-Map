import folium
import pandas as pd
from geopy.distance import geodesic


def compute_confusion_matrix_with_matches(df_groundtruth, df_predictions, threshold=10):
    # Extract coordinates
    groundtruth_coords = df_groundtruth[["tree_lat", "tree_lng"]].values
    prediction_coords = df_predictions[["tree_lat", "tree_lng"]].values

    # Initialize tracking variables
    tp_count = 0
    false_positives = []
    false_negatives = set(range(len(groundtruth_coords)))
    matched_predictions = set()
    tp_matches = []  # Store matched ground truth and predictions

    # Compute distances and match predictions to ground truth
    for i, gt_coord in enumerate(groundtruth_coords):
        min_distance = float("inf")
        best_match = None

        for j, pred_coord in enumerate(prediction_coords):
            if j in matched_predictions:
                continue  # Skip already matched predictions

            distance = geodesic(gt_coord, pred_coord).meters
            if distance < threshold and distance < min_distance:
                min_distance = distance
                best_match = j

        if best_match is not None:
            tp_count += 1
            matched_predictions.add(best_match)
            false_negatives.discard(i)
            tp_matches.append((gt_coord, prediction_coords[best_match]))

    # Remaining predictions are false positives
    false_positives = [
        j for j in range(len(prediction_coords)) if j not in matched_predictions
    ]

    # Compute FN and FP counts
    fn_count = len(false_negatives)
    fp_count = len(false_positives)

    # Create confusion matrix
    confusion_matrix = {
        "True Positives (TP)": tp_count,
        "False Positives (FP)": fp_count,
        "False Negatives (FN)": fn_count,
    }

    return confusion_matrix, tp_matches, false_negatives, false_positives


def plot_with_matches(
    df_groundtruth, df_predictions, tp_matches, map_center, zoom_start=16
):
    # Create a folium map centered at the provided coordinates
    fmap = folium.Map(
        location=map_center,
        zoom_start=zoom_start,
        zoom_control=True,
        max_zoom=25,
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr='&copy; <a href="https://www.esri.com">Esri</a> | Imagery © <a href="https://www.esri.com/en-us/arcgis/products/arcgis-online/overview">Esri</a>',
        name="ESRI World Imagery",
        control=True,
        max_zoom=25,
    ).add_to(fmap)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr='&copy; <a href="https://www.esri.com">Esri</a>',
        name="ESRI World Street Map",
        control=True,
        max_zoom=25,
    ).add_to(fmap)

    # Add ground truth points
    for _, row in df_groundtruth.iterrows():
        folium.Marker(
            location=[row["tree_lat"], row["tree_lng"]],
            popup="Ground Truth",
            icon=folium.Icon(color="green", icon="info-sign"),
        ).add_to(fmap)

    # Add predicted points
    for _, row in df_predictions.iterrows():
        folium.Marker(
            location=[row["tree_lat"], row["tree_lng"]],
            popup="Prediction",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(fmap)

    # Highlight true positives with a circle around both points
    for gt_coord, pred_coord in tp_matches:
        # Calculate the midpoint between ground truth and prediction
        midpoint = [
            (gt_coord[0] + pred_coord[0]) / 2,
            (gt_coord[1] + pred_coord[1]) / 2,
        ]

        # Calculate distance between the two points for the radius
        radius = geodesic(gt_coord, pred_coord).meters / 2 + 2  # Add small buffer

        # Draw a circle around the pair
        folium.Circle(
            location=midpoint,
            radius=radius,
            color="blue",
            fill=True,
            fill_opacity=0.2,
            popup="True Positive Pair",
        ).add_to(fmap)

    folium.LayerControl().add_to(fmap)
    return fmap


# Example usage
df_groundtruth = pd.read_csv("annotations.csv")
df_predictions = pd.read_csv("street_panoramas.csv")

confusion_matrix, tp_matches, false_negatives, false_positives = (
    compute_confusion_matrix_with_matches(df_groundtruth, df_predictions)
)

print(confusion_matrix)

# Define the map center
map_center = [
    df_groundtruth["tree_lat"].mean(),
    df_groundtruth["tree_lng"].mean(),
]

# Generate the map
map_with_matches = plot_with_matches(
    df_groundtruth, df_predictions, tp_matches, map_center
)

# Save or display the map
map_with_matches.save("map_with_matches.html")
