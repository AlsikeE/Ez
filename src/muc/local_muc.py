import sys
import socket
import json
import logging
import os

sys.path.append(os.path.realpath("../../simulator"))
sys.path.append('/root/ez-segway')
import simulator.misc.logger as logger

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
 
class LocalController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(LocalController, self).__init__(*args, **kwargs)
        
        self.topo = {}
        self.status = False
        self.client_id = 1
        self.send_queue = hub.Queue(16)
        self.socket = socket.socket()
        self.start_serve('127.0.0.1', 9999)
        self.time = 0

        logger.init('/root/ez-segway/logs/local-muc/locallog%d'% (self.client_id +1 ) ,logging.INFO)
 
    def start_serve(self, server_addr, server_port):
        try:
            self.socket.connect((server_addr, server_port))
            self.status = True
            hub.spawn(self._rece_loop)
            hub.spawn(self._send_loop)
        except Exception as e:
            raise e
 
    def _send_loop(self):
        try:
            while self.status:
                message = self.send_queue.get()
                message += '\n'
                self.socket.sendall(message)
        finally:
            self.send_queue = None
 
    def _rece_loop(self):
        while self.status:
            try:
                message = self.socket.recv(128)
                if len(message) == 0:
                    self.logger.info('connection fail, close')
                    self.status = False
                    break
                data = message.split("\n")
                for temp in data:
                    print (temp)
                    msg = json.loads(temp)
                    if msg['cmd'] == 'set_id':
                        self.client_id = msg['client_id']
 
            except ValueError:
                print('Value error for %s, len: %d', message, len(message))
 
    def send(self, msg):
        if self.send_queue != None:
            self.send_queue.put(msg)
 
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id     
        self.logger.info("switch %s connect to controller",datapath.id)
        actions = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(type_=ofproto.OFPIT_APPLY_ACTIONS,actions=actions)]
        mod = parser.OFPFlowMod(datapath=datapath,priority=0,match=parser.OFPMatch(),instructions=inst)
        datapath.send_msg(mod) 
        self.send_features(msg)
    
    def send_features(self, features):
        self.logger.info("------------features--------")
        self.logger.info(features)
        status_msg = json.dumps({"status":"ok i'm fine",
                      "fb":None,
                      "topo":None})
        self.send(status_msg)
    

    def send_feedback(self, fb):
        fb_msg = json.dumps({"status":None,
                  "fb":fb})
        self.send(fb_msg)
     
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
         
        try:
            #LLDP handler
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            dst_dpid, dst_port_no = datapath.id, msg.match['in_port']
            self.add_topo(src_dpid,dst_dpid,src_port_no,dst_port_no)
            link = api.get_link(self)
            print (self.topo)
            for i in link:
                src = i.src
                dst = i.dst
                self.topo[(src.dpid,dst.dpid)] = (src.port_no,dst.port_no)
             
        except LLDPPacket.LLDPUnknownFormat:
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocols(ethernet.ethernet)[0]
            mac = eth.src
            dpid,port = datapath.id,msg.match['in_port']
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                    in_port=port, actions=actions, data=data)
            datapath.send_msg(out)
    


    def add_topo(self,src_dpid,dst_dpid,src_port_no,dst_port_no):
        msg = json.dumps({"topo":{
            'cmd': 'add_topo',
            'src_dpid': src_dpid,
            'dst_dpid': dst_dpid,
            'src_port_no': src_port_no,
            'dst_port_no': dst_port_no
            },
            "fb": None,
            "status": None}
        )
        self.send(msg)