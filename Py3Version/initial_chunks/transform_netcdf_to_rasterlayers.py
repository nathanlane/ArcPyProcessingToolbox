# !/usr/bin/python
# -*- coding: utf-8 -*-
"""Run process NetCDFs to rasters in Python. Batch."""

__author__ = "Nathan Lane"
__email__ = "nathan.lane@gmail.com"

# Created by Nathan on April 03, 2018
# Project: May1

import arcpy, os, itertools, datetime, sys, numpy, re
from arcpy.sa import *


################################################ I. DEFINE HELPER FUNCTIONS


################ 1. Helper functions.
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

def enablePrint():
    sys.stdout = sys.__stdout__


def unzip(iterable):
    return list(zip(*iterable))


def setup_arcpyenvironment():
    '''
    Setup the ArcPy stuff, required for
    to run ArcMap jobs in Python.

    ArcPy requires us to setup an environment.
    :return:
    '''


    # Prepare the ArcGIS environment
    arcpy.AddMessage(arcpy.ProductInfo())
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.parallelProcessingFactor = "100%"

    # Setup workspace and project management:
    arcpy.env.workspace = "in_memory"
    arcpy.env.overwriteOutput = True



################ 2. Functions for preparing NetCDF files, outputs, etc. for loops.

def get_listofnetcdfs(startyear, endyear):

    '''
    Generate a list of files that we'll process.
    '''

    # Create list of NOAA files using list comprehension and fast concatination:
    listofnoaafilenames = ['.'.join(map(str, [noaafile_type, fileyear, 'nc'])) for
                           fileyear in range(startyear, endyear)]

    # Remove corrupted file from list.
    # There are issues with PRATE 1899 files...
    try:
        listofnoaafilenames.remove('prate.1899.nc')
    except:
        pass

    # Attach input path to NetCDF file names.
    clean_listofnoaapaths = [os.path.join(inputpath, file) for file in listofnoaafilenames]

    # Return list of files.
    return clean_listofnoaapaths, listofnoaafilenames


def prepare_rasterpaths(listofnoaafilenames):
    '''
    Prepare directories for each of the NetCDF files.

    Take list of the NetCDF file names (only) and create output paths.

    This is where rasters are stored.
    '''

    # Generate new output paths from filename lists.
    newoutputfilepaths = [os.path.join(outputpath, os.path.splitext(file)[0]) for
                          file in listofnoaafilenames]

    # Make list of directories.
    [os.makedirs(path) for path in newoutputfilepaths if not os.path.isdir(path)]

    return newoutputfilepaths


def make_iterators(listofnoaapaths, listofnewouputpaths):
    '''
    Creates tuples of NetCDF files AND top bands for the main loop
    of the code.

    I'm using a generator since the NetCDF files can be large.

    :param listofnoaafiles
    :return: tuples of TOP bands and NetCDF files
    '''

    netcdffiles = [arcpy.NetCDFFileProperties(file) for file in listofnoaapaths]

    # Get number of bands in the time dimension_type.
    # Do it directly with the getDim... function!
    topbands = [netcdffile.getDimensionSize('time') for netcdffile in netcdffiles]

    # Convert list of output path to generator:
    outputpaths = [path for path in listofnewouputpaths]

    # Chain together three lists: the NetCDF files, bands, and output path:
    return topbands, netcdffiles, listofnoaapaths, outputpaths


################ 3. Core "INNER" functions for processing, exporting NetCDF bands.

def sub_processdatesfromnetcdf(dimensionargument):
    '''
    Within the inner NetCDF processing loop we efficiently
    process the date object extracted from the label.

    I use a list comprehension to do this efficiently,
    and return the split strings.
    '''

    datestring = str(dimensionargument)
    filemonth, fileday, fileyear = [str(chunk) for chunk in datestring.split('/')]

    return filemonth, fileday, fileyear


def sub_getdatefromcurrentband(netcdffile, dateband):
    '''
    With current NetCDF, use current date band and
    extract the date and string date value (09/09/99)
    and (time 09/09/99).

    This is a key function! It uses ArcPy NetCDF function
    to directly extract dates instead of guessing.

    :param netcdffile:
    :param dateband:
    :return: dimension_date, dimension_value:
    '''

    # Extract dates used in each NetCDF slice--e.x. 01/01/1990
    dimension_date = netcdffile.getDimensionValue(dimension_type, dateband)

    # Make string for the value of the current NetCDF time band.
    # Using a faster join command.
    dimension_value = ''.join(['time ', str(dimension_date)])

    return dimension_date, dimension_value


def exportbands(timeband,
                inputproperties,
                inputfilepath,
                outputpath):
    '''
    Within the NetCDF processing loop we create raster files
    and save them to new folders.

    Take date arguments...

    Along with the dimension value, the input file, and the
    output file.
    '''

    # Grab a string value and the date value from current band.
    dimension_date, dimension_value = sub_getdatefromcurrentband(inputproperties,
                                                                 timeband)

    # Parse date variable of current file into logical chunks.
    # The string is in the Month/Day/Year format:
    filemonth, fileday, fileyear = sub_processdatesfromnetcdf(dimension_date)

    # Make filename from year, month, and day:
    arguments = [noaafile_type, fileyear, filemonth, fileday]
    outputrastername = '_'.join(map(str, arguments))
    print(('Exporting raster {}.tif'.format(outputrastername)))

    # Take CURRENT dimensions from current NetCDF.
    # Pull current layer out as raster layer in memory named 'outfilename'.
    # rainfall (PRATE) is the value that will be mapped.
    makenetcdf = arcpy.MakeNetCDFRasterLayer_md(inputfilepath,
                                                "prate",
                                                "lon",
                                                "lat",
                                                "temporaryraster",
                                                "",
                                                dimension_value,
                                                "BY_VALUE")

    # Convert in-memory raster layer to a saved layer, also named 'outfilename'.
    outputrasterfile = os.path.join(outputpath, ''.join([outputrastername, '.tif']))
    copyraster = arcpy.CopyRaster_management("temporaryraster",
                                             outputrasterfile,
                                             "",
                                             "")

    # Print errors and delete objects from ArcPy environment,
    # ... emptying the temporary memory of the environment.
    print(copyraster.getMessages())
    print(makenetcdf.getMessages())
    arcpy.Delete_management(outputrastername)
    arcpy.Delete_management("in_memory")


def loopovernetcdfbands(toptimeband,
                        inputproperties,
                        inputfilepath,
                        outputpath):

    '''
    Process all ~365 time bands of a NetCDF file.

    This function takes four arguments:
    1) NetCDF properties
    2) The top-most time band for every NetCDF
    3) The path string for the NetCDF file
    4) The output path for the rasters.
    '''

    [exportbands(t, inputproperties, inputfilepath, outputpath) for t in range(toptimeband)]



################################################ II. MAIN PIPELINE

# Define main workflow function...
def main():

    '''
    Execute the main ArcPy processing pipeline.

    Run core functions.
    '''

    ## A - HEADER: Define global variables for project.
    workingpath = os.path.join('c:' + os.sep, 'Users', 'nlane')
    arcgisenvironmentpath = os.path.join(workingpath, 'Documents', 'ArcGIS')
    arcgispath = os.path.join(workingpath, 'Documents', 'ArcGIS', '20180127')
    inputpath = os.path.join(arcgispath, 'input')
    outputpath = os.path.join(arcgispath, 'outputtest')


    ## B - SETUP ArcPy: Setup the API for ArcGis in Python (ArcPy)
    setup_arcpyenvironment()

    # Define some variables we use for processing NetCDFs:
    # In this code, we only care about the TIME dimension.
    dimension_type = "time"

    # We're working with precipitation files:
    noaafile_type = "prate"

    # Start and end year:
    startyear, endyear = 1851, 2015


    ## C - MAIN: Functions.

    # Get list of NetCDF files (with full paths and filenames only)
    listofnoaapaths, listofnoaafilenames = get_listofnetcdfs(startyear, endyear)

    # Make directories for rasters output.
    listofnewouputpaths = prepare_rasterpaths(listofnoaafilenames)

    # Create pairs (zip) for looping over:
    iterators = make_iterators(listofnoaapaths, listofnewouputpaths)

    # Main wrapper loop: for each set of set of tuples, executes
    # a processing file and executes the processing functions.
    [loopovernetcdfbands(*args) for args in zip(*iterators)]


# Run with main function.
if __name__ == "__main__":
    main()