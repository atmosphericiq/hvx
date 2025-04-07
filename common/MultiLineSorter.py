from osgeo import ogr, osr
import math

class MultiLineSorter:

  def _last_point(self, linegeo):
    num_points = linegeo.GetPointCount()
    points = [linegeo.GetPoint_2D(i) for i in range(num_points)]
    return points[-1]

  def _cartesian_dist(self, x1, y1, x2, y2):
    return math.sqrt(pow(x1 - x2, 2) + pow(y1 - y2, 2))

  def _nearest(self, x, y, point_struct):
    min_dist = None
    nearest_id = None
    for (id, points) in point_struct.items():
      for p in points:
        d = self._cartesian_dist(x, y, p[0], p[1])
        if min_dist is None or d < min_dist:
          nearest_id = id
          min_dist = d
    return nearest_id

  def sort(self, geom):
    multiline_count = geom.GetGeometryCount()
    if multiline_count == 1:
      return geom
    point_struct = {}
    for i in range(multiline_count):
      g = geom.GetGeometryRef(i)
      num_points = g.GetPointCount()
      point_struct[i] = [g.GetPoint_2D(i) for i in range(num_points)]

    new_multiline = ogr.Geometry(ogr.wkbMultiLineString)
    first_segment = geom.GetGeometryRef(0)
    new_multiline.AddGeometry(first_segment)
    del point_struct[0]

    while len(point_struct) > 0:
      (x, y) = self._last_point(first_segment)
      next_id = self._nearest(x, y, point_struct)
      linegeo = geom.GetGeometryRef(next_id)
      new_multiline.AddGeometry(linegeo)
      del point_struct[next_id]
      #print(len(point_struct))

    return new_multiline
