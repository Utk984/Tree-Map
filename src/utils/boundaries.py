from OSMPythonTools.overpass import Overpass

overpass = Overpass()


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
