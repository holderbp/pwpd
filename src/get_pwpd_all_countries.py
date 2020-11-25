# Use the pwpd.yml conda environment
import sys
import numpy as np
import pwpd


#=== Parameters for the population image
#popimage_type = 'GHS'   # 'GHS', 'GPW'
#popimage_epoch = '2015'  # '2015', '2020'
#popimage_lengthscale = '1km' # '1km', '250m', '30as'
popimage_type = 'GPW'   # 'GHS', 'GPW'
popimage_epoch = '2020'  # '2015', '2020'
popimage_lengthscale = '30as' # '1km', '250m', '30as'

#=== Output
outdir = "../output/"
pwpd_outfilepath = outdir + "pwpd" + "_" + popimage_type \
    + "_" + popimage_epoch + "_" + popimage_lengthscale \
    + ".csv"

#=== Set the population image parameters
pwpd.set_popimage_pars(popimage_type, popimage_epoch, popimage_lengthscale)

#=== Load the shapefiles for all countries
allcountries_df = pwpd.load_world_shapefiles()

#
#=== Copy to new dataframe, make columns for pwpd etc, get country areas
#
#   columns = [name, threelett, area, pop, pwpd, pwlogpd, popdens, gamma]
#
pwpd_countries = pwpd.create_dataframe_with_areas(allcountries_df)

#=== Make calculations for each country, output result to user, save csv
for index, row in pwpd_countries.iterrows():
    countrycode = row['threelett']
    area = row['area']
    if (area > 0.0):
        # Get the shapefile for the requested country
        (country, countryname) = \
            pwpd.get_country_by_countrycode(allcountries_df, countrycode)
        # Transform shapefile to coordinate system of population image
        country_t = pwpd.transform_shapefile(country)
        # Get population and population-weighted--population density
        (pop_orig, pwd_orig, pwlogpd_orig, imgshape) = \
            pwpd.get_pop_pwpd_pwlogpd(country_t)
        # Save in dataframe
        pwpd_countries.at[index, 'pop'] = pop_orig
        pwpd_countries.at[index, 'pwpd'] = pwd_orig
        pwpd_countries.at[index, 'pwlogpd'] = pwlogpd_orig
        # Calculate population density
        pwpd_countries.at[index, 'popdens'] = pop_orig/area
        # Calculate population sparsity (gamma)
        pwpd_countries.at[index, 'gamma'] = \
            pwpd.get_gamma(pop_orig, area, pwd_orig,
                           popimage_type, popimage_lengthscale)
        # Print result to user
        print("=" * 80)
        print(f"Using a {imgshape[0]:d}x{imgshape[1]:d} window of the "
              + popimage_epoch + " " + popimage_type 
              + " image with resolution " + popimage_lengthscale + "...\n")
        print("The country of " + countryname + " (" + countrycode
              + f") has a population of {int(pop_orig):,d}.\n"
              + f"The PWPD_{popimage_type:s}_{popimage_lengthscale:s}"
              + f" is {pwd_orig:.1f} per km^2"
              + f" and exp[ PWlogPD ] = {np.exp(pwlogpd_orig):.1f}")
    else:
        print("No area found for " + countrycode)
    pwpd_countries.to_csv(pwpd_outfilepath)

