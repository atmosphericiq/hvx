import unittest
import math
from hvx import MetalPipelineTransmissionSegment

class MetalPipelineTransmissionSegmentTestCase(unittest.TestCase):

  # 100m long, 0.5m outer diameter and 0.01m wall thickness
  # https://www.omnicalculator.com/math/cross-sectional-area
  def test_area_cross_sectional(self):
    mp = MetalPipelineTransmissionSegment(100, 0.5, 0.01, 'CARBON_STEEL')
    expected_area = math.pi * ((0.5 / 2)**2 - ((0.5 - 2 * 0.01) / 2)**2)
    self.assertAlmostEqual(mp._get_cross_sectional_area(), expected_area, places=5)
    self.assertAlmostEqual(mp._get_cross_sectional_area(), 0.0153494, places=4)

  # 100m long, 0.5m outer diameter and 0.01m wall thickness
  def test_total_resistance(self):
    mp = MetalPipelineTransmissionSegment(100, 0.5, 0.01, 'CARBON_STEEL')
    self.assertAlmostEqual(mp._get_total_resistance_of_pipe(), 0.0009289451780465725, places=4)

  # 100m long, 0.5m outer diameter and 0.01m wall thickness
  def test_surface_area(self):
    mp = MetalPipelineTransmissionSegment(100, 0.5, 0.01, 'CARBON_STEEL')
    outer_diameter_surface_area = 157.07963267948966
    self.assertAlmostEqual(mp._get_outer_surface_area(), outer_diameter_surface_area, places=5)

  # 100m long, 0.5m outer diameter and 0.7m wall thickness, should throw error
  def test_invalid_wall_thickness(self):
    with self.assertRaises(ValueError):
      MetalPipelineTransmissionSegment(100, 0.5, 0.7, 'CARBON_STEEL')

  def test_get_resistance_to_ground(self):
    mp = MetalPipelineTransmissionSegment(100, 0.5, 0.01, 'CARBON_STEEL')
    self.assertAlmostEqual(mp._get_outer_surface_area(), 157.08, places=2)
    mp.set_coating(1, 0.001) # 1 ohm-m and 0.001 thickness
    self.assertAlmostEqual(mp._get_resistance_to_ground(), 0.00000637, places=4)

  def test_get_rsistance_to_ground_high_resistance(self):
    mp = MetalPipelineTransmissionSegment(100, 0.5, 0.01, 'CARBON_STEEL')
    self.assertAlmostEqual(mp._get_outer_surface_area(), 157.08, places=2)
    mp.set_coating(100, 0.001)
    self.assertAlmostEqual(mp._get_resistance_to_ground(), 0.000637, places=4)

  # test the inductance function _get_inductance
  def test_get_inductance(self):
    mp = MetalPipelineTransmissionSegment(100, 0.5, 0.01, 'CARBON_STEEL')
    self.assertAlmostEqual(mp._get_inductance(), 0.00000082, places=8)

  def test_get_rsistance_to_ground_very_high_r(self):
    mp = MetalPipelineTransmissionSegment(100, 0.5, 0.01, 'CARBON_STEEL')
    mp.set_coating(1000, 0.001)
    self.assertAlmostEqual(mp._get_resistance_to_ground(), 0.00637, places=4)
