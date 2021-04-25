import sys
import json
import logging
import os
import multiprocessing
import threading
# from queue import Queue
from collections import defaultdict
# from fours_topo import fourswitch
from time import time 
import time
import cPickle as pickle
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import *
from ryu.topology import api
from ryu.lib import hub
from ryu.topology.switches import LLDPPacket

from buffer_manager import BufferManager
import consts

hub.patch()
def extract_topo(Topo):
    t = defaultdict(dict)
    for link in Topo.iterLinks(withKeys=True, withInfo=True):
        src, dst, key, info = link
        if Topo.isSwitch(src) and Topo.isSwitch(dst):
            s = int(src[1:])
            d = int(dst[1:])
            t[s][d] = info['port1']
            t[d][s] = info['port2']
    return t 

class LocalController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(LocalController, self).__init__(*args, **kwargs)

        # self.topo = extract_topo(fourswitch())
        self.topo = {}
        self.time = 0
        self.datapaths={}
        self.eth_to_port = {}
        self.flows_final = False

        self.buffer = dict()
        
        self.bm = None
        self.conn = None
        self.thread = None
        # self.bm.setDaemon(True)
        self.init_my_bm()
        self.packts_buffed = 0

        # self.queue = Queue()
        # logger.init('buftest' ,logging.INFO)

    def init_my_bm(self):
        self.conn, bm_conn = multiprocessing.Pipe()
        self.bm = BufferManager(name="bm",conn = bm_conn)
        # self.bm = BufferManager(name="bm")

        # self.thread = threading.Thread(target=self.listen_to_my_conn)
        # self.thread.start()
        hub.spawn(self.listen_to_my_conn)

        self.bm.start()
        

    def listen_to_my_conn(self):
        while(True):
            # print("but in the list" + str(len(self.pkg_to_save)))
            packet_to_me = None
            try:
                packet_to_me = self.conn.recv()
            except Exception as err:
                # print("I'm waiting for your bilibili")
                time.sleep(0.01) 
                pass
            if(packet_to_me):
                packet = pickle.loads(packet_to_me)
                # print(packet)
                dpid = packet["dpid"]
                pkg = packet["pkg"]
                in_port = packet["in_port"]
                self.send_back(pkg,dpid,in_port)
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id     
        self.datapaths[dpid]=datapath
        print(self.datapaths)
        print(ofproto.OFPP_CONTROLLER)
        actions = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
        # actions = [parser.OFPActionOutput(port=0 ,max_len=ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(type_=ofproto.OFPIT_APPLY_ACTIONS,actions=actions)]
        mod = parser.OFPFlowMod(datapath=datapath,priority=0,match=parser.OFPMatch(),instructions=inst)
        datapath.send_msg(mod) 
        # buf_match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ipv4_src="192.168.1.1",ipv4_dst="192.168.1.2")
        # buf_match = parser.OFPMatch(in_port=1)
        # self.send_buf_cmd(self.datapaths[1],buf_match)
        # buf_match = parser.OFPMatch(in_port=2)
        # self.send_buf_cmd(self.datapaths[1],buf_match)
        self.disable_dhcp(datapath)
        # self.install(datapath)

    

    @set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
    def _barrier_reply_handler(self,ev):
        #nononononono   don't 
        print(ev.msg)
        print("---------------------------------------------------------")
        datapath = ev.msg.datapath
        cmd_pop = self.make_buf_message(consts.BUF_POP,src="10.0.0.1",dst="10.0.0.2",dst_port=None,dpid=None,pkg=None,in_port=None)
        try:
            self.conn.send(cmd_pop)
        except Exception as e:
            print("Error in barrier!!!!!!!!!!!")
            print(e)
        # if(len(self.buffer)>0):
        #     self.send_back(1,datapath)
        # self.install34(self.datapaths[1])

    def install(self,datapath):
        # time.sleep(2)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        priority = 2
        buffer_id = ofproto.OFP_NO_BUFFER
        match = parser.OFPMatch(in_port=1)
        actions = [parser.OFPActionOutput(2)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
        # time.sleep(10)
        # datapath.send_barrier()
        match = parser.OFPMatch(in_port=2)
        actions = [parser.OFPActionOutput(1)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

        # datapath.send_barrier()
        req = parser.OFPBarrierRequest(datapath,xid=1)
        datapath.send_msg(req)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        pkt_in = ev.msg
        datapath = pkt_in.datapath
        ofproto = datapath.ofproto
        in_port = pkt_in.match["in_port"]
        print(in_port)
        src,dst,dst_port,dpid,pkg = self.identify_pkg(pkt_in)
        self.packts_buffed += 1
        if(self.packts_buffed == 100):
            self.install(self.datapaths[1])
        # print(pkg)
        # self.bm.pkg_to_save.append(pkt_in)
        cmd_to_bm = self.make_buf_message(consts.BUF_PUSH,src,dst,dst_port=dst_port,dpid=dpid,pkg=pkg,in_port=in_port)
        try: 
            self.conn.send(cmd_to_bm)#for process
        except Exception as e:
            print("Error!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(e)
        # ("go and save")

    def make_buf_message(self,msg_type,src,dst,dst_port,dpid,pkg,in_port):
        return pickle.dumps({
            "msg_type":msg_type,
            "src":src,
            "dst":dst,
            "dst_port":dst_port,
            "dpid":dpid,
            "pkg":pkg,
            "in_port":in_port
        })

    

    def cal_update(self,src,dst,old,new):
        n_buf = new[0]
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=ipAdd(dst))
        actions_buf = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
        dp_buf = self.datapaths[n_buf]
        self.add_flow(datapath=dp_buf,priority=233,match=match,actions=actions)

        match_remove = parser.OFPMatch(eth_type=ether_types.ETH_TYPEk_IP, ipv4_dst=ipAdd(dst))
        for node in old:
            dp = self.datapaths[node]
            self.remove_flow(datapath=dp,priority=1,match=match)

        new_reverse = new[::-1]
        for node in new:
            dp = self.datapaths[node]
            actions = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath=dp,priority=1,match=match,actions=actions)

    

    #drop packet for udp 68
    def disable_dhcp(self,datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match_dhcp = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ip_proto=in_proto.IPPROTO_UDP,udp_src=68,udp_dst=67)
        instruction = [
            parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS,[])
        ]
        mod = parser.OFPFlowMod(datapath,priority=1,match=match_dhcp,instructions=instruction)
        datapath.send_msg(mod)
    
    def remove_flow(self, datapath, priority, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE,
                                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                                match=match, priority=priority)
        datapath.send_msg(mod)


    def send_back(self,pkg,dpid,in_port):
        datapath = self.datapaths[dpid]
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        actions = [parser.OFPActionOutput(port=ofproto.OFPP_TABLE)]
        req = parser.OFPPacketOut(datapath,in_port=in_port,buffer_id=ofproto.OFP_NO_BUFFER,actions=actions,data=pkg)
        datapath.send_msg(req)
        # print("sent back")


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _features_handler(self,ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id     
        self.datapaths[dpid]=datapath
        print("haha"+str(self.datapaths))
        actions = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(type_=ofproto.OFPIT_APPLY_ACTIONS,actions=actions)]
        mod = parser.OFPFlowMod(datapath=datapath,priority=0,match=parser.OFPMatch(),instructions=inst)
        datapath.send_msg(mod)

    def save_to_buffer(self,flow_id,pkg):
        if (pkg.datapath.id):
            flow_id = pkg.datapath.id
        if(not self.buffer.has_key(flow_id)):
            self.buffer[flow_id] = []
        print(flow_id)
        
        self.buffer[flow_id].append(pkg)
        print(len(self.buffer[flow_id]))
    
    def identify_pkg(self,pkt_in):
        (src,dst,dst_port,dpid,pkg) = ("","",None,None,None)
        dpid = pkt_in.datapath.id
        pkg = packet.Packet(pkt_in.data)
        # pkg = pkt_in.data
        ipkg = pkg.get_protocol(ipv4.ipv4)
        if(ipkg):
            src = ipkg.src
            dst = ipkg.dst
            upkg = pkg.get_protocol(udp.udp) or pkg.get_protocol(tcp.tcp) #udp and tcp are not seperated
            if(upkg):
                dst_port = upkg.dst_port
        # print(ipkg)
        return src,dst,dst_port,dpid,pkg


    def add_flow(self,datapath,priority,match):
        pass

    def start_update(self):
        old = [0,1,2]
        new = [0,3,2]
        src = 0
        dst = 2
        self.cal_update(src,dst,old,new)

 
            





    
