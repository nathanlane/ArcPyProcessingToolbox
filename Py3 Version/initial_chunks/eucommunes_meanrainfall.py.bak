#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Run country-level spatial statistics in ArcPy
"""

__author__ = "Nathan Lane"
__email__ = "nathan.lane@gmail.com"

# Created by Nathan on April 16, 2018
# Project: May 1

import arcpy, os, datetime, sys, numpy, re, time
from arcpy.sa import *
import pandas

######################################################################################
# DEFINE HELPER FUNCTIONS

# Two functions for turning off/on printing for testing.
def blockprint():
    sys.stdout = open( os.devnull , 'w' )
def enableprint():
    sys.stdout = sys.__stdout__

# Grab and parse the filename.
def cleanfilename( rasterfileinput ):

    '''
    Clean the input name.

    :param rasterfileinput:
    :return cleanedfilename:
    '''

    # Grab root/file of the path:
    path, file = os.path.split( rasterfileinput )

    return os.path.splitext( file )[0]

# Get file name.
def getfileyear( filename ):

    '''
    Grab each file year from the file name.

    :param filename:
    :return fileyear:
    '''

    # Grab first 4 numbers from cleaned file name:
    fileyear = re.findall( r'(\d{4}$)' , filename )

    # Re.findall gets a list, but it's only 1 object.
    # ... grab first object (0), convert to number, overwrite
    fileyear = int( fileyear[0] )

    return fileyear


# Grab matching raster files from a list of rasters.
def getrasters(fileyear,
               allrasters):

    '''
    Helper function for tiff file list.

    :param fileyear:
    :param allrasters:
    :return tifffilepaths:
    '''

    # Get strings matching year:
    stringtomatch = ".*{0}.*".format(str(fileyear))

    # Grab a list filepaths and filenames using the file year.
    matchedrasters = filter(lambda rasterfile: re.match(stringtomatch, rasterfile),
                            allrasters)

    matchedpath = filter(lambda rasterpath: re.match(stringtomatch, rasterpath),
                          listofnoaapaths)

    # Make list comprehension.
    tifffilepaths = [os.path.join(matchedpath[0], raster) for raster in matchedrasters]

    return tifffilepaths

# Grab right output subdirectory.
def getsubfile(fileyear, listofoutputsubpaths):
    '''

    Grab a the right subfile we'll assemble files from.

    :param fileyear:
    :param listofoutputsubpaths:
    :return: matchedsubpath
    '''

    # Get strings matching year:
    stringtomatch = ".*{0}.*".format(str(fileyear))

    matchedsubpath = filter(lambda rasterpath: re.match(stringtomatch, rasterpath),
                         listofoutputsubpaths)

    return matchedsubpath


# Grab matching raster files from a list of rasters.
def getarrays(outputsubfile):

    '''
    Helper function for NumPy array file list.

    :param fileyear:
    :param listofoutputsubpaths:
    :return arrayfilepaths:
    '''

    # Make list comprehension.
    matchedarrays = [array for array in os.listdir(outputsubfile[0]) if array.endswith('.npy') ]

    return matchedarrays


# Making data output directory for our data project:
def makedataoutputdirectory( dataprojectstring ):

    '''
    Makes a clean output directory for the outputs.

    :param dataprojectstring:
    :return:
    '''

    # Our new path is the global output path + string
    newdatapath = os.path.join( outputpath ,
                                dataprojectstring )

    # Now try making directory if it doesn't exist:
    try:
        os.makedirs( newdatapath )

    except OSError:
        if not os.path.isdir( newdatapath ):
            raise

    return newdatapath


# Grab values matching the points.
def extractvaluesatpoints(rasterperiodfile):

    '''
    Process the raster using points.

    :param inputshapefile, rasterperiodfile:
    :return:
    '''

    start = time.time()

    # Grab file date use this to limit scope of the loop.
    cleanedfilename=cleanfilename(rasterperiodfile)

    # Define zonal table name, which we keep "in_memory"...
    pointfilename='_'.join(["pointfile", cleanedfilename])
    pointfile=r'in_memory\{}'.format(pointfilename)

    # Grab values associated with points.
    # NOTE: Use only "VALUE_ONLY", else we'll have errors.
    ExtractValuesToPoints('eu_commune_points',
                          rasterperiodfile,
                          pointfile,
                          'NONE',
                          'VALUE_ONLY')

    # Export features to a NumPy array:
    numpy_array = arcpy.da.FeatureClassToNumPyArray(pointfile,
                                                    numpyfields,
                                                    skip_nulls=False)

    # Save the NumPy array:
    daily_tablename = ''.join([pointfilename, '.npy'])
    daily_tablenamepath = os.path.join(outputsubfile[0], daily_tablename)
    numpy.save(daily_tablenamepath, numpy_array)

    # Clean-up environment.
    arcpy.Delete_management(pointfile)

    # Print processing time to give you a sense of progress.
    print cleanedfilename
    print(time.time() - start)


# For each NumPy array, convert them into a dataframe.
def process_numpyarrays_to_dataframe(arrayfile):

    '''
    Get the array file and save them.

    :param arrayfile:
    :return: array_dataframe
    '''

    # Start timer:
    start = time.time()

    ## Process the arrays.

    # Create path:
    fullarraypath = os.path.join(annualoutputsubfile[0],arrayfile)

    # Load the array.
    array_numpy = numpy.load(fullarraypath)

    # Feed the array-list.
    array_dataframe = pandas.DataFrame.from_records(array_numpy.tolist(),
                                          columns = array_numpy.dtype.names)

    ## Grab numbers to the files.

    # Numbers:
    numbers = re.findall('\d+', arrayfile)

    # Join the numbers together with a dash:
    date_string = '-'.join(numbers)

    # Add date string to a date variable:
    array_dataframe['date'] = date_string

    print(time.time() - start)
    return array_dataframe



########################################################
# DEFINE MAIN FUNCTION.

def main():

    '''
    Executes the main ArcPy processing pipeline
    using the functions we defined above.
    '''

    ### A. Setup ArcPy and main environment.

    # Core global variables:
    workingpath = os.path.join('c:' + os.sep, 'Users', 'nlane')
    arcgispath = os.path.join(workingpath, 'Documents', 'ArcGIS', '20180127')
    #inputpath = os.path.join(arcgispath, 'input')
    outputpath = os.path.join(arcgispath, 'output')
    dropboxprojectpath = os.path.join(workingpath, 'Dropbox', 'MAY1')

    # Prepare the ArcGIS environment
    arcpy.CheckOutExtension( "Spatial" )
    arcpy.env.workspace = r'in_memory'
    arcpy.env.overwriteOutput = True
    arcpy.env.parallelProcessingFactor = "100%"

    # Set the scratchWorkspace environment to local file geodatabase
    arcpy.env.scratchWorkspace = os.path.join(arcgispath, "scratch")
    scratch_gdb = arcpy.env.scratchGDB


    ### B. Set global parameters.

    # Define a list of the NOAA folder names:
    typeofnoaafile = "prate"

    # Start and end year:
    startyear, endyear = 1851, 2015

    # Define fields in shapefile for use in dataframe:
    numpyfields = ["FID", "SHAPE@XY", "OBJECTID_1",
                   "OBJECTID", "COMM_ID", "Shape_Leng",
                   "ORIG_FID", "RASTERVALU"]


    ### C.Create feature layers for the points.

    # In this Python project, we use raster files from the OUTPUT directory.
    inputrasterpath = os.path.join(arcgispath, "output")

    # Shapefiles and its path we'll use (country-level):
    inputshapepath = os.path.join(dropboxprojectpath,
                                  'ARCGIS',
                                  'reprojected')
    inputshapefilepath = os.path.join(inputshapepath,
                                      r'COMM_RG_01M_2013_eucommunes_centroids_reprojected.shp')

    # Make feature layer from the input shape.
    arcpy.MakeFeatureLayer_management(inputshapefilepath,
                                      'eu_commune_points')
    arcpy.Describe('eu_commune_points').spatialReference.name


    ### D. Setup lists to use for data processing.

    ## Generate a list of files we'll be using for the project.
    listofnoaafiles = [".".join([typeofnoaafile,str(i)]) for i in xrange(startyear, endyear)]
    listofnoaapaths = [os.path.join(outputpath, path) for path in listofnoaafiles]
    allrasters = [raster for path in listofnoaapaths for raster in os.listdir(path) if raster.endswith('.tif')]


    ## Generate annual output path, sub-files for the project.

    # Make the project-specific output path.
    newoutputdatapath = makedataoutputdirectory("annualeucommune_test")

    # Make type X annual sub-files.
    listofoutputsubpaths = [os.path.join(newoutputdatapath, file) for file in listofnoaafiles]
    [os.makedirs(path) for path in listofoutputsubpaths if not os.path.isdir(path)]


    ### 1. MAIN LOOP FOR EXTRACTING DAILY RASTER VALUES.

    # Loop over the files saved in the raster paths.
    for fileyear in xrange(startyear, endyear):

        # Grab list of rasters matching year.
        tiffiles = getrasters(fileyear, allrasters)

        # Grab output subfile:
        outputsubfile = getsubfile(fileyear, listofoutputsubpaths)

        # The inner loop:
        map(extractvaluesatpoints, tiffiles)


    ### 2. MAIN LOOP OVER SAVED NUMPY FILES TO DATAFRAME.

    # Loop over saved annual NumPy arrays, assemble into files.
    for fileyear in xrange(startyear, endyear):

        # Grab output subfile:
        annualoutputsubfile = getsubfile(fileyear, listofoutputsubpaths)

        arrayfilelist = getarrays(annualoutputsubfile)

        # Create a list of arrays converted to dataframes:
        dataframelist = (process_numpyarrays_to_dataframe(array) for array in  arrayfilelist)

        # Concatenate list of dataframes:
        combined_dataframe = pandas.concat(dataframelist)

        # Save combined list:
        combined_dataframe.to_csv(newoutputdatapath, combined_dataframe, sep=',')

        # Clean up.
        del combined_dataframe, dataframelist, arrayfilelist, annualoutputsubfile


# Execute main functional:
if __name__ == "__main__":
    main()