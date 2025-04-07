import os
import shutil
import logging
import numpy as np
from osgeo import ogr, osr

logger = logging.getLogger(__name__)

epsg3857 = osr.SpatialReference()
epsg3857.ImportFromEPSG(3857)
epsg4326 = osr.SpatialReference()
epsg4326.ImportFromEPSG(4326)
epsg4326.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

SHAPE_TYPES = ['POINT', 'LINE', 'POLYGON', 'MULTIPOLYGON']
PROJECTIONS = [4326, 3857]

class VectorLayer:

  def __init__(self):
    self._datasource = None
    pass

  def get_layer(self):
    return self._layer

  def set_spatial_filter(self, geom):
    self._layer.SetSpatialFilter(geom)

  def add_feature(self, ogr_feature):
    self._layer.CreateFeature(ogr_feature)
    return ogr_feature

  # copies an old feature, creates a new one but
  # with the proper layer defn
  def copy_feature(self, ogr_feature):
    old_defn = ogr_feature.GetDefnRef()
    feature_defn = self._layer.GetLayerDefn()
    new_feature = ogr.Feature(feature_def=feature_defn)
    old_geom = ogr_feature.GetGeometryRef()
    new_geom = old_geom.Clone()

    # if the SRS dont match, then we have to reproject
    old_authority = (old_defn.GetGeomFieldDefn(0)
      .GetSpatialRef()
      .GetAttrValue("AUTHORITY", 1))
    new_authority = (feature_defn.GetGeomFieldDefn(0)
      .GetSpatialRef()
      .GetAttrValue("AUTHORITY", 1))
    if old_authority != new_authority:
      new_geom = self.reproject_geom(old_geom.Clone(),
        int(old_authority), int(new_authority))
    new_feature.SetGeometry(new_geom)

    new_field_names = []
    for i in range(feature_defn.GetFieldCount()):
      new_name = feature_defn.GetFieldDefn(i).GetName()
      new_field_names.append(new_name)

    for i in range(old_defn.GetFieldCount()):
      old_name = old_defn.GetFieldDefn(i).GetName()
      if old_name in new_field_names:
        new_feature.SetField(old_name, ogr_feature.GetField(old_name))
    return new_feature

  def reproject_geom(self, geom, old_epsg, new_epsg=4326):
    new_geom = geom.Clone()
    epsg_from = osr.SpatialReference()
    epsg_from.ImportFromEPSG(old_epsg)
    epsg_to = osr.SpatialReference()
    epsg_to.ImportFromEPSG(new_epsg)
    if old_epsg == 4269:
      epsg_from.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    if new_epsg == 4326:
      epsg_to.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    transform_func = osr.CoordinateTransformation(epsg_from, epsg_to)
    new_geom.Transform(transform_func)
    return new_geom

  def get_feature(self, feature_id=None):
    if feature_id == None:
      f = self._layer.GetNextFeature()
      return f.Clone()

  def blank_feature(self, geometry=None):
    feature_defn = self._layer.GetLayerDefn()
    feature = ogr.Feature(feature_def=feature_defn)
    if type(geometry) in [list, tuple]:
      geometry = (float(i) for i in geometry)
      point = ogr.Geometry(ogr.wkbPoint)
      point.AddPoint(*geometry)
      feature.SetGeometry(point)
    elif geometry is not None:
      feature.SetGeometry(geometry)
    return feature

  def createmem(self, name):
    logger.info("creating in memory layer %s" % name)
    driver = ogr.GetDriverByName('MEMORY')
    self._datasource = driver.CreateDataSource(name)

  def createf(self, vector_file, overwrite=False):
    logger.info("creating file @ %s" % vector_file)
    if 'gdb' in vector_file:
      driver = ogr.GetDriverByName('FileGDB')
    elif 'shp' in vector_file:
      driver = ogr.GetDriverByName('ESRI Shapefile')
    elif 'gpkg' in vector_file:
      driver = ogr.GetDriverByName('GPKG')
    elif 'kml' in vector_file:
      driver = ogr.GetDriverByName('KML')

    if overwrite is True:
      if os.path.isfile(vector_file):
        os.remove(vector_file)
      if os.path.isdir(vector_file):
        shutil.rmtree(vector_file)
    self._datasource = driver.CreateDataSource(vector_file)

  def copy_blank_layer(self, vectorfile2, new_name):
    logger.info("Copying layer from %s" % vectorfile2)
    assert self._datasource is not None, "No datasource set. call createf"
    old_layer_def = vectorfile2.get_layer().GetLayerDefn()
    self._layer = self._datasource.CreateLayer(new_name,
      srs=vectorfile2.get_layer().GetSpatialRef(),
      geom_type=old_layer_def.GetGeomType())
    feature0 = vectorfile2.get_layer().GetNextFeature()
    [self._layer.CreateField(feature0.GetFieldDefnRef(i)) for \
      i in range(feature0.GetFieldCount())]
    logger.info("Layer copy completed")

  def create_layer(self, layer_name, shape_type='POINT', proj=4326):
    assert self._datasource is not None, "No datasource set. call createf"
    assert proj in PROJECTIONS, "Invalid projection"
    assert shape_type.upper() in SHAPE_TYPES, "Invalid shape type"
    logging.info("creating layer %s" % layer_name)
    if proj == 4326:
      use_proj = epsg4326
    elif proj == 3857:
      use_proj = epsg3857
    if shape_type.upper() == 'POINT':
      use_shape = ogr.wkbPoint
    elif shape_type.upper() == 'LINE':
      use_shape = ogr.wkbLineString
    elif shape_type.upper() == 'POLYGON':
      use_shape = ogr.wkbPolygon
    elif shape_type.upper() == 'MULTIPOLYGON':
      use_shape = ogr.wkbMultiPolygon
    self._layer = self._datasource.CreateLayer(layer_name,
      use_proj, use_shape)

  def add_field_def(self, field_name, field_type='int'):
    if field_type == 'int':
      fd = ogr.FieldDefn(field_name, ogr.OFTInteger)
    elif field_type == 'float':
      fd = ogr.FieldDefn(field_name, ogr.OFTReal)
    elif field_type == 'str':
      fd = ogr.FieldDefn(field_name, ogr.OFTString)
    else:
      fd = ogr.FieldDefn(field_name, ogr.OFTString)
    self._layer.CreateField(fd)

  def loadf(self, vector_file, layer_id=0):
    logger.info("opening %s" % vector_file)
    if 'gdb' in vector_file:
      driver = ogr.GetDriverByName('OpenFileGDB')
    elif 'gpkg' in vector_file:
      driver = ogr.GetDriverByName('GPKG')
    elif 'shp' in vector_file:
      driver = ogr.GetDriverByName('ESRI Shapefile')
    elif 'kml' in vector_file:
      driver = ogr.GetDriverByName('KML')
    else:
      raise Exception("Unknown vector format for %s" % vector_file)

    self._source = driver.Open(vector_file, 0)
    num_layers = self._source.GetLayerCount()
    logger.info("found %s number of layers" % num_layers)
    if type(layer_id) == int:
      self._layer = self._source.GetLayer(layer_id)
    elif type(layer_id) == str:
      logger.info("fetching layer by name = %s" % layer_id)
      for idx in range(self._source.GetLayerCount()):
        candidate_layer = self._source.GetLayerByIndex(idx)
        candidate_layer_name = candidate_layer.GetName()
        if candidate_layer_name == layer_id:
          logger.info("found layer matching = %s" % idx)
          self._layer = self._source.GetLayer(idx)
    assert self._layer is not None, "cannot find layer id = %s" % layer_id

  def find_distance_m(self, geom1, geom2):
    if type(geom1) == tuple and len(geom1) == 2:
      (x, y) = geom1
      tmp_g = ogr.Geometry(ogr.wkbPoint)
      tmp_g.AddPoint_2D(x, y)
      geom1 = tmp_g
    if type(geom2) == tuple and len(geom2) == 2:
      (x, y) = geom2
      tmp_g = ogr.Geometry(ogr.wkbPoint)
      tmp_g.AddPoint_2D(x, y)
      geom2 = tmp_g
    transform_func = osr.CoordinateTransformation(epsg4326, epsg3857)
    geom1.Transform(transform_func)
    geom2.Transform(transform_func)
    return geom1.Distance(geom2)

  def find_nearest_feature(self, x, y, bounding_shape=None):
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint_2D(x, y)
    if type(bounding_shape) is float:
      radius = bounding_shape
      bounding_shape = point.Buffer(radius)
    if bounding_shape is not None:
      self._layer.SetSpatialFilter(bounding_shape)
    dists = [(f, point.Distance(f.GetGeometryRef())) for f in self._layer]
    sorted_records = sorted(dists, key=lambda i: i[1])
    if len(sorted_records) > 0:
      closest = sorted_records[0][0]
      return closest
    return None

