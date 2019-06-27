# Import Requried Libraries
import arcpy
from arcpy.sa import *
import os, sys, string, gc
from fnmatch import fnmatch

# Get user defined variables from ArcGIS tool GUI

root = arcpy.GetParameterAsText(0)      # Input Folder
ptshp = arcpy.GetParameterAsText(1)     # Input Point Shapefile
ptvf = arcpy.GetParameterAsText(2)      # Point Value Field
ptinter = arcpy.GetParameter(3)         # Interpolate values at point locations
pgshp = arcpy.GetParameterAsText(4)     # Input Polygon Shapefile
pgvf = arcpy.GetParameterAsText(5)      # Polygon Value Field
pgsf = arcpy.GetParameterAsText(6)      # Polygon Split Field

# Define local variables for calculating statistics
if ptinter == True:
    ptinterval = "INTERPOLATE"
else:
    ptinterval = "NONE"

# Enforce the value field selection for each shapefile (if defined)

if ptshp:
    if not ptvf:
        arcpy.AddMessage("ERROR: Please select a unique values field from point shapefile")
        arcpy.AddMessage("ERROR: Process will now terminate")
        quit()

if pgshp:
    if not pgvf:
        arcpy.AddMessage("ERROR: Please select a unique values field from Polygon shapefile")
        arcpy.AddMessage("ERROR: Process will now terminate")
        quit()   

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
            
fc_count = len(lTIFs)
            
# Loop through each raster file and calculate statistics
for tif in lTIFs:
    tifpath, tifname = os.path.split(tif)       # Split filenames and paths
    
    # Set the Progressor
    arcpy.SetProgressor("step", "Processing Tiff Files ...",
                        0, fc_count,1)

    ##############################################################
    ## Start process to calulate statistics for point shapefile ##
    ##############################################################
    
    if ptshp:

        ###################################################################
        ## Definition of variables related to Point Shapefile Processing ##
        ###################################################################
        
        ptout = tif.replace('.tif', '.shp')         # Full name & Path of temp output point shp
        ptcsv = tifname.replace('.tif', '_pt.csv')  # Define output csv file (add _pt after filename)
        ptcsv = ptcsv.replace('prate_', '')         # Finalize CSV name by stripping "prate_"
        tbloutfield = ptcsv.split('.')[0]           # Get output csv filname without extension
        tbloutfield = tbloutfield.replace('_pt', '')# Strip _pt from name
        tbloutfield = "d"+tbloutfield[1:]           # Replace first char of date(year) by "d" to overrule a restriction

        # Start Process

        # Update the progressor label for current tif file
        arcpy.SetProgressorLabel("Processing {0}...".format(tifname))

        # Delete temporary point shapefile if already exists
        if os.path.exists(ptout):
            arcpy.Delete_management(ptout)

        # Compute statistics only if output CSV file doesn't exist
        if not os.path.exists(os.path.join(tifpath, ptcsv)):
     
            arcpy.AddMessage('Calculating point statistics for ' + tifname)
            arcpy.sa.ExtractValuesToPoints(ptshp, tif, ptout,
                              ptinterval, "VALUE_ONLY")

            # Delete unnecessary fields and rename the statistics field to date
##            arcpy.AddMessage("  Dropping and renaming fields")
            fieldList = arcpy.ListFields(ptout)  #get a list of temp point shp fields 
            for field in fieldList: #loop through each field
                if field.name == 'RASTERVALU':  #look for the name RASTERVALU                    
                    arcpy.AddField_management(ptout, tbloutfield, "DOUBLE", "", "", "", "", "NULLABLE")                     
                    arcpy.CalculateField_management(ptout, tbloutfield, "!RASTERVALU!", "PYTHON")
                    arcpy.DeleteField_management(ptout, "RASTERVALU")
                else:
                    if not (field.name == ptvf or field.name == "FID" or field.name == "Shape"):
                        try:
                            arcpy.DeleteField_management(ptout, field.name)
                        except:
                            arcpy.AddMessage("Error Deleting Field " + field.name)

            # Convert shapefile to CSV
##            arcpy.AddMessage("  Writing " + ptcsv)
            arcpy.TableToTable_conversion(ptout, tifpath, ptcsv)
            arcpy.Delete_management(ptout)
            
        else:
            arcpy.AddMessage('Output already exists. Skipping ' + tifname)

        # Update the Progressor position
        arcpy.SetProgressorPosition()
        
        del ptcsv
        del ptout
        del tbloutfield
        gc.collect()
        
    ################################################################
    ## Start process to calulate statistics for polygon shapefile ##
    ################################################################
        
    if pgshp:

        #####################################################################
        ## Definition of variables related to Polygon Shapefile Processing ##
        #####################################################################

        pgcsv = ptcsv.replace('_pt.csv', '_pg.csv')
        pgdbf = ptcsv.replace('_pt.csv', '_pg.dbf')
        pgcsvp = os.path.join(tifpath, pgcsv)
        inTables = []

        # Start Process

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
        gc.collect()
        for tbl in inTables:
            arcpy.Delete_management(tbl)
    
    arcpy.ResetProgressor()
       

