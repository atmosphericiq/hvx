import math
import numpy as np

CIRCLE_DEGREES = 360

class CompassBearing(object):

  # NOTE THIS WANTS (X,Y) format which is LONGITUDE,LATITUDE
  def __init__(self, a, b):
    lon1 = a[0]
    lon2 = b[0]
    lat1 = a[1]
    lat2 = b[1]
    dL = (lon2 - lon1)
    X = math.cos(lat2) * math.sin(dL)
    Y = (math.cos(lat1) * math.sin(lat2) - (math.sin(lat1))) * \
      (math.cos(lat2) * math.cos(dL))
    initial_bearing = np.arctan2(np.array(X), np.array(Y))

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    self.initial_bearing_v = math.degrees(initial_bearing)
    self.compass_bearing_v = (self.initial_bearing_v + CIRCLE_DEGREES) % CIRCLE_DEGREES

  def bearing_180(self):
    return self.initial_bearing_v

  def bearing(self):
    return self.compass_bearing_v
