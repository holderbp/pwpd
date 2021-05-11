# Use the pwpd.yml conda environment
import sys
import datetime
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import rasterio
import rasterio.mask
import pyproj
import folium  # for making html maps with leaflet.js 

############################################################
#         Population image parameters and methods          #
############################################################
popimage_type = None
#
# === GHS-POP images downloaded from here:
#
#      https://ghsl.jrc.ec.europa.eu/ghs_pop2019.php
#
#  Read with rasterio
#
#      import rasterio
#      src = rasterio.open("../data/ghs/.../GHS_POP_E2015_...tif")
#
#  Coordinate system is World Mollweide (equal areas):
#
#        src.crs = CRS.from_wkt('PROJCS["World_Mollweide",
#                  GEOGCS["WGS 84",DATUM["WGS_1984",
#                  SPHEROID["WGS 84",6378137,298.257223563,
#                  AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],
#                  PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]],
#                  PROJECTION["Mollweide"],PARAMETER["central_meridian",0],
#                  PARAMETER["false_easting",0],PARAMETER["false_northing",0],
#                  UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],
#                  AXIS["Northing",NORTH]]')
#        src.read().shape = (1, 18000, 36082)
#        src.nodatavals = (-200.0,)
#        src.indexes = (1,)
#        src.dtypes = ('float64',)
#        src.transform = Affine(1000.0, 0.0, -18041000.0,
#                               0.0, -1000.0, 9000000.0)
#
# === GHS-POP parameters
#
GHS_dir = "../data/ghs/"
GHS_file_string1 = "GHS_POP"
GHS_file_string2 = "GLOBE_R2019A_54009"
GHS_file_string3 = "V1_0" 
GHS_filepath = None
GHS_resolution_string = None
GHS_epoch_string = None
GHS_Acell_in_kmsqd = None
GHS_coordinates = 'esri:54009'   # Mollweide
#
# === GPW (Gridded Population of the World) images downloaded from here:
#
#    https://sedac.ciesin.columbia.edu/data/collection/gpw-v4
#
# Open with rasterio as with GHS-POP
#
# Coordinate system is WSG84 Geographic (Lat/Lon).  E.g., for 30 as resolution tif:
#
#        src.crs = CRS.from_epsg(4326)
#        src.read().shape = (1, 21600, 43200)
#        src.nodatavals = (-3.4028230607370965e+38,)
#        src.indexes = (1,)
#        src.dtypes = ('float32',)
#        src.transform = Affine(0.00833333333333333, 0.0, -180.0,
#                               0.0, -0.00833333333333333, 89.99999999999991)
#
# === GPW parameters  
#
GPW_resolution_string = None
GPW_epoch_string = None
GPW_dir = "../data/gpw/"
GPW_file_string1 = "gpw_v4"
#GPW_file_string2 = "rev11"   # not UN-adjusted pops
GPW_file_string2 = "adjusted_to_2015_unwpp_country_totals_rev11"
GPW_popcount_filepath = None
GPW_popdensity_filepath = None
GPW_coordinates = 'epsg:4326'   # WSG84 Lat/Lon
GPW_area_warning_not_given_yet = True # currently uses Apixel = (1km)^2 for 30as

def set_popimage_pars(popimtype, epoch, lengthstring):
    """Set parameters for the population raster image"""
    global popimage_type
    global GHS_resolution_string, GHS_epoch_string, GHS_Acell_in_kmsqd
    global GHS_filepath
    global GPW_resolution_string, GPW_epoch_string
    global GPW_popcount_filepath, GPW_popdensity_filepath
    # Set population image type  ('GHS' or 'GPW')
    popimage_type = popimtype
    # and it's associated parameters
    if (popimtype == 'GHS'):
        # Set epoch string
        GHS_epoch_string = 'E' + epoch
        # Set lengthscale string and value
        if (lengthstring == '250m'):
            GHS_resolution_string = '250'
            GHS_resolution_in_km = 0.250
        elif (lengthstring == '1km'):
            GHS_resolution_string = '1K'
            GHS_resolution_in_km = 1.0
        else:
            print("\n***Error: GHS lengthscale", lengthstring, "not recognized.")
            print("          Only 250m and 1km resolutions are set up in pwpd.py")
            exit(0)
        # Set GHS pixel area: The 250m and 1km resolution
        # images use equal-area, Mollweide coords)
        GHS_Acell_in_kmsqd = GHS_resolution_in_km**2
        # set GHS image filepath
        #   e.g., "GHS_POP_E2015_GLOBE_R2019A_54009_1K_V1_0"
        filestring = GHS_file_string1 \
            + "_" + GHS_epoch_string + "_" \
            + GHS_file_string2 \
            + "_" + GHS_resolution_string + "_" \
            + GHS_file_string3
        GHS_filepath =  GHS_dir + filestring + "/" + filestring + ".tif"
    elif (popimtype == 'GPW'):
        # set epoch
        GPW_epoch_string = epoch
        # set lengthscale string
        if (lengthstring == '30as'):
            GPW_resolution_string = '30_sec'
        elif (lengthstring == '2.5am'):
            GPW_resolution_string = '2pt5_min'
        elif (lengthstring == '15am'):
            GPW_resolution_string = '15_min'
        elif (lengthstring == '30am'):
            GPW_resolution_string = '30_min'
        elif (lengthstring == '1deg'):
            GPW_resolution_string = '1_deg'
        else:
            print("\n***Error: The resolution", lengthstring, "does not exist for GPW.")
            exit(0)
        # set GPW image filepath  
        GPW_popcount_filepath =  GPW_dir + GPW_file_string1 \
            + "_population_count_" + GPW_file_string2 \
            + "_" + GPW_epoch_string \
            + "_" + GPW_resolution_string + ".tif"
        GPW_popdensity_filepath =  GPW_dir + GPW_file_string1 \
            + "_population_density_" + GPW_file_string2 \
            + "_" + GPW_epoch_string \
            + "_" + GPW_resolution_string + ".tif"
    else:
        print("\n***Error: Population image", popimtype, "not recognized.")
        exit(0)

def get_windowed_subimage(window_df, filepath):
    # get polygon shape(s) from the geopandas dataframe
    windowshapes = window_df["geometry"]
    # mask GHS-POP image with entire set of shapes
    try:
        with rasterio.open(filepath) as src:
            img, img_transform = \
                rasterio.mask.mask(src, windowshapes, crop=True)
            img_profile = src.profile
            img_meta = src.meta
            img_meta.update( { "driver": "GTiff",
                               "height": img.shape[1],
                               "width": img.shape[2],
                               "transform": img_transform} )
    except rasterio.errors.RasterioIOError:
        print("\n***Error: File with path:")
        print("\n", filepath, "\n")
        print("          not found. Check the popimage type, epoch, and resolution.")
        exit(0)
    # return only the first band (rasterio returns 3D array)
    return img[0], img_transform


############################################################
#  Political region shapefiles and areas: data and methods #
############################################################

#
#=== Areas for countries of the world.
#
#      Used this database:
#
#         https://data.worldbank.org/indicator/AG.SRF.TOTL.K2
#
#      with relevant columns:
#
#          ["Country Name", "Country Code", ... "2015"]
#
#      where "country code" is threelett code and "2015 is the area of country in 2015.
#      below I translate these to the same labels as the country codes file:
#      ['name', 'threelett', 'area_kmsqd_2015']
#
areas_filepath = "../data/area/API_AG.SRF.TOTL.K2_DS2_en_csv_v2_1346843.csv"
areas_collist = ["Country Name", "Country Code", "2015"]
areas_newcolnames = ["name", "threelett", "area_kmsqd_2015"]
#
#      There are lots of places listed in the country codes file that do not
#      have an area in the world bank database (most of these are small islands), and
#      they are excluded using the list below. (Taiwan doesn't appear in the world
#      bank list either, so I add it in by hand).
areas_places_w_no_area = ['AIA', 'ALD', 'ATA', 'ATC', 'ATF', 'BLM', 'COK',
                          'CYN', 'FLK', 'GGY', 'HMD', 'IOA', 'IOT', 'JEY',
                          'KAS', 'KOS', 'MSR', 'NFK', 'NIU', 'PCN', 'PSX',
                          'SAH', 'SDS', 'SGS', 'SHN', 'SOL', 'SPM', 'VAT',
                          'WLF']
areas_taiwan = {'name': 'Taiwan', 'threelett': 'TWN', 'area_kmsqd_2015': 36193}

#=== Shapefiles for the countries of the world.
#
#   Used file from here:
#
#     https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/
#
#   Load with geopandas
#
#     import geopandas as gpd
#     infile = ../data/shapefiles/world/ne_50m_admin_0_countries/ne_50m_admin_0_countries.sh
#     df = gpd.read_file(infile)
#
#   Columns in dataframe:
#        df.columns =
#    Index(['featurecla', 'scalerank', 'LABELRANK', 'SOVEREIGNT', 'SOV_A3',
#    'ADM0_DIF', 'LEVEL', 'TYPE', 'ADMIN', 'ADM0_A3', 'GEOU_DIF', 'GEOUNIT',
#    'GU_A3', 'SU_DIF', 'SUBUNIT', 'SU_A3', 'BRK_DIFF', 'NAME', 'NAME_LONG',
#    'BRK_A3', 'BRK_NAME', 'BRK_GROUP', 'ABBREV', 'POSTAL', 'FORMAL_EN',
#    'FORMAL_FR', 'NAME_CIAWF', 'NOTE_ADM0', 'NOTE_BRK', 'NAME_SORT',
#    'NAME_ALT', 'MAPCOLOR7', 'MAPCOLOR8', 'MAPCOLOR9', 'MAPCOLOR13',
#    'POP_EST', 'POP_RANK', 'GDP_MD_EST', 'POP_YEAR', 'LASTCENSUS',
#    'GDP_YEAR', 'ECONOMY', 'INCOME_GRP', 'WIKIPEDIA', 'FIPS_10_', 'ISO_A2',
#    'ISO_A3', 'ISO_A3_EH', 'ISO_N3', 'UN_A3', 'WB_A2', 'WB_A3', 'WOE_ID',
#    'WOE_ID_EH', 'WOE_NOTE', 'ADM0_A3_IS', 'ADM0_A3_US', 'ADM0_A3_UN',
#    'ADM0_A3_WB', 'CONTINENT', 'REGION_UN', 'SUBREGION', 'REGION_WB',
#    'NAME_LEN', 'LONG_LEN', 'ABBREV_LEN', 'TINY', 'HOMEPART', 'MIN_ZOOM',
#    'MIN_LABEL', 'MAX_LABEL', 'NE_ID', 'WIKIDATAID', 'NAME_AR', 'NAME_BN',
#    'NAME_DE', 'NAME_EN', 'NAME_ES', 'NAME_FR', 'NAME_EL', 'NAME_HI',
#    'NAME_HU', 'NAME_ID', 'NAME_IT', 'NAME_JA', 'NAME_KO', 'NAME_NL',
#    'NAME_PL', 'NAME_PT', 'NAME_RU', 'NAME_SV', 'NAME_TR', 'NAME_VI',
#    'NAME_ZH', 'geometry'],
#
#  The three-letter country code is 'ADM0_A3' and name is 'SOVEREIGNT'
#
#  Coordinate system is geographic (lat/lon):
#
#       df.crs =
#             <Geographic 2D CRS: EPSG:4326>
#             Name: WGS 84
#             Axis Info [ellipsoidal]:
#             - Lat[north]: Geodetic latitude (degree)
#             - Lon[east]: Geodetic longitude (degree)
#             Area of Use:
#             - name: World
#             - bounds: (-180.0, -90.0, 180.0, 90.0)
#             Datum: World Geodetic System 1984
#             - Ellipsoid: WGS 84
#             - Prime Meridian: Greenwich
#
world_shape_dir = "../data/shapefiles/world/ne_50m_admin_0_countries/"
world_shape_filepath = world_shape_dir + "ne_50m_admin_0_countries.shp"
# these countries have no entry
places_w_no_shapefile = ['PSE', 'GIB', 'SSD', 'TUV']

def load_world_shapefiles():
    #=== read in dataframe of shapefiles for all countries
    #    (keep only relevant columns and rename like in "codes")
    allcountries_df = gpd.read_file(world_shape_filepath)
    allcountries_df = allcountries_df[['SOVEREIGNT', 'ADM0_A3', 'geometry']]
    allcountries_df.columns = ['name', 'threelett', 'geometry']
    return allcountries_df

def create_countries_dataframe_with_areas(allcountries_df):
    # load the areas dataframe, keep only three columns and rename, add Taiwan
    areas_df = pd.read_csv(areas_filepath)
    areas_df = areas_df[areas_collist]
    areas_df.columns = areas_newcolnames
    areas_df = areas_df.append(areas_taiwan, ignore_index=True)
    # make new dataframe for putting the pwpd etc (don't keep 'geometry')
    pwpd_countries = allcountries_df[['name', 'threelett']].copy()
    # put areas into this dataframe
    pwpd_countries['area'] = 0.0
    for index, row in pwpd_countries.iterrows():
        code = row['threelett']
        if (code not in areas_places_w_no_area):
            try:
                area = areas_df[areas_df['threelett'] == code]['area_kmsqd_2015'].to_numpy()[0]
                pwpd_countries.at[index, 'area'] = area
            except IndexError:
                print("\n***Error: Couldn't find area for", code)
    # make columns for other values
    pwpd_countries['pop'] = 0.0
    pwpd_countries['pwpd'] = 0.0
    pwpd_countries['pwlogpd'] = 0.0
    pwpd_countries['popdens'] = 0.0
    pwpd_countries['gamma'] = 0.0
    return pwpd_countries

def get_country_by_countrycode(allcountries_df, countrycode):
    country = allcountries_df[allcountries_df['threelett'] == countrycode]
    try:
        countryname = country['name'].to_list()[0]
    except IndexError:
        print("\n***Error: Country with three-letter country code",
              countrycode, "not found.")
        exit(0)
    return (country, countryname)

def transform_shapefile(shapefile):
    if (popimage_type == 'GHS'):
        # transform to Mollweide
        return shapefile.to_crs(crs=GHS_coordinates)
    elif (popimage_type == 'GPW'):
        # transform to WGS84
        return shapefile.to_crs(crs=GPW_coordinates)        
    else:
        print("\n***Error: Population image coordinates unknown/undefined.")
        exit(0)

#=== Shapefiles for the Canadian Health Regions
#
#   Downloaded from "Statistics Canada --- Health region boundary files"
#   (ESRI shapefile, ArcGIS Digital Boundary Files)
#
#       https://www150.statcan.gc.ca/n1/pub/82-402-x/2018001/hrbf-flrs-eng.htm
#
#   df.columns = ['HR_UID', 'ENGNAME', 'FRENAME', 'SHAPE_AREA', 'SHAPE_LEN', 'geometry']
#
#   df.crs =
#           <Projected CRS: PROJCS["PCS_Lambert_Conformal_Conic",GEOGCS["NAD83 ...>
#           Name: PCS_Lambert_Conformal_Conic
#           Axis Info [cartesian]:
#           - [east]: Easting (metre)
#           - [north]: Northing (metre)
#           Area of Use:
#           - undefined
#           Coordinate Operation:
#           - name: unnamed
#           - method: Lambert Conic Conformal (2SP)
#           Datum: North American Datum 1983
#           - Ellipsoid: GRS 1980
#           - Prime Meridian: Greenwich
#
#
CanadaHR_shape_dir = "../data/shapefiles/CanadaHR/"
#=== Shape files:
#
# The Canadian health regions used for reporting COVID are slightly different
# than the actual health regions.  This file can use the actual health regions
# and merge them to create the larger COVID-reporting health regions, or it can
# just use the COVID health regions shapefile, found here:
#
#   Statistics Canada
#
#   https://www150.statcan.gc.ca/n1/pub/82-402-x/2018001/hrbf-flrs-eng.htm
#
#   COVID-ArcGIS
#
#   https://resources-covid19canada.hub.arcgis.com/datasets/regionalhealthboundaries-1?geometry=12.702%2C38.665%2C153.678%2C83.576
#
CanadaHR_shape_filepath_actual = \
    CanadaHR_shape_dir + "StatisticsCanada_2018a/" +  "HR_000a18a_e.shp"
CanadaHR_shape_filepath_covid = \
    CanadaHR_shape_dir + "COVID-ArcGIS_regionalhealthboundaries/" + "RegionalHealthBoundaries.shp"
# see below for contents of this file
CanadaHR_province_filepath = CanadaHR_shape_dir + "canada-provinces_w-hr-prefix.csv"


def load_CanadaHR_shapefiles(hr_type):
    #=== read in Canada Health Regions dataframe
    #    (keep only relevant columns and rename like in "codes")
    if (hr_type == "statscanada"):
        df = gpd.read_file(CanadaHR_shape_filepath_actual)
        df = df[['HR_UID', 'ENGNAME', 'SHAPE_AREA', 'geometry']]
        # StatsCanada's SHAPE_AREA already seems to be land area in m^2
    elif (hr_type == "covid19"):
        df = gpd.read_file(CanadaHR_shape_filepath_covid)        
        # convert area to m^2 ... see Fabio G's answer (21Jan2021):
        #
        #     https://gis.stackexchange.com/questions/218450
        #  
        test = df.copy()
        test = test.to_crs({'proj': 'cea'})
        df['area'] = test['geometry'].area
        df = df[['HR_UID', 'ENGNAME', 'area', 'geometry']]
    df.columns = ['hr_uid', 'region', 'area', 'geometry']
    #=== Ensure the hr_uid is an integer
    df['hr_uid'] = df['hr_uid'].astype(int)
    #=== Remove accents from names
    df['region'] = \
        df['region'].str.normalize('NFKD')\
                        .str.encode('ascii', errors='ignore').str.decode('utf-8')
    #=== Add the province name and abbreviation for each region
    #    using the file of Canadian provinces with abb and hr_uid prefix
    #
    #         cols = [abb, name, hr_prefix]
    #
    df['province'] = ""
    df['province_abb'] = ""
    prov_df = pd.read_csv(CanadaHR_province_filepath)
    prov_df['hr_prefix'] = prov_df['hr_prefix'].astype(int)
    for index,row in df.iterrows():
        hr_prefix = row.hr_uid // 100
        if (hr_prefix == 5):
            # If using the BC shortened numbers
            hr_prefix = 59
        df.at[index, 'province'] = \
            prov_df[prov_df.hr_prefix == hr_prefix].name.to_list()[0]
        df.at[index, 'province_abb'] = \
            prov_df[prov_df.hr_prefix == hr_prefix].abb.to_list()[0]
    return df

def create_canada_hr_dataframe(df):
    # copy over all but the geometry column
    pwpd_df = df.copy()[['hr_uid', 'region', 'area', 'province',
                         'province_abb']]
    # make columns for other values
    pwpd_df['pop'] = 0.0
    pwpd_df['pwpd'] = 0.0
    pwpd_df['pwlogpd'] = 0.0
    pwpd_df['popdens'] = 0.0
    pwpd_df['gamma'] = 0.0
    return pwpd_df

def get_CanadaHR_by_hr_uid(shapes_df, hr_uid):
    the_hregion = (shapes_df['hr_uid'] == hr_uid)
    Nselected = len(shapes_df[the_hregion])
    if (Nselected != 1):
        print(f"\n***Error: For the requested Health Region ({hr_uid:d})")
        print(f"          {Nselected:d} regions were found.")
        exit(0)
    return shapes_df[the_hregion]

def create_Canada_province_regions(df):
    # don't bother with the single-region provinces
    df = df[~df.province_abb.isin(['PE', 'YT', 'NU', 'NT'])]
    # otherwise create a single-row dissolve for each province
    prov_df = df.dissolve(by='province_abb', as_index=False)
    # fix the names, areas and populations for these merged shapes
    for index, row in prov_df.iterrows():
        prov_abb = row.province_abb
        hr_uid = (row.hr_uid // 100) * 100
        area = df[df.province_abb == prov_abb]['area'].sum()
        prov_df.at[index, 'hr_uid'] = hr_uid
        prov_df.at[index, 'area'] = area
        prov_df.at[index, 'region'] = 'Entire Province'
    return prov_df

def reassign_hr_uid(df, old_hr_uid, new_hr_uid):
    newdf = df.copy()
    for index, row in df.iterrows():
        if (row.hr_uid == old_hr_uid):
            newdf.at[index, 'hr_uid'] = new_hr_uid
    return newdf

def rename_hr(df, hr_uid, new_name):
    newdf = df.copy()
    for index, row in df.iterrows():
        if (row.hr_uid == hr_uid):
            newdf.at[index, 'region'] = new_name
    return newdf

def create_CanadaHR_composite_regions(df, hr_uid_list, new_hr_uid, new_hr_name):
    # get dataframe with just the HRs to combine
    df = df[df.hr_uid.isin(hr_uid_list)].copy()
    # all in same province, so this should merge all
    new_df = df.dissolve(by='province_abb', as_index=False)
    # fix the names, areas and populations for these merged shapes
    area = df['area'].sum()
    for index, row in new_df.iterrows():
        new_df.at[index, 'hr_uid'] = new_hr_uid
        new_df.at[index, 'area'] = area
        new_df.at[index, 'region'] = new_hr_name
    return new_df

#=== Shapefiles for the US Counties
#
#   Used file from the US Census:
#
#       https://www2.census.gov/geo/tiger/TIGER2019/COUNTY
#
#   columns = ['STATEFP', 'COUNTYFP', 'COUNTYNS', 'GEOID', 'NAME',
#              'NAMELSAD', 'LSAD', 'CLASSFP', 'MTFCC', 'CSAFP',
#              'CBSAFP', 'METDIVFP', 'FUNCSTAT', 'ALAND',
#              'AWATER', 'INTPTLAT', 'INTPTLON', 'geometry']
#
#   where 'NAME' is the county name (e.g., Saratoga), and
#   'NAMELSAD' is the full county (e.g., Saratoga County).
#
#  Coordinate system is geographic 2D (lat/lon):
#
#       df.crs =
#             <Geographic 2D CRS: EPSG:4269>
#             Name: NAD83
#             Axis Info [ellipsoidal]:
#             - Lat[north]: Geodetic latitude (degree)
#             - Lon[east]: Geodetic longitude (degree)
#             Area of Use:
#             - name: North America - NAD83
#             - bounds: (167.65, 14.92, -47.74, 86.46)
#             Datum: North American Datum 1983
#             - Ellipsoid: GRS 1980
#             - Prime Meridian: Greenwich
#
UScounty_shape_dir = "../data/shapefiles/UScounties/"
UScounty_shape_filepath = UScounty_shape_dir + "tl_2019_us_county/tl_2019_us_county.shp"
#
#=== File of US State FIPS codes to get names and abbreviations
#    (these are not given in the shapefiles file)
#
#       columns = ['name','abb','fips']
#  
#    Adapted from:
#
#       https://www2.census.gov/programs-surveys/popest/
#               geographies/2017/all-geocodes-v2017.xlsx
#
#    retaining only states ("Summary Level" = 040), and adding a
#    few extra locations to match the county shapefiles file:
#
#       [American Samoa (AS), Guam (GU), North. Mar. Isl (MP),
#        Puerto Rico (PR), Virgin Islands (VI)]
#
#  
#
USstate_fips_filepath = UScounty_shape_dir + "US-state_fips-codes.csv"

def load_UScounty_shapefiles():
    #=== read in UScounties dataframe
    #    (keep only relevant columns and rename like in "codes")
    allcounties_df = gpd.read_file(UScounty_shape_filepath)
    allcounties_df = allcounties_df[['STATEFP', 'COUNTYFP', 'NAME',
                                   'NAMELSAD', 'ALAND', 'geometry']]
    allcounties_df.columns = ['fips_state', 'fips_county', 'county',
                             'countylong', 'landarea', 'geometry']
    #=== Make FIPS codes integer-valued
    allcounties_df['fips_state'] = allcounties_df['fips_state'].astype(int)
    allcounties_df['fips_county'] = allcounties_df['fips_county'].astype(int)
    #=== Add the state name and abbreviation for each county
    #    using the file of US state FIPS codes
    allcounties_df['state'] = ""
    allcounties_df['stateabb'] = ""
    statefips_df = pd.read_csv(USstate_fips_filepath)
    statefips_df['fips'] = statefips_df['fips'].astype(int)
    for index,row in allcounties_df.iterrows():
        fips = row.fips_state
        thestate = (statefips_df['fips'] == fips)
        allcounties_df.at[index,'state'] = \
            statefips_df[thestate]['name'].to_list()[0]
        allcounties_df.at[index,'stateabb'] = \
            statefips_df[thestate]['abb'].to_list()[0]
    return allcounties_df

def create_uscounties_dataframe(allcounties_df):
    # copy over all but the geometry column
    pwpd_counties = allcounties_df.copy()[['fips_state', 'fips_county', 'county',
                                           'countylong', 'state', 'stateabb', 'landarea']]
    # make columns for other values
    pwpd_counties['pop'] = 0.0
    pwpd_counties['pwpd'] = 0.0
    pwpd_counties['pwlogpd'] = 0.0
    pwpd_counties['popdens'] = 0.0
    pwpd_counties['gamma'] = 0.0
    return pwpd_counties

def get_UScounty_by_fips(allcounties_df, fips_state, fips_county):
    thecounty = ( (allcounties_df['fips_state'] == fips_state)
                  & (allcounties_df['fips_county'] == fips_county) )
    Nselected = len(allcounties_df[thecounty])
    if (Nselected != 1):
        print(f"\n***Error: For the requested FIPS = ({fips_state:d},{fips_county:d})")
        print(f"          {Nselected:d} counties were found.")
        exit(0)
    county = allcounties_df[thecounty]
    state = county['state'].to_list()[0]
    stateabb = county['stateabb'].to_list()[0]
    countylong = county['countylong'].to_list()[0]
    return (county, state, stateabb, countylong)

def get_UScounty_by_name(allcounties_df, stateabb, name_county):
    # Check county name against both short and long to handle, e.g.,
    # Virginia's "Richmond city" and "Richmond County"
    thecounty = ( (allcounties_df['stateabb'].str.lower() == stateabb)
                  & ( (allcounties_df['county'].str.lower() == name_county)
                      | (allcounties_df['countylong'].str.lower() == name_county) ) )
    Nselected = len(allcounties_df[thecounty])
    if (Nselected != 1):
        print(f"\n***Error: For {name_county:s}, {stateabb.upper():s}")
        print(f"          {Nselected:d} counties were found.")
        exit(0)
    county = allcounties_df[thecounty]
    state = county['state'].to_list()[0]
    countylong = county['countylong'].to_list()[0]
    fips_state = county['fips_state'].to_list()[0]
    fips_county = county['fips_county'].to_list()[0]

    return (county, fips_state, fips_county, state, countylong)


############################################################
#        Population-weighted Density Calculation           #
############################################################

def get_pop_pwpd_pwlogpd(window_df):
    # get windowed subimage(s) of population/popdensity rasters
    if (popimage_type == 'GHS'):
        popimg, popimg_transform = \
            get_windowed_subimage(window_df, GHS_filepath)
        totalpop, pwd, pwlogpd = \
            get_pwpd_from_count(popimg)
    elif (popimage_type == 'GPW'):
        popimg, popimg_transform = \
            get_windowed_subimage(window_df, GPW_popcount_filepath)
        pdimg, pdimg_transform = \
            get_windowed_subimage(window_df, GPW_popdensity_filepath)
        totalpop, pwd, pwlogpd = get_pwpd_from_count_and_density(popimg, pdimg)
    else:
        print("\n***Error: Population image type unknown/unset")
        exit(0)
    return (totalpop, pwd, pwlogpd, np.array(popimg).shape)

def get_gamma(pop, area, pwpd, popimage_type, popimage_resolution_string):
    """Calculate the so-called population sparsity"""
    global GPW_area_warning_not_given_yet
    # Get pwpd pixel area in km^2
    if ((popimage_type == 'GHS') & (popimage_resolution_string == '1km')):
        areascale = 1.0**2
    elif ((popimage_type == 'GHS') & (popimage_resolution_string == '250m')):
        areascale = 0.25**2
    elif (popimage_type == 'GPW'):
        if (popimage_resolution_string == '30as'):
            # FIXME: this should really be set based on 30as**2 at avg latitude
            lengthscale = 1.0
            areascale = lengthscale**2
            if GPW_area_warning_not_given_yet:
                print(f"***Warning: Setting GPW pixel area to {lengthscale:.1f}km x {lengthscale:.1f}km,")
                print(f"            which is approximately correct for the resolution {popimage_resolution_string:s}")
                print(f"            at the equator but is generally incorrect because pixels are not")
                print(f"            equal area in the Geographic coordinate system.")
                GPW_area_warning_not_given_yet = False
        else:
            print("***Error: No areascale available for GPW pixels at >30as resolution.")
            print("          Set \"do_gamma=False\" to get pwpd without gamma calculation.")
            exit(0)
    return ( ( np.log(pwpd) - np.log(pop/area) ) \
             / (np.log(area) - np.log(areascale)) )

def get_pwpd_from_count(img, nparr=False):
    if (nparr == True):
        arr=img
    else:
        arr = np.array(img)
        # set (negative) no data values to zero
        arr[arr < 0.0] = 0.0
    # First flatten the array and remove zero-valued elements
    farr = arr.flatten()
    selected = (farr > 0)
    farr = farr[selected]
    # total population is sum of population in each pixel
    totalpop = np.sum(farr)
    if (totalpop > 0):
        if (popimage_type == 'GHS'):
            # calculate population-weighted population density
            pwd = np.sum(np.multiply(farr / GHS_Acell_in_kmsqd, farr)) / totalpop
            # calculate the pop-weighted log(popdensity)
            pwlogpd = \
                np.sum( np.multiply( np.log(farr/GHS_Acell_in_kmsqd), farr)) \
                / totalpop 
        elif (popimage_type == 'GPW'):
            print("\n***Error: GPW not yet set up to measure areas...")
            exit(0)
    else:
        pwd = 0.0
        pwlogpd = 0.0
    return (totalpop, pwd, pwlogpd)

def get_pwpd_from_count_and_density(pcimg, pdimg):
    if (popimage_type == 'GHS'):
        print("\n***Error: GHS has no population density image...")
        exit(0)
    pcarr = np.array(pcimg)
    pdarr = np.array(pdimg)
    # Set (negative) no data values to zero
    pcarr[pcarr < 0.0] = 0.0
    # Flatten the arrays and remove zero-pop elements
    fpcarr = pcarr.flatten()
    fpdarr = pdarr.flatten()
    selected = (fpcarr > 0)
    fpcarr = fpcarr[selected]
    fpdarr = fpdarr[selected]
    # total population is sum of population in each pixel
    totalpop = np.sum(fpcarr)
    if (totalpop > 0):
        # calculate population-weighted population density
        pwd = np.sum(np.multiply(fpdarr, fpcarr)) / totalpop
        # calculate the pop-weighted log(popdensity)
        pwlogpd = \
            np.sum( np.multiply( np.log(fpdarr), fpcarr) ) \
            / totalpop
    else:
        pwd = 0.0
        pwlogpd = 0.0
    return (totalpop, pwd, pwlogpd)

def GHS_pixels_to_coordinates(xpix, ypix, img_shape, img_transform,
                              inverse=False):
    """Transform pixel locations to coordinates in the
    georeferenced space"""
    #
    #  <copied in from metrocounties.py>
    #
    Nrows = img_shape[0]
    Ncols = img_shape[1]
    if (inverse):
        x = xpix; y = ypix
        col = np.clip(1.0/img_transform[0]*(x-img_transform[2]),
                      0.0, Ncols - 1)
        row = np.clip(1.0/img_transform[4]*(y-img_transform[5]),
                      0.0, Nrows - 1)
        return (int(col), int(row))
    xgeo = img_transform[2] + xpix*img_transform[0]
    ygeo = img_transform[5] + ypix*img_transform[4]
    # FIXME: There is an issue here about xpix = 1 or xpix = 1 etc...
    # I should try to figure this out sometime, but can't now.
    return (xgeo, ygeo)

def transform_mollweide_to_latlon(x, y):
    # Transform Mollweide (esri:54009) to LatLong coordinates (epsg:4326)
    #  <copied in from metrocounties.py>
    transformer = pyproj.Transformer.from_crs('esri:54009', 'epsg:4326')
    lat, lon = transformer.transform(x, y)
    return (lat, lon)

def transform_NAD83_to_WGS84(x, y):
    # Transform between the two Geographic (Lat/Lon) Coordinate systems:
    #      NAD83 (epsg:4269) to WSG84 (epsg:4326)
    transformer = pyproj.Transformer.from_crs('epsg:4269', 'epsg:4326')
    lat, lon = transformer.transform(x, y)
    return (lat, lon)

def get_latlon(xpix, ypix, img_shape, img_transform):
    (xgeo, ygeo) = GHS_pixels_to_coordinates(xpix, ypix,
                                             img_shape, img_transform)
    (lat, lon) = transform_mollweide_to_latlon(xgeo, ygeo)
    return (lat, lon)

############################################################
#    Image cleaning subroutines (only for GHS-POP images)  #
############################################################

def count_nonzero_neighbors(arr, r, c, rows, cols):
    if ( (r==0) | (r==(rows-1))  | (c==0) | (c==(cols-1)) ):
        print(f"***Warning: edge pixel at ({r:d},{c:d}) not checked, but deleted.")
        return 0
    rr = [r-1, r-1, r-1, r, r, r+1, r+1, r+1]
    cc = [c-1, c, c+1, c-1, c+1, c-1, c, c+1]
    count = 0
    for rrr,ccc in zip(rr,cc):
        if (arr[rrr,ccc] > 0):
            count += 1
    return count
    
def get_cleaned_pwpd(window_df, Nclean, Ncheck, maxNzero, Nmaxpix):
    # only do this for GHS-POP images
    if (popimage_type == 'GPW'):
        print("\n***Error: Not currently set up to do cleaning of GPW images.")
        exit(0)
    # Get windowed subimage(s) of population raster
    popimg, popimg_transform = \
        get_windowed_subimage(window_df, GHS_filepath)
    arr = np.array(popimg)
    (rows,cols) = arr.shape
    # set no data valued (negative) pixels to zero
    arr[arr < 0.0] = 0.0
    # make new copy of image for cleaning
    cl_arr = arr.copy()
    # and another one for for checking (will delete max each check)
    ch_arr = arr.copy()    
    Ncleaned = 0
    Nchecked = 0
    totalpop = []; pwd = []; pwlogpd = []; lat = []; lon = []
    checked = []; zeros = []
    while ( (Ncleaned < Nclean) & (Nchecked < Ncheck) ):
        Nchecked += 1
        # find max-valued pixel in checked image and zero out that pixel
        (y,x) = np.unravel_index(np.argmax(ch_arr, axis=None), arr.shape)
        ch_arr[y,x] = 0.0
        # but check for neighbors in uncleaned image
        nonzeropix = count_nonzero_neighbors(arr, y, x, rows, cols)
        if ((8-nonzeropix) > maxNzero):
            Ncleaned += 1
            # zero out that pixel in the cleaned image
            cl_arr[y,x] = 0.0
            # get the latitude and longitude of the pixel
            (la, lo) = get_latlon(x, y, popimg.shape, popimg_transform)
            lat.append(la); lon.append(lo)
            # calculate pwpd etc from cleaned image
            (p, pw, pl) = get_pwpd_from_count(cl_arr, nparr=True)
            totalpop.append(p); pwd.append(pw); pwlogpd.append(pl)
            checked.append(Nchecked); zeros.append(8-nonzeropix)
    # After cleaning, find the new max pixels
    maxpix = []
    for i in np.arange(Nmaxpix):
        (y,x) = np.unravel_index(np.argmax(arr, axis=None), arr.shape)
        arr[y,x] = 0.0
        (la, lo) = get_latlon(x, y, popimg.shape, popimg_transform)
        maxpix.append((la,lo))
    return (checked, zeros, totalpop, pwd, pwlogpd, lat, lon, maxpix)

def get_cleaned_pwpd_force(window_df, Npixels, Nmaxpix):
    # only do this for GHS-POP images
    if (popimage_type == 'GPW'):
        print("\n***Error: Not currently set up to do cleaning of GPW images.")
        exit(0)
    # Get windowed subimage(s) of population raster
    popimg, popimg_transform = \
        get_windowed_subimage(window_df, GHS_filepath)
    arr = np.array(popimg)
    # set no data valued (negative) pixels to zero    
    arr[arr < 0.0] = 0.0
    # make new copy of image for cleaning    
    for i in np.arange(Npixels):
        (y,x) = np.unravel_index(np.argmax(arr, axis=None), arr.shape)
        arr[y,x] = 0.0
    # After cleaning, find the new max pixels
    maxpix = []
    for i in np.arange(Nmaxpix):
        (y,x) = np.unravel_index(np.argmax(arr, axis=None), arr.shape)
        arr[y,x] = 0.0
        (la, lo) = get_latlon(x, y, popimg.shape, popimg_transform)
        maxpix.append((la,lo))
    return (maxpix, arr)

############################################################
#        Sorting the Image  (only for GHS-POP images)      #
############################################################

def flatten_and_sort_image(img):
    # First record the (row,col) values in arrays
    arr = np.array(img)
    (rows,cols) = arr.shape
    grid = np.indices((rows,cols))
    farr = arr.flatten()
    farr_r = grid[0].flatten()
    farr_c = grid[1].flatten()
    # Then delete all nonpositive values in the flattened array
    selected = (farr > 0)
    farr = farr[selected]
    farr_r = farr_r[selected]
    farr_c = farr_c[selected]
    # Then sort the remaining values
    sortind = np.flip(farr.argsort())
    # return the flattened array, sorted from max to min,
    # along with the corresponding row and column labels
    return farr[sortind], farr_r[sortind], farr_c[sortind]

def get_sorted_imarray(window_df, sort_Ntop, printout=True):
    # Get windowed subimage
    if (popimage_type == 'GHS'):
        img, img_transform = \
            get_windowed_subimage(window_df, GHS_filepath)
    elif (popimage_type == 'GPW'):
        print("\n***Error: Not currently set up to do sorting for GPW images.")
        exit(0)
    # Set no data valued (negative) pixels to zero    
    arr = np.array(img)
    arr[arr < 0.0] = 0.0
    (rows,cols) = arr.shape
    # Get a flattened and sorted array
    print("\tFlattening and sorting the array...")
    farr, farr_r, farr_c = flatten_and_sort_image(img)
    sorted_df = pd.DataFrame({'pixpop': farr[0:sort_Ntop],
                              'r': farr_r[0:sort_Ntop],
                              'c': farr_c[0:sort_Ntop]})
    sorted_df['NnonzeroN'] = 0
    sorted_df['lat'] = 0.0
    sorted_df['lon'] = 0.0
    count = 0
    print(f"\tGetting neighbors and positions of top {sort_Ntop:d} pixels...")
    print("\t\tStarted: ", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    for index, row in sorted_df.iterrows():
        x = int(row.c)
        y = int(row.r)
        (la, lo) = get_latlon(x, y, img.shape, img_transform)
        sorted_df.at[index,'lat'] = la
        sorted_df.at[index,'lon'] = lo
        nonzeropix = count_nonzero_neighbors(arr, y, x, rows, cols)
        sorted_df.at[index,'NnonzeroN'] = nonzeropix
        if printout:
            print(f"{count:d}   ({x:d},{y:d}) {row.pixpop:.1f} {nonzeropix:d} ({la:.3f},{lo:.3f})")
        count += 1
    print("\t\tEnded:   ", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))    
    return sorted_df

def plot_sorted(sorted_df, outfile):
    # only do this for GHS-POP images
    if (popimage_type == 'GPW'):
        print("\n***Error: Not currently set up to do sorting of GPW images.")
        exit(0)
    # First make a 10-point average of the NnonzeroN
    sorted_df['NnonzeroN_avg'] = sorted_df['NnonzeroN'].rolling(10).mean()
    # Then make plots of NnonzeroN_avg and pixpop
    fig, (ax1,ax2) = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(6,8))
    nonzero = sorted_df['NnonzeroN_avg'].to_numpy()
    pixpop = sorted_df['pixpop'].to_numpy()
    ax1.plot(nonzero)
    ax1.set_ylabel("Nonzero neighbors")
    ax1.set_ylim([0,9])
    ax2.plot(pixpop)
    ax2.set_ylabel("Pixel population")
    ax2.set_xlabel("Pixel rank")
    plt.tight_layout()
    plt.savefig(outfile)

############################################################
#                     Mapping Methods                      #
############################################################

