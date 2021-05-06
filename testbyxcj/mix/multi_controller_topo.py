from bricks.basetopo import BaseTopo
from bricks.basenet import BaseNet
# from simulator.datasender import DataSender

from mininet.node import RemoteController,OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from itertools import chain, groupby

import argparse
# DATADIR = '/root/ez-segway/data/randomhaha/'
def read_matrix_from_file(file,type):
    result = []
    with open(file) as f:
        for line in f:
            result.append([type(x) for x in line.strip().split(' ')])
    return result

def read_mapping_from_file(file):
    result = {}
    with open(file) as f:
        for line in f:
            a,b = line.split(':')
            objs = b.split(',')
            result.update({int(a):map(lambda x: int(x),objs)})
    return result

class Multi(BaseTopo):
    "Random topology by me haha."

    def __init__( self, topo_file, latency_file, local_dp_file, dp_host_file):
        "Create custom topo."

        # Initialize topology
        BaseTopo.__init__( self )
        
        self.topo_matrix = read_matrix_from_file(topo_file,int)
        self.latency_matrix = read_matrix_from_file(latency_file, float)
        # self.local_dp = read_mapping_from_file(local_dp_file)
        self.dp_host = read_mapping_from_file(dp_host_file)
        length = len(self.topo_matrix)
        # Add switches
        self.hs = [None]
        self.ss = [None]
        # self.cs = [None]
        for i in range(0, length):
            self.ss.append(self.addSwitch(BaseTopo.get_switch_name(i+1)))
        # Add links
        for i in range(0, length):
            for j in range(i,length):
                if self.latency_matrix[i][j] != 0:
                    self.addLink(self.ss[i+1], self.ss[j+1], delay= self.latency_matrix[i][j], loss=0)

        for (dp,hosts) in self.dp_host.items():
            for h in hosts:
                print((dp,h))
                self.hs.append(self.addHost(BaseTopo.get_host_name(h),ip='10.0.0.' + str(h)))
                print(self.hs[h])
                self.addLink(self.ss[dp],self.hs[h])

        # for c in self.local_dp.keys():
        #     self.cs.append(c)

        

def start_net(topo_file, latency_file, local_dp_file, dp_host_file,baseport):
    topo = Multi(topo_file, latency_file, local_dp_file, dp_host_file)
    net = BaseNet( topo=topo, switch=OVSSwitch, link=TCLink, build=False, autoStaticArp=True )
    local_dp = read_mapping_from_file(local_dp_file)
    # cs = []
    for c in local_dp.keys():
        locals()['c'+str(c)] = net.addController(BaseTopo.get_controller_name(c),controller=RemoteController,ip='127.0.0.1',port=baseport+c)
        # cs.append(locals()['c' + str(c)])
    print(net.controllers)
    # iperf = args.iperf
    # filepath = args.filepath
    # # print(filepath)
    # wait_time = 10
    net.build()
    for c in net.controllers:
        c.start()
    
    
    for (c,dps) in local_dp.items():
        for dp in dps:
            net['s' + str(dp)].start([net['c' + str(c)]])

    started = {}
    for swclass, switches in groupby(
                sorted( net.switches,
                        key=lambda s: str( type( s ) ) ), type ):
            switches = tuple( switches )
            if hasattr( swclass, 'batchStartup' ):
                success = swclass.batchStartup( switches )
                started.update( { s: s for s in success } )
    
    if net.waitConn:
        net.waitConnected( net.waitConn )
    net.disable_ipv6()
    CLI( net )
    net.stop()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='mix')
    parser.add_argument('--matrix', nargs='?',
                        type=str, default='./data/topo.intra')
    parser.add_argument('--latmatrix', nargs='?',
                        type=str, default='./data/latencies.intra')                
    parser.add_argument('--localdp', nargs='?',
                        type=str, default='./data/local_dp.intra')
    parser.add_argument('--dphost', nargs='?',
                        type=str, default='./data/dp_host.intra')
    parser.add_argument('--baseport',nargs='?',
                        type = int,default='6666')
    args = parser.parse_args()
    start_net(args.matrix,args.latmatrix,args.localdp,args.dphost,args.baseport)
    # local_dp = read_mapping_from_file(args.localdp)
    # dp_host = read_mapping_from_file(args.dphost)
    # print(local_dp)
    # print(dp_host)