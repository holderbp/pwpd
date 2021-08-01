# Use the pwpd.yml conda environment
import sys
import numpy as np
import pwpd

outdir = "../output/"

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

#==============================
#=== Output directory/files ===
#==============================
outdir = "../output/"
pwpd_counties_outfilepath = outdir + "pwpd_all-us-counties" + "_" + popimage_type \
    + "_" + popimage_epoch + "_" + popimage_resolution + ".csv"

#=================
#=== Main code ===
#=================
#
#=== Set the population image parameters
pwpd.set_popimage_pars(popimage_type, popimage_epoch, popimage_resolution)

#=== Load the dataframe all US-county shapefiles
countyshapes_df = pwpd.load_UScounty_shapefiles()
# sort by state FIPS then county FIPS
countyshapes_df = countyshapes_df.sort_values( by=['fips_state', 'fips_county'])

#=== Run the PWPD etc calculations for each county
#
#    The subroutine will output info to user and save file after
#    every state
#
#    Format of output:
#
#      columns = ['fips_state', 'fips_county', 'county',
#                 'countylong', 'state', 'stateabb', 'landarea'
#                 'pop', 'pwpd', 'pwlogpd', 'popdens', 'gamma']
#           
pwpd_counties = \
    pwpd.get_pwpd_UScounties(countyshapes_df, pwpd_counties_outfilepath,
                             do_gamma, popimage_type, popimage_resolution,
                             popimage_epoch)
