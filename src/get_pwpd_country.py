# Use the pwpd.yml conda environment
import sys
import numpy as np
import pwpd

GHS_epoch = '2015'
GHS_lengthscale = '250m' # '1km' or '250m'

#=== Accept three-letter country code from commandline input
if (len(sys.argv) == 1):
    print("***Error: Three-letter country code is a required argument.")
    exit(0)
elif (len(sys.argv) == 2):
    countrycode = sys.argv[1].upper()  # country code must be all-caps
else:
    print("***Error: Unrecognized commandline option")
    exit(0)

#=== load the shapefiles for all countries
allcountries_df = pwpd.load_world_shapefiles()

#=== get the shapefile for the requested country
(country, countryname) = \
    pwpd.get_country_by_countrycode(allcountries_df, countrycode)

#=== transform to Mollweide
#
#       The "country" dataframe is a geopandas object
#       so it has the "to_crs" method)
#
country_m = country.to_crs(crs=pwpd.eps_mollweide)

#=== Set the lengthscale choice for GHS image
pwpd.set_GHS_lengthscale(GHS_lengthscale)

#=== Mask GHS-POP image on county, get raster subimage
img, img_transform = pwpd.get_GHS_windowed_subimage(country_m)

#=== Get population and population-weighted--population density
arr = np.array(img)
arr[(arr == pwpd.GHS_no_data_value)] = 0.0
(pop, pwd, pwlogpd) = pwpd.get_pop_pwpd_pwlogpd(arr)

#=== Print result to user
print("=" * 80)
print("Using the " + GHS_epoch + " GHS-POP image with resolution " + GHS_lengthscale + "...\n")
print("The country of " + countryname + " (" + countrycode
      + f") has a population of {int(pop):,d}.\n"
      + f"The PWPD_{GHS_lengthscale:s} is {pwd:.1f} per km^2"
      + f" and exp[ PWlogPD ] = {np.exp(pwlogpd):.1f}")
print("=" * 80)
