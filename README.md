# Population-weighted population density (PWPD)
### Authors: Ben Holder and Niayesh Afshordi

This repository contains a module of subroutines, `src/pwpd.py`, for calculating the population weighted population density (PWD):

<img src="https://latex.codecogs.com/gif.latex?{\rm&space;PWD}=\sum_j\frac{\left(p_j/a_j\right)p_j}{\sum_i&space;p_i}" title="{\rm PWD}=\sum_j\frac{\left(p_j/a_j\right)p_j}{\sum_i p_i}" />

For a region divided into pixels of area <i>a<sub>j</sub></i> and population <i>p<sub>j</sub></i>, the PWD provides a measure of the "lived" population density, or that experienced by the average inhabitant.

## Data Sets

#### Population Raster Images (must be downloaded separately)

Calculation of PWD for a political region relies on a high resolution dataset of population.  The code here utilizes one of two [GeoTiff](https://earthdata.nasa.gov/esdis/eso/standards-and-references/geotiff) raster datasets (read with Python's [`rasterio`](https://rasterio.readthedocs.io/en/latest/) package), with the following resolution options and coordinate system options:

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

  * [30as GPW UN WPP-adjusted Population Count (2020)](https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals-rev11/data-download) (405MB)

  * [30as GPW UN WPP-adjusted Population Density (2020)](https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-adjusted-to-2015-unwpp-country-totals-rev11/data-download) (347MB)

in the following directories, respectively:

 * `data/ghs/GHS_POP_E2015_GLOBE_R2019A_54009_1K_V1_0`
 * `data/ghs/GHS_POP_E2015_GLOBE_R2019A_54009_250_V1_0`
 * `data/gpw/`
 * `data/gpw/`

Lower resolutions of GHS-POP have not yet been implemented and would require slight adjustment of the code due to the different coordinate system; lower resolutions of GPW should work but have not been tested.

The choice of image type and resolution is set by the helper function `set_popimage_pars`.

#### Shapefiles (countries provided; US counties must be downloaded separately)

To calculate PWD for a particular political region, the boundaries of that region must be provided using a [ESRI Shapefile](https://www.esri.com/library/whitepapers/pdfs/shapefile.pdf) (read with Python's [`geopandas`](https://geopandas.org) package).

Shape files for countries of the world are provided here in the `data/shapefiles/world` directory.  These are used, e.g., by the `src/get_pwpd_country.py` helper function, which takes a single commandline argument: the three-letter country code (e.g., USA, AFG, FRA). World shapefiles were taken from the public domain [_Natural Earth Vector_ dataset](https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/) (also available on [Github](https://github.com/nvkelso/natural-earth-vector)), and use the WGS84 coordinate system (EPSG:4326).

Shape files for US counties should be downloaded from the [US Census](https://www2.census.gov/geo/tiger/TIGER2019/COUNTY/) (79MB) and the unzipped directory `tl_2019_us_county` should be placed in the `data/shapefiles/UScounties` directory.  These shapefiles use the North American Datum Geographic (Lat/Lon) coordinate system (NAD83; EPSG:4269).
