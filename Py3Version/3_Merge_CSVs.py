import os, pandas, arcpy

# Get user defined variables

path = arcpy.GetParameterAsText(0)   # Input Folder
ptcsv = arcpy.GetParameterAsText(1)  # ptcsv for Point CSV
pgcsv = arcpy.GetParameterAsText(2)  # ptcsv for Polygon CSV

if not ptcsv.endswith('.csv') and ptcsv:
    ptcsv = ptcsv + ".csv"
    
if not pgcsv.endswith('.csv') and pgcsv:
    pgcsv = pgcsv + ".csv"


ptfiles=[]                           # Empty list that will contain all point CSVs
pgfiles=[]                           # Empty list that will contain all polygon CSVs


# Prepare list of all CSV files in their corresponding variables
for root, dirs, files in os.walk(path):
    for mfile in files:
        if mfile.endswith("_pt.csv"):
             ptfiles.append(os.path.join(root, mfile))
        if mfile.endswith("_pg.csv"):
             pgfiles.append(os.path.join(root, mfile))

def mergecsvs(clist, fout):
    for c in clist:
        cdataframe = pandas.read_csv( c )
        cdf = cdataframe.drop('OID', axis =1)
        if not os.path.exists(fout):
            arcpy.AddMessage('Appending ' + os.path.split(c)[1])
            cdf.to_csv(fout, index=False)
        else:
            arcpy.AddMessage('Appending ' + os.path.split(c)[1])
            fdf = pandas.read_csv(fout)
            cname = list(cdf.columns.values)[0]
            fdf[cname] = cdf[cname]
            fdf.to_csv(fout, index=False)

# Merge point CSVs if present
if (ptcsv and ptfiles):
    mergecsvs(ptfiles, ptcsv)
    
# Merge polygon CSVs if present
if (pgcsv and pgfiles):
    mergecsvs(pgfiles, pgcsv)   
