# -*- coding: utf-8 -*-

import os

from bokeh.plotting import figure, show
from bokeh.palettes import RdYlGn8 as palette
from bokeh.models import (
    HoverTool,
    GeoJSONDataSource,
    LinearColorMapper,
    Title
)
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon

palette.reverse()

DATA_DIR = 'data'


def multipolygons_to_polygons(geodataframe, geometry_column='geometry', min_area=0):
    """
    Turns rows with MultiPolygons into groups of rows with single Polygon each.
    :param geodataframe:
    :param geometry_column: Column containing Polygons and Multipolygons.
    :param min_area: Size of Polygons to be removed
    :return: enlargened geodataframed with each Polygon in its own row
    """
    new_geodataframe = gpd.GeoDataFrame(columns=geodataframe.columns)
    for _, row in geodataframe.iterrows():
        geom = row[geometry_column]
        if geom.type == 'Polygon':
            new_geodataframe = new_geodataframe.append(row)
        elif geom.type == 'MultiPolygon':
            for poly in geom:
                new_row = row.copy()
                new_row[geometry_column] = poly
                if poly.area >= min_area:
                    new_geodataframe = new_geodataframe.append(new_row)
    return new_geodataframe.reset_index()


if __name__ == '__main__':
    os.chdir(DATA_DIR)
    kunnat = gpd.read_file('kuntienAvainluvut_2016.shp')
    kunnat.to_crs(epsg=3067)

    kunnat = multipolygons_to_polygons(kunnat, min_area=2000000)
    kunnat['x'] = kunnat['geometry'].apply(lambda geom: tuple(geom.exterior.coords.xy[0]))
    kunnat['y'] = kunnat['geometry'].apply(lambda geom: tuple(geom.exterior.coords.xy[1]))

    kunnat['poly_area'] = kunnat.geometry.apply(lambda p: p.area)
    # kunnat = kunnat[kunnat['poly_area'] > 2000000]

    kunnat.geometry = kunnat.geometry.apply(lambda poly: poly.simplify(1000))

    kunnat.columns = [w.replace(r'%', '_pct') for w in kunnat.columns]

    kunnat_src = GeoJSONDataSource(geojson=kunnat.to_json())
    color_mapper = LinearColorMapper(palette=palette)
    fig = figure(
        title='Muuttovoitto ja muuttotappio 2016',
        x_axis_location=None,
        y_axis_location=None,
        plot_width=600,
        plot_height=950
    )
    fig.title.text_font_size = "20px"
    fig.grid.grid_line_color = None
    fig.add_layout(Title(text="© Tilastokeskus, Kuntien avainluvut, 2016", align="left"), "below")
    fig.patches(
        xs='x',
        ys='y',
        source=kunnat_src,
        fill_color={
            'field': 'PopChange',
            'transform': color_mapper,
        },
        fill_alpha=0.9,
        line_color='black',
        line_width=0.8
    )

    hover = HoverTool()
    hover.tooltips = [
        ('Kunta', '@NIMI'),
        ('Väkiluku', '@Population'),
        ('Työttömyysaste', '@Tyottom_pct{0.0 a}'),
        ('Muuttovoitto tai -tappio', '@PopChange{0.0 a}'),
    ]
    fig.add_tools(hover)
    show(fig)
