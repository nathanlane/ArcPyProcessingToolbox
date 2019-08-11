# Import Requried Libraries
import arcpy
from arcpy.sa import *
import os, sys, string
from fnmatch import fnmatch

# Get user defined variables from ArcGIS tool GUI

root = arcpy.GetParameterAsText(0)      # Input Folder
ptshp = arcpy.GetParameterAsText(1)     # Input Point Shapefile
ptinter = arcpy.GetParameter(2)         # Interpolate values at point locations

# Set Workspace to input folder
arcpy.env.workspace = root

# Enable overwriting
arcpy.env.overwriteOutput = True

# Define variables related to tiff files in the input folder
pattern = "prate_*.tif"                 # Pattern that will be used to find & prepare a list of raster files
dpattern = "prate.*"                    # Pattern that will be used to find & prepare a list of input folders
mydirs = []                             # Create a blank list that would be populated by input folders later

# Create a list of child folders in the root folder containing GeoTiff Files
for path, subdirs, files in os.walk(root):
    for mydir in subdirs:
        if fnmatch(mydir, dpattern):
            mydirpath = os.path.join(path, mydir)
            mydirs.append(mydirpath)

# define function to calculate stats from files in a given folder
def calcstats(mydir):
    lTIFs = []                              # Create a blank list that would be populated by input geotiff files later
    for path, subdirs, files in os.walk(mydir):
        arcpy.AddMessage("\n" + 'Processing Folder ' + mydir + "\n")
        for name in files:
            if fnmatch(name, pattern):
                TIF = os.path.join(path, name)
                lTIFs.append(TIF)                 
        # Loop through each raster file and calculate statistics
        for tif in lTIFs:
            tifpath, tifname = os.path.split(tif)       # Split filenames and paths
            tbloutfield = tifname.split('.')[0]         # Get output csv filname without extension
            tbloutfield = tbloutfield.replace('prate_', '')# Strip _pt from name
            outcsv = tbloutfield + '.csv'
            tbloutfield = "d"+tbloutfield[1:]           # Replace first char of date(year) by "d" to overrule a restriction

            ###################################################################
            ## Definition of variables related to Point Shapefile Processing ##
            ###################################################################
            
            ptout = tif.replace('.tif', '.dbf')         # Full name & Path of temp output point shp
           
            ##############################################################
            ## Start process to calulate statistics for point shapefile ##
            ##############################################################
            
            # Skip if output table already exists
            if not os.path.exists(ptout):

                arcpy.AddMessage('Processing ' + tifname)
                try:
                    arcpy.ExtractValuesToTable_ga(ptshp, tif, ptout, "", "")                                
                    fmap = '{} \\\"'.format(tbloutfield) + tbloutfield + "\\\" " + "true true false 19 Double 0 0 ,First,#," + ptout + ",Value,-1,-1;SrcID_Feat \\\"SrcID_Feat\\\" true true false 10 Long 0 10 ,First,#," + ptout + ",SrcID_Feat,-1,-1"
                    arcpy.TableToTable_conversion(ptout, tifpath, outcsv, "", fmap, "")

                    # Define local variables for calculating statistics
                    if ptinter == True:
                        arcpy.Delete_management(ptout)
                        
                except:
                    arcpy.AddMessage('Error in processing ' + tifname)
            else:
                arcpy.AddMessage('Skipping ' + tifname + " (Already Exists)")

            del ptout, tif, tbloutfield, fmap, outcsv
        lTIFs = []

# Prepare a list of geotiff files matching the defined pattern from input folder
if len(mydirs) > 0:
    for mydir in mydirs:
        calcstats(mydir)
else:
    calcstats(root)
            
        

           

