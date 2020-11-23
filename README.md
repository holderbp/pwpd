# Population-weighted population density (PWPD)
### Authors: Ben Holder and Niayesh Afshordi

This repository contains a module of subroutines, `src/pwpd.py`, for calculating the population weighted population density (PWD):

<img src="https://latex.codecogs.com/gif.latex?{\rm&space;PWD}=\sum_j\frac{\left(p_j/a_j\right)p_j}{\sum_i&space;p_i}" title="{\rm PWD}=\sum_j\frac{\left(p_j/a_j\right)p_j}{\sum_i p_i}" />

For a region divided into pixels of area <i>a<sub>j</sub></i> and population <i>p<sub>j</sub></i>, the PWD provides a measure of the "lived" population density, or that experienced by the average inhabitant.

## Data Sets

#### Population Raster Images (must be downloaded separately)

The calculation of PWD for a political region relies on a high resolution dataset of population.  The code here utilizes one of two raster datasets, with the following resolution options and coordinate system specifications:


* [Global Human Settlement (GHS-POP)](https://ghsl.jrc.ec.europa.eu/ghs_pop2019.php)
  * 250m-scale resolution; World Mollweide coords (EPSG:54009)
  * 1km-scale resolution; World Mollweide coords
  * 9 arcsec resolution; Geographic (Lat/Lon) coords (EPSG:4326)
  * 30 arcsec resolution; Geographic (Lat/Lon) coords 

or,

* [Gridded Population of the World (GPWv4)](https://sedac.ciesin.columbia.edu/data/collection/gpw-v4l)
  * 30-arcsec resolution; Geographic (Lat/Lon) coords
  * 2.5-arcmin resolution; Geographic (Lat/Lon) coords
  * 15-arcmin resolution; Geographic (Lat/Lon) coords
  * 1-degree resolution; Geographic (Lat/Lon) coords

which should be placed in the `data/ghs` and `data/gpw` sub-directories. Specifically, the code currently assumes the existence the following GeoTiff images:

  * [1km scale GHS-POP (2015)](https://cidportal.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_MT_GLOBE_R2019A/GHS_POP_E2015_GLOBE_R2019A_54009_1K/V1-0/GHS_POP_E2015_GLOBE_R2019A_54009_1K_V1_0.zip) (139MB)
  * [250m scale GHS-POP (2015)](https://cidportal.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_MT_GLOBE_R2019A/GHS_POP_E2015_GLOBE_R2019A_54009_250/V1-0/GHS_POP_E2015_GLOBE_R2019A_54009_250_V1_0.zip) (529MB)

  * [30as GPW UN WPP-adjusted Population Count (2020)](https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals-rev11)

  * [30as GPW UN WPP-adjusted Population Density (2020)](https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-adjusted-to-2015-unwpp-country-totals-rev11)

in the following directories, respectively:

 * `data/ghs/GHS_POP_E2015_GLOBE_R2019A_54009_1K_V1_0`
 * `data/ghs/GHS_POP_E2015_GLOBE_R2019A_54009_250_V1_0`
 * `data/gpw/`
 * `data/gpw/`

Lower resolutions of GHS-POP have not yet been implemented and would require slight adjustment of the code due to the different coordinate system; lower resolutions of GPW should work but have not been tested.

The choice of image type and resolution is set by the helper function `set_popimage_pars`.

#### Shapefiles (countries provided; US counties must be downloaded separately)
To calculate PWD for a particular political region, the boundaries of that region must be provided using a `geopandas` shape file.

Shape files for countries of the world are provided here in the `data/shapefiles/world` directory.  These are used, e.g., by the `src/get_pwpd_country.py` helper function, which takes a single commandline argument: the three-letter country code (e.g., USA, AFG, FRA). World shapefiles were taken from the public domain [_Natural Earth Vector_ dataset](https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/) (also available on [Github](https://github.com/nvkelso/natural-earth-vector)).

Shape files for US counties should be downloaded from the [US Census](https://www2.census.gov/geo/tiger/TIGER2019/COUNTY/) (79MB) and the unzipped directory `tl_2019_us_county` should be placed in the `data/shapefiles/UScounties` directory.  
