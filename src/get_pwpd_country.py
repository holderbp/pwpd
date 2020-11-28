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
#popimage_resolution = '1deg'

#================================================================
#=== Parameters for getting sorted array of image  (GHS only) ===
#================================================================
#
getsorted = False
sort_Ntop = 5000  # number of top pixels to return

#=====================================================
#=== Parameters for cleaning the image  (GHS only) ===
#=====================================================
#
#--- Type of cleaning: 'by_neighbors' or 'by_force' or None
cleanpwd = None
#--- Maximum number of pixels to check for cleaning
clean_Ncheck = 500     
#--- Maximum number of pixels to "clean" (remove/zero-out)
clean_Npixels = 500    
#--- Number of neighboring zeros to tolerate before cleaning pixel
clean_maxNzero = 4     
#--- Number of max-valued pixels to output to user in cleaned image
clean_Nmaxpix = 100    

#=============================================================
#=== Commandline input:  Accept three-letter country code  ===
#=============================================================
#
if (len(sys.argv) == 1):
    print("***Error: Three-letter country code is a required argument.")
    exit(0)
elif (len(sys.argv) == 2):
    countrycode = sys.argv[1].upper()  # country code must be all-caps
else:
    print("***Error: Unrecognized commandline option")
    exit(0)

#=================
#=== Main code ===
#=================
#
#=== Set the population image parameters
pwpd.set_popimage_pars(popimage_type, popimage_epoch, popimage_resolution)

#=== Load the shapefiles for all countries
allcountries_df = pwpd.load_world_shapefiles()

#=== Get the shapefile for the requested country
(country, countryname) = \
    pwpd.get_country_by_countrycode(allcountries_df, countrycode)

#=== Transform shapefile to coordinate system of the population image
country_t = pwpd.transform_shapefile(country)

#=== Get population, population-weighted population density
#    and the population-weighted log(pop density)
(pop_orig, pwd_orig, pwlogpd_orig, imgshape) = \
    pwpd.get_pop_pwpd_pwlogpd(country_t)

#=== Display result for user
print("=" * 80)
print(f"Using a {imgshape[0]:d}x{imgshape[1]:d} window of the "
      + popimage_epoch + " " + popimage_type 
      + " image with resolution " + popimage_resolution + "...\n")
print("The country of " + countryname + " (" + countrycode
      + f") has a population of {int(pop_orig):,d}.\n"
      + f"The PWPD_{popimage_type:s}_{popimage_resolution:s}"
      + f" is {pwd_orig:.1f} per km^2"
      + f" and exp[ PWlogPD ] = {np.exp(pwlogpd_orig):.1f}")
print("=" * 80)



#=======================================================
#===   Sorting the GHS-POP image to view max pixels  ===
#===                                                 ===
#===                   (GHS only)                    ===
#===                                                 ===
#=======================================================
if ( getsorted & (popimage_type == 'GHS') ):
    #=== Return a dataframe with the top sort_Ntop pixels
    #
    #  df.columns = [pixpop, Nnonzeroneighbors, lat, lon]
    #
    print(f"\nGetting a sorted list of top {sort_Ntop:d} pixels in the GHS-POP image.")
    print(f"[Note: It will take some time to find positions of these pixels!]")
    imgarr_sorted_df = \
        pwpd.get_sorted_imarray(country_t, sort_Ntop, printout=False)
    #=== Save the sorted data to csv
    sort_outfile = outdir + countrycode \
        + "_" + popimage_type \
        + "-" + popimage_resolution +  "_sorted-data.csv"
    print("Saving the sorted list of top pixels to the file:")
    print("\t" + sort_outfile)
    imgarr_sorted_df.to_csv(sort_outfile, index=False)
    #=== Plot the Nnonzero and pixvalue and save plots
    sort_plot_outfile = outdir + countrycode \
        + "_" + popimage_type \
        + "-" + popimage_resolution + "_plot-sorted.pdf"
    print("Plotting the number of nonzero neighbors and the")
    print("values of the top pixels, and saving plot to the file:")
    print("\t" + sort_plot_outfile)
    pwpd.plot_sorted(imgarr_sorted_df, sort_plot_outfile)
    
#================================================================
#===        Cleaning (removing hot pixels from) image         ===
#===                                                          ===
#===                     (GHS only)                           ===
#===                                                          ===
#===  The GHS-POP images have problems with "hot pixels" and  ===
#===  might need to be "cleaned" prior to giving a good       ===
#===  estimate of the population-weighted population density. ===
#================================================================
#
if ((cleanpwd == 'by_neighbors') & (popimage_type == 'GHS')):
    #=== Clean by checking neighbors of max-valued pixels
    print("\nCleaning the image and re-calculating PWPD...")
    print(f"Checking {clean_Ncheck:d} pixels," 
          + f" and removing up to {clean_Npixels:d}"
          + f" with more than {clean_maxNzero:d} zero-valued neighbors.")
    print("\tstep\trank\tNzeros\tpop\t\tpwd\tpwlogpd\t(lat,lon)")
    # Returns list of image characteristics after each cleaning
    # operation (each time a pixel is zeroed out):
    #
    #    checked = number checked so far
    #    zeros = number of zero-valued neighboring pixels of cleaned pixel
    #    pop = new population after zeroing out the pixel
    #    pwd = new pwpd after zeroing out the pixel
    #    pwlogpd = new pw-log(pd) after zeroing out the pixel
    #    (lat, lon) = geographic position of zeroed pixel
    #    maxpix = locations of new max-valued pixels after cleaning
    #
    (checked, zeros, pop, pwd, pwlogpd, lat, lon, maxpix) = \
        pwpd.get_cleaned_pwpd(country_t, clean_Npixels,
                              clean_Ncheck, clean_maxNzero, clean_Nmaxpix)
    #=== Output results of cleaning (at each step) to user
    # First pre-pend the characteristics of the uncleaned image data
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
    #=== Clean by simply removing the top clean_Npixels pixels
    print(f"\nCleaning the image by simply removing the top {clean_Npixels:d} pixels.")
    (maxpix, newimg) = pwpd.get_cleaned_pwpd_force(country_t, clean_Npixels,
                                                   clean_Nmaxpix)
    (pop, pwd, pwlogpd) = pwpd.get_pwpd_from_count(newimg, nparr=True)
    print(f"New pwd = {pwd:.1f}, with pop = {int(pop):,d} and pwlogpd = {pwlogpd:.4f}\n")

#=== Print out locations of top clean_Nmaxpix pixels after cleaning
if (bool(cleanpwd) & (popimage_type == 'GHS')):
    print(f"The locations of the top-valued {clean_Nmaxpix:d} pixels after cleaning:")
    for p in maxpix:
        print("\t",p)
        

