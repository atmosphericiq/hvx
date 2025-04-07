import sys
import argparse
import copy
import math
import numpy as np
from multiprocessing import Pool
from multiprocessing import current_process
from osgeo import ogr
from osgeo import osr
from common.LineSegmenter import LineSegmenter
from common.LineDissolver import LineDissolver
from common.MultiLineSorter import MultiLineSorter
from field_helper import process_segment, voltage_at_distance, get_suscept
from split_line2 import split_line_at_length_np
import logging

parser = argparse.ArgumentParser()
parser.add_argument("--continuity-shapefile", type=str, required=True)
parser.add_argument("--output-shapefile", type=str, required=True)
parser.add_argument("--parallelism", type=int, required=True)
parser.add_argument("--base-height", type=int, required=True)
parser.add_argument("--powerline-file", type=str, required=True)
parser.add_argument("--resistivity-file", type=str, required=True)
parser.add_argument("--resistivity-field-name", type=str, required=True)
parser.add_argument("--decouplers-gpkg", type=str, required=True) # gpkg
parser.add_argument("--annual-survey-gpkg", type=str, required=True) # gpkg
args = parser.parse_args()

srs4326 = osr.SpatialReference()
srs4326.ImportFromEPSG(4326)
srs4326.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

srs3857 = osr.SpatialReference()
srs3857.ImportFromEPSG(3857)
transform = osr.CoordinateTransformation(srs3857, srs4326)

logging.basicConfig(level=logging.INFO)

esri_driver = ogr.GetDriverByName('FileGDB')
gpkg_driver = ogr.GetDriverByName('GPKG')

MU0 = 1.25663706212 * math.pow(10, -6)
V = 0.00266573
logging.info("setting pool size to %s" % args.parallelism)
POOL = Pool(args.parallelism)

METER_RESOLUTION = 1

def clean_voltage(voltage):
  if ';' in str(voltage):
    voltage = voltage.strip(";")[0]
  if ',' in str(voltage):
    voltage = voltage.replace(",", "")
  try:
    voltage = int(voltage)
  except:
    return None
  return voltage

logging.info("using m0 = %s" % MU0)

# load the annual survey data
# note that AC observed is TestPointInspectionACPS
logging.info("loading annual survey data")
survey_src = gpkg_driver.Open(args.annual_survey_gpkg, 0)
survey_layer = survey_src.GetLayer(0)

# load the decouplers
logging.info("loading decouplers")
decoupler_src = gpkg_driver.Open(args.decouplers_gpkg, 0)
decoupler_layer = decoupler_src.GetLayer(0)

# load the nodes
shp_source = gpkg_driver.Open(args.continuity_shapefile, 0)
num_layers = shp_source.GetLayerCount()
logging.info("found %s number of layers" % num_layers)
layer = shp_source.GetLayer(0)
total_nodes = layer.GetFeatureCount()
processed = 0

fieldnames = []
layer_def = layer.GetLayerDefn()
for n in range(layer_def.GetFieldCount()):
  field_def = layer_def.GetFieldDefn(n)
  fieldnames.append((field_def.name, field_def.type, n))

# create the output file
# open the output file and set the fields
logging.info("creating output file %s" % args.output_shapefile)
ds = esri_driver.CreateDataSource(args.output_shapefile)
out_layer = ds.CreateLayer("line", srs3857, ogr.wkbLineString)
out_layer_def = out_layer.GetLayerDefn()
for (fname, ftype, fidx) in fieldnames:
  new_field = ogr.FieldDefn(fname, ftype)
  out_layer.CreateField(new_field, ftype)
out_layer.CreateField(ogr.FieldDefn("total_flux_T", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("total_flux_uT", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("total_voltage", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("self_voltage", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("length_meters", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("amps_per_m2", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("mean_resistivity_ohm_cm", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("mean_resistivity_ohm_m", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("nace_susceptibility", ogr.OFTString))
out_layer.CreateField(ogr.FieldDefn("nearest_acps", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("nearest_acps_dist_m", ogr.OFTReal))
out_layer.CreateField(ogr.FieldDefn("nearest_decoupler_m", ogr.OFTReal))

# populate the pool
# splitting into ~10m segments, which we will have to
# tie back up in the end
logging.info("splitting into 10m segments to populate pool")
pool_results = []
for feature in layer:
  logging.info("processing feature %s" % feature.GetFID())
  geom = feature.GetGeometryRef()
  chunks = split_line_at_length_np(geom, 1000)
  logging.info("feature split into %s chunks" % len(chunks))
  for chunk in chunks:
    new_feature = feature.Clone()
    new_feature.SetGeometry(chunk)
    json_feature = new_feature.ExportToJson()
    params = {'base_height': args.base_height,
      'powerline_file': args.powerline_file}
    res = POOL.apply_async(process_segment, (json_feature, fieldnames, params,))
    pool_results.append(res)
    if len(pool_results) % 10 == 0:
      logging.info("put %s rows into pool" % len(pool_results))

processed = 0
logging.info("pool size = %s" % len(pool_results))
for res in pool_results:
  new_feature_json = res.get()
  if new_feature_json is False:
    raise Exception("Failure processing batch")

  newds = ogr.Open(new_feature_json)
  newlayer = newds.GetLayer()
  of = newlayer.GetNextFeature().Clone()
  of.SetFID(processed + 1) # fid cannot be zero
  out_layer.CreateFeature(of)
  processed += 1
  if processed % 1000 == 0:
    logging.info("completed %s/%s" % (processed, total_nodes))

logging.info("done processing pool")

driver = ogr.GetDriverByName('Memory')  
cloned_ds = driver.CreateDataSource('cloned')  
cloned_layer = cloned_ds.CreateLayer('cloned_layer', 
  geom_type=out_layer.GetGeomType())
layer_defn = out_layer.GetLayerDefn()
for i in range(layer_defn.GetFieldCount()):
  cloned_layer.CreateField(layer_defn.GetFieldDefn(i))
for feature in out_layer:
  cloned_layer.CreateFeature(feature)

# reset readings
out_layer.ResetReading()
cloned_layer.ResetReading()

# REPLACE THIS CHUNK OF CODE WITH PYSPICE HVX
# second pass which takes the computed values
# and calculates the total V using the dropoff function
rho_src = esri_driver.Open(args.resistivity_file, 0)
rho_layer = rho_src.GetLayer(0)

for f1 in out_layer:
  cloned_shape = f1.GetGeometryRef().Clone()
  buffed = cloned_shape.Buffer(400)
  f1_v = copy.deepcopy(f1.GetField('total_voltage'))
  V0 = copy.deepcopy(f1_v)
  f1_pt = f1.GetGeometryRef().Centroid()
  cloned_layer.SetSpatialFilter(buffed)
  for f2 in cloned_layer:
    f2_pt = f2.GetGeometryRef().Centroid()
    f2_v = f2.GetField('total_voltage')
    if f2_v <= 0:
      continue
    dist_m = f1_pt.Distance(f2_pt)
    if dist_m > 0:
      f1_v += voltage_at_distance(dist_m, f2_v, 0.5)

  #### END OF REPLACEMENT

  #print("setting %s => %s" % (V0, f1_v))
  f1.SetField('total_voltage', f1_v)
  f1.SetField('self_voltage', V0)

  # how look at the nearest ACPS
  survey_layer.SetSpatialFilter(cloned_shape.Buffer(1000))
  nearest_acps = None
  nearest_acps_dist_m = None
  for survey in survey_layer:
    acps = survey.GetField('TestPointInspectionACPS')
    if acps is not None and acps != '':
      acps = float(acps)
      acps_dist_m = survey.GetGeometryRef().Distance(cloned_shape)
      if nearest_acps is None or acps_dist_m < nearest_acps_dist_m:
        nearest_acps = acps
        nearest_acps_dist_m = acps_dist_m

  f1.SetField(out_layer_def.GetFieldIndex('nearest_acps'), nearest_acps)
  f1.SetField(out_layer_def.GetFieldIndex('nearest_acps_dist_m'), nearest_acps_dist_m)

  # find nearest decoupler
  decoupler_layer.SetSpatialFilter(cloned_shape.Buffer(10000))
  nearest_decoupler = None
  for decoupler in decoupler_layer:
    dist = decoupler.GetGeometryRef().Distance(cloned_shape)
    if nearest_decoupler is None or dist < nearest_decoupler:
      nearest_decoupler = dist
  f1.SetField(out_layer_def.GetFieldIndex('nearest_decoupler_m'), nearest_decoupler)

  # now get the soil resistivity for this area
  # rho_layer, grab anything that intersects and compute
  # the mean nearby resistivity
  rho_layer.SetSpatialFilter(cloned_shape.Buffer(100))
  resistivity_blocks = []
  for soil_polygon in rho_layer:
    resistivity_ohm_cm = float(soil_polygon.GetField(args.resistivity_field_name))
    if resistivity_ohm_cm is None or resistivity_ohm_cm == 0:
      continue
    resistivity_blocks.append(resistivity_ohm_cm)
  mean_rho = np.mean(resistivity_blocks)
  f1.SetField(out_layer_def.GetFieldIndex('mean_resistivity_ohm_cm'), mean_rho)
  f1.SetField(out_layer_def.GetFieldIndex('mean_resistivity_ohm_m'), mean_rho/100)

  # compute total susceptibility
  leakage = None
  if mean_rho > 0:
    coating_diameter_m = 0.01
    leakage = round((8 * f1_v) / ((mean_rho/100.00) * math.pi * coating_diameter_m), 4)
    if leakage > 0:
      logging.info("leakage = %s A/m^2" % leakage)
    f1.SetField(out_layer_def.GetFieldIndex('amps_per_m2'), leakage)

  suscept = get_suscept(f1_v, leakage)
  f1.SetField(out_layer_def.GetFieldIndex('nace_susceptibility'), suscept) 

  out_layer.SetFeature(f1)
