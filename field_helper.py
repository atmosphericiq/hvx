import sys
import cmath
import math
import numpy as np
import uuid
from multiprocessing import current_process
from osgeo import ogr
from osgeo import osr
from common.LineSegmenter import LineSegmenter
from common.LineDissolver import LineDissolver
from common.MultiLineSorter import MultiLineSorter
from split_line import split_line_multiple
from split_line2 import split_line_at_length_np
import logging

METER_RESOLUTION = 1.0
MU0 = 1.25663706212 * math.pow(10, -6)

esri_driver = ogr.GetDriverByName('FileGDB')
gpkg_driver = ogr.GetDriverByName('GPKG')
mem_driver = ogr.GetDriverByName('memory')

srs4326 = osr.SpatialReference()
srs4326.ImportFromEPSG(4326)
srs4326.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

srs3857 = osr.SpatialReference()
srs3857.ImportFromEPSG(3857)  

transform = osr.CoordinateTransformation(srs3857, srs4326)

def voltage_at_distance(x, V0=1, attenuation_factor=2):  
  alpha = 0.000116188 * attenuation_factor
  beta = 0.0162233
  gamma = alpha + 1j*beta  # Using 1j to represent the imaginary unit in Python
  Vx = V0 * cmath.exp(-gamma * x)
  if Vx.real < 0:
    return 0
  return Vx.real

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

def process_segment(feature_json, fieldnames, params={},):
  process_id = current_process().pid
  logging.info("process id = %s" % process_id)

  src = mem_driver.CreateDataSource(str(uuid.uuid4()))
  out_layer = src.CreateLayer("line", srs3857, ogr.wkbLineString)
  out_layer_def = out_layer.GetLayerDefn()
  for (fname, ftype, fidx) in fieldnames:
    new_field = ogr.FieldDefn(fname, ftype)
    out_layer.CreateField(new_field, ftype)
  out_layer.CreateField(ogr.FieldDefn("total_flux_T", ogr.OFTReal))
  out_layer.CreateField(ogr.FieldDefn("total_flux_uT", ogr.OFTReal))
  out_layer.CreateField(ogr.FieldDefn("total_voltage", ogr.OFTReal))
  out_layer.CreateField(ogr.FieldDefn("length_meters", ogr.OFTReal))

  # scoring + amps
  out_layer.CreateField(ogr.FieldDefn("amps_per_m2", ogr.OFTReal))
  out_layer.CreateField(ogr.FieldDefn("mean_resistivity_ohm_cm", ogr.OFTReal))
  out_layer.CreateField(ogr.FieldDefn("mean_resistivity_ohm_m", ogr.OFTReal))
  out_layer.CreateField(ogr.FieldDefn("nace_susceptibility", ogr.OFTString))

  # process params
  base_height = params.get('base_height', 10)

  # OK now open the file
  ds = ogr.Open(feature_json)
  feature_layer = ds.GetLayer(0)

  # grab the first feature (should be only)
  feature = feature_layer.GetNextFeature()
  geom = feature.GetGeometryRef()
  geom_length = geom.Length()
  cloned_geom = geom.Clone()
  logging.info(f"geom length = {geom_length}")

  # now filter the powerline file so near us
  psrc = gpkg_driver.Open(params['powerline_file'], 0)
  powerlayer = psrc.GetLayer(0)
  powerlayer.SetSpatialFilter(cloned_geom.Buffer(1000))

  # cast the geom to linestring
  #new_line = ogr.ForceToLineString(geom.Clone())

  # break this into one meter chunks
  segment_flux = 0.0
  geom_type = geom.GetGeometryType()
  chunks = split_line_at_length_np(geom, METER_RESOLUTION)

  logging.info("split into %s chunks" % len(chunks))

  # iterate thru each 1 meter chunk
  # and get that chunk's latitude and longitude
  chunk_id = 0
  for chunk in chunks:
    x = chunk.Centroid().GetX()
    y = chunk.Centroid().GetY()
    chunk_id += 1
    chunk_total_flux = 0.0

    chunk_h = chunk.Length()

    # buffer the shape to 300 m
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint_2D(x, y)
    buffered_shape = point.Buffer(300)

    # find all powerlines that intersect that buffer
    # and compute the total magnetic flux received
    # by that little area of land
    for pl in powerlayer:
      pl_geom = pl.GetGeometryRef()
      does_intersect = buffered_shape.Intersects(pl_geom)
      if does_intersect:
        osm_id = pl.GetField("EDI_SOURCE_ID")
        voltage = clean_voltage(pl.GetField("EDI_VOLTAGE"))
        distance_m = point.Distance(pl_geom)

        if voltage is None or voltage <= 0:
          voltage = 138000
        if voltage and voltage < 1000:
          voltage = voltage * 1000

        # convert to an int
        assert voltage > 1000, "Invalid voltage %s" % voltage
        assert voltage < 1000000, "Invalid voltage %s" % voltage
        assert type(voltage) == int, "voltage not an int %s" % voltage

        if voltage is None:
          current = 500.00
        elif voltage <= 138000:
          current = 1400.00
        elif voltage < 240000:
          current = 4500.00
        elif voltage <= 345000:
          current = 6000.0
        elif voltage <= 500000:
          current = 10000.0
        else:
          current = 500.00

        # pythagoras to get dist
        r = math.sqrt(math.pow(base_height, 2) + math.pow(distance_m, 2))

        # now compute the total flux for this little area
        # note that this is the peak current (not RMS!)
        # B(t)= u0I(t)/2πr
        chunk_flux = (MU0 * current) / (2 * math.pi * r)
        chunk_flux *= chunk_h # this is A for us
        chunk_total_flux += chunk_flux

        #print((chunk_id, osm_id, voltage, distance_m, r, chunk_flux))

      #print((chunk_id, chunk_total_flux))
    segment_flux += chunk_total_flux

  of = ogr.Feature(out_layer_def) # create feature

  segment_flux_uT = segment_flux * math.pow(10,6)
  if segment_flux_uT > 0:
    logging.info('total segment flux = %s uT' % segment_flux_uT)

  # set geometry fields
  old_geom = geom.Clone()
  of.SetGeometry(old_geom)

  for (fname, ftype, fidx) in fieldnames:
    field_value = feature.GetField(fidx)
    of.SetField(fidx, field_value)

  of.SetField(out_layer_def.GetFieldIndex('total_flux_T'), segment_flux)
  of.SetField(out_layer_def.GetFieldIndex('total_flux_uT'), segment_flux_uT)

  total_voltage = 120 * math.pi * segment_flux # 100 bc 50hz, 120 at 60hz

  of.SetField(out_layer_def.GetFieldIndex('total_voltage'), total_voltage)
  of.SetField(out_layer_def.GetFieldIndex('length_meters'), geom_length)

  if total_voltage > 0:
    logging.info('total voltage = %s V' % total_voltage)

  logging.info(f"Process ID = {process_id} Done")
  return (of.ExportToJson())

def get_suscept(total_voltage, leakage):
  if total_voltage is None and leakage is None:
    suscept = 'UNKNOWN'
  elif leakage is None and total_voltage > 1.0:
    suscept = 'MEDIUM'
  elif leakage is None and total_voltage > 3.0:
    suscept = 'HIGH'
  elif leakage is None and total_voltage < 1.0:
    suscept = 'LOW'
  elif leakage < 20:
    suscept = 'LOW'
  elif leakage < 100:
    suscept = 'MEDIUM'
  elif leakage > 100:
    suscept = 'HIGH'
  else:
    suscept = 'UNKNOWN'
  return suscept
