import math
from PySpice.Spice.Netlist import Circuit, SubCircuit
from PySpice.Unit import *
from PySpice.Logging.Logging import setup_logging
from PySpice.Probe.Plot import plot

# this represents a simple transmission line
# with a self resistance, a ground resistance, and a self inductance
class TransmissionLine(SubCircuit):
  __nodes__ = ('in_node', 'ground', 'out_node')

  def __init__(self, name, RSELF=0, RGND=0, L=1):
    SubCircuit.__init__(self, name, *self.__nodes__)
    self.R(1, 'in_node', 't2', RSELF)
    self.R(2, 'in_node', 'ground', RGND)
    self.L(3, 't2', 'out_node', L)
