#!/usr/bin/python
 
import sys

import time
import os
from mininet.net import Mininet
from mininet.node import RemoteController,OVSSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.topo import Topo



def topology(remoteip):
    # topo = SingleSwitchTopo( n=4, lossy=lossy )
    "***Create a network."
    net = Mininet(controller=RemoteController,switch=OVSSwitch,autoStaticArp=True)
     
    print("***Creating hosts")
    h1 = net.addHost("h1",mac="00:00:00:00:00:01",ip="192.168.1.1/16")
    h2 = net.addHost("h2",mac="00:00:00:00:00:02",ip="192.168.1.2/16")
    h3 = net.addHost("h3",mac="00:00:00:00:00:03",ip="192.168.1.3/16")
    h4 = net.addHost("h4",mac="00:00:00:00:00:04",ip="192.168.1.4/16")
     
    print("***Creating switches")
    s1 = net.addSwitch("s1")
    # s99 = net.addSwitch("s99")
     
    c1 = net.addController("c1",controller=RemoteController,ip=remoteip,port=6666)
    # c99 = net.addController("c99",controller=RemoteController,ip=remoteip,port=6667)
 
    print("***Create links")
    #switchLinkOpts = dict(bw=10,delay="1ms")
    #hostLinksOpts = dict(bw=100)
     
    net.addLink(s1, h1, 1)
    net.addLink(s1, h2, 2)
    net.addLink(s1, h3, 3)
    net.addLink(s1, h4, 4)
    # net.addLink(s1, s99, 99, 1)

    #disable arp and ipv6
    for h in net.hosts:
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    for sw in net.switches:
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
 
    print("***Building network.")

    net.start()
    # s99.start([c99])
    # s3.start([c2,c2])
    # s4.start([c2,c2])
     
    print("***Starting network")
    # c1.start()
    # c99.start()
    CLI(net)
     
    print("***Stoping network")
    net.stop()



if __name__ == "__main__":
    setLogLevel("info")
    topology("127.0.0.1")