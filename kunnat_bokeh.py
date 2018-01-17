import os

from bokeh.plotting import figure, show
from bokeh.models import HoverTool, GeoJSONDataSource
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon

DATA_DIR = 'data'


def multipolygons_to_polygons(geodataframe):
    """
    Turns rows with MultiPolygons into groups of rows with single Polygon each.
    :param geodataframe:
    :return:
    """
    new_geodataframe = gpd.GeoDataFrame(columns=geodataframe.columns)
    for _, row in geodataframe.iterrows():
        geom = row['geometry']
        if isinstance(geom, Polygon):
            new_geodataframe = new_geodataframe.append(row)
        elif isinstance(geom, MultiPolygon):
            for poly in geom:
                new_row = row.copy()
                new_row['geometry'] = poly
                new_geodataframe = new_geodataframe.append(new_row)
    return new_geodataframe.reset_index()


if __name__ == '__main__':
    os.chdir(DATA_DIR)
    kunnat = gpd.read_file('kuntienAvainluvut_2016.shp')
    kunnat.to_crs(epsg=3067)
    kunnat = multipolygons_to_polygons(kunnat)
    kunnat['x'] = kunnat['geometry'].apply(lambda geom: tuple(geom.exterior.coords.xy[0]))
    kunnat['y'] = kunnat['geometry'].apply(lambda geom: tuple(geom.exterior.coords.xy[1]))
    kunnat.columns = [sanitize_name(w) for w in kunnat.columns]
    kunnat_src = GeoJSONDataSource(geojson=kunnat.to_json())
    fig = figure(title='Kuntien avainluvut')
    fig.patches(xs='x', ys='y', source=kunnat_src)

    hover = HoverTool()
    hover.tooltips = [
        ('Kunta', '@NIMI'),
        ('Väkiluku', '@Population'),
    ]
    fig.add_tools(hover)
    show(fig)
