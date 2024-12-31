import unittest
import math
from hvx.PipelineNetwork import PipelineNetwork

class PipelineNetworkTest(unittest.TestCase):

  def test_simple(self):
    pl = PipelineNetwork('wolf')
    self.assertEqual(pl.get_node_count(), 1) #always ground node
