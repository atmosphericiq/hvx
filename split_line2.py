import numpy as np
from osgeo import ogr

def distance_np(a, b):
  """ Calculate the Euclidean distance between 2D points a and b using numpy. """
  a_2d = np.array(a[:2])  # Ensure it's 2D
  b_2d = np.array(b[:2])  # Ensure it's 2D
  return np.linalg.norm(b_2d - a_2d)

def interpolate_point_np(a, b, dist):
  """ Interpolate a point on the 2D line segment a-b at distance 'dist' from point a using numpy. """
  a_2d = np.array(a[:2])  # Ensure it's 2D
  b_2d = np.array(b[:2])  # Ensure it's 2D
  total_dist = np.linalg.norm(b_2d - a_2d)
  ratio = dist / total_dist
  return a_2d + ratio * (b_2d - a_2d)

def split_line_at_length_np(line, chunk_length):
  """ Split a LINESTRING or MULTILINESTRING into chunks of specified length, ensuring 2D points. """
  if line.GetGeometryType() == ogr.wkbMultiLineString:
    # If it's a MultiLineString, decompose it into individual LineStrings
    segments = []
    for i in range(line.GetGeometryCount()):
      segments.extend(split_line_at_length_np(line.GetGeometryRef(i), chunk_length))
    return segments

  elif line.GetGeometryType() == ogr.wkbLineString:
    # Handle a single LineString
    segments = []
    line_points = np.array([line.GetPoint(i)[:2] for i in range(line.GetPointCount())])  # Ensure 2D
    sub_line = ogr.Geometry(ogr.wkbLineString)
    remaining_length = chunk_length

    while len(line_points) > 1:
      p1 = line_points[0]
      p2 = line_points[1]
      segment_length = distance_np(p1, p2)

      if segment_length > remaining_length:
        # Split the line at the remaining_length
        split_point = interpolate_point_np(p1, p2, remaining_length)
        sub_line.AddPoint_2D(p1[0], p1[1])  # Add the point as 2D
        sub_line.AddPoint_2D(split_point[0], split_point[1])  # Add the split point as 2D
        segments.append(sub_line)

        # Update the current start point and remaining length
        line_points[0] = split_point
        sub_line = ogr.Geometry(ogr.wkbLineString)
        remaining_length = chunk_length
      else:
        # Add the whole segment to the current sub-line
        sub_line.AddPoint_2D(p1[0], p1[1])  # Add the point as 2D
        line_points = np.delete(line_points, 0, axis=0)
        remaining_length -= segment_length

    # Add the last segment
    if len(line_points) == 1:
      sub_line.AddPoint_2D(line_points[0][0], line_points[0][1])  # Add the last point as 2D
      segments.append(sub_line)

    return segments

  else:
    raise ValueError("Input must be a LINESTRING or MULTILINESTRING")

