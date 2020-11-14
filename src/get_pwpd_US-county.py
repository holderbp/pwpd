# Use the pwpd.yml conda environment
import sys
import numpy as np
import pwpd

GHS_epoch = '2015'
GHS_lengthscale = '250m' # '1km' or '250m'

#=== Accept either [stateabb county] or their FIPS codes
fips_input = False
if (len(sys.argv) < 3):
    print("***Error: Two command-line arguments are required\n")
    print("\t python get_pwpd_US-county.py <state_abbrev> <county>")
    print("\t\tOR")
    print("\t python get_pwpd_US-county.py <stateFIPS> <countyFIPS>")
    print("\nUse quotes if a state/county has multiple words.")
    exit(0)
elif (len(sys.argv) == 3):
    # check if it is a FIPS code
    try:
        fips_state = int(sys.argv[1])
        fips_county = int(sys.argv[2])
        fips_input = True
    except ValueError:
        stateabb = sys.argv[1].lower()
        name_county = sys.argv[2].lower()
else:
    print("***Error: Unrecognized commandline option(s)")
    exit(0)

#=== load the US-county shapefiles
countyshapes_df = pwpd.load_UScounty_shapefiles()

#=== get country polygon
if fips_input:
    thecounty = ( (countyshapes_df['fips_state'] == fips_state)
                  & (countyshapes_df['fips_county'] == fips_county) )
    Nselected = len(countyshapes_df[thecounty])
    if (Nselected != 1):
        print(f"***Error: For the requested FIPS = ({fips_state:d},{fips_county:d})")
        print(f"          {Nselected:d} counties were found.")
        exit(0)
    county = countyshapes_df[thecounty]
    name_state = county['state'].to_list()[0]
    stateabb = county['stateabb'].to_list()[0]
    name_countylong = county['countylong'].to_list()[0]
else:
    thecounty = ( (countyshapes_df['stateabb'].str.lower() == stateabb)
                  & (countyshapes_df['county'].str.lower() == name_county) )
    Nselected = len(countyshapes_df[thecounty])
    if (Nselected != 1):
        print(f"***Error: For {name_county:s}, {stateabb.upper(),s}")
        print(f"          {Nselected:d} counties were found.")
        exit(0)
    county = countyshapes_df[thecounty]
    name_state = county['state'].to_list()[0]
    name_countylong = county['countylong'].to_list()[0]
    fips_state = county['fips_state'].to_list()[0]
    fips_county = county['fips_county'].to_list()[0]

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
(pop, pwd, pwlogpd) = pwpd.get_pop_pwpd_pwlogpd(arr)

#=== Print result to user
print("=" * 80)
print("Using the " + GHS_epoch + " GHS-POP image with resolution " + GHS_lengthscale + "...\n")
print(name_countylong + " in " + name_state
      + f", with FIPS = ({fips_state:d}, {fips_county:d}), "
      + f"has a population of {int(pop):,d}.\n"
      + f"The PWPD_{GHS_lengthscale:s} is {pwd:.1f} per km^2"
      + f" and exp[ PWlogPD ] = {np.exp(pwlogpd):.1f}")
print("=" * 80)
