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
    filtered = [i for i in result.toJSON()["elements"] if "tags" not in i]
    return filtered
