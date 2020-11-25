# Use the pwpd.yml conda environment
import sys
import numpy as np
import pwpd

outdir = "../output/"

#=== Parameters for the population image
#popimage_type = 'GHS'   # 'GHS', 'GPW'
#popimage_epoch = '2015'  # '2015', '2020'
#popimage_lengthscale = '1km' # '1km', '250m', '30as'
popimage_type = 'GPW'   # 'GHS', 'GPW'
popimage_epoch = '2020'  # '2015', '2020'
popimage_lengthscale = '30as' # '1km', '250m', '30as'

#=== Parameters for cleaning the image
cleanpwd = None # 'by_neighbors' or 'by_force' or None
clean_Npixels = 500    # number of pixels to remove
clean_Ncheck = 500     # max number of pixels to check for cleaning
clean_maxNzero = 4      # number of zeros to tolerate before cleaning
clean_Nmaxpix = 100     # number of pixels to output in cleaned image

#=== Parameters for getting sorted array of image
getsorted = False
sort_Ntop = 10000  # number of top pixels to return

#=== Accept three-letter country code from commandline input
if (len(sys.argv) == 1):
    print("***Error: Three-letter country code is a required argument.")
    exit(0)
elif (len(sys.argv) == 2):
    countrycode = sys.argv[1].upper()  # country code must be all-caps
else:
    print("***Error: Unrecognized commandline option")
    exit(0)

#=== Set the population image parameters
pwpd.set_popimage_pars(popimage_type, popimage_epoch, popimage_lengthscale)

#=== Load the shapefiles for all countries
allcountries_df = pwpd.load_world_shapefiles()

#=== Get the shapefile for the requested country
(country, countryname) = \
    pwpd.get_country_by_countrycode(allcountries_df, countrycode)

#=== Transform shapefile to coordinate system of population image
country_t = pwpd.transform_shapefile(country)

#=== Get population and population-weighted--population density
(pop_orig, pwd_orig, pwlogpd_orig, imgshape) = \
    pwpd.get_pop_pwpd_pwlogpd(country_t)

#=== Print result to user
print("=" * 80)
print(f"Using a {imgshape[0]:d}x{imgshape[1]:d} window of the "
      + popimage_epoch + " " + popimage_type 
      + " image with resolution " + popimage_lengthscale + "...\n")
print("The country of " + countryname + " (" + countrycode
      + f") has a population of {int(pop_orig):,d}.\n"
      + f"The PWPD_{popimage_type:s}_{popimage_lengthscale:s}"
      + f" is {pwd_orig:.1f} per km^2"
      + f" and exp[ PWlogPD ] = {np.exp(pwlogpd_orig):.1f}")
print("=" * 80)

#=== Get sorted array
if ( (getsorted) & (popimage_type == 'GHS') ):
    # return a dataframe with the top sort_Ntop pixels
    #     [pixpop, Nnonzeroneighbors, lat, lon]
    imgarr_sorted_df = \
        pwpd.get_sorted_imarray(country_t, sort_Ntop, printout=False)
    # save the sorted data to csv
    sort_outfile = outdir + countrycode \
        + "_" + GHS_lengthscale +  "_sorted-data.csv"
    imgarr_sorted_df.to_csv(sort_outfile, index=False)
    # plot the Nnonzero and pixvalue
    sort_plot_outfile = outdir + countrycode \
        + "_" + GHS_lengthscale + "_plot-sorted.pdf"
    pwpd.plot_sorted(imgarr_sorted_df, sort_plot_outfile)
    
#=== Get cleaned PWD
if ((cleanpwd == 'by_neighbors') & (popimage_type == 'GHS')):
    print("\nCleaning the image and re-calculating PWPD...")
    print(f"Checking {clean_Ncheck:d} pixels," 
          + f" and removing up to {clean_Npixels:d}"
          + f" with more than {clean_maxNzero:d} zero-valued neighbors.")
    print("\tstep\trank\tNzeros\tpop\t\tpwd\tpwlogpd\t(lat,lon)")
    # Clean by checking neighbors of max pixels
    (checked, zeros, pop, pwd, pwlogpd, lat, lon, maxpix) = \
        pwpd.get_cleaned_pwpd(img, img_transform, clean_Npixels,
                              clean_Ncheck, clean_maxNzero, clean_Nmaxpix)
    # pre-append the uncleaned data
    checked.insert(0,0); zeros.insert(0,0)
    pop.insert(0,pop_orig); pwd.insert(0,pwd_orig)
    pwlogpd.insert(0,pwlogpd_orig); lat.insert(0,0.0); lon.insert(0,0.0)
    step = 0
    for (c, z, po, pw, pl, la, lo) in zip(checked, zeros, pop, pwd, pwlogpd, lat, lon):
        print("\t" + str(step) + "\t"
              + f"{c:d}" + "\t"
              + f"{z:d}" + "\t"
              + f"{int(po):,d}" + "\t"
              + f"{pw:.1f}" + "\t"
              + f"{pl:.2f}" + "\t"
              + f"({la:.6f},{lo:.6f})")
        step += 1
elif ((cleanpwd == 'by_force') & (popimage_type == 'GHS')):
    print(f"\nCleaning the image by simply removing the top {clean_Npixels:d} pixels")
    # Clean by simply removing the top clean_Npixels pixels
    (maxpix, newimg) = pwpd.get_cleaned_pwpd_force(img, img_transform, clean_Npixels,
                                                   clean_Nmaxpix)
    (pop, pwd, pwlogpd) = pwpd.get_pop_pwpd_pwlogpd(newimg)        
    print(f"New pwd = {pwd:.1f}, with pop = {int(pop):d} and pwlogpd = {pwlogpd:.4f}\n\n")

# print out locations of top clean_Nmaxpix pixels after cleaning
if (cleanpwd):
    print(f"The {clean_Nmaxpix:d} max pixels after cleaning:")
    for p in maxpix:
        print(p)
        

