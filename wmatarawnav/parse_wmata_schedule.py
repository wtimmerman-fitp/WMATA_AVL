# -*- coding: utf-8 -*-
"""
Create by: abibeka, wytimmerman
Created on Tue Apr 28 15:07:59 2020
Purpose: Functions for processing rawnav & wmata_schedule data
"""
import inflection
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import LineString
from shapely.ops import nearest_points
from scipy.spatial import cKDTree
import numpy as np
import folium
from folium import plugins


# Eventually will clean the parse_rawnav.py functions to get these updated column names.
def fix_rawnav_names(data):
    """
    Parameters
    ----------
    data: pd.DataFrame
    data with mixed case and camel case column names.
    Returns
    -------
    data: pd.DataFrame
    data with snake_case format for column names
    """
    if 'Unnamed: 0' in data.columns:
        data = data.drop(columns='Unnamed: 0')
    col_names = data.columns
    data.columns = [inflection.underscore(name) for name in col_names]
    return data


def merge_stops_wmata_schedule_rawnav(wmata_schedule_dat, rawnav_dat):
    '''
    Parameters
    ----------
    wmata_schedule_dat : pd.DataFrame
        wmata schedule data with unique stops per route and info on short/long and direction.
    rawnav_dat : pd.DataFrame
        rawnav data.
    Returns
    -------
    nearest_rawnav_point_to_wmata_schedule_data : gpd.GeoDataFrame
        A geopandas dataframe with nearest rawnav point to each of the GTFS stops on that route.
    '''
    # Convert to geopandas dataframe
    geometry_stops = [Point(xy) for xy in zip(wmata_schedule_dat.stop_lon.astype(float),
                                              wmata_schedule_dat.stop_lat.astype(float))]
    geometry_points = [Point(xy) for xy in zip(rawnav_dat.long.astype(float), rawnav_dat.lat.astype(float))]
    gd_wmata_schedule_dat = gpd.GeoDataFrame(wmata_schedule_dat, geometry=geometry_stops, crs={'init': 'epsg:4326'})
    gd_rawnav_dat = gpd.GeoDataFrame(rawnav_dat, geometry=geometry_points, crs={'init': 'epsg:4326'})
    # Project to 2-D plane
    # https://gis.stackexchange.com/questions/293310/how-to-use-geoseries-distance-to-get-the-right-answer
    gd_wmata_schedule_dat.to_crs(epsg=3310, inplace=True)  # Distance in meters---Default is in degrees!
    gd_rawnav_dat.to_crs(epsg=3310, inplace=True)  # Distance in meters---Default is in degrees!
    wmata_schedule_groups = gd_wmata_schedule_dat.groupby(['route', 'pattern'])  # Group GTFS data
    rawnav_groups = gd_rawnav_dat.groupby(
        ['filename', 'index_trip_start_in_clean_data', 'route', 'pattern'])  # Group rawnav data
    nearest_rawnav_point_to_wmata_schedule_data = pd.DataFrame()
    for name, rawnav_group in rawnav_groups:
        # print(name)
        wmata_schedule_relevant_route_dat = \
            wmata_schedule_groups.get_group(
                (name[2], name[3]))  # Get the relevant group in GTFS corresponding to rawnav.
        nearest_rawnav_point_to_wmata_schedule_data = \
            pd.concat([nearest_rawnav_point_to_wmata_schedule_data,
                       ckdnearest(wmata_schedule_relevant_route_dat, rawnav_group)])
    nearest_rawnav_point_to_wmata_schedule_data.dist = \
        nearest_rawnav_point_to_wmata_schedule_data.dist * 3.28084  # meters to feet
    nearest_rawnav_point_to_wmata_schedule_data.lat = \
        nearest_rawnav_point_to_wmata_schedule_data.lat.astype('float')
    geometry_nearest_rawnav_point = []
    for xy in zip(nearest_rawnav_point_to_wmata_schedule_data.long,
                  nearest_rawnav_point_to_wmata_schedule_data.lat):
        geometry_nearest_rawnav_point.append(Point(xy))
    geometry_stop_on_route = []
    for xy in zip(nearest_rawnav_point_to_wmata_schedule_data.stop_lon,
                  nearest_rawnav_point_to_wmata_schedule_data.stop_lat):
        geometry_stop_on_route.append(Point(xy))
    geometry = [LineString(list(xy)) for xy in zip(geometry_nearest_rawnav_point, geometry_stop_on_route)]
    nearest_rawnav_point_to_wmata_schedule_data = \
        gpd.GeoDataFrame(nearest_rawnav_point_to_wmata_schedule_data, geometry=geometry, crs={'init': 'epsg:4326'})
    nearest_rawnav_point_to_wmata_schedule_data.rename(columns={'dist': 'dist_nearest_point_from_stop'}, inplace=True)
    return nearest_rawnav_point_to_wmata_schedule_data


def ckdnearest(gdA, gdB):
    # TODO: Write Documentation
    '''
    # https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
    Parameters
    ----------
    gdA : TYPE
        DESCRIPTION.
    gdB : TYPE
        DESCRIPTION.

    Returns
    -------
    gdf : TYPE
        DESCRIPTION.
    '''
    gdA.reset_index(inplace=True, drop=True);
    gdB.reset_index(inplace=True, drop=True)
    nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)))
    nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    gdf = pd.concat(
        [gdA.reset_index(drop=True),
         gdB.loc[idx, ['filename', 'index_trip_start_in_clean_data', 'index_loc', 'lat', 'long']].reset_index(
             drop=True),
         pd.Series(dist, name='dist')], axis=1)
    return gdf


def remove_stops_with_dist_over_100ft(nearest_rawnav_point_to_wmata_schedule_data_):
    row_before = nearest_rawnav_point_to_wmata_schedule_data_.shape[0]
    nearest_rawnav_point_to_wmata_schedule_data_ = \
        nearest_rawnav_point_to_wmata_schedule_data_.query('dist_nearest_point_from_stop<100')
    row_after = nearest_rawnav_point_to_wmata_schedule_data_.shape[0]
    print(f'deleted {row_before-row_after} rows from {row_before} with distance to the nearest stop > 100 ft.')
    return  nearest_rawnav_point_to_wmata_schedule_data_

def assert_clean_stop_order_increase_with_odom(nearest_rawnav_point_to_wmata_schedule_data_):
    row_before = nearest_rawnav_point_to_wmata_schedule_data_.shape[0]
    nearest_rawnav_point_to_wmata_schedule_data_.\
        sort_values(['filename','index_trip_start_in_clean_data','stop_sort_order'],inplace=True)
    assert (nearest_rawnav_point_to_wmata_schedule_data_.duplicated(
        ['filename', 'index_trip_start_in_clean_data','stop_sort_order']).sum() == 0)
    while(sum(nearest_rawnav_point_to_wmata_schedule_data_.
                groupby(['filename', 'index_trip_start_in_clean_data']).index_loc.diff().dropna() < 0) != 0):
        nearest_rawnav_point_to_wmata_schedule_data_ = \
            delete_rows_with_incorrect_stop_order(nearest_rawnav_point_to_wmata_schedule_data_)
    row_after = nearest_rawnav_point_to_wmata_schedule_data_.shape[0]
    print(f'deleted {row_before-row_after} from {row_before} stops with incorrect order')
    return nearest_rawnav_point_to_wmata_schedule_data_

def delete_rows_with_incorrect_stop_order(nearest_rawnav_point_to_wmata_schedule_data_):
    '''
    Keep deleting stops where the index location does not increase with stop order
    :param nearest_rawnav_point_to_wmata_schedule_data_:
    :return:
    '''
    nearest_rawnav_point_to_wmata_schedule_data_.loc[:, 'diff_index'] = \
        nearest_rawnav_point_to_wmata_schedule_data_.groupby(['filename', 'index_trip_start_in_clean_data']). \
            index_loc.diff().fillna(0)
    wrong_snapping_dat = nearest_rawnav_point_to_wmata_schedule_data_.query('diff_index<0')
    nearest_rawnav_point_to_wmata_schedule_data_ = nearest_rawnav_point_to_wmata_schedule_data_.query('diff_index>=0')
    return(nearest_rawnav_point_to_wmata_schedule_data_)


def include_wmata_schedule_based_summary(rawnav_q_dat, rawnav_sum_dat, nearest_stop_dat):
    #TODO: Write Documentation
    '''
    Parameters
    ----------
    FinDat_ : TYPE
        DESCRIPTION.
    SumDat_ : TYPE
        DESCRIPTION.
    DatFirstLastStops_ :
    Returns
    -------
    None.

    '''
    #5 Get summary after using GTFS data
    ########################################################################################
    first_last_stop_dat = get_first_last_stop_rawnav(nearest_stop_dat)
    rawnav_q_stop_dat = \
        rawnav_q_dat.merge(first_last_stop_dat,on=['filename','index_trip_start_in_clean_data'],how='right')
    rawnav_q_stop_dat = rawnav_q_stop_dat.query('index_loc>=index_loc_first_stop & index_loc<=index_loc_last_stop')
    rawnav_q_stop_dat = \
        rawnav_q_stop_dat[['filename','index_trip_start_in_clean_data','lat','long','heading','odomt_ft','sec_past_st'
                           ,'first_stop_dist_nearest_point','trip_length','route_text']]
    Map1 = lambda x: max(x)-min(x)
    rawnav_q_stop_sum_dat =\
        rawnav_q_stop_dat.groupby(['filename','index_trip_start_in_clean_data']).\
            agg({'odomt_ft':['min','max',Map1],
                 'sec_past_st':['min','max',Map1],
                 'lat':['first','last'],
                 'long':['first','last'],
                 'first_stop_dist_nearest_point':['first'],
                 'trip_length':['first'],
                 'route_text':['first']})
    rawnav_q_stop_sum_dat.columns = ['start_odom_ft_wmata_schedule','end_odom_ft_wmata_schedule',
                                     'trip_dist_mi_odom_and_wmata_schedule','start_sec_wmata_schedule',
                                     'end_sec_wmata_schedule','trip_dur_sec_wmata_schedule',
                                     'start_lat_wmata_schedule','end_lat_wmata_schedule',
                                     'start_long_wmata_schedule','end_long_wmata_schedule',
                                     'dist_first_stop_wmata_schedule','trip_length_mi_direct_wmata_schedule',
                                     'route_text_wmata_schedule']
    rawnav_q_stop_sum_dat.loc[:,['trip_dist_mi_odom_and_wmata_schedule']] =\
        rawnav_q_stop_sum_dat.loc[:,['trip_dist_mi_odom_and_wmata_schedule']]/5280
    rawnav_q_stop_sum_dat.loc[:,['trip_length_mi_direct_wmata_schedule']] =\
        rawnav_q_stop_sum_dat.loc[:,['trip_length_mi_direct_wmata_schedule']]/5280
    rawnav_q_stop_sum_dat.loc[:,'trip_speed_mph_wmata_schedule'] =\
        round(3600*
              rawnav_q_stop_sum_dat.trip_dist_mi_odom_and_wmata_schedule/
              rawnav_q_stop_sum_dat.trip_dur_sec_wmata_schedule,2)
    rawnav_q_stop_sum_dat.loc[:,['trip_dist_mi_odom_and_wmata_schedule','dist_first_stop_wmata_schedule',
                                 'trip_length_mi_direct_wmata_schedule']] = \
        round(rawnav_q_stop_sum_dat.loc[:,['trip_dist_mi_odom_and_wmata_schedule','dist_first_stop_wmata_schedule',
                                           'trip_length_mi_direct_wmata_schedule']],2)
    rawnav_q_stop_sum_dat = \
        rawnav_q_stop_sum_dat.merge(rawnav_sum_dat,on=['filename','index_trip_start_in_clean_data'],how='left')
    return rawnav_q_stop_sum_dat

def get_first_last_stop_rawnav(nearest_rawnav_stop_dat):
    last_stop_dat = nearest_rawnav_stop_dat.copy()
    last_stop_dat.loc[:, "tempCol"] = \
        last_stop_dat.groupby(['filename', 'index_trip_start_in_clean_data']).stop_sort_order.transform(max)
    last_stop_dat = last_stop_dat.query('stop_sort_order==tempCol').reset_index(drop=True).drop(columns='tempCol')
    last_stop_dat = last_stop_dat[['filename', 'index_trip_start_in_clean_data','index_loc',
                                   'dist_nearest_point_from_stop']]
    last_stop_dat.rename(columns={'index_loc': 'index_loc_last_stop',
                                  'dist_nearest_point_from_stop': 'last_stop_dist_nearest_point'},inplace=True)
    first_stop_dat = \
        nearest_rawnav_stop_dat.groupby(['filename', 'index_trip_start_in_clean_data']).stop_sort_order.transform(min)
    first_stop_dat = nearest_rawnav_stop_dat.copy()
    first_stop_dat.loc[:, "tempCol"] = \
        first_stop_dat.groupby(['filename', 'index_trip_start_in_clean_data']).stop_sort_order.transform(min)
    first_stop_dat = first_stop_dat.query('stop_sort_order==tempCol').reset_index(drop=True).drop(columns='tempCol')
    first_stop_dat.rename(columns={'index_loc': 'index_loc_first_stop',
                                  'dist_nearest_point_from_stop': 'first_stop_dist_nearest_point'},inplace=True)
    first_stop_dat.sort_values(['filename', 'index_trip_start_in_clean_data'], inplace=True)
    first_last_stop_dat = first_stop_dat.merge(last_stop_dat,on=['filename','index_trip_start_in_clean_data'],how='left')
    first_last_stop_dat.drop(columns=['geometry','lat','long','pattern','route'],inplace=True)
    return first_last_stop_dat

def plot_rawnav_trajectory_with_wmata_schedule_stops(rawnav_dat, wmata_schedule_stop_dat):
    ## Link to Esri World Imagery service plus attribution
    #https://www.esri.com/arcgis-blog/products/constituent-engagement/constituent-engagement/esri-world-imagery-in-openstreetmap/
    esri_imagery = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    esri_attribution = "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
    this_map = folium.Map( tiles='cartodbdark_matter', zoom_start=16,max_zoom=25,control_scale=True)
    folium.TileLayer(name="EsriImagery",tiles=esri_imagery, attr=esri_attribution,
                     zoom_start=16,max_zoom=25,control_scale=True).add_to(this_map)
    folium.TileLayer('cartodbpositron',zoom_start=16,max_zoom=20,control_scale=True).add_to(this_map)
    folium.TileLayer('openstreetmap',zoom_start=16,max_zoom=20,control_scale=True).add_to(this_map)
    fg = folium.FeatureGroup(name="Rawnav Trajectory")
    this_map.add_child(fg)
    line_grp = folium.FeatureGroup(name="WMATA Schedule Stops and Nearest Rawnav Point")
    this_map.add_child(line_grp)
    plot_marker_clusters(this_map, rawnav_dat,"lat","long",fg)
    plot_lines_clusters(this_map, wmata_schedule_stop_dat, line_grp)
    lat_longs = [[x,y] for x,y in zip(rawnav_dat.lat,rawnav_dat.long)]
    this_map.fit_bounds(lat_longs)
    folium.LayerControl(collapsed=True).add_to(this_map)
    return(this_map)


def plot_marker_clusters(this_map, dat, lat, long, feature_grp):
    #TODO: Write Documentation
    popup_field_list = list(dat.columns)
    for i,row in dat.iterrows():
        label = '<br>'.join([field + ': ' + str(row[field]) for field in popup_field_list])
        #https://deparkes.co.uk/2019/02/27/folium-lines-and-markers/
        folium.CircleMarker(
                location=[row[lat], row[long]], radius= 2,
                popup=folium.Popup(html = label,parse_html=False,max_width='200')).add_to(feature_grp)


def plot_lines_clusters(this_map, dat, feature_grp):
    #TODO: Write Documentation
    '''
    Parameters
    ----------
    this_map : TYPE
        DESCRIPTION.
    Dat : TYPE
        DESCRIPTION.
    FeatureGrp : TYPE
        DESCRIPTION.
    Returns
    -------
    None.
    '''
    popup_field_list = list(dat.columns)
    popup_field_list.remove('geometry')
    for i,row in dat.iterrows():
        temp_grp = \
            plugins.FeatureGroupSubGroup(feature_grp,f"{row.stop_sort_order}-{row.geo_description}-{row.pattern}")
        this_map.add_child(temp_grp)
        label = '<br>'.join([field + ': ' + str(row[field]) for field in popup_field_list])
        #https://deparkes.co.uk/2019/02/27/folium-lines-and-markers/
        line_points = [(tuples[1],tuples[0]) for tuples in list(row.geometry.coords)]
        folium.PolyLine(line_points, color="red", weight=4, opacity=1\
        ,popup=folium.Popup(html = label,parse_html=False,max_width='300')).add_to(temp_grp)