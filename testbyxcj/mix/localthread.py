import sys
sys.path.append("../")
import logging
import redis

from collections import defaultdict
from time import time 
import time
import cPickle as pickle
import json
import struct
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import *
from ryu.lib import hub

import eventlet
from eventlet import wsgi
from eventlet.green import socket
from bricks.flow_des import FlowDes
from bricks.message import InfoMessage,UpdateMessageByFlow,FeedbackMessge
import consts
import tools
import logging
import logger as logger

class LocalController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(LocalController, self).__init__(*args, **kwargs)
        logger.init('./localhapi.log',logging.INFO)
        self.logger=logger.getLogger('local',logging.INFO)

        self.local_id = 0 #remember change me !
        self.topo = {}
        self.time = 0
        self.datapaths={}

        self.neighbors = {}#port:dpid
        self.hosts = {"10.0.0.1":1,
                      "10.0.0.2":2}#ip:port
        # self.flows_final = False
        self.packts_buffed = 0 #temp for update trigger

        self.pool = redis.ConnectionPool(host='localhost',port=6379)
        self.rds = redis.Redis(connection_pool=self.pool)
        self.packets_to_save = []

        flowdes0 = FlowDes("10.0.0.1","10.0.0.2",5001,[],[0,1,2],consts.BUF,'udp')
        flowdes0.up_step = consts.BUF_ADD
        self.flows = {"10.0.0.110.0.0.25001":flowdes0} # flow_id(src,dst,dst_port):{src,dst,dst_port,update_type:"BUF",xids=[],doing="BUF_DEL"}
        self.xid_find_flow = {} #xid:[flow_id]

        self.conn_with_global = socket.socket()
        hub.spawn_after(5,self.conn_with_global.connect,('127.0.0.1',9999))

        hub.spawn(self.run_server)
#methods for buffer
    def get_from_buffer(self,key):
        msg = self.rds.lpop(key)    
        while(msg):
            obj = pickle.loads(msg)
            pkg = obj["pkg"]
            dpid = obj["dpid"]
            in_port = obj["in_port"]
            self.send_back(pkg,dpid,in_port)
            msg = self.rds.lpop(key)

    def save_to_buffer(self,pkt_in):
        src,dst,dst_port,dpid,pkg = self.identify_pkg(pkt_in)
        in_port = pkt_in.match["in_port"]
        key = self.make_buf_key(src,dst,dst_port)
        value = pickle.dumps({
            "dpid":dpid,
            "pkg":pkg,
            "in_port":in_port
        })
        self.rds.rpush(key,value)
    
    def make_buf_key(self,src,dst,dst_port):
        return src + dst + str(dst_port)

    def send_back(self,pkg,dpid,in_port):
        datapath = self.datapaths[dpid]
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        actions = [parser.OFPActionOutput(port=ofproto.OFPP_TABLE)]
        req = parser.OFPPacketOut(datapath,in_port=in_port,buffer_id=ofproto.OFP_NO_BUFFER,actions=actions,data=pkg)
        datapath.send_msg(req)
    
    def identify_pkg(self,pkt_in):
        (src,dst,dst_port,dpid,pkg) = ("","",None,None,None)
        dpid = pkt_in.datapath.id
        pkg = packet.Packet(pkt_in.data)
        ipkg = pkg.get_protocol(ipv4.ipv4)
        if(ipkg):
            src = ipkg.src
            dst = ipkg.dst
            (upkg,tpkg) = (None,None)

            try:
                upkg = pkg.get_protocol(udp.udp) 
                dst_port = upkg.dst_port
            except:
                pass#not udp
            try:
                tpkg = pkg.get_protocol(tcp.tcp) 
                dst_port = tpkg.dst_port
            except:
                pass#udp and tcp are not seperated
                
        # print(ipkg)
        return src,dst,dst_port,dpid,pkg


#methods for control
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

        self.disable_dhcp(datapath)
        
        # self.install(datapath)

    @set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
    def _barrier_reply_handler(self,ev):
        print("---------------------------------------------------------")
        print("hello this is reply for xid" +str(ev.msg.xid))
        xid = ev.msg.xid
        flows_move_on = self.get_flows_move_on(xid)

        #both global and local need this operation
        for f in flows_move_on:
            if(f.up_type == consts.BUF and f.up_step == consts.BUF_ADD):
                pop_key = f.flow_id
                hub.spawn(self.get_from_buffer,pop_key)
                f.barrs_wait = []
                f.barrs_ok = 0
                self.xid_find_flow[xid].remove(pop_key)
                fb_msg = FeedbackMessge(f.flow_id,self.local_id)
                self.send_fb_to_global(fb_msg)
            # elif(f.up_type == consts.BUF and f.up_step == consts.BUF_DEL):
            # elif (f.up_step)
        # datapath = ev.msg.datapath
        # pop_key = "10.0.0.110.0.0.25001"
        # hub.spawn(self.get_from_buffer,pop_key)
      

    #get the flows move on
    #should be in global
    def get_flows_move_on(self,xid):
        flows = self.xid_find_flow[xid]
        flows_move_on = []
        for f_name in flows:
            f = self.flows[f_name]
            f.barrs_ok += 1
            if f.barrs_ok == len(f.barrs_wait):
                flows_move_on.append(f)
        return flows_move_on    

    def ana_new_flows(self,new_flows):
        for nf in new_flows:
            #should be from global to local
            self.flows.update({nf.flow_id:nf})

    def any_up_msg(self,up_msg):
        f = self.flows[up_msg.flow_id]
        f.up_step = up_msg.up_step
        to_barr_dp = []
        self.logger.info("opguonai")
        self.logger.info(str(up_msg))
        for d in up_msg.to_del:
            dplast,dpid,dpnext = d
            datapath = self.datapaths[dpid]
            if (dpid not in to_barr_dp):
                to_barr_dp.append(dpid)
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ipv4_dst=f.dst,ipv4_src=f.src)
            self.remove_flow(datapath,2,match)
            match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ipv4_dst=f.src,ipv4_src=f.dst)
            self.remove_flow(datapath,2,match)

        for a in up_msg.to_add:
            dplast,dpid,dpnext = a
            print(dpid)
            if (dpid not in to_barr_dp):
                to_barr_dp.append(dpid)
            print("haha" + str(self.datapaths))
            datapath = self.datapaths[dpid]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            trans_pro  = None
            server_port = None
            
            if(f.trans_type=='udp'):
                trans_pro =in_proto.IPPROTO_UDP
            elif(f.trans_type=='tcp'):
                trans_pro =in_proto.IPPROTO_TCP
            elif(f.trans_type == 'icmp'):
                trans_pro =in_proto.IPPROTO_ICMP

            if(f.dst_port):
                server_port = f.dst_port

            match_dict = dict(eth_type=ether_types.ETH_TYPE_IP,ipv4_dst=f.dst,ipv4_src=f.src)
            reverse_dict = dict(eth_type=ether_types.ETH_TYPE_IP,ipv4_dst=f.src,ipv4_src=f.dst)
            if(trans_pro):
                match_dict['ip_proto'] = trans_pro
                reverse_dict['ip_proto'] = trans_pro
            if(server_port):
                index1 = f.trans_type + '_dst'
                index2 = f.trans_type + '_src'
                match_dict[index1] = f.dst_port
                reverse_dict[index2] = f.dst_port

            match = parser.OFPMatch(**match_dict)
            match_reverse = parser.OFPMatch(**reverse_dict)
            self.logger.info(str(match))
            self.logger.info(str(match_reverse))
            out = self.hosts[f.dst] if(dpid == dpnext) else self.neighbors[dpnext]
            out_reverse = self.hosts[f.src] if(dpid==dplast) else self.neighbors[dplast]
            actions = [parser.OFPActionOutput(out)]
            actions_reverse = [parser.OFPActionOutput(out_reverse)]
            priority = 2
            self.add_flow(datapath,priority,match,actions)
            self.add_flow(datapath,priority,match_reverse,actions_reverse)
        
        for dpid in to_barr_dp:
            self.send_barrier(self.datapaths[dpid],f.up_step,f.flow_id)

    def process_info_msg(self,info_msg):
        new_flows = info_msg.new_flows
        if(len(new_flows)):
            self.ana_new_flows(new_flows)
        for up_msg in info_msg.ums:
            self.any_up_msg(up_msg)
    
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        pkt_in = ev.msg
        datapath = pkt_in.datapath
        ofproto = datapath.ofproto
        in_port = pkt_in.match["in_port"]
        print(in_port)
        src,dst,dst_port,dpid,pkg = self.identify_pkg(pkt_in)

        #for simulating the latency of updateing
        self.packts_buffed += 1
        if(self.packts_buffed == 30):
            # self.install(self.datapaths[1])
            self.install()

        # hub.spawn(self.save_to_buffer,pkt_in)
        self.save_to_buffer(pkt_in)

#methods for update
    def send_barrier(self,datapath,up_step,flow_id):
        if(not self.xid_find_flow):
            xid = 1
        else:
            xid = max(self.xid_find_flow.keys()) + 1

        parser = datapath.ofproto_parser
        req = parser.OFPBarrierRequest(datapath,xid)
        datapath.send_msg(req)
        print("i've sent xid barrier" + str(xid))

        if(not self.xid_find_flow or (not self.xid_find_flow.get(xid))):
            self.xid_find_flow[xid] = [flow_id]
        else:
            self.xid_find_flow[xid].append(flow_id)


        self.flows[flow_id].barrs_wait.append(xid)
        print(self.flows['10.0.0.110.0.0.25001'].barrs_wait)
        print(self.xid_find_flow)

    def remove_flow(self, datapath, priority, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE,
                                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                                match=match, priority=priority)
        datapath.send_msg(mod)

    def add_flow(self,datapath,priority,match,actions):
        self.logger.info(match)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        buffer_id = ofproto.OFP_NO_BUFFER
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

#methods for comm with global
    def send_fb_to_global(self,fb_msg):
        str_message = pickle.dumps(fb_msg)
        msg_len = len(str_message)
        data = struct.pack('L', msg_len) + str_message
        self.conn_with_global.sendall(data)

#methods for experiment
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

#methods for demo
    def connection_handler(self,fd):
        self.logger.info("--------------a connection-------------------")
        while True:
            data = fd.recv(8)
            print("thisis " + data)
            if(len(data) == 0):
                fd.close()
                return
            msg_len = struct.unpack('L',data)[0]
            self.logger.info(msg_len)
            more_msg = tools.recv_size(fd,msg_len)
            msg = pickle.loads(more_msg)
            hub.spawn(self.process_info_msg,msg)
    
    def run_server(self):
        server = eventlet.listen(('127.0.0.1', 6000 + self.local_id))
        # server = eventlet.listen(('127.0.0.1', 8700 + self.switch_id))
        while True:
            fd, addr = server.accept()  #accept returns (conn,address) so fd is a connection
            self.logger.info("receive a connection")
            self.connection_handler(fd)            





    