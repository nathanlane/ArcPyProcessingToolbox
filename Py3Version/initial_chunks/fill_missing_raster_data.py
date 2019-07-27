#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This file is run on the directory of /PRATE.1XXX raster files--
and thus AFTER the initial NetCDF processing files.

The following programs fills in for missing raster data.
"""

__author__ = "Nathan Lane"
__email__ = "nathan.lane@gmail.com"


import arcpy, os, numpy, re, time

#############################################################################
### I. DEFINE HELPER FUNCTIONS.

# Prepare the ArcPy environment:
def setup_arcpyenvironment():

    # Setup spatial reference.
    WKID = 4326  # WGS-1984
    sr = arcpy.SpatialReference()
    sr.factoryCode = WKID
    sr.create()
    arcpy.env.outputCoordinateSystem = sr

    # Prepare the ArcGIS environment
    arcpy.CheckOutExtension( "Spatial" )
    arcpy.env.workspace = r'IN_MEMORY'
    arcpy.env.overwriteOutput = True
    arcpy.env.parallelProcessingFactor = "100%"

    # Here I set the extent clearly, since there has been weird behavior otherwise.
    # Set the extent environment using the Extent class.
    arcpy.env.extent = arcpy.Extent(-180, -90.05477905273438, 180, 88.07022094726563)


    # Make a snap raster:
    arcpy.env.snapRaster = os.path.join(outputpath,"prate.1851","prate.1851.tif")


    # Set the scratchWorkspace environment to local file geodatabase
    arcpy.env.scratchWorkspace = os.path.join(arcgispath, "scratch")
    scratch_gdb = arcpy.env.scratchGDB

    return scratch_gdb, WKID


# Here we generate path lists, rasters, etcs., for used in processing:
def make_lists_to_process():

    '''
    Using global variables, we generate form paths, files, and rasters
    before running some functions.

    :param :
    :return: all_noaanetcdf_list, all_noaapath_list, all_raster_list:
    '''

    ## Generate a list of files we'll be using for the project.
    all_noaanetcdf_list = [".".join([typeofnoaafile,str(i)]) for i in range(startyear, endyear)]
    all_noaanetcdf_list.remove(".".join([typeofnoaafile,str(1899)]))
    all_noaapath_list = [os.path.join(outputpath, path) for path in all_noaanetcdf_list]
    all_raster_list = [file for path in all_noaapath_list for file in os.listdir(path) if file.endswith('.tif')]

    return all_noaanetcdf_list, all_noaapath_list, all_raster_list


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


# Grab matching raster files from a list of rasters.
def getrasters(fileyear,
               all_raster_list):

    '''
    Helper function for tiff file list.

    :param fileyear:
    :param all_raster_list:
    :return tifffilepaths:
    '''

    # Get strings matching year:
    stringtomatch = ".*{0}.*".format(str(fileyear))

    # Grab a list filepaths and filenames using the file year.
    matchedrasters = [rasterfile for rasterfile in all_raster_list if re.match(stringtomatch, rasterfile)]

    matchedpath = [rasterpath for rasterpath in all_noaapath_list if re.match(stringtomatch, rasterpath)]

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

    matchedsubpath = [rasterpath for rasterpath in listofoutputsubpaths if re.match(stringtomatch, rasterpath)]

    return matchedsubpath


# Making data output directory for our data project:
def make_project_dataoutput_path(dataprojectstring):

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


# Core GIS function for filling in missing data.
def fill_raster_files(currentrasterfilepath):

    '''
    This function processes each daily raster.

    It takes the "current raster" file name, then

    1) creates a raster for filling in the raster gap,

    2) merges the filling raster with the main function.

    The MosaicToRaster() function in 2) saves the merged
    file automatically.

    :param currentrasterfilepath:
    :return none (saved single, filled raster layer):
    '''

    start_time = time.time()

    ## A. PREPARE FILES.

    # Grab file name from the long path string; it's on the end:
    currentrasterfilename=str.split(currentrasterfilepath,"\\")[-1]

    # Load the current raster into temporary feature layer:
    # Note: for some reason this is better than copying into memory.
    arcpy.MakeRasterLayer_management(currentrasterfilepath, "rasterlayer")


    ## B. CLIP A PIECE FROM THE RASTER

    # Note: This chunk contains the missing data: one full cell, where about 1/2 the cell
    # is the missing data, and half is the actual data.

    # Clip raster extent:
    cliprasterextent="-0.937500 -90 0.938 88.000000"

    # Clip raster function:
    # Arguments:
    # 1) input raster layer.
    # 2) clipping window.
    # 3) output raster.
    # 4) the raster environment we want to use in clipping.
    # 5) # as the no data value...
    # 6) IMPORTANTLY, we want to resample things to maintain main extent.
    arcpy.Clip_management("rasterlayer",
                          cliprasterextent,
                          "currentrasterclip",
                          os.path.join(scratch_gdb,"fillingrasterlayer"),
                          "#",
                          "NONE",
                          "MAINTAIN_EXTENT")

    # Resample, this is because the clipping produced a
    # ... 1.875 x 1.875 cell size. However, we need it to
    # better match the extent of the base raster, which is
    # 1.875 x 1.8949468.
    arcpy.Resample_management( "currentrasterclip",
                               "currentrasterclip_resampled",
                               "1.875 1.8949468",
                               "NEAREST")



    ## C. MERGE RASTER CLIP (B) AND MAIN RASTER INTO SINGLE RASTER.

    # Raster list, which the MosaicToRaster() takes as input:
    rasterlist="currentrasterclip_resampled;rasterlayer"

    # Create output file for filled raster:
    currentoutput_rasterfilename=''.join(["filledgap_",
                                          currentrasterfilename,'.tif'])

    # Function for combining filled clip and main raster:
    arcpy.MosaicToNewRaster_management(rasterlist,
                                       currentoutputpath,
                                       currentoutput_rasterfilename,
                                       WKID,
                                       "32_BIT_FLOAT",
                                       "",
                                       "1",
                                       "LAST",
                                       "LAST")


    ## CLEAN ENVIRONMENT/PRINT TIMING, PROGRESS.
    arcpy.Delete_management('IN_MEMORY')
    print((time.time() - start_time))
    print("Saving filled tif: {0}".format(currentrasterfilename))



#############################################################################
### II. MAIN FUNCTION PIPELINE, EXECUTE IT.


# Execute main pipeline:
if __name__ == "__main__":

    ### A - DEFINE global variables for project.
    workingpath = os.path.join('c:' + os.sep, 'Users', 'nlane')
    arcgisenvironmentpath = os.path.join(workingpath, 'Documents', 'ArcGIS')
    arcgispath = os.path.join(workingpath, 'Documents', 'ArcGIS', '20180127')
    inputpath = os.path.join(arcgispath, 'input')
    outputpath = os.path.join(arcgispath, 'outputtest')
    dropboxprojectpath = os.path.join(workingpath, 'Dropbox', 'MAY1')
    coreobjectpath = os.path.join(dropboxprojectpath,
                                         'ARCGIS',
                                         'reprojected')

    ### B - SETUP ArcPy AND GLOBAL VARIABLES.
    scratch_gdb, WKID = setup_arcpyenvironment()

    # Define a list of the NOAA folder names:
    typeofnoaafile = "prate"

    # Start and end year:
    startyear, endyear = 1851, 2015



    ### C - SETUP LISTS FOR INPUT AND OUTPUT DIRECTORIES (FILES)

    # Create lists to loop over: using global project paths,
    all_noaanetcdf_list, all_noaapath_list, all_raster_list = make_lists_to_process()

    # Make the project-specific output path.
    new_project_path = make_project_dataoutput_path("filled_rasters")

    # Make type X annual sub-files, if they don't exist.
    all_outputsubpaths_list = [os.path.join(new_project_path, file) for file in all_noaanetcdf_list]
    [os.makedirs(path) for path in all_outputsubpaths_list if not os.path.isdir(path)]


    ### D - LOAD FILLER OUTLINE MASK for the filling process.

    # NOTE: This is a blank raster that is used for filling "missing data"
    # in each daily raster.

    # Make the raster file path:
    filling_mask_rasterfile = os.path.join(coreobjectpath,
                                           r'fillraster_resampled.tif')

    # Load filling mask raster, copy into global scratch memory.
    arcpy.MakeRasterLayer_management(filling_mask_rasterfile,
                                     r'fillingrasterlayer')

    # Put in scratch environment, since we may want to clear IN_MEMORY environment:
    arcpy.CopyRaster_management(r'fillingrasterlayer',
                                os.path.join(scratch_gdb,
                                             'fillingrasterlayer'))


    ### E - MAIN LOOP: PROCESSES ALL DAILY FILES FOR EACH YEAR.
    startyear = 1898

    # Make iterable for the year range of the project.
    yearlist_iterable=iter(range(startyear, endyear))

    # Loop over each year.
    for fileyear in yearlist_iterable:

        # Skip forward if the year is 1899.
        try:

            # E.1 - Grab list of full tiff files for current year of loop.
            annual_raster_list = getrasters(fileyear, all_raster_list)

            # E.2 - Make output year filepath for the current year.
            # Note: combining 'prate.1888' and rest of file path:
            # Grab this from file path in file list:
            projectdirectory = str.split(annual_raster_list[0], "\\")[-2]
            currentoutputpath = os.path.join(new_project_path, projectdirectory)

            # E.3 - Inner loop for daily raster slides:
            list(map(fill_raster_files, annual_raster_list))

            pass

        # Skip if something goes wrong
        # Specifically, if year is 1899:
        except:

            continue
