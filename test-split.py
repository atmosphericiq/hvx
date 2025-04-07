from split_line import split_line_multiple
from split_line2 import split_line_at_length_np
from osgeo import ogr, osr

# open this gpkg fed004eb-e6ac-4f72-930c-a43fc749cded.gpkg
ds = ogr.Open("fed004eb-e6ac-4f72-930c-a43fc749cded.gpkg")
lyr = ds.GetLayer()

for feature in lyr:
  geom = feature.GetGeometryRef()
  # print featur elength
  print(geom.Length())


  if geom is None:
    continue
  chunks = split_line_at_length_np(geom, 10)
  print(len(chunks))
