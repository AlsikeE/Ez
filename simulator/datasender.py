#coding:utf-8
from mininet.net import Mininet
from mininet.topo import LinearTopo
from mininet.cli import CLI

from misc import constants
# from eventlet import greenthread
import argparse
import threading
import re
from time import sleep


import logging
logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("./hahahahahlog.txt")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


IPERF_SERVER_LOG_DIR = '/root/ez-segway/logs/iperflogs/server/'
IPERF_CLIENT_LOG_DIR = '/root/ez-segway/logs/iperflogs/client/'
class DataSender(object):
    def __init__(self,net, filepath, wait_time):
        self.net = net
        self.filepath = filepath
        self.wait_time = wait_time
        self.conf = []#all flows' confs

        self.srv_ports = [] #(server,port)
    
    def read_conf(self,filepath):
        f = open(filepath, 'r')
        line  = f.readline()
        while line:
            des = line.strip('\n').split("\t")
            nodes_index =  des[1].strip('(').strip(')').split(',')
            logger.info("hhhhhhhhhhhhhhhhhhhhhhhhhhh")
            logger.info(nodes_index)
            hosts = (self.net.hosts[int(nodes_index[0])], self.net.hosts[int(nodes_index[1])])
            logger.info(hosts)
            obj = dict()
            obj['uuid'] = des[0]
            obj['hosts'] = hosts
            obj['port'] = int(des[2])
            obj['vol'] = (des[3] + 'M')
            obj['seconds'] = float(des[4])
            obj['goal'] = float(des[5])
            self.conf.append(obj)
            line  = f.readline()
        # return self.conf

    def _iperf(self, hosts, l4Type="UDP", udpBw='10M', fmt=None, seconds=10, port=5001,uuid=None):
        server, client = hosts
        if((server,port) not in self.srv_ports):
            self.srv_ports.append((server,port))
            logger.info('mxdhhhhhhhhhhhhhhhhhhh')
            logger.info('iperf -s -u -p %d -i 1 > '%port +IPERF_SERVER_LOG_DIR+'server%s.txt&'% uuid)



# 'iperf -s -u -p %d -i 1 > '%port +IPERF_SERVER_LOG_DIR+'server%s.txt&'% uuid

            server.cmd('iperf -s -u -p %d -i 5 > '%port +IPERF_SERVER_LOG_DIR+'server%s.txt&'% uuid)
            logger.info('operf -s -p %d' %port)

        iperfArgs = 'iperf -p %d ' % port
        bwArgs = ''
        if l4Type == 'UDP':
            iperfArgs += '-u '
            bwArgs = '-b ' + udpBw + ' '
        elif l4Type != 'TCP':
            raise Exception( 'Unexpected l4 type: %s' % l4Type )
        if fmt:
            iperfArgs += '-f %s ' % fmt
        if l4Type == 'TCP':
            if not waitListening( client, server.IP(), port ):
                raise Exception( 'Could not connect to iperf on port %d'
                                 % port )
        client.cmd( iperfArgs + '-t %d -i 5 -c ' % seconds +
                             server.IP() + ' ' + bwArgs +' > ' + IPERF_CLIENT_LOG_DIR +'client%s.txt &'%uuid)
        logger.info(iperfArgs + '-t %d -c ' % seconds +
                             server.IP() + ' ' + bwArgs)


    def send_iperfs(self):
        sleep(self.wait_time)
        for c in self.conf:
            self._iperf(hosts=c['hosts'], l4Type="UDP", udpBw=c['vol'], seconds=c['seconds'], port=c['port'],uuid=c['uuid'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ctrl')
    parser.add_argument('--iperf', nargs='?',
                        type=int, default=0)
    parser.add_argument('--filepath', nargs='?',
                        type=str, default=None)
    args = parser.parse_args()

    iperf = args.iperf
    filepath = args.filepath
    print(filepath)
    wait_time = 10
    Linear4 = LinearTopo(k=4)
    net = Mininet(topo=Linear4)
    net.start()
    
    if(filepath):
        ds = DataSender(net, filepath, wait_time)
        ds.read_conf(ds.filepath)
        logger.info(ds.conf)
    if(iperf):
        ds.send_iperfs()    
    CLI(net)
    # net.pingAll()
    net.stop()
