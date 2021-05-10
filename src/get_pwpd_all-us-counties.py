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
popimage_resolution = '250m'
#popimage_resolution = '2.5am'
# set this to False for GPW with resolution > 30as
do_gamma = True

#==============================
#=== Output directory/files ===
#==============================
outdir = "../output/"
pwpd_outfilepath = outdir + "pwpd_all-us-counties" + "_" + popimage_type \
    + "_" + popimage_epoch + "_" + popimage_resolution + ".csv"

#=================
#=== Main code ===
#=================
#
#=== Set the population image parameters
pwpd.set_popimage_pars(popimage_type, popimage_epoch, popimage_resolution)

#=== Load the dataframe all US-county shapefiles
countyshapes_df = pwpd.load_UScounty_shapefiles()

#=== Make copy of all US-counties dataframe for output
#
#    columns = ['fips_state', 'fips_county', 'county',
#               'countylong', 'state', 'stateabb', 'landarea'
#               'pop', 'pwpd', 'pwlogpd', 'popdens', 'gamma']
#
pwpd_counties = pwpd.create_uscounties_dataframe(countyshapes_df)
# sort by state FIPS then county FIPS
pwpd_counties = pwpd_counties.sort_values( by=['fips_state', 'fips_county'])
countyshapes_df = countyshapes_df.sort_values( by=['fips_state', 'fips_county'])
# convert area to km^2 from m^2
pwpd_counties['landarea'] = pwpd_counties['landarea']/1e6

#=== Make calculations for each country, output result to user, save csv
prev_fips_state = 0
for index, row in pwpd_counties.iterrows():
    fips_state = row['fips_state']
    fips_county = row['fips_county']
    area = row['landarea']
    name_countylong = row['countylong']
    name_state = row['state']
    (county, name_state, stateabb, name_countylong) = \
        pwpd.get_UScounty_by_fips(countyshapes_df, fips_state, fips_county)
    # Transform shapefile to coordinate system of population image
    county_t = pwpd.transform_shapefile(county)
    # Get population and population-weighted--population density
    (pop_orig, pwd_orig, pwlogpd_orig, imgshape) = \
        pwpd.get_pop_pwpd_pwlogpd(county_t)
    pwpd_counties.at[index, 'pop'] = pop_orig
    pwpd_counties.at[index, 'pwpd'] = pwd_orig
    pwpd_counties.at[index, 'pwlogpd'] = pwlogpd_orig
    # Calculate population density
    pwpd_counties.at[index, 'popdens'] = pop_orig/area
    # Calculate population sparsity (gamma)
    if do_gamma:
        pwpd_counties.at[index, 'gamma'] = \
            pwpd.get_gamma(pop_orig, area, pwd_orig,
                           popimage_type, popimage_resolution)
    # Print result to user
    print("=" * 80)
    print(f"Using a {imgshape[0]:d}x{imgshape[1]:d} window of the "
          + popimage_epoch + " " + popimage_type 
          + " image with resolution " + popimage_resolution + "...\n")
    print(name_countylong + " in " + name_state
      + f", with FIPS = ({fips_state:d}, {fips_county:d}), "
      + f"has a population of {int(pop_orig):,d}.\n"
      + f"The PWPD_{popimage_type:s}_{popimage_resolution:s}"
      + f" is {pwd_orig:.1f} per km^2"
      + f" and exp[ PWlogPD ] = {np.exp(pwlogpd_orig):.1f}")
    # Save to csv file after each state
    if (fips_state != prev_fips_state):
        pwpd_counties.to_csv(pwpd_outfilepath, index=False)
    prev_fips_state = fips_state

