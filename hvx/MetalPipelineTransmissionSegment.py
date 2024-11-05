import math
import matplotlib.pyplot as plt
from PySpice.Spice.Netlist import Circuit, SubCircuit
from PySpice.Unit import *
from PySpice.Logging.Logging import setup_logging
from PySpice.Probe.Plot import plot
from .TransmissionLine import TransmissionLine

setup_logging()

MU_0 = 4 * math.pi * 1e-7  # Permeability of free space in H/m
RESISTIVITY_OHM_M = {
  'CARBON_STEEL': 1.43e-7,
  'COPPER': 1.68e-8,
  'ALUMINUM': 2.82e-8,
  'NICKEL': 6.99e-8,
  'IRON': 9.71e-8,
  'LEAD': 2.20e-7
}

# this represnets a metal pipeline as a 
# transmission line, so it takes as inputs:
# length = the length of the pipeline, used to calculate L and RSELF
# diameter = the diameter of the pipeline, used to calculate L and RSELF
# substrate = the material of the pipeline, used to calculate RSELF
# ground resistance = the resistance of the ground used to calculate RGND
class MetalPipelineTransmissionSegment:

  def __init__(self, length_m, outer_diameter_m, wall_thickness_m, 
    substrate, coating_rho=None, coating_thickness_m=None):

    if wall_thickness_m > outer_diameter_m:
      raise ValueError('Wall thickness cannot be greater than outer diameter')

    self.wall_thickness_m = wall_thickness_m
    self.length_m = float(length_m)
    self.substrate = substrate
    self.outer_diameter_m = outer_diameter_m
    self.inner_diameter_m = outer_diameter_m - (2.0 * wall_thickness_m)
    self.coating_rho = coating_rho
    self.coating_thickness_m = coating_thickness_m

  # set some of the coating parameters
  # rho = resistivity of the coating
  # thickness = thickness of the coating in m
  def set_coating(self, rho, thickness_m):
    if thickness_m > 0.01:
      raise ValueError('Coating thickness is probably too large. Are units meters?')

    self.coating_rho = rho
    self.coating_thickness_m = thickness_m

  def _get_outer_surface_area(self):
    radius = self.outer_diameter_m / 2.0
    return 2 * math.pi * radius * self.length_m

  def _get_inductance(self):
    outer_radius = self.outer_diameter_m / 2
    inner_radius = outer_radius - self.wall_thickness_m
    inductance = (MU_0 * self.length_m / (2 * math.pi)) * math.log(outer_radius / inner_radius)
    return inductance

  def _get_total_resistance_of_pipe(self):
    resistivity = RESISTIVITY_OHM_M.get(self.substrate, None)
    assert resistivity is not None
    return (resistivity * self.length_m) / self._get_cross_sectional_area()

  # get the resistance to the ground, through the coating
  # assuming 14 mils coating thickness 0.3556 mm×0.001 m/mm=0.0003556 m
  # this will treat the coating like a cylinder around the pipe
  # which is itself a resistor, basically
  def _get_resistance_to_ground(self):
    surface_area = self._get_outer_surface_area()
    if self.coating_rho is None:
      raise ValueError('coating_rho must be set')
    if self.coating_thickness_m is None:
      raise ValueError('coating_thickness_m must be set')
    return (self.coating_rho * self.coating_thickness_m) / surface_area

  # calculate the area of the hollow pipe
  def _get_cross_sectional_area(self):
    outer_radius_m = self.outer_diameter_m / 2.0
    inner_radius_m = self.inner_diameter_m / 2.0
    return math.pi * (outer_radius_m**2.0 - inner_radius_m**2.0)

  def get_transmission_line(self, name):
    assert self.coating_rho is not None

    self_resistance = self._get_total_resistance_of_pipe()
    gnd_resistance = self._get_resistance_to_ground()
    total_inductance = self._get_inductance()

    return TransmissionLine(name, RSELF=self_resistance, 
      RGND=gnd_resistance, L=total_inductance)
