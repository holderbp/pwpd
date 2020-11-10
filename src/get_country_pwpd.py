# Use the pwpd.yml conda environment
import sys
import numpy as np
import pwpd

GHS_lengthscale = '1K' # '1K' or '250'

#=== Accept country code (three-letter) from commandline input
if (len(sys.argv) == 1):
    print("***Error: Three letter country code is a required argument.")
    exit(0)
elif (len(sys.argv) == 2):
    countrycode = sys.argv[1]
else:
    print("***Error: Unrecognized commandline option")
    exit(0)

#=== load the countries polygons
countryshapes_df = pwpd.load_country_shapefiles()

#=== get country polygon
country = countryshapes_df[countryshapes_df['threelett'] == countrycode]

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
(pop, pwd) = pwpd.get_pop_and_pwpd(arr)

#=== Print result to user
print("The country " + countrycode +  f" has a population of {pop:.2e} and a PWPD of {pwd:.1f}")

