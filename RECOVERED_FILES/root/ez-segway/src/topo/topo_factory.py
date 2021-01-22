from triangle import Triangle
from b4 import B4
from internet2 import Internet2
from example import Example
from rf_6462 import rf_6462
from get_random_topo import Randomhaha

DATADIR = '/root/ez-segway/data/randomhaha/'

class TopoFactory(object):
    @staticmethod
    def create_topo(topo_name):
        return topos[topo_name]()


# topos = { "triangle": (lambda: Triangle()), "b4": (lambda: B4()),
#           "i2": (lambda: Internet2()), "ex": (lambda: Example()),
#           "6462": (lambda: rf_6462())}
        

topos = { "triangle": (lambda: Triangle()), "b4": (lambda: B4()),
          "i2": (lambda: Internet2()), "ex": (lambda: Example()),
          "6462": (lambda: rf_6462()),"randomhaha":(lambda: Randomhaha(DATADIR+'topo.intra',DATADIR+'latencies.intra'))}
