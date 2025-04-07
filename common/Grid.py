'''
Grid - grid is a library which constructs a
grid of aribtrary square size and can in 
linear time return grid membership stuff
'''
import numpy as np
from osgeo import ogr, osr, gdal
import math
import logging

logger = logging.getLogger(__name__)
gdal.UseExceptions()

class Grid:

  def __init__(self, x_range, y_range, x_resolution, y_resolution):
    self.x_min = float(x_range[0])
    self.x_max = float(x_range[1])
    self.y_min = float(y_range[0])
    self.y_max = float(y_range[1])
    self.x_resolution = float(x_resolution)
    self.y_resolution = float(y_resolution)
    self._boxes = {}
    for boxkey in self.boxkeys():
      (xmin, xmax, ymin, ymax) = boxkey
      logger.info(boxkey)
      shp = self.vector_shape(xmin, xmax, ymin, ymax)
      self._boxes[boxkey] = shp

  def vector_shape(self, x_min, x_max, y_min, y_max):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(x_min, y_min)
    ring.AddPoint(x_max, y_min)
    ring.AddPoint(x_max, y_max)
    ring.AddPoint(y_min, y_max)
    ring.AddPoint(x_min, y_min)
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)
    return polygon

  def size(self):
    return len(self._boxes)

  def boxkeys(self):
    for y in np.arange(self.y_min, self.y_max, self.y_resolution):
      for x in np.arange(self.x_min, self.x_max, self.x_resolution):
        yield (x, x + self.x_resolution, y, y + self.y_resolution)

  def num_distance(self, a, b):
    if a < b:
      return np.abs(b-a)
    return np.abs(a-b)

  # determine which box a point is in 
  # which should return (xmin, xmax, ymin, ymax)
  def whichbox(self, point):
    (x, y) = point
    x = float(x)
    y = float(y)
    x_box_no = math.floor(self.num_distance(x, self.x_min) / self.x_resolution)
    y_box_no = math.floor(self.num_distance(y, self.y_min) / self.y_resolution)
    x_min = self.x_min + (x_box_no * self.x_resolution)
    x_max = x_min + self.x_resolution
    y_min = self.y_min + (y_box_no * self.y_resolution)
    y_max = y_min + self.y_resolution

    return (x_min, x_max, y_min, y_max)

  def box(self, point):
    box_key = self.whichbox(point)
    return self._boxes[box_key]
