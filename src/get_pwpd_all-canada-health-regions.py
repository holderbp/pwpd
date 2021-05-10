# Use the pwpd.yml conda environment
import sys
import numpy as np
import pandas as pd
import pwpd

pd.set_option('display.max_rows', None)

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
#popimage_resolution = '30as'
# set this to False for GPW with resolution > 30as
do_gamma = True

# get shapefile and all pop measures for entire province
get_entire_province = True

#==============================
#=== Output directory/files ===
#==============================
outdir = "../output/"
pwpd_outfilepath = outdir + "pwpd_all-canada-health-regions" + "_" + popimage_type \
    + "_" + popimage_epoch + "_" + popimage_resolution + ".csv"

#=================
#=== Main code ===
#=================
#
#=== Set the population image parameters
pwpd.set_popimage_pars(popimage_type, popimage_epoch, popimage_resolution)

#=== Load the dataframe all Canadian health region shapefiles
#
#    df.columns = ['hr_uid', 'region', 'area', 'geometry',
#                  'province', 'province_abb']
#
shapes_df = pwpd.load_CanadaHR_shapefiles()

#=== Create regions for entire province
if get_entire_province:
    shapes_df = shapes_df.append(
        pwpd.create_Canada_province_regions(shapes_df),
        ignore_index=True)

#=== Create new composite regions
#
#   The health regions in my shapefile, found here:
#
#       https://www150.statcan.gc.ca/n1/pub/82-402-x/2018001/hrbf-flrs-eng.htm
#
#   mostly reproduced in these maps:
#
#       https://www150.statcan.gc.ca/n1/pub/82-402-x/2013003/map-cart-eng.htm
#
#   are different than those used by the Covid19Canada group (w/ Jean
#   Paul Soucy and Isha Berry). Instead they use the regions shown on this
#   map:
#
#       https://resources-covid19canada.hub.arcgis.com/datasets/regionalhealthboundaries-1?geometry=-86.235%2C41.505%2C-73.568%2C44.321
#
#   which I think are the current health regions.  See this page:
#
#       https://www12.statcan.gc.ca/health-sante/82-228/help-aide/Q01.cfm?Lang=E
#
#   Based on that page, though, it seems that the Covid19Canada group has
#   mis-named the composite "Health Authorities" of BC, which comprise
#   multiple "Health Regions"  (e.g., the Vancouver (5932) health region
#   should be merged into the 593 Vancouver Coastal health authority, but
#   instead it is called 595 ... All five health authorities are mis-named
#   like that).
#
#   Also, the current Saskatchewan regions are not exactly the union of
#   the regions I am using. Compare the statcan map for Saskatchewan to
#   the resources-covid19canada.hub.arcgis.com map, above.
#
#   The differences are the following merged/renamed regions:

#
#     ##### Ontario #####
#
#         Oxford Elgin St. Thomas Health Unit (3575)
#                      == Southwestern Health Unit (3575)
#
# Just rename this health region
shapes_df = pwpd.rename_hr(shapes_df, 3575, "Southwestern Health Unit")
#
#         Huron (3539 -> 93539) + Perth (3554)
#                      == Huron Perth Public Health Unit (3539)
#
# Change the old Huron region hr_uid to 93539 and create merged region
shapes_df = pwpd.reassign_hr_uid(shapes_df, 3539, 93539)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [93539, 3554], 3539,
                                           "Huron Perth Health Unit"),
    ignore_index = True)
#
#     ##### British Columbia #####
#
#         Fraser East (5921) + Fraser North (5922) + Fraser South (5923)
#                      == Fraser Health (591)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [5921, 5922, 5923], 591,
                                           "Fraser Health"),
    ignore_index = True)
#
#         East Kootenay (5911) + Kootenay-Boundary (5912)
#            + Okanagan (5913) +  Thompson/Cariboo (5914)
#                      == Interior Health (592)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [5911, 5912, 5913, 5914], 592,
                                           "Interior Health"),
    ignore_index = True)
#
#         South Vancouver Island (5941) + Central Vancouver Island (5942)
#            + North Vancouver Island (5943)
#                      == [Vancouver] Island Health (593)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [5941, 5942, 5943], 593,
                                           "Vancouver Island Health"),
    ignore_index = True)
#
#         Northwest (5951) + Northern Interior (5952) + Northeast (5953)
#                      == Northern Health (594)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [5951, 5952, 5953], 594,
                                           "Northern Health"),
    ignore_index = True)
#
#         Richmond (5931) + Vancouver (5932)
#            + North Shore / Coast Garibaldi (5933)
#                      == Vancouver Coastal Health (595)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [5931, 5932, 5933], 595,
                                           "Vancouver Coastal Health"),
    ignore_index = True)
#
#     ##### Saskatchewan #####  
#
#     (***Warning*** these are approximate, not exact)
#
#         Mamawetan Churchill River (4711) + Keewatin Yatthe (4712)
#            + Athabasca (4713)
#                      == Far North (471)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [4711, 4712, 4713], 471,
                                           "Far North"),
    ignore_index = True)
#
#         Kelsey Trail (4708) + Prince Albert Parkland (4709)
#            + Prairie North (4710)
#                      == North (472)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [4708, 4709, 4710], 472,
                                           "North"),
    ignore_index = True)
#
#         Sunrise (4705) + Heartland (4707)
#                      == Central (473)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [4705, 4707], 473,
                                           "Central"),
    ignore_index = True)
#
#         Saskatoon (4706) == Saskatoon (474)
shapes_df = pwpd.reassign_hr_uid(shapes_df, 4706, 474)

#
#         Regina (4704) == Regina (475)
shapes_df = pwpd.reassign_hr_uid(shapes_df, 4704, 475)
#
#         Sun Country (4701) + Five Hills (4702) + Cypress (4703)
#                      == South (476)
shapes_df = shapes_df.append(
    pwpd.create_CanadaHR_composite_regions(shapes_df,
                                           [4701, 4702, 4703], 476,
                                           "Central"),
    ignore_index = True)

#=== Make copy of HR shapefile dataframe for output,
#    removing 'geometry' and adding relevant pop data
#
#    pwpd_df.columns = ['hr_uid', 'region', 'area', 'province',
#                       'province_abb', 'pop', 'pwpd',
#                       'pwlogpd', 'popdens', 'gamma']
#
pwpd_df = pwpd.create_canada_hr_dataframe(shapes_df)
# sort by province then by hr_uid
pwpd_df = pwpd_df.sort_values( by=['province_abb', 'hr_uid'])
shapes_df = shapes_df.sort_values( by=['province_abb', 'hr_uid'])
# convert area to km^2 from m^2
pwpd_df['area'] = pwpd_df['area']/1e6

#=== Make calculations for each region, output result to user, save csv
prev_fips_state = 0
for index, row in pwpd_df.iterrows():
    name = row.region
    prov_id = row.province_abb
    hr_uid = row.hr_uid
    area = row.area
    # Get the shapefile for this health region
    hregion = pwpd.get_CanadaHR_by_hr_uid(shapes_df, hr_uid)
    # Transform shapefile to coordinate system of population image
    hregion_t = pwpd.transform_shapefile(hregion)
    # Get population and population-weighted--population density
    (pop_orig, pwd_orig, pwlogpd_orig, imgshape) = \
        pwpd.get_pop_pwpd_pwlogpd(hregion_t)
    pwpd_df.at[index, 'pop'] = pop_orig
    pwpd_df.at[index, 'pwpd'] = pwd_orig
    pwpd_df.at[index, 'pwlogpd'] = pwlogpd_orig
    # Calculate population density
    pwpd_df.at[index, 'popdens'] = pop_orig/area
    # Calculate population sparsity (gamma)
    if do_gamma:
        pwpd_df.at[index, 'gamma'] = \
            pwpd.get_gamma(pop_orig, area, pwd_orig,
                           popimage_type, popimage_resolution)
    # Print result to user
    print("=" * 80)
    print(f"Using a {imgshape[0]:d}x{imgshape[1]:d} window of the "
          + popimage_epoch + " " + popimage_type 
          + " image with resolution " + popimage_resolution + "...\n")
    print(name + " (" + prov_id + "_" + str(hr_uid) + ") "
          + f"has a population of {int(pop_orig):,d}.\n"
          + f"The PWPD_{popimage_type:s}_{popimage_resolution:s}"
          + f" is {pwd_orig:.1f} per km^2"
          + f" and exp[ PWlogPD ] = {np.exp(pwlogpd_orig):.1f}")
# save to file
pwpd_df.to_csv(pwpd_outfilepath, index=False)

