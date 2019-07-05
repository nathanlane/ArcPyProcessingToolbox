# Import Requried Libraries
import arcpy
from arcpy.sa import *
import os, sys, string
from fnmatch import fnmatch

# Get user defined variables from ArcGIS tool GUI

root = arcpy.GetParameterAsText(0)      # Input Folder
ptshp = arcpy.GetParameterAsText(1)     # Input Point Shapefile
ptinter = arcpy.GetParameter(2)         # Interpolate values at point locations

# Define local variables for calculating statistics
if ptinter == True:
    ptinterval = "INTERPOLATE"
else:
    ptinterval = "NONE"

# Set Workspace to input folder
arcpy.env.workspace = root

# Enable overwriting
arcpy.env.overwriteOutput = True

# Define variables related to tiff files in the input folder
pattern = "prate_*.tif"                 # Pattern that will be used to find & prepare a list of raster files
spattern = "prate_*.shp"                # Pattern that will be used to find & prepare a list of shapefiles
dpattern = "prate.*"                    # Pattern that will be used to find & prepare a list of input folders
lTIFs = []                              # Create a blank list that would be populated by input geotiff files later
mydirs = []                             # Create a blank list that would be populated by input folders later

# Create a list of child folders in the root folder containing GeoTiff Files
for path, subdirs, files in os.walk(root):
    for mydir in subdirs:
        if fnmatch(mydir, dpattern):
            mydirpath = os.path.join(path, mydir)
            mydirs.append(mydirpath)
# Delete empty shapefiles so that they may be generated anew
    for name in files:        
        if fnmatch(name, spattern):
            SHP = os.path.join(path, name)               
            if arcpy.management.GetCount(SHP)[0] == "0":
                arcpy.AddMessage('Deleting empty shapefiles if any') 
                arcpy.Delete_management(SHP)

# Prepare a list of geotiff files matching the defined pattern from input folder
for mydir in mydirs:
    for path, subdirs, files in os.walk(mydir):
        arcpy.AddMessage("\n" + 'Processing Folder ' + mydir + "\n")
        for name in files:
            if fnmatch(name, pattern):
                TIF = os.path.join(path, name)
                lTIFs.append(TIF)                 
        # Loop through each raster file and calculate statistics
        for tif in lTIFs:
            tifpath, tifname = os.path.split(tif)       # Split filenames and paths

            ###################################################################
            ## Definition of variables related to Point Shapefile Processing ##
            ###################################################################
            
            ptout = tif.replace('.tif', '.shp')         # Full name & Path of temp output point shp
           
            ##############################################################
            ## Start process to calulate statistics for point shapefile ##
            ##############################################################
            
            # Delete temporary point shapefile if already exists
            if not os.path.exists(ptout):

                arcpy.AddMessage('Processing ' + tifname)
                try:
                    arcpy.sa.ExtractValuesToPoints(ptshp, tif, ptout,
                                      ptinterval, "VALUE_ONLY")
                except:
                    arcpy.AddMessage('Error in processing ' + tifname)
            else:
                arcpy.AddMessage('Skipping ' + tifname + " (Already Exists)")

            del ptout
            del tif
        lTIFs = []
            
        

           

