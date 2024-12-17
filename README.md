# Interactive Map with Tree Marker Annotations

This project is a **Streamlit web app** designed for **Tree Inventorization**, which uses **Folium** to display an interactive map with various layers. Users can explore geographic locations, select map types, and visualize individual tree markers. The app supports displaying country, state, and city-specific locations, with the number of tree markers updated dynamically based on the selected area. Tree locations are fetched from a PostGIS server.

## Features

- **Interactive map:** Displays a map centered on the selected country, state, or city.
- **Map layers:** Supports various map types like OpenStreetMap and Esri Satellite.
- **Marker display:** Shows individual tree markers with additional information.
- **Sidebar controls:** Allows the user to select the map type, country, state, and city.
- **Tree tracking:** Automatically updates the count of trees based on the selected area or region.

## Table of Contents

1. [Installation](#installation)
2. [How to Run the App](#how-to-run-the-app)
3. [Usage](#usage)
4. [Customization](#customization)
5. [Acknowledgments](#acknowledgment)

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/Utk984/Tree-Web-Map.git
    cd Tree-Web-Map
    ```

2. **Install dependencies**:

    The dependencies are listed in the `requirements.txt` file. To install them, run:

    ```bash
    pip install -r requirements.txt
    ```

    The following key packages are used:
    
    - **Streamlit**: For creating the web app interface
    - **Pandas**: For handling CSV files containing location data
    - **Folium**: For interactive mapping
    - **Streamlit-Folium**: For integrating Folium maps into the Streamlit interface
    - **PostGIS**: For fetching tree location data from a PostGIS server (details to be configured)

## How to Run the App

Once all dependencies are installed and the PostGIS server is configured, you can run the Streamlit app locally with the following steps:

```bash
cd static/streetview_images
python -m http.server 8000
cd ..
./run.sh
```

This will launch the app in your web browser, where you can explore the map and adjust various settings from the sidebar.

## Usage

### 1. **Map Types**

- **OpenStreetMap**: Default map layer provided by OpenStreetMap contributors.
- **Esri Satellite**: Satellite imagery provided by Esri.
- **Esri Labels**: Adds labels for world boundaries and places from Esri.

You can select the desired map type from the dropdown in the sidebar. The map will update instantly based on the selected map type.

### 2. **Location Selection**

- **Country**: Select a country from the dropdown to focus on that area.
- **State**: If a country is selected, you can choose a state within that country.
- **City**: If a state is selected, you can choose a city within that state.

The map will automatically center and zoom to the selected location.

### 3. **Tree Markers**

- Markers are placed at tree locations fetched from the PostGIS server. Clicking on a marker will display a popup with information about the latitude and longitude.
- The sidebar displays the total number of trees in the selected area or region. If no area is selected, it shows the total count of all markers.

## Customization

### 1. **Adding More Map Layers**

To add new map types, you can modify the `map_types` dictionary in `app.py`. For example, to add **Stamen Terrain** maps:

```python
"Stamen Terrain": {
    "url": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
    "attribution": '&copy; <a href="https://stamen.com">Stamen</a>',
    "name": "Stamen Terrain",
},
```

### 2. **Connecting to PostGIS Server**

### 3. **Location Data**

If you want to expand the location data with more countries, states, or cities, update the corresponding CSV files located in the `./assets/locations/` directory.

## Acknowledgment

This project was undertaken in collaboration with the [Geospatial Computer Vision Group](https://anupamsobti.github.io/geospatial-computer-vision/) led by [Dr. Anupam Sobti](https://anupamsobti.github.io/). I am grateful for the support and guidance provided throughout the development of this project.
