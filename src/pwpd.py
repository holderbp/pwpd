# Use the pwpd.yml conda environment
import sys
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import rasterio
import rasterio.mask
import pyproj
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

def get_pop_pwpd_pwlogpd(img, nparr=False):
    if (nparr == True):
        arr=img
    else:
        arr = np.array(img)
        arr[(arr == GHS_no_data_value)] = 0.0
    # First flatten the array and remove zero-valued elements
    farr = arr.flatten()
    selected = (farr > 0)
    farr = farr[selected]
    # total population is sum of population in each pixel
    totalpop = np.sum(farr)
    if (totalpop > 0):
        # calculate population-weighted population density
        pwd = np.sum(np.multiply(farr / GHS_Acell_in_kmsqd, farr) / totalpop)
        # calculate the pop-weighted log(popdensity)
        pwlogpd = np.sum( np.multiply( np.log(farr/GHS_Acell_in_kmsqd),
                                       farr) / totalpop )
    else:
        pwd = 0.0
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
    # Transform Mollweide (esri:54009) to LatLong coordinates (epsg:4226)
    #  <copied in from metrocounties.py>
    transformer = pyproj.Transformer.from_crs('esri:54009', 'epsg:4326')
    lat, lon = transformer.transform(x, y)
    return (lat, lon)

def get_latlon(xpix, ypix, img_shape, img_transform):
    (xgeo, ygeo) = GHS_pixels_to_coordinates(xpix, ypix,
                                             img_shape, img_transform)
    (lat, lon) = transform_mollweide_to_latlon(xgeo, ygeo)
    return (lat, lon)

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
    
def get_cleaned_pwpd(img, img_transform, Nclean, Ncheck, maxNzero, Nmaxpix):
    arr = np.array(img)
    (rows,cols) = arr.shape
    arr[(arr == GHS_no_data_value)] = 0.0
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
            (la, lo) = get_latlon(x, y, img.shape, img_transform)
            lat.append(la); lon.append(lo)
            # calculate pwpd etc from cleaned image
            (p, pw, pl) = get_pop_pwpd_pwlogpd(cl_arr, nparr=True)
            totalpop.append(p); pwd.append(pw); pwlogpd.append(pl)
            checked.append(Nchecked); zeros.append(8-nonzeropix)
    # After cleaning, find the new max pixels
    maxpix = []
    for i in np.arange(Nmaxpix):
        (y,x) = np.unravel_index(np.argmax(arr, axis=None), arr.shape)
        arr[y,x] = 0.0
        (la, lo) = get_latlon(x, y, img.shape, img_transform)
        maxpix.append((la,lo))
    return (checked, zeros, totalpop, pwd, pwlogpd, lat, lon, maxpix)

def get_cleaned_pwpd_force(img, img_transform, Npixels, Nmaxpix):
    arr = np.array(img)
    arr[(arr == GHS_no_data_value)] = 0.0
    # make new copy of image for cleaning    
    for i in np.arange(Npixels):
        (y,x) = np.unravel_index(np.argmax(arr, axis=None), arr.shape)
        arr[y,x] = 0.0
    # After cleaning, find the new max pixels
    maxpix = []
    for i in np.arange(Nmaxpix):
        (y,x) = np.unravel_index(np.argmax(arr, axis=None), arr.shape)
        arr[y,x] = 0.0
        (la, lo) = get_latlon(x, y, img.shape, img_transform)
        maxpix.append((la,lo))
    return (maxpix, arr)

############################################################
#                   Sorting the Image                      #
############################################################

def flatten_and_sort_image(img):
    # First record the (row,col) values in arrays
    arr = np.array(img)
    (rows,cols) = arr.shape
    grid = np.indices((rows,cols))
    farr = arr.flatten()
    farr_r = grid[0].flatten()
    farr_c = grid[1].flatten()
    # Then delete all nonzero values in the flattened array
    selected = (farr > 0)
    farr = farr[selected]
    farr_r = farr_r[selected]
    farr_c = farr_c[selected]
    # Then sort the remaining values
    sortind = np.flip(farr.argsort())
    # return the flattened array, sorted from max to min,
    # along with the corresponding row and column labels
    return farr[sortind], farr_r[sortind], farr_c[sortind]

def get_sorted_imarray(img, img_transform, sort_Ntop, printout=False):
    arr = np.array(img)
    arr[(arr == GHS_no_data_value)] = 0.0
    (rows,cols) = arr.shape
    farr, farr_r, farr_c = flatten_and_sort_image(img)
    sorted_df = pd.DataFrame({'pixpop': farr[0:sort_Ntop],
                              'r': farr_r[0:sort_Ntop],
                              'c': farr_c[0:sort_Ntop]})
    sorted_df['NnonzeroN'] = 0
    sorted_df['lat'] = 0.0
    sorted_df['lon'] = 0.0
    count = 0
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
    return sorted_df

def plot_sorted(sorted_df, outfile):
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

