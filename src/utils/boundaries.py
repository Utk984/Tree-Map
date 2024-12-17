import geopandas as gpd
from OSMPythonTools.overpass import Overpass

overpass = Overpass()


def get_sector_boundary(sector_name):
    gdf = gpd.read_file("Chandigarh_Sectors.geojson")
    sector_boundary = gdf[gdf["Sector_nam"] == sector_name]
    if not sector_boundary.empty:
        sector_geometry = sector_boundary.geometry.iloc[0]
        if sector_geometry.geom_type == "Polygon":
            boundary_coords = list(sector_geometry.exterior.coords)
        elif sector_geometry.geom_type == "MultiPolygon":
            boundary_coords = []
            for polygon in sector_geometry:
                boundary_coords.extend(list(polygon.exterior.coords))

        boundary_coords = [(lon, lat) for lat, lon in boundary_coords]
        return boundary_coords
    else:
        return f"Sector {sector_name} not found."


def get_osm_data(location):
    query = f"""
    area[name="{location}"]->.searchArea;
    (
      relation["type"="boundary"]["name"="{location}"];
    );
    (._;>;);
    out body;
    """

    result = overpass.query(query)
    result = [i for i in result.toJSON()["elements"] if "tags" not in i]
    boundary_coords = [
        (element["lat"], element["lon"])
        for element in result
        if "lat" in element and "lon" in element
    ]
    if len(boundary_coords) < 3:
        return None

    return boundary_coords
