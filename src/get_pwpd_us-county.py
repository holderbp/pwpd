# Use the pwpd.yml conda environment
import sys
import numpy as np
import pwpd

GHS_epoch = '2015'
GHS_lengthscale = '250m' # '1km' or '250m'

#=== Parse commandline input:
#
#    Accept either [stateabb countyname] or their FIPS codes
#
fips_input = False
if (len(sys.argv) == 3):
    try:
        # check if it is a FIPS code
        fips_state = int(sys.argv[1])
        fips_county = int(sys.argv[2])
        fips_input = True
    except ValueError:
        # if it is not, then accept the names
        stateabb = sys.argv[1].lower()
        name_county = sys.argv[2].lower()
else:
    print("\nTwo command-line arguments are required:\n")
    print("\t python get_pwpd_us-county.py <state_abbrev> <countyname>")
    print("\n\t\tOR\n")
    print("\t python get_pwpd_us-county.py <stateFIPS> <countyFIPS>")
    print("\nExample input:")
    print("\t python get_pwpd_us-county.py NY Saratoga")
    print("\t python get_pwpd_us-county.py 36 91")
    print("\t python get_pwpd_us-county.py NY \"Saratoga County\"")
    print("\t python get_pwpd_us-county.py VA \"Richmond County\"")
    print("\t python get_pwpd_us-county.py VA \"Richmond City\"")
    print("\n(Use the conda file pwpd.yml)")
    exit(0)

#=== load the dataframe all US-county shapefiles
countyshapes_df = pwpd.load_UScounty_shapefiles()

#=== get the shapefile for the requested county
if fips_input:
    (county, name_state, stateabb, name_countylong) = \
        pwpd.get_UScounty_by_fips(countyshapes_df, fips_state, fips_county)
else:
    (county, fips_state, fips_county, name_state, name_countylong) = \
        pwpd.get_UScounty_by_name(countyshapes_df, stateabb, name_county)

#=== transform to Mollweide
#
#       The "county" dataframe is a geopandas object
#       so it has the "to_crs" method
#
county_m = county.to_crs(crs=pwpd.eps_mollweide)

#=== Set the lengthscale choice for GHS image
pwpd.set_GHS_lengthscale(GHS_lengthscale)

#=== Mask GHS-POP image on county, get raster subimage
img, img_transform = pwpd.get_GHS_windowed_subimage(county_m)

#=== Get population and population-weighted--population density
arr = np.array(img)
arr[(arr == pwpd.GHS_no_data_value)] = 0.0
(pop, pwd, pwlogpd) = pwpd.get_pop_pwpd_pwlogpd(arr, nparr=True)

#=== Print result to user
print("=" * 80)
print("Using the " + GHS_epoch + " GHS-POP image with resolution " + GHS_lengthscale + "...\n")
print(name_countylong + " in " + name_state
      + f", with FIPS = ({fips_state:d}, {fips_county:d}), "
      + f"has a population of {int(pop):,d}.\n"
      + f"The PWPD_{GHS_lengthscale:s} is {pwd:.1f} per km^2"
      + f" and exp[ PWlogPD ] = {np.exp(pwlogpd):.1f}")
print("=" * 80)
