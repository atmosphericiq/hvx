from osgeo import ogr, osr
import math

ALLOWEDTYPES = ['LINESTRING', 'MULTILINESTRING']

class LineDissolver:

  # dissolve multiline takes a multiline and attempts to
  # make it a single linestring if they share start/end
  def dissolve_multiline(self, geom, buffer_param):
    multiline_count = geom.GetGeometryCount()
    if multiline_count == 1:
      return geom

    # create a new multi-line array
    new_multiline = ogr.Geometry(ogr.wkbMultiLineString)
    tmp_linegeo = ogr.Geometry(ogr.wkbLineString)

    for i in range(multiline_count):
      linegeo = geom.GetGeometryRef(i)
      geom_type = linegeo.GetGeometryName()
      assert geom_type == 'LINESTRING', "Invalid type %s" % geom_type

      # get points in this particular line
      num_points = linegeo.GetPointCount()
      points = [linegeo.GetPoint_2D(i) for i in range(num_points)]
      first_point = points[0]
      last_point = points[-1]

      # get the last point of the current tmp_linegeo
      # if the first point of current set == last point in there
      # then skip first and append
      num_roll = tmp_linegeo.GetPointCount()
      if num_roll > 0:
        running_pts = [tmp_linegeo.GetPoint_2D(i) for i in range(num_roll)]
        trailing_pt = running_pts[-1]

        # intersect has to consider a buffer param
        trailing_geom = ogr.Geometry(ogr.wkbPoint)
        trailing_geom.AddPoint(*trailing_pt)
        if buffer_param > 0:
          buffered_geom = trailing_geom.Buffer(buffer_param)
        else:
          buffered_geom = trailing_geom

        first_point_geom = ogr.Geometry(ogr.wkbPoint)
        first_point_geom.AddPoint(*first_point)

        #if trailing_geom.Intersects(first_point_geom):
        #print((first_point, trailing_pt, trailing_geom.Intersects(first_point_geom)))
        if buffered_geom.Contains(first_point_geom):
          [tmp_linegeo.AddPoint(x, y) for (x, y) in points[1:]]
        else:
          new_multiline.AddGeometry(tmp_linegeo)
          tmp_linegeo = ogr.Geometry(ogr.wkbLineString)
          [tmp_linegeo.AddPoint(x, y) for (x, y) in points]
      else:
        [tmp_linegeo.AddPoint(x, y) for (x, y) in points]

    new_multiline.AddGeometry(tmp_linegeo)
    return new_multiline

