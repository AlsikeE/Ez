import sys
import json
import logging
import os


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import *
from ryu.topology import api
from ryu.lib import hub


class BufferManager(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self):
        super(BufferManager, self).__init__()
        self.buffer = dict()
        self.datapaths = dict()
    
    def save_to_buffer(self,flow_id,pkg):
        if (pkg.datapath.id):
            flow_id = pkg.datapath.id
        if(not self.buffer.has_key(flow_id)):
            self.buffer[flow_id] = []
        print(flow_id)
        
        self.buffer[flow_id].append(pkg)
        print(len(self.buffer[flow_id]))
    
    def identify_pkg(self,pkg):
        datapath = pkg.datapath
        in_port = pkg.match['in_port']
        dpid = datapath.id
        msg = packet.Packet(pkg.data)
        return msg,datapath

    def send_back(self,flow_id,dp):
        for msg in self.buffer[flow_id]:
            print(msg)
            datapath = dp
            parser = datapath.ofproto_parser
            in_port = msg.match['in_port']
            ofproto = datapath.ofproto
            actions = [parser.OFPActionOutput(port=ofproto.OFPP_TABLE)]
            req = parser.OFPPacketOut(datapath,in_port=in_port,buffer_id=ofproto.OFP_NO_BUFFER,actions=actions,data=msg.data)
            # out_port = self.eth_to_port[dpid][dst]
            datapath.send_msg(req)
            self.buffer[flow_id].pop(0)
            print("sent back")

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
        

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        pkg = ev.msg
        datapath = pkg.datapath
        ofproto = datapath.ofproto
        msg,dp= self.identify_pkg(pkg)
        # # dp_buf = msg.datapath
        # print("jiexi----------")
        print("dp is " + str(dp))
        print("reason is" +str(pkg.reason == ofproto.OFPR_NO_MATCH))
        self.save_to_buffer(0,pkg)


    @set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
    def _barrier_reply_handler(self,ev):
        #nononononono   don't 
        print("---------------------------------------------------------")
        datapath = ev.msg.datapath
        if(len(self.buffer)>0):
            self.send_back(1,datapath)
    


        