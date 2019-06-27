import os, pandas
myfiles=[]
path = "" #Your Directory containing CSV files
filename = "" #Define your output/merged csv filename
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith(".csv"):
             myfiles.append(os.path.join(root, file))
##print myfiles
dataframes = [ pandas.read_csv( f ) for f in myfiles ] # add arguments as necessary to the read_csv method
mydfs = [df.drop('OID', axis =1) for df in dataframes]
merged = reduce(lambda left,right: pandas.merge(left,right,on='COMM_ID', how='outer'), mydfs)
result = merged.to_csv(os.path.join(path,filename))
