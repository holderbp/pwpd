# Use the pwpd.yml conda environment
import sys
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
import rasterio.mask
import folium  # for making html maps with leaflet.js 

############################################################
#             GHS-POP parameters and methods               #
############################################################
#
#
# GHS-POP parameters
#
GHS_dir = "../data/ghs/"
GHS_file_string1 = "GHS_POP_E2015_GLOBE_R2019A_54009_"
GHS_file_string2 = "_V1_0" 
GHS_filepath = None
GHS_no_data_value = -200
GHS_lengthscale = None
GHS_Acell_in_kmsqd = None
# code for the Mollweide coordinate system
eps_mollweide = 'esri:54009'
    
def set_GHS_lengthscale(lengthstring):
    """Set the lengthscale (250m or 1km) for the GHS data set"""
    global GHS_lengthscale, GHS_Acell_in_kmsqd, GHS_filepath
    # set lengthscale string for file manipulation
    if (lengthstring == '250m'):
        GHS_lengthscale = '250'
    elif (lengthstring == '1km'):
        GHS_lengthscale = '1K'
    else:
        print("***Error: GHS lengthscale", lengthstring, "not recognized.")
        exit(0)
    # set lengthscale value and pixel area
    if (GHS_lengthscale == '250'):
        GHS_resolution_in_km = 0.250
    elif (GHS_lengthscale == '1K'):
        GHS_resolution_in_km = 1.0
    GHS_Acell_in_kmsqd = GHS_resolution_in_km**2
    # set GHS image filepath
    GHS_filepath =  GHS_dir + GHS_file_string1 \
        + GHS_lengthscale + GHS_file_string2 + "/" + GHS_file_string1 \
        + GHS_lengthscale + GHS_file_string2 +  ".tif"

def get_GHS_windowed_subimage(window_df):
    # get polygon shape(s) from the geopandas dataframe
    windowshapes = window_df["geometry"]
    # mask GHS-POP image with entire set of shapes
    with rasterio.open(GHS_filepath) as src:
        img, img_transform = \
            rasterio.mask.mask(src, windowshapes, crop=True)
        img_profile = src.profile
        img_meta = src.meta
    img_meta.update( { "driver": "GTiff",
                       "height": img.shape[1],
                       "width": img.shape[2],
                       "transform": img_transform} )
    # return only the first band (rasterio returns 3D array)
    return img[0], img_transform


############################################################
#    Political region shapefiles: data and methods         #
############################################################


#=== Shapefiles for the countries of the world.
#
#   Used file from here:
#
#     https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/
#
# columns =
#  Index(['featurecla', 'scalerank', 'LABELRANK', 'SOVEREIGNT', 'SOV_A3',
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
#  The three-letter codes seem to be 'ADM0_A3' and name is 'SOVEREIGNT'
#
world_shape_dir = "../data/shapefiles/world/ne_50m_admin_0_countries/"
world_shape_filepath = world_shape_dir + "ne_50m_admin_0_countries.shp"
# these countries have no entry
places_w_no_shapefile = ['PSE', 'GIB', 'SSD', 'TUV']

def load_world_shapefiles():
    #=== read in countries dataframe
    #    (keep only relevant columns and rename like in "codes")
    world_shapes = gpd.read_file(world_shape_filepath)
    world_shapes = world_shapes[['SOVEREIGNT', 'ADM0_A3', 'geometry']]
    world_shapes.columns = ['name', 'threelett', 'geometry']
    return world_shapes

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
USstate_fips_filepath = UScounty_shape_dir + "US-state_fips-codes.csv"

def load_UScounty_shapefiles():
    #=== read in UScounties dataframe
    #    (keep only relevant columns and rename like in "codes")
    county_shapes = gpd.read_file(UScounty_shape_filepath)
    county_shapes = county_shapes[['STATEFP', 'COUNTYFP', 'NAME',
                                   'NAMELSAD', 'ALAND', 'geometry']]
    county_shapes.columns = ['fips_state', 'fips_county', 'county',
                             'countylong', 'landarea', 'geometry']
    #=== Make FIPS codes integer-valued
    county_shapes['fips_state'] = county_shapes['fips_state'].astype(int)
    county_shapes['fips_county'] = county_shapes['fips_county'].astype(int)
    #=== Add the state name and abbreviation for each county
    #    using the file of US state FIPS codes
    county_shapes['state'] = ""
    county_shapes['stateabb'] = ""
    statefips_df = pd.read_csv(USstate_fips_filepath)
    statefips_df['fips'] = statefips_df['fips'].astype(int)
    for index,row in county_shapes.iterrows():
        fips = row.fips_state
        thestate = (statefips_df['fips'] == fips)
        county_shapes.at[index,'state'] = \
            statefips_df[thestate]['name'].to_list()[0]
        county_shapes.at[index,'stateabb'] = \
            statefips_df[thestate]['abb'].to_list()[0]
    return county_shapes


############################################################
#        Population-weighted Density Calculation           #
############################################################

def get_pop_pwpd_pwlogpd(arr):
    # total population is sum of population in each pixel
    totalpop = np.sum(arr)
    if (totalpop > 0):
        # calculate population-weighted population density
        pwpd = np.sum(np.multiply(arr / GHS_Acell_in_kmsqd, arr) / totalpop)
        # calculate the pop-weighted log(popdensity)
        nonzero = (arr > 0)
        pwlogpd = np.sum( np.multiply( np.log(arr[nonzero]/GHS_Acell_in_kmsqd),
                                       arr[nonzero]) / totalpop )
    else:
        pwpd = 0.0
    return (totalpop, pwpd, pwlogpd)



############################################################
#                     Mapping Methods                      #
############################################################

