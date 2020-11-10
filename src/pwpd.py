# Use the pwpd.yml conda environment
import sys
import numpy as np
import geopandas as gpd
import rasterio
import rasterio.mask

#
# GHS-POP info
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


#
# Countries polygons.
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
countryshape_dir = "../data/world-shapefiles/ne_50m_admin_0_countries/"
countryshape_filepath = countryshape_dir + "ne_50m_admin_0_countries.shp"
# these countries have no entry
places_w_no_shapefile = ['PSE', 'GIB', 'SSD', 'TUV']


def load_country_shapefiles():
    #=== read in countries dataframe
    #    (keep only relevant columns and rename like in "codes")
    countryshapes = gpd.read_file(countryshape_filepath)
    countryshapes = countryshapes[['SOVEREIGNT', 'ADM0_A3', 'geometry']]
    countryshapes.columns = ['name', 'threelett', 'geometry']
    return countryshapes
    
def set_GHS_lengthscale(lengthstring):
    global GHS_lengthscale, GHS_Acell_in_kmsqd, GHS_filepath
    GHS_lengthscale = lengthstring
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

def get_pop_and_pwpd(arr):
    totalpop = np.sum(arr)
    if (totalpop > 0):
        pwpd = np.sum(np.multiply(arr, arr)) \
            / GHS_Acell_in_kmsqd / totalpop
    else:
        pwpd = 0.0
    return (totalpop, pwpd)

