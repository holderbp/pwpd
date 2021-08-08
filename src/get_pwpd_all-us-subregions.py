# Use the pwpd.yml conda environment
import sys
import numpy as np
import pandas as pd
import pwpd

#######################################################
# NOTE: Run the script:                               #
#                                                     #
#                get_pwpd_all-us-counties.py          #
#                                                     #
#       first (for your chosen popimage_type,         #
#       popimage_epoch, and popimage_resolution).     #
#       This script will load the output of that      #
#       as a starting point.                          #
#######################################################

#===========================================
#=== Parameters for the population image ===
#===========================================
#
#--- possible types are 'GHS' and 'GPW'
popimage_type = 'GHS' 
#popimage_type = 'GPW'  
#--- possible epochs are 2015 (GHS or GPW) and 2020 (GPW only)
popimage_epoch = '2015'  
#--- possible resolutions (~ pixel length scale) are:
#      GHS: '250m', '1km'
#      GPW: '30as' (~1km), 2.5am', '15am', '30am', '1deg'
popimage_resolution = '1km'
#popimage_resolution = '2.5am'
# set this to False for GPW with resolution > 30as
do_gamma = True
# set this to True to check some of the values produced by dissolving composites
check_summable_values_for_composites = False

#==============================
#=== Output directory/files ===
#==============================
outdir = "../output/"
# output data for all subregions (including composite counties, metro, states)
pwpd_subregions_outfilepath = outdir + "pwpd_all-us-subregions" + "_" + popimage_type \
    + "_" + popimage_epoch + "_" + popimage_resolution + ".csv"

#===================
#=== Input files ===
#===================
# The output file from "get_pwpd_all-us-counties.py" is used as a starting point
pwpd_counties_filepath = outdir + "pwpd_all-us-counties" + "_" + popimage_type \
    + "_" + popimage_epoch + "_" + popimage_resolution + ".csv"
# The output of "projects/2021-04-02.../external-data/covid19/curate_covid19.py"
# which has the FIPS (or fake-FIPS) values for every county, every composite county,
# every metro region, and every state
fips_filepath = "../../2021-04-02_new-python-implementation-nonlinear-regression/" \
    + "external-data/covid19/" + "UScounty_fips_dma.csv"

#=================
#=== Main code ===
#=================
#
#=== Set the population image parameters
pwpd.set_popimage_pars(popimage_type, popimage_epoch, popimage_resolution)

#=== Load the dataframe of all US-county shapefiles
countyshapes_df = pwpd.load_UScounty_shapefiles()
countyshapes_df = countyshapes_df.sort_values( by=['fips_state', 'fips_county'])

#=== Load the counties data from file, with format:
#
#    columns = ['fips_state', 'fips_county', 'county',
#               'countylong', 'state', 'stateabb', 'landarea'
#               'pop', 'pwpd', 'pwlogpd', 'popdens', 'gamma']
#
pwpd_counties = pd.read_csv(pwpd_counties_filepath)

#=== Load the FIPS file with composite counties
fips_df = pd.read_csv(fips_filepath)

#=== Merge the counties information into the fips file
# first make a fips column
pwpd_counties['fips'] = 0
for index, row in pwpd_counties.iterrows():
    sfips = row['fips_state']
    cfips = row['fips_county']
    pwpd_counties.at[index, 'fips'] = int(f"{sfips:02d}{cfips:03d}")
# change the fips for old Alaska HR "Valdez-Cordova"
thecounty = (pwpd_counties.fips == 2261)
pwpd_counties.loc[thecounty, 'fips'] = 2903
pwpd_counties.loc[thecounty, 'county'] = "Chugach plus Copper River"
pwpd_counties.loc[thecounty, 'countylong'] = "Chugach plus Copper River (formerly Valdez-Cordova)"
# then merge into fips file
df = pd.merge(fips_df, pwpd_counties, how='left', on='fips')
# keep only necessary columns
# columns = ['fips_state_x', 'fips_county_x', 'fips', 'county_type', 'ccFIPS',
#              'state_x', 'stateabb_x', 'county_x', 'countylong_x', 'dma', 'dmaname',
#              'fips_state_y', 'fips_county_y', 'county_y', 'countylong_y',
#              'state_y', 'stateabb_y', 'landarea', 'pop', 'pwpd', 'pwlogpd',
#              'popdens', 'gamma']
df = df[['fips_state_x', 'fips_county_x', 'fips', 'county_type', 'ccFIPS', 'state_x',
         'county_x', 'dma', 'dmaname', 'landarea', 'pop', 'pwpd', 'pwlogpd',
         'popdens', 'gamma']].copy()
df.columns = ['sfips', 'cfips', 'fips', 'county_type', 'ccFIPS', 'state', 'county', 'dma', 'dmaname',
              'landarea', 'pop', 'pwpd', 'pwlogpd', 'popdens', 'gamma']

#=== Calculate PWPD for composites
#
#       save to csv file after each category
#
# add fips column to shapes dataframe
countyshapes_df['fips'] = 0
for index, row in countyshapes_df.iterrows():
    countyshapes_df.at[index, 'fips'] = int(f"{row['fips_state']:02d}{row['fips_county']:03d}")
# do all states
df = pwpd.get_composite_pwds(df, countyshapes_df, 'state')
df.to_csv(pwpd_subregions_outfilepath, index=False)
# do all composite counties
df = pwpd.get_composite_pwds(df, countyshapes_df, 'composite-county')
df.to_csv(pwpd_subregions_outfilepath, index=False)
# do all DMAs
df = pwpd.get_composite_pwds(df, countyshapes_df, 'metro')
df.to_csv(pwpd_subregions_outfilepath, index=False)


if check_summable_values_for_composites:
    #=== Calculate summable values for composites
    # states
    sfips_list = np.unique(df[df['sfips'] < 99].sfips.to_list())
    for s in sfips_list:
        thestate = (df['sfips'] == s)
        statesum = df[thestate & (df['cfips'] > 0)].sum()
        df.loc[( thestate & (df['cfips'] == 0) ), 'landarea'] = statesum['landarea']
        df.loc[( thestate & (df['cfips'] == 0) ), 'pop'] = statesum['pop']
        df.loc[( thestate & (df['cfips'] == 0) ), 'popdens'] = \
            statesum['pop'] / statesum['landarea']
    # metro areas
    mfips_list = np.unique(df[df['sfips'] == 99].cfips.to_list())
    for m in mfips_list:
        themetro = ( (df['dma'] == m) &
                     ( (df['county_type'] == "regular") | (df['county_type'] == "part-of-composite") ) )
        msum = df[themetro].sum()
        df.loc[( (df['sfips'] == 99) & (df['cfips'] == m) ), 'landarea'] = msum['landarea']
        df.loc[( (df['sfips'] == 99) & (df['cfips'] == m) ), 'pop'] = msum['pop']
        df.loc[( (df['sfips'] == 99) & (df['cfips'] == m) ), 'popdens'] = \
            msum['pop'] / msum['landarea'] 
    # composite counties (but 2903 is already taken care of as former Valdez-Cordova)
    cc_list = np.unique(df[df['county_type'] == "composite"]['fips'].to_list())
    for c in cc_list:
        if (c != 2903):
            ccsum = df[df['ccFIPS'] == c].sum()
            df.loc[(df['fips'] == c), 'landarea'] = ccsum['landarea']
            df.loc[(df['fips'] == c), 'pop'] = ccsum['pop']
            df.loc[(df['fips'] == c), 'popdens'] = \
                ccsum['pop'] / ccsum['landarea']


