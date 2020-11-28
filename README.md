# Population-weighted population density (PWPD)
### Authors: Ben Holder and Niayesh Afshordi

This repository contains a module of subroutines, `src/pwpd.py`, for calculating the population weighted population density (PWD):

<img src="https://latex.codecogs.com/gif.latex?{\rm&space;PWD}=\sum_j\frac{\left(p_j/a_j\right)p_j}{\sum_i&space;p_i}" title="{\rm PWD}=\sum_j\frac{\left(p_j/a_j\right)p_j}{\sum_i p_i}" />

For a region divided into pixels of area <i>a<sub>j</sub></i> and population <i>p<sub>j</sub></i>, the PWD provides a measure of the "lived" population density, or that experienced by the average inhabitant.

## Data Sets

#### Population Raster Images (must be downloaded separately)

Calculation of PWD for a political region relies on a high resolution dataset of population.  The code here utilizes one of two [GeoTiff](https://earthdata.nasa.gov/esdis/eso/standards-and-references/geotiff) raster datasets (read with Python's [`rasterio`](https://rasterio.readthedocs.io/en/latest/) package), with the following resolution and coordinate system options:

* [Global Human Settlement (GHS-POP)](https://ghsl.jrc.ec.europa.eu/ghs_pop2019.php)
  * 250m-scale resolution; World Mollweide (equal-area) Coordinates (EPSG:54009)
  * 1km-scale resolution; World Mollweide
  * 9 arcsec resolution; World Geodetic System Datum Geographic (Lat/Lon) Coordinates (WGS84; EPSG:4326)
  * 30 arcsec resolution; WGS84  
* [Gridded Population of the World (GPWv4)](https://sedac.ciesin.columbia.edu/data/collection/gpw-v4)
  * 30-arcsec resolution; WGS84 
  * 2.5-arcmin resolution; WGS84 
  * 15-arcmin resolution; WGS84 
  * 1-degree resolution; WGS84 

which should be placed in the `data/ghs` and `data/gpw` sub-directories. Specifically, the code currently assumes the existence the following GeoTiff images:

  * [1km scale GHS-POP (2015)](https://cidportal.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_MT_GLOBE_R2019A/GHS_POP_E2015_GLOBE_R2019A_54009_1K/V1-0/GHS_POP_E2015_GLOBE_R2019A_54009_1K_V1_0.zip) (138MB)
  * [250m scale GHS-POP (2015)](https://cidportal.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_MT_GLOBE_R2019A/GHS_POP_E2015_GLOBE_R2019A_54009_250/V1-0/GHS_POP_E2015_GLOBE_R2019A_54009_250_V1_0.zip) (529MB)

  * [30as GPWv4 UN WPP-adjusted Population Count (2020)](https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals-rev11/data-download) (405MB)

  * [30as GPWv4 UN WPP-adjusted Population Density (2020)](https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-adjusted-to-2015-unwpp-country-totals-rev11/data-download) (347MB)

in the following directories, respectively:

 * `data/ghs/GHS_POP_E2015_GLOBE_R2019A_54009_1K_V1_0`
 * `data/ghs/GHS_POP_E2015_GLOBE_R2019A_54009_250_V1_0`
 * `data/gpw/`
 * `data/gpw/`

Lower resolutions of GHS-POP have not yet been implemented and would require slight adjustment of the code due to the different coordinate system; lower resolutions of GPWv4 should work but have not been tested.

The choice of image type and resolution is set by the helper function `set_popimage_pars`.

#### Shapefiles (countries provided; US counties must be downloaded separately)

To calculate PWD for a particular political region, the boundaries of that region must be provided using a [ESRI Shapefile](https://www.esri.com/library/whitepapers/pdfs/shapefile.pdf) (read with Python's [`geopandas`](https://geopandas.org) package).

Shapefiles for countries of the world are provided here in the `data/shapefiles/world` directory.  These are used, e.g., by the `src/get_pwpd_country.py` helper function, which takes a single commandline argument: the three-letter country code (e.g., USA, AFG, FRA). World shapefiles were taken from the public domain [_Natural Earth Vector_ dataset](https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/) (also available on [Github](https://github.com/nvkelso/natural-earth-vector)), and use the WGS84 coordinate system (EPSG:4326).

Shapefiles for US counties should be downloaded from the [US Census](https://www2.census.gov/geo/tiger/TIGER2019/COUNTY/) (79MB) and the unzipped directory `tl_2019_us_county` should be placed in the `data/shapefiles/UScounties` directory.  These shapefiles use the North American Datum Geographic (Lat/Lon) coordinate system (NAD83; EPSG:4269).

## PWPD Module and Helper Functions

### Helper Functions

These three helper functions can be run with python (after generating the conda environment using `src/pwpd.yml`).  They import and use the `pwpd` module (described below).

 * `src/get_pwpd_country.py` --- Output the PWD (and other characteristics) of a single country by specifying the three-letter country code on the command line.  Edit parameters at beginning of file to select the population image, epoch and resolution.  See also information on "cleaning" below.
 * `src/get_pwpd_all_countries.py` --- Output and write a csv file with the PWD (and other characteristics) for all countries for which there is an area and shapefile available.  Files will be written to `output`. Edit parameters at beginning of file to select the population image, epoch and resolution. 
 * `src/get_pwpd_us-county.py` --- Output the PWD (and other characteristics) of a single US county by specifying the state and county name (or FIPS codes). Run the code without arguments for usage examples.  Edit parameters at beginning of file to select the population image, epoch and resolution.

The `src/get_pwpd_country.py` helper function has options for "cleaning" the population image prior to calculating the PWD, when using the GHS-POP population image.  The GHS-POP image does a poor job at estimating the PWD for countries without high-resolution satellite imagery (e.g., AFG and ETH).  The algorithm used to clustering low-resolution population maps (taken from census data) into higher-resolution maps by assigning populations to pixels with human structures seems to mistake certain geographic patterns (in unpopulated areas) for built-up structures. It therefore creates "hot pixels" in rural areas, leading to erroneously large PWD values.  The problem is worst for the 250m-resolution image, but remains for the 1km-scale image.  The cleaning functions are designed to zero out high-valued pixels in affected countries.  Specifically, high-valued pixels with too many zero-valued neighboring pixels are deleted (this is the `by_neighbors` mode for the `cleanpwd` option; alternatively one can simply delete the top N pixels using the `by_force` mode).  This strategy will delete many of the bad pixels in a country with the problem, but leave a country that does not have this problem unaffected (since its high-valued pixels rarely occur alone).

To analyze a country for the above-described problem, one can use the `getsorted` option. This will: (1) sort the image to determine the N max-valued pixels, (2) return a csv file of these top-valued pixels including their lat/lon location and the number of non-zero neighbors each has, and (3) plot the values and the number of non-zero neighbors as a function of pixel rank. Images with a problem will show very low values on the "number of non-zero neighbors" plot, while images without the problem will have very close to eight nonzero neighbors (see `output/AFG_250m_plot-sorted.pdf` and `output/AUS_250m_plot-sorted.pdf` for examples of good and bad country images).

### PWPD Module (`src/pwpd.py`)

This module contains all subroutines used by the above-described helper functions.

