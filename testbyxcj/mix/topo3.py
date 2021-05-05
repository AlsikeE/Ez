import sys
sys.path.append("../../")
sys.path.append("./")

import argparse
from bricks.basenet import BaseNet
from bricks.basetopo import BaseTopo
from simulator.datasender import DataSender

from mininet.node import RemoteController,OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from itertools import chain, groupby

class FourHosts(BaseTopo):
    def __init__(self):
        BaseTopo.__init__(self)

        hs = [None]
        ss = [None]

        for i in range(0,3):
            hs.append(self.addHost(BaseTopo.get_host_name(i+1)))
        for i in range(0,2):
            ss.append(self.addSwitch(BaseTopo.get_switch_name(i+1)))

        for h in hs[1:3]:
            self.addLink(ss[1],h)
        for h in hs[3:]:
            self.addLink(ss[2],h)
        self.addLink(ss[1],ss[2])
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ctrl')

    # parser.add_argument('--topo', nargs='?',
    #                     type=str, default="triangle")
    parser.add_argument('--iperf', nargs='?',
                        type=int, default=0)
    parser.add_argument('--filepath', nargs='?',
                        type=str, default=None)
    args = parser.parse_args()

    topo = FourHosts()
    net = BaseNet( topo=topo, switch=OVSSwitch, link=TCLink, build=False, autoStaticArp=True )
    c1 = net.addController("c1",controller=RemoteController,ip='127.0.0.1',port=6666)
    c2 = net.addController("c2",controller=RemoteController,ip='127.0.0.1',port=6667)
    print(net.controllers)

    iperf = args.iperf
    filepath = args.filepath
    # print(filepath)
    wait_time = 10

    
    net.build()
    for c in net.controllers:
        c.start()
    s1,s2 = net.switches
    print(s1.ports)
    s1.start([c1])
    s2.start([c2])
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
    # s1,s2 = net.switches
    # print(s1.ports)
    # s1.start([c1])
    # s2.start([c2])
    # c1.start()
    # c2.start()
    net.disable_ipv6()
    # execute iPerl command according to the flow that is generated
    # monitoring packet loss
    ds = None
    if(filepath):
        ds = DataSender(net, filepath, wait_time)
        ds.read_conf(ds.filepath)
    if(iperf):
        ds.send_iperfs()

    CLI( net )
    net.stop()