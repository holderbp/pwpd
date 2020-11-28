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
#popimage_type = 'GHS' 
popimage_type = 'GPW'  
#--- possible epochs are 2015 (GHS or GPW) and 2020 (GPW only)
popimage_epoch = '2015'  
#--- possible resolutions (~ pixel length scale) are:
#      GHS: '250m', '1km'
#      GPW: '30as' (~1km), 2.5am', '15am', '30am', '1deg'
#popimage_resolution = '1km'
popimage_resolution = '30as'

#================================================================
#===                  Commandline input:                      ===
#===  Accept either [stateabb countyname] or their FIPS codes ===
#================================================================
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

#=================
#=== Main code ===
#=================
#
#=== Set the population image parameters
pwpd.set_popimage_pars(popimage_type, popimage_epoch, popimage_resolution)

#=== load the dataframe all US-county shapefiles
countyshapes_df = pwpd.load_UScounty_shapefiles()

#=== get the shapefile for the requested county
if fips_input:
    (county, name_state, stateabb, name_countylong) = \
        pwpd.get_UScounty_by_fips(countyshapes_df, fips_state, fips_county)
else:
    (county, fips_state, fips_county, name_state, name_countylong) = \
        pwpd.get_UScounty_by_name(countyshapes_df, stateabb, name_county)

#=== Transform shapefile to coordinate system of the population image
county_t = pwpd.transform_shapefile(county)

#=== Get population, population-weighted population density
#    and the population-weighted log(pop density)
(pop_orig, pwd_orig, pwlogpd_orig, imgshape) = \
    pwpd.get_pop_pwpd_pwlogpd(county_t)

#=== Print result to user
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
print("=" * 80)
