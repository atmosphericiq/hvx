import math
import uuid
from PySpice.Spice.Netlist import Circuit, SubCircuit
from PySpice.Unit import *
from PySpice.Logging.Logging import setup_logging
from PySpice.Probe.Plot import plot
from MetalPipelineTransmissionSegment import MetalPipelineTransmissionSegment

class PipelineNetwork:

  def __init__(self, name, substrate='CARBON_STEEL'):
    self.name = name
    self.circuit = Circuit(self.name)
    self.substrate = substrate
    self._x_iter = 1
    self._v_iter = 1

  def get_node_count(self):
    return len(self.circuit.nodes)

  def add_dc_source(self, name, positive_node, negative_node, voltage):
    self.circuit.V(name, positive_node, negative_node, voltage)

  def add_weld_to_weld(self, pipe_od_m, pipe_wallthickness_m, coating_rho, coating_thickness):
    if not self.circuit.has_node('n0'):
      raise Exception('No init node found in the circuit')

    length = 10 
    segment = MetalPipelineTransmissionSegment(length, pipe_od_m, pipe_wallthickness_m, self.substrate)
    segment.set_coating(coating_rho, coating_thickness)
    tl_id = 'tl' + str(self._x_iter)
    circuit.subcircuit(segment.get_transmission_line(tl_id))
    circuit.X(self._x_iter, tl_id, 'n0', circuit.gnd, 'divider')
    self._x_iter += 1

