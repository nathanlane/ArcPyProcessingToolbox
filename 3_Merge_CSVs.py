import os, pandas, arcpy

# Get user defined variables

path = arcpy.GetParameterAsText(0)   # Input Folder
ptcsv = arcpy.GetParameterAsText(1)  # ptcsv for Point CSV
pgcsv = arcpy.GetParameterAsText(2)  # ptcsv for Polygon CSV

ptfiles=[]                           # Empty list that will contain all point CSVs
pgfiles=[]                           # Empty list that will contain all polygon CSVs

# Prepare list of all CSV files in their corresponding variables
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith("_pt.csv"):
             ptfiles.append(os.path.join(root, file))
        if file.endswith("_pg.csv"):
             pgfiles.append(os.path.join(root, file))

# Merge point CSVs if present
if (ptcsv and ptfiles):
    ptdataframes = [ pandas.read_csv( f ) for f in ptfiles ] # add arguments as necessary to the read_csv method
    ptdfs = [df.drop('OID', axis =1) for df in ptdataframes]
    ptmerged = reduce(lambda left,right: pandas.merge(left,right,on='COMM_ID', how='outer'), ptdfs)
    ptresult = ptmerged.to_csv(os.path.join(path,ptcsv))

# Merge polygon CSVs if present
if (pgcsv and pgfiles):
    pgdataframes = [ pandas.read_csv( f ) for f in pgfiles ] # add arguments as necessary to the read_csv method
    pgdfs = [df.drop('OID', axis =1) for df in pgdataframes]
    pgmerged = reduce(lambda left,right: pandas.merge(left,right,on='NUTS_ID1', how='outer'), pgdfs)
    pgresult = pgmerged.to_csv(os.path.join(path,pgcsv))
