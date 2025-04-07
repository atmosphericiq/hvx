import logging
import numpy as np
import numpy.ma as ma
from osgeo import gdal

logger = logging.getLogger(__name__)

class RasterBand:

  def __init__(self):
    pass

  def shape(self):
    return (self._cols, self._rows)

  def size(self):
    return self._cols * self._rows

  # returns the centroid for a given box, where the point
  # is the UL point
  def _centroid(self, x, y):
    center_x = x + (self._pixel_w/2)
    center_y = y + (self._pixel_h/2)
    return (center_x, center_y)

  def rows(self, return_centroids=False):
    for i in range(self._rows):
      y = self._y_origin - (i * self._pixel_h)
      x = self._x_origin
      if return_centroids is True:
        coords = [self._centroid(x + (j * self._pixel_w), y) \
          for j in range(self._cols)]
      else:
        coords = [(x + (j * self._pixel_w), y) for j in range(self._cols)]
      data = self._band.ReadAsArray(0, i, self._cols, 1)[0]
      data = [d if d != self._nodata else None for d in data]
      yield list(zip(coords, data))

  # retrieve a single value at a location
  def get_value(self, x, y):
    if x > self._x_origin:
      offset_x = np.floor(np.abs(x - self._x_origin) / self._pixel_w)
    else:
      offset_x = 0
    if y < self._y_origin:
      offset_y = np.floor(np.abs(self._y_origin - y) / self._pixel_h)
    else:
      offset_y = 0
    
    # note this error: ERROR 5: Access window out of range in RasterIO().  
    # which means we need to confirm the values we want are in the range
    # and if not, return nodata values for the areas missing
    if offset_x >= self._cols:
      return None
    if offset_y >= self._rows:
      return None

    try:
      data = self._band.ReadAsArray(offset_x, offset_y, 1, 1).tolist()[0][0]
    except:
      return None
    if data == self._nodata:
      return None
    return data

  def copy_empty(self, band_obj, filename):
    driver = gdal.GetDriverByName("GTiff")
    self._tif = driver.Create(filename, band_obj._cols, 
      band_obj._rows, 1, gdal.GDT_Float32,
      options=['COMPRESS=LZW'])
    self._tif.SetGeoTransform(band_obj._tif.GetGeoTransform())
    self._tif.SetProjection(band_obj._tif.GetProjection())
    self._nodata = band_obj._nodata
    self._cols = band_obj._cols
    self._rows = band_obj._rows
    self._x_origin = band_obj._x_origin
    self._y_origin = band_obj._y_origin
    self._pixel_w = band_obj._pixel_w
    self._pixel_h = band_obj._pixel_h

  def write_array(self, array_out, band_id=1):
    self._tif.GetRasterBand(band_id).WriteArray(array_out)
    self._tif.GetRasterBand(band_id).SetNoDataValue(self._nodata)
    self._tif.FlushCache() 

  def loadf(self, gtif, band_id=1):
    logger.debug("opening %s" % gtif)
    self._tif = gdal.Open(gtif)
    self._band = self._tif.GetRasterBand(band_id)
    self._nodata = self._band.GetNoDataValue()
    logger.debug("nodata value = %s" % self._nodata)
    self._cols = self._tif.RasterXSize
    self._rows = self._tif.RasterYSize
    transform = self._tif.GetGeoTransform()
    self._x_origin = transform[0]
    self._y_origin = transform[3]
    self._pixel_w = transform[1]
    self._pixel_h = -transform[5]
