# Population-weighted population density (PWPD)
## Ben Holder and Niayesh Afshordi

This repository contains a module of subroutines for calculating the population weighted population density(PWD):

<img src="https://latex.codecogs.com/gif.latex?{\rm&space;PWD}=\sum_j\frac{\left(p_j/a_j\right)p_j}{\sum_i&space;p_i}" title="{\rm PWD}=\sum_j\frac{\left(p_j/a_j\right)p_j}{\sum_i p_i}" />

For a region divided into pixels of area <i>a<sub>j</sub></i> and population <i>p<sub>j</sub></i>, the PWD provides a measure of the "lived" population density, or that experienced by the average inhabitant.

The calculation of PWD for a political region therefore relies on a high resolution dataset of population.  The code here utilizes the [Global Human Settlement Population (GHS-POP)](https://ghsl.jrc.ec.europa.eu/ghs_pop2019.php) raster image, which must be placed in the `data/ghs` sub-directory.

