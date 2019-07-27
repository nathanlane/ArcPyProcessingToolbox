#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Run country-level spatial statistics in ArcPy.

This processes aggregates for only country-level data.
"""

__author__ = "Nathan Lane"
__email__ = "nathan.lane@gmail.com"

# Created by Nathan on April 16, 2018
# Project: May 1
import arcpy, os, datetime, sys, numpy, re, time
from arcpy.sa import *


######################################################################################
# DEFINE HELPER FUNCTIONS

# Two functions for turning off/on printing for testing.
def blockprint():
    sys.stdout = open( os.devnull , 'w' )

def enableprint():
    sys.stdout = sys.__stdout__


# Grab and parse the file name
def cleanfilename( rasterfileinput ):

    '''
    Clean the input name.

    :param rasterfileinput:
    :return cleanedfilename:
    '''

    # Grab root/file of the path:
    path, file = os.path.split( rasterfileinput )

    return os.path.splitext( file )[0]


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

def getrasters(fileyear,
               allrasters):

    '''
    Helper function for tiff file list.



    :param fileyear:
    :param allrasters:
    :return tiffpaths:
    '''

    # Get
    stringtomatch = ".*{0}.*".format(str(fileyear))

    # Grab a list filepaths and filenames using the file year.
    matchedrasters = [rasterfile for rasterfile in allrasters if re.match(stringtomatch, rasterfile)]

    matchedpath = [rasterpath for rasterpath in listofnoaapaths if re.match(stringtomatch, rasterpath)]

    # Make list comprehension.
    tifffilepaths = [os.path.join(matchedpath[0], raster) for raster in matchedrasters]

    return tifffilepaths


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

    return( newdatapath )



def makecountryshapefile(inputshapefilepath):

    # Manage the shapefiles; make a feature layer.
    inputshapefile = os.path.join(inputshapefilepath, "countries.shp")
    arcpy.MakeFeatureLayer_management(inputshapefile, "countries_lyr")
    shapefile_inmemorypath = r"in_memory\country.shp"
    arcpy.CopyFeatures_management( "countries_lyr" , shapefile_pathinscratch)

    return shapefile_inmemorypath


def processzonalstatistics(rasterperiodfile):

    '''
    Get/process the raster .TIF file.

    :param inputshapefile, rasterperiodfile:
    :return:
    '''

    start = time.time()

    # Grab file date use this to limit scope of the loop.
    cleanedfilename=cleanfilename(rasterperiodfile)

    # Define zonal table name, which we keep "in_memory"...
    zonalfile='_'.join(["zonaltable", cleanedfilename])
    zonalstaticstablename=r'in_memory\{}'.format(zonalfile)

    # Calculate zonal statistics:
    ZonalStatisticsAsTable(inputshapefile,
                           "OBJECTID",
                           rasterperiodfile,
                           zonalstaticstablename,
                           "DATA",
                           "ALL")

    # Add and populate a date field for each raster.
    # Date string taken from filename.
    arcpy.AddField_management(zonalstaticstablename,
                              "date",
                              "TEXT")

    arcpy.CalculateField_management(zonalstaticstablename,
                                    "date",
                                    "'{0}'".format(cleanedfilename),
                                    "PYTHON")

    # Print processing time to give you a sense of progress.
    print((time.time() - start))


def export_rasterstats_as_annual_table(fileyear):

    '''
    Collect the raster tables in memory, stack them,
    and export them as a table.

    :param fileyear: (stack of tables in environment)
    :return: (exports main table)
    '''

    # List all tables in the current workspace:
    zonaltablelist = arcpy.ListTables()

    print(("Merging table for %s" % fileyear))

    # Generate the filename:
    annualtablename = ''.join([typeofnoaafile, str(fileyear), '.dbf'])
    annualtablefile = os.path.join(newoutputdatapath, annualtablename)

    # Merge tables, which are saved as dbf file:
    arcpy.Merge_management(zonaltablelist, annualtablefile)


######################################################################################

# Finally define main function.
def main():

    '''
    Executes the main ArcPy processing pipeline
    using the functions we defined above.
    '''

    ##### A - Header content.

    # Core global variables:
    workingpath = os.path.join('c:' + os.sep, 'Users', 'nlane')
    arcgispath = os.path.join(workingpath, 'Documents', 'ArcGIS', '20180127')
    inputpath = os.path.join(arcgispath, 'input')
    outputpath = os.path.join(arcgispath, 'output')

    # Setup our ArcPy Environment
    # Prepare the ArcGIS environment
    arcpy.CheckOutExtension( "Spatial" )
    arcpy.env.workspace = r"in_memory"
    arcpy.env.overwriteOutput = True

    # Create scratch workspace for inputs.
    arcpy.CreateFileGDB_management(outputpath, "countrymeanrainfall.gdb")
    arcpy.env.scratchWorkspace = os.path.join(outputpath, "countrymeanrainfall.gdb")
    scratchpath = arcpy.env.scratchWorkspace

    # In this Python project, we use raster files from the OUTPUT directory.
    inputrasterpath = os.path.join(arcgispath, "output")

    # Shapefile we'll use (country-level):
    inputshapefilepath = os.path.join(inputpath, "DIVAS")
    inputshapefile = os.path.join(inputshapefilepath, "countries.shp")



    ##### B - Set parameters.

    # But first create an output folder for project:
    newoutputdatapath = makedataoutputdirectory( "annualcountrypratedata_test" )

    # Define a list of the NOAA folder names:
    typeofnoaafile = "prate"

    # Start and end year:
    startyear, endyear = 1851, 2015


    ##### C - Setup lists to use for data processing

    # Generate a list of files we'll be using for the project.
    listofnoaafiles = [".".join([typeofnoaafile,str(i)]) for i in range(startyear, endyear)]

    # Remove corrupted file from list: issues with PRATE 1899 files...
    try:
        listofnoaafilenames.remove('prate.1899.nc')
    except:
        pass

    listofnoaapaths = [os.path.join(outputpath, path) for path in listofnoaafiles]
    allrasters = [raster for path in listofnoaapaths for raster in os.listdir(path) if raster.endswith('.tif')]


    ##### D - Run our loop for each NOAA file:

    year_iterable=iter(range(startyear, endyear))

    # Loop over the files saved in the raster paths:
    for fileyear in year_iterable:


        # Skip forward if the year is 1899.
        try:

            # Getgrab list of rasters matching year.
            tiffiles = getrasters(fileyear, allrasters)

            # Process the file of raster TIFs. (Replacement inner loop.)
            list(map(processzonalstatistics, tiffiles))

            # Export tables.
            export_rasterstats_as_annual_table(fileyear)

            # Cleanup.
            arcpy.Delete_management("in_memory")

            pass

        # Skip if something goes wrong
        # Specifically, if year is 1899:
        except:

            continue


# Execute main functional:
if __name__ == "__main__":
    main()