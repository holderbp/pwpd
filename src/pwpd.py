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
#  The three-letter country code is 'ADM0_A3' and name is 'SOVEREIGNT'
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

def get_country_by_countrycode(allcountries_df, countrycode):
    country = allcountries_df[allcountries_df['threelett'] == countrycode]
    countryname = country['name'].to_list()[0]
    return (country, countryname)

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

def get_UScounty_by_fips(allcounties_df, fips_state, fips_county):
    thecounty = ( (allcounties_df['fips_state'] == fips_state)
                  & (allcounties_df['fips_county'] == fips_county) )
    Nselected = len(allcounties_df[thecounty])
    if (Nselected != 1):
        print(f"***Error: For the requested FIPS = ({fips_state:d},{fips_county:d})")
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
        print(f"***Error: For {name_county:s}, {stateabb.upper(),s}")
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

