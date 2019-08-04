# ArcPyProcessingToolbox
A toolbox for bulk processing NetCDFs in ArcPy/ArcMap

This is a toolbox front end for geoprocessing generic NOAA Reanalysis V2c data (precipitation, layer one) in mass.

It is currently used for processesing and matching geospatial raster data (in the form of NetCDF files) to shapefile features--points or shapes. Importantly, this code is meant to process 100+ years of daily weather data and match to (potentially) thousand of shapefile points or shapes.

Toolbox 1 - Converts NetCDF raw NOAA files to raster TIFFs. ~40 hours for ~100 years of daily data.

Toolbox 2a - Bulk extracts raster values to points. ~ 30 hour per 25 years of daily data.

Toolbox 2b - Bulk Exports shapes to CSVs. ~ 30 hour per 25 years of daily data.

Toolbox 3 - Bulk extracts values to shapes.

Toolbox 4 - Combines CSVs into common file.
