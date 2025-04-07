'''
LineSegmenter

takes a line and break it into smaller parts
'''
from osgeo import ogr, osr
import numpy as np
import logging
from .LineDissolver import LineDissolver
from .split_line import split_line_multiple
import math

ALLOWEDTYPES = ['LINESTRING', 'MULTILINESTRING']

logger = logging.getLogger(__name__)

class LineSegmenter:

  def __init__(self):
    pass

  def _distance_meters(self, x1, y1, x2, y2):
    point1 = ogr.Geometry(ogr.wkbPoint)
    point1.AddPoint_2D(x1, y1)
    point2 = ogr.Geometry(ogr.wkbPoint)
    point2.AddPoint_2D(x2, y2)
    distance = point1.Distance(point2)
    return distance

  def line_segment(self, pts):
    driver = ogr.GetDriverByName("Memory")
    ds = driver.CreateDataSource(str(uuid.uuid4()))
    layer = ds.CreateLayer("line", srs, ogr.wkbMultiLineString)
    multiline = ogr.Geometry(ogr.wkbMultiLineString)
    linegeo = ogr.Geometry(ogr.wkbLineString)
    for (x,y) in pts:
      linegeo.AddPoint(x, y)
    multiline.AddGeometry(linegeo)
    f = ogr.Feature(layer.GetLayerDefn())
    f.SetGeometry(linegeo)
    return f

  def _angle(self, pt1, pt2):
    if type(pt1) == tuple:
      x1 = pt1[0]
      y1 = pt1[1]
    else:
      x1 = pt1.GetX()
      y1 = pt1.GetY()
    if type(pt2) == tuple:
      x2 = pt2[0]
      y2 = pt2[1]
    else:
      x2 = pt2.GetX()
      y2 = pt2.GetY()
    chng_x = (x2 - x1)
    chng_y = (y2 - y1)
    if chng_x == 0 and abs(chng_y) > 0:
      return 90.0
    elif chng_x == 0:
      return 0
    return math.degrees(math.atan(abs(chng_y) / abs(chng_x)))

  #
  # note we need objects in EPSG:3857 so we can do distance
  #
  def segment_single_linestring_by_dist(self, geom, distance):
    output_geoms = []
    #for i in range(num_points):
    #  (x1, y1) = geom.GetPoint_2D(i)

    #  # 0) point is the first point
    #  if i == 0:
    #    geom_sequence.AddPoint(x1, y1)
    #    continue

    #  (x2, y2) = geom.GetPoint_2D(i - 1)
    #  calc_dist = self._distance_meters(x1, y1, x2, y2)

      # 1) is a point < 10m
      #if np.abs(calc_dist) < distance:
      #  geom_sequence.AddPoint(x1, y1)
      #  output_geoms.append(geom_sequence)
      #  geom_sequence = ogr.Geometry(ogr.wkbLineString)
      #  geom_sequence.AddPoint(x1, y1)

      # 2) is a point > 10m, make a new point
      # implement this later when we have longer spans (?)
      #elif calc_dist >= distance:
      # from split_line import split_line_multiple
    output_geoms = split_line_multiple(geom, distance)
    return output_geoms

  # segment_single_linestring - should return a list
  # of geom objects, this is the meat of the algorithm
  def segment_single_linestring(self, geom, threshold):
    output_geoms = []
    num_points = geom.GetPointCount()
    if num_points <= 2:
      return [geom]
    geom_sequence = ogr.Geometry(ogr.wkbLineString)
    prior_direction = None
    seq_start = None
    for i in range(num_points):
      (x, y) = geom.GetPoint_2D(i)
      if seq_start is None:
        seq_start = (x, y)
      if i == (num_points - 1):
        geom_sequence.AddPoint_2D(x, y)
        continue
      (xn, yn) = geom.GetPoint_2D(i + 1)
      direction = self._angle((xn, yn), seq_start)
      if prior_direction == None:
        angle_change = None
      else:
        angle_change = abs(prior_direction - direction)
      #print(seq_start, (xn, yn), prior_direction, direction, angle_change)
      geom_sequence.AddPoint_2D(x, y)
      prior_direction = self._angle((xn, yn), (x, y))
      if angle_change is not None and angle_change > threshold:
        output_geoms.append(geom_sequence)
        geom_sequence = ogr.Geometry(ogr.wkbLineString)
        geom_sequence.AddPoint_2D(x, y) # add to start of next
        seq_start = (x, y)
    output_geoms.append(geom_sequence)
    return output_geoms

  def _deepcopy_feature(self, feature):
    feature_defn = feature.GetDefnRef()
    f_new = ogr.Feature(feature_def=feature_defn)
    geom = feature.GetGeometryRef()
    #geom_wkt = geom.ExportToWkt()
    #new_geom = ogr.CreateGeometryFromWkt(geom_wkt)
    #f_new.SetGeometry(geom)
    return f_new

  # def split line based on a fixed distance
  def feature_to_linefeatures_fixed(self, feature, meters=0):
    geom = feature.GetGeometryRef()
    geom_type = geom.GetGeometryName()
    logger.info("geometry length = %s" % geom.Length())
    assert geom_type in ALLOWEDTYPES, "Invalid type %s" % geom_type
    features = []
    if geom_type == 'LINESTRING':
      output_geoms = self.segment_single_linestring_by_dist(geom, meters)
    elif geom_type == 'MULTILINESTRING':
      segments = ogr.Geometry(ogr.wkbMultiLineString)
      output_geoms = []
      no_lines = geom.GetGeometryCount()
      logger.info("Found %s lines" % no_lines)
      for i in range(no_lines):
        g = geom.GetGeometryRef(i)
        go_geoms = self.segment_single_linestring_by_dist(g, meters)
        for go in go_geoms:
          output_geoms.append(go)
        if i % 10 == 0:
          logger.info("completed %i lines / %i lines" % (i, no_lines))

    logger.info("found output_geoms of size %i" % len(output_geoms))
    count = 0
    for new_geom in output_geoms:
      new_feature = self._deepcopy_feature(feature)
      new_feature.SetGeometry(new_geom)
      features.append(new_feature)
      count += 1
      if count % 100 == 0:
        logger.info("finished %i / %i" % (count, len(output_geoms)))
    
    return features

  # take a feature which is a line or a multiline 
  # and split it into smaller features based on
  # geometric curvature; note that there won't be any
  # multi-line segments in this model
  def feature_to_line_features(self, feature, threshold=10, buffer_param=0.0, simplify=True):
    geom = feature.GetGeometryRef()
    geom_type = geom.GetGeometryName()
    assert geom_type in ALLOWEDTYPES, "Invalid type %s" % geom_type
    features = []
    if geom_type == 'LINESTRING':
      output_geoms = self.segment_single_linestring(geom, threshold)
    elif geom_type == 'MULTILINESTRING':
      segments = ogr.Geometry(ogr.wkbMultiLineString)
      output_geoms = []
      
      if simplify is True:
        dissolver = LineDissolver()
        simplified_geom = dissolver.dissolve_multiline(geom, buffer_param)
      else:
        simplified_geom = geom
      no_lines = simplified_geom.GetGeometryCount()

      for i in range(no_lines):
        g = simplified_geom.GetGeometryRef(i)
        go_geoms = self.segment_single_linestring(g, threshold)
        for go in go_geoms:
          output_geoms.append(go)
    for new_geom in output_geoms:
      new_feature = self._deepcopy_feature(feature)
      new_feature.SetGeometry(new_geom)
      features.append(new_feature)
    return features
