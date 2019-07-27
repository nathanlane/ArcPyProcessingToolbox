# Import Requried Libraries
import arcpy
from arcpy.sa import *
import os, sys, string
from fnmatch import fnmatch

# Get user defined variables from ArcGIS tool GUI

root = arcpy.GetParameterAsText(0)      # Input Folder
ptshp = arcpy.GetParameterAsText(1)     # Input Point Shapefile
ptvf = arcpy.GetParameterAsText(2)      # Point Value Field
delshp = arcpy.GetParameter(3)         # Interpolate values at point locations

# Set Workspace to input folder
arcpy.env.workspace = root

# Enable overwriting
arcpy.env.overwriteOutput = True

# Define variables related to shpf files in the input folder
pattern = "prate_*.shp"                 # Pattern that will be used to find & prepare a list of raster files
SHPs = []                              # Create a blank list that would be populated by input geoshpf files later

# Prepare a list of geoshpf files matching the defined pattern from input folder

for path, subdirs, files in os.walk(root):
    for name in files:
        if fnmatch(name, pattern):
            SHP = os.path.join(path, name)
            SHPs.append(SHP)            
            
# Loop through each raster file and calculate statistics
for shp in SHPs:
    shppath, shpname = os.path.split(shp)       # Split filenames and paths       
    
    ptcsv = shpname.replace('.shp', '_pt.csv')  # Define output csv file (add _pt after filename)
    ptcsv = ptcsv.replace('prate_', '')         # Finalize CSV name by stripping "prate_"
    tbloutfield = ptcsv.split('.')[0]           # Get output csv filname without extension
    tbloutfield = tbloutfield.replace('_pt', '')# Strip _pt from name
    tbloutfield = "d"+tbloutfield[1:]           # Replace first char of date(year) by "d" to overrule a restriction
   
    ##############################################################
    ## Start process to calulate statistics for point shapefile ##
    ##############################################################
    

    # Compute statistics only if output CSV file doesn't exist
    if not os.path.exists(os.path.join(shppath, ptcsv)):
        arcpy.AddMessage('Processing ' + shpname)        

        # Delete unnecessary fields and rename the statistics field to date
        arcpy.AddMessage("  Dropping and renaming fields")
        fieldList = arcpy.ListFields(shp)  #get a list of point shp fields 
        for field in fieldList: #loop through each field
            if field.name == 'RASTERVALU':  #look for the name RASTERVALU                    
                arcpy.AddField_management(shp, tbloutfield, "DOUBLE", "", "", "", "", "NULLABLE")                     
                arcpy.CalculateField_management(shp, tbloutfield, "!RASTERVALU!", "PYTHON")
                arcpy.DeleteField_management(shp, "RASTERVALU")
            else:
                if not (field.name == ptvf or field.name == "FID" or field.name == "Shape"):
                    try:
                        arcpy.DeleteField_management(shp, field.name)
                    except:
                        arcpy.AddMessage("Error Deleting Field " + field.name)

        # Convert shapefile to CSV
        arcpy.AddMessage("  Writing " + ptcsv)
        arcpy.TableToTable_conversion(shp, shppath, ptcsv)
        arcpy.Delete_management(shp)            
    else:
        arcpy.AddMessage('Output already exists. Skipping ' + shpname)

    # Perform Cleanup
    if delshp == True:
        arcpy.Delete_management(shp)
        
    del shp
    del ptcsv
    del tbloutfield

    
        
    

       

