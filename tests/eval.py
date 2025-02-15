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

    print(f"True Positives: {tp_count}")
    print(f"False Positives: {fp_count}")
    print(f"False Negatives: {fn_count}")
    print(f"\nPrecision: {tp_count / (tp_count + fp_count):.2f}")
    print(f"Recall: {tp_count / (tp_count + fn_count):.2f}")

    return tp_matches


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

    # Add ground truth points
    for _, row in df_groundtruth.iterrows():
        folium.Marker(
            location=[row["tree_lat"], row["tree_lng"]],
            popup=row["pano_id"],
            icon=folium.Icon(color="green", icon="info-sign"),
        ).add_to(fmap)

    for _, row in df_predictions.iterrows():
        # HTML content for the popup with an image
        path = "../static/28_29_images/" + row["image_path"].split("/")[-1]
        image_popup = folium.Popup(
            f"""
        <div style="width: 150px; height: auto; text-align: center;">
            <p>{row["pano_id"]}</p>
            <img src="{path}" alt="Prediction Image" style="width: 100%; height: auto;" />
        </div>
        """,
            max_width=200,
        )

        folium.Marker(
            location=[row["tree_lat"], row["tree_lng"]],
            popup=image_popup,
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(fmap)

    blue_count = 0

    # Highlight true positives with a circle around both points
    for gt_coord, pred_coord in tp_matches:
        midpoint = [
            (gt_coord[0] + pred_coord[0]) / 2,
            (gt_coord[1] + pred_coord[1]) / 2,
        ]

        # get pano_id of gt_cord from df_groundtruth
        gt_pano_id = df_groundtruth[
            (df_groundtruth["tree_lat"] == gt_coord[0])
            & (df_groundtruth["tree_lng"] == gt_coord[1])
        ]["pano_id"].values[0]

        # get pano_id of pred_cord from df_predictions
        pred_pano_id = df_predictions[
            (df_predictions["tree_lat"] == pred_coord[0])
            & (df_predictions["tree_lng"] == pred_coord[1])
        ]["pano_id"].values[0]

        color = "purple"
        if gt_pano_id == pred_pano_id:
            blue_count += 1
            color = "blue"

        # Calculate distance between the two points for the radius
        radius = geodesic(gt_coord, pred_coord).meters / 2 + 2

        # Draw a circle around the pair
        folium.Circle(
            location=midpoint,
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.2,
            popup="True Positive Pair",
        ).add_to(fmap)

    folium.LayerControl().add_to(fmap)

    print(f"\nMatches with same pano_id: {blue_count / len(tp_matches) * 100:.2f}%")
    return fmap


# Example usage
df_groundtruth = pd.read_csv("./28_29_groundtruth.csv")
# df_predictions = pd.read_csv("./28_29_predicted.csv")
df_predictions = pd.read_csv("./tree_data 2.csv")

df_predictions = df_predictions[
    df_predictions["image_path"].str.contains("view0|view2")
]

tp_matches = compute_confusion_matrix_with_matches(df_groundtruth, df_predictions)

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
map_with_matches.save("map_with_matches2.html")
# map_with_matches.save("map_with_matches1.html")
