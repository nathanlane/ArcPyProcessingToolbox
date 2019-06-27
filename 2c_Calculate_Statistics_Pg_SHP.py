# Import Requried Libraries
import arcpy
from arcpy.sa import *
import os, sys, string
from fnmatch import fnmatch

# Get user defined variables from ArcGIS tool GUI

root = arcpy.GetParameterAsText(0)      # Input Folder
pgshp = arcpy.GetParameterAsText(1)     # Input Polygon Shapefile
pgvf = arcpy.GetParameterAsText(2)      # Polygon Value Field
pgsf = arcpy.GetParameterAsText(3)      # Polygon Split Field

# List of all shapefiles in the workspace
shps = arcpy.ListFiles("*.shp")

# If splitted shapefiles not already exist
if not shps:

    # Start procedure to split input shapefiles
    fgdb = root + os.sep + "fGDB.gdb"
    fcname = os.path.split(pgshp)[1]
    fcname = fcname.replace('.shp', '')
    infc = fgdb + os.sep + fcname

    # Create File GDB
    if not arcpy.Exists(fgdb):
        arcpy.CreateFileGDB_management(root, "fGDB.gdb")

    # Convert input polygon shp to feature class
    arcpy.FeatureClassToGeodatabase_conversion(pgshp, fgdb)

    # Split shapefile by unique field into layers
    arcpy.AddMessage("Splitting polygon shapefile")
    arcpy.SplitByAttributes_analysis(infc, root, pgsf)

    # Delete file Geodatabase
    if arcpy.Exists(fgdb):
        arcpy.Delete_management(fgdb)

# Set Workspace to input folder
arcpy.env.workspace = root

# Enable overwriting
arcpy.env.overwriteOutput = True

# Define variables related to tiff files in the input folder
pattern = "prate_*.tif"                 # Pattern that will be used to find & prepare a list of raster files
lTIFs = []                              # Create a blank list that would be populated by input geotiff files later

# Prepare a list of geotiff files matching the defined pattern from input folder

for path, subdirs, files in os.walk(root):
    for name in files:
        if fnmatch(name, pattern):
            TIF = os.path.join(path, name)
            lTIFs.append(TIF)
      
# Loop through each raster file and calculate statistics
for tif in lTIFs:
    tifpath, tifname = os.path.split(tif)       # Split filenames and paths
   

    #####################################################################
    ## Definition of variables related to Polygon Shapefile Processing ##
    #####################################################################

    pgcsv = tifname.replace('.tif', '_pg.csv')    
    pgdbf = tifname.replace('.tif', '_pg.dbf')
    tbloutfield = tifname.split('.')[0]                 # Get tif filname without extension
    tbloutfield = tbloutfield.replace('prate_', '') # Strip prate_ from name
    tbloutfield = "d"+tbloutfield[1:]               # Replace first char of date(year) by "d" to overrule a restriction
    pgcsvp = os.path.join(tifpath, pgcsv)
    inTables = []
    
        
    ################################################################
    ## Start process to calulate statistics for polygon shapefile ##
    ################################################################
        
    if pgshp:

        arcpy.AddMessage('Processing ' + tifname)
        try:
            arcpy.Delete_management("tempras")
        except:
            continue
        arcpy.Resample_management(tif, "tempras", "0.04 0.04", "NEAREST")
        # list all fcs in workspace
        fcs = arcpy.ListFiles("*.shp")
        for fc in fcs:           
      
            sfcname = fc.replace('.shp', '')        # Splited shapefile name without extension
            
            pgtmpdbf = fc.replace('.shp', '_pg_')   # Prepare temporary table name that'll contain mean values
            pgtmpdbf = pgtmpdbf + sfcname + '.dbf'  # Finalize temporary table name
            arcpy.AddMessage('Calculating Polygon statistics for ' + sfcname)

            ZonalStatisticsAsTable(fc, pgvf, "tempras", pgtmpdbf, "DATA", "MEAN")
            arcpy.AddField_management(pgtmpdbf, "NUTS_ID1", "TEXT", field_length="5")
            arcpy.CalculateField_management(pgtmpdbf, "NUTS_ID1", '!NUTS_ID!', "PYTHON_9.3")
            arcpy.AddField_management(pgtmpdbf, tbloutfield, "DOUBLE", "", "", "", "", "NULLABLE")
            arcpy.CalculateField_management(pgtmpdbf, tbloutfield, '!MEAN!', "PYTHON_9.3")
            pgfieldList = arcpy.ListFields(pgtmpdbf)  #get a list of temp point shp fields 
            for pgfield in pgfieldList: #loop through each field                
                if not (pgfield.name == "OID" or pgfield.name == "NUTS_ID1" or pgfield.name == tbloutfield):
                    try:
                        arcpy.DeleteField_management(pgtmpdbf, pgfield.name)
                    except:
                        arcpy.AddMessage("Error Deleting Field " + pgfield.name)

            inTables.append(pgtmpdbf)

        arcpy.AddMessage('Merging temp tables into ' + pgdbf)
        arcpy.Merge_management(inTables,pgdbf)
        arcpy.TableToTable_conversion(pgdbf, root, pgcsv)
        arcpy.Delete_management(pgdbf)
        arcpy.Delete_management("tempras")
        for tbl in inTables:
            arcpy.Delete_management(tbl)
    

       

