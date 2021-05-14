import sys
import os
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
from multi_controller_topo import get_local_neighbors,get_local_hosts
import consts
import tools
import logging
import logger as logger

class LocalController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(LocalController, self).__init__(*args, **kwargs)
        logger.init('./localhapi.log',logging.INFO)
        
        
        self.local_id = int(os.environ.get("LOCAL_ID", 0))
        topofile = os.environ.get("TOPO", './data/topo.intra')
        local_dpfile = os.environ.get('LOCAL_DP','./data/local_dp.intra')
        dp_hostfile = os.environ.get('DP_HOST','./data/dp_host.intra')
        self.buf_size = os.environ.get('BUF_SIZE',10000)
        dp_tcamfile = os.environ.get('TCAM_SIZE','./data/dp_tcam.intra')

        self.redis_port = os.environ.get('REDIS_PORT',6379)
        self.logger=logger.getLogger('local' + str(self.local_id),logging.INFO)
        self.topo = None
        # self.topo_input = os.environ.get("TOPO_INPUT", 1)
        # self.local_id = 0 #remember change me !
        self.neighbors = get_local_neighbors(topofile,local_dpfile,self.local_id)
        self.hosts = get_local_hosts(self.neighbors,dp_hostfile)
        self.dp_tcam_size = self.read_dp_tcam(dp_tcamfile)
        self.logger.info(self.neighbors)
        self.logger.info(self.hosts)
        self.time = 0
        self.datapaths={}

        # self.neighbors = {1:{2:3}}#dpid:port
        # self.hosts = {1:{"10.0.0.1":1,
        #               "10.0.0.2":2}}#ip:port

        self.packts_buffed = 0 #temp for update trigger

        self.pool = redis.ConnectionPool(host='localhost',port=self.redis_port)
        self.rds = redis.Redis(connection_pool=self.pool)
        self.packets_to_save = []

        # flowdes0 = FlowDes("10.0.0.1","10.0.0.2",5001,[],[0,1,2],consts.BUF,'udp')
        # flowdes0.up_step = consts.BUF_ADD
        #self.flows = {"10.0.0.110.0.0.25001":flowdes0} # flow_id(src,dst,dst_port):{src,dst,dst_port,update_type:"BUF",xids=[],doing="BUF_DEL"}
        self.flows={}
        self.xid_find_flow = {} #xid:[flow_id]

        self.conn_with_global = socket.socket()
        hub.spawn_after(5,self.conn_with_global.connect,('127.0.0.1',9999))

        hub.spawn(self.run_server)

    def read_dp_tcam(self,file):
        result = {}
        with open(file) as f:
            for line in f:
                a,b = line.split(':')
                if(int(a) in self.neighbors.keys()):
                    result[int(a)] = int(b)
        return result
    
#methods for buffer
    def get_from_buffer(self,key):
        msg = self.rds.lpop(key)    
        while(msg):
            self.buf_size =int( self.buf_size) + 1
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
        self.buf_size = int(self.buf_size) - 1
    
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

    #for step 1 del and step 2 add
    def any_up_msg_BUF(self,f,up_msg):
        # f = self.flows[up_msg.flow_id]
        f.up_step = up_msg.up_step
        to_barr_dp = []
        self.logger.info("----------in any up msg buf-------------")
        self.logger.info(self.datapaths)
        self.logger.info(str(up_msg))
        if(f.up_step == consts.BUF_DEL and len(up_msg.to_del) == 0):
            fb_msg = FeedbackMessge(f.flow_id,self.local_id)
            self.send_fb_to_global(fb_msg)
            return
        for d in up_msg.to_del: 
            dplast,dpid,dpnext = d
            datapath = self.datapaths[dpid]
            if (dpid not in to_barr_dp):
                to_barr_dp.append(dpid)
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match,match_reverse = self.make_match(parser,f,version_tag=None)
            priority = 2
            self.remove_flow(datapath,priority,match)
            self.remove_flow(datapath,priority,match_reverse)

        for a in up_msg.to_add:
            dplast,dpid,dpnext = a
            print(dpid)
            if (dpid not in to_barr_dp):
                to_barr_dp.append(dpid)
            print("haha" + str(self.datapaths))
            datapath = self.datapaths[dpid]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match,match_reverse = self.make_match(parser,f,version_tag=None)
            self.logger.info(str(match))
            self.logger.info(str(match_reverse))
            out = self.hosts[dpid][f.dst] if(dpid == dpnext) else self.neighbors[dpid][dpnext]
            out_reverse = self.hosts[dpid][f.src] if(dpid==dplast) else self.neighbors[dpid][dplast]
            actions = [parser.OFPActionOutput(out)]
            actions_reverse = [parser.OFPActionOutput(out_reverse)]
            priority = 2
            self.add_flow(datapath,priority,match,actions)
            self.add_flow(datapath,priority,match_reverse,actions_reverse)
        
        for dpid in to_barr_dp:
            self.send_barrier(self.datapaths[dpid],f.up_step,f.flow_id)

    #for step 3 release buf
    def any_up_msg_RLS_BUF(self,f,up_msg):
        pop_key = f.flow_id
        hub.spawn(self.get_from_buffer,pop_key)
        fb_msg = FeedbackMessge(f.flow_id,self.local_id)
        self.send_fb_to_global(fb_msg)

#methods for tag

    #tag 1
    def remove_tag_on_packets(self,f,up_msg):
        dplast,dpid,dpnext = up_msg.to_add[0]
        f.dp_tag = dpid
        datapath = self.datapaths[dpid]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match_pop,match_pop_reverse = self.make_match(parser,f,version_tag=(up_msg.version_tag|0x1000))
        priority = 2
        if(up_msg.if_reverse):
            out = self.hosts[dpid][f.dst] if(dpid == dplast) else self.neighbors[dpid][dplast]
            self.logger.info("reverse pop tag")
            action_pop = [parser.OFPActionPopVlan(),
                          parser.OFPActionOutput(out)]
            self.add_flow(datapath,priority,match_pop,action_pop)#when the dp is end-node pop the tag
        else:
            out_reverse = self.hosts[dpid][f.src] if(dpid==dplast) else self.neighbors[dpid][dplast]
            self.logger.info("normal pop tag")
            action_pop = [parser.OFPActionPopVlan(),
                          parser.OFPActionOutput(out_reverse)]
            self.add_flow(datapath,priority,match_pop_reverse,action_pop)
        self.send_barrier(datapath,f.up_step,f.flow_id)
        self.logger.info("sent a barrier for pop tag on pks")

    #tag 2 5
    def add_tag_for_packets(self,f,up_msg):
        self.logger.info("---------in add tag for pkts--------")

        dplast,dpid,dpnext = up_msg.to_add[0]
        f.dp_tag = dpid
        datapath = self.datapaths[dpid]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match,match_reverse = self.make_match(parser,f)
        
        priority = 2
        if(up_msg.if_reverse):
            out_reverse = self.hosts[dpid][f.src] if(dpid==dpnext) else self.neighbors[dpid][dpnext]
            self.logger.info("reverse add tag")
            actions = [parser.OFPActionPushVlan(),
                       parser.OFPActionSetField(vlan_vid =(up_msg.version_tag|0x1000)),
                       parser.OFPActionOutput(out_reverse)]
            self.add_flow(datapath,priority,match_reverse,actions)#for the <--flow to add tag
        else:
            out = self.hosts[dpid][f.dst] if(dpid == dpnext) else self.neighbors[dpid][dpnext]
            self.logger.info("normal add tag")
            actions = [parser.OFPActionPushVlan(),
                       parser.OFPActionSetField(vlan_vid =(up_msg.version_tag|0x1000)),
                       parser.OFPActionOutput(out)]
            self.add_flow(datapath,priority,match,actions)
        self.send_barrier(datapath,f.up_step,f.flow_id)
        self.logger.info("sent a barrier for tag pks")
    
    #tag 3 4
    def add_tag_for_entries(self,f,up_msg):
        self.logger.info("add flows")
        f.up_step = up_msg.up_step
        version_tag = up_msg.version_tag
        to_barr_dp = []
        if(len(up_msg.to_add) == 0):
            fb_msg = FeedbackMessge(f.flow_id,self.local_id)
            self.send_fb_to_global(fb_msg)
            return 
        for a in up_msg.to_add:
            dplast,dpid,dpnext = a
            # print(dpid)
            if (dpid not in to_barr_dp):
                to_barr_dp.append(dpid)
            # print("haha" + str(self.datapaths))
            datapath = self.datapaths[dpid]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match,match_reverse = self.make_match(parser,f,version_tag = up_msg.version_tag)
            self.logger.info(str(match))
            self.logger.info(str(match_reverse))
            out = self.hosts[dpid][f.dst] if(dpid == dpnext) else self.neighbors[dpid][dpnext]
            out_reverse = self.hosts[dpid][f.src] if(dpid==dplast) else self.neighbors[dpid][dplast]
            actions = [parser.OFPActionOutput(out)]
            actions_reverse = [parser.OFPActionOutput(out_reverse)]
            priority = 2
            self.add_flow(datapath,priority,match,actions)
            self.add_flow(datapath,priority,match_reverse,actions_reverse)
        self.logger.info(to_barr_dp)
        for dpid in to_barr_dp:
            self.send_barrier(self.datapaths[dpid],f.up_step,f.flow_id)
    
    #tag6
    def remove_tag_flow(self,f,up_msg):
        to_barr_dp = []
        if(len(up_msg.to_del) > 0):
            for d in up_msg.to_del: 
                dplast,dpid,dpnext = d
                datapath = self.datapaths[dpid]
                if (dpid not in to_barr_dp):
                    to_barr_dp.append(dpid)
                ofproto = datapath.ofproto
                parser = datapath.ofproto_parser
                match,match_reverse = self.make_match(parser,f,version_tag=up_msg.version_tag)
                priority = 2
                self.remove_flow(datapath,priority,match)
                self.remove_flow(datapath,priority,match_reverse)
            for dpid in to_barr_dp:
                self.send_barrier(self.datapaths[dpid],f.up_step,f.flow_id)
        else:
            fb_msg = FeedbackMessge(f.flow_id,self.local_id)
            self.send_fb_to_global(fb_msg)
    #tag7
    def mod_flow_vid(self,f,up_msg):
        self.logger.info("mod flows vid")
        f.up_step = up_msg.up_step
        version_tag = up_msg.version_tag
        to_barr_dp = []
        if(len(up_msg.to_add) == 0):
            fb_msg = FeedbackMessge(f.flow_id,self.local_id)
            self.send_fb_to_global(fb_msg)
            return 
        for a in up_msg.to_add:
            dplast,dpid,dpnext = a
            # print(dpid)
            if (dpid not in to_barr_dp):
                to_barr_dp.append(dpid)
            # print("haha" + str(self.datapaths))
            datapath = self.datapaths[dpid]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match,match_reverse = self.make_match(parser,f,version_tag = None)
            match_del,match_reverse_del = self.make_match(parser,f,version_tag = up_msg.version_tag)
            self.logger.info(str(match))
            self.logger.info(str(match_reverse))
            self.logger.info(str(match_del))
            self.logger.info(str(match_reverse_del))
            out = self.hosts[dpid][f.dst] if(dpid == dpnext) else self.neighbors[dpid][dpnext]
            out_reverse = self.hosts[dpid][f.src] if(dpid==dplast) else self.neighbors[dpid][dplast]
            actions = [parser.OFPActionOutput(out)]
            actions_reverse = [parser.OFPActionOutput(out_reverse)]
            priority = 2
            self.add_flow(datapath,priority,match,actions)
            self.add_flow(datapath,priority,match_reverse,actions_reverse)
            self.remove_flow(datapath,2,match_del)
            self.remove_flow(datapath,2,match_reverse_del)
        self.logger.info(to_barr_dp)
        for dpid in to_barr_dp:
            self.send_barrier(self.datapaths[dpid],f.up_step,f.flow_id)

    #tag entry
    def any_up_msg_TAG_new(self,f,up_msg):
        f.up_step = up_msg.up_step
        self.logger.info("it's in " + str(f.up_step))
        if(f.up_step == 0):
            fb_msg = FeedbackMessge(f.flow_id,self.local_id)
            self.send_fb_to_global(fb_msg)
        if(f.up_step == consts.TAG_POP_ADD):
            self.remove_tag_on_packets(f,up_msg)
        elif(f.up_step == consts.TAG_PUSH_OLD):
            self.add_tag_for_packets(f,up_msg)
        elif(f.up_step == consts.TAG_OLD_TAG):
            self.add_tag_for_entries(f,up_msg)
        elif(f.up_step == consts.TAG_NEW_TAG):
            self.add_tag_for_entries(f,up_msg)
        elif(f.up_step == consts.TAG_PUSH_NEW):
            self.logger.info("--------yes in 5")
            self.add_tag_for_packets(f,up_msg)
        elif(f.up_step == consts.TAG_DEL_OLD):
            self.remove_tag_flow(f,up_msg)
        elif(f.up_step == consts.TAG_MOD_NEW):
            self.mod_flow_vid(f,up_msg)

            


###############################################
    #Tag step 1 add_tagged_entry
    def any_up_msg_TAG(self,f,up_msg):
        f.up_step = up_msg.up_step
        f.version_tag = up_msg.version_tag
        self.logger.info(f.up_step)
        if(f.up_step == consts.TAG_ADD):
            self.logger.info("add flows")
            version_tag = f.version_tag
            to_barr_dp = []
            for a in up_msg.to_add:
                dplast,dpid,dpnext = a
                # print(dpid)
                if (dpid not in to_barr_dp):
                    to_barr_dp.append(dpid)
                # print("haha" + str(self.datapaths))
                datapath = self.datapaths[dpid]
                ofproto = datapath.ofproto
                parser = datapath.ofproto_parser
                match,match_reverse = self.make_match(parser,f,version_tag = f.version_tag)
                self.logger.info(str(match))
                self.logger.info(str(match_reverse))
                out = self.hosts[dpid][f.dst] if(dpid == dpnext) else self.neighbors[dpid][dpnext]
                out_reverse = self.hosts[dpid][f.src] if(dpid==dplast) else self.neighbors[dpid][dplast]
                actions = [parser.OFPActionOutput(out)]
                actions_reverse = [parser.OFPActionOutput(out_reverse)]
                priority = 2
                self.add_flow(datapath,priority,match,actions)
                self.add_flow(datapath,priority,match_reverse,actions_reverse)
            self.logger.info(to_barr_dp)
            for dpid in to_barr_dp:
                self.send_barrier(self.datapaths[dpid],f.up_step,f.flow_id)
        elif(f.up_step == consts.TAG_TAG):
            self.logger.info("-----------in tag tag")
            self.add_tag_for_packets(f,up_msg)

        elif(f.up_step == consts.TAG_DEL):
            to_barr_dp = []
            if(len(up_msg.to_del) > 0):
                for d in up_msg.to_del: 
                    dplast,dpid,dpnext = d
                    datapath = self.datapaths[dpid]
                    if (dpid not in to_barr_dp):
                        to_barr_dp.append(dpid)
                    ofproto = datapath.ofproto
                    parser = datapath.ofproto_parser
                    match,match_reverse = self.make_match(parser,f,version_tag=None)
                    priority = 2
                    self.remove_flow(datapath,priority,match)
                    self.remove_flow(datapath,priority,match_reverse)
                for dpid in to_barr_dp:
                    self.send_barrier(self.datapaths[dpid],f.up_step,f.flow_id)
            else:
                fb_msg = FeedbackMessge(f.flow_id,self.local_id)
                self.send_fb_to_global(fb_msg)
        elif(f.up_step == consts.TAG_MOD):
            self.logger.info("--------in tag mod------")

        elif(f.up_step == consts.TAG_UNTAG):
            pass
        
    #old version this method
    def _add_tag_for_packets(self,f,up_msg):
        
        
        self.logger.info("---------in add tag for pkts--------")
        self.logger.info(f.version_tag)
        self.logger.info(up_msg.to_add)

        dplast,dpid,dpnext = up_msg.to_add[0]
        f.dp_tag = dpid
        datapath = self.datapaths[dpid]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match,match_reverse = self.make_match(parser,f)
        match_pop,match_pop_reverse = self.make_match(parser,f,version_tag=(f.version_tag|0x1000))
        # out = self.hosts[dpid][f.dst] if(dpid == dpnext) else self.neighbors[dpid][dpnext]
        # out_reverse = self.hosts[dpid][f.src] if(dpid==dplast) else self.neighbors[dpid][dplast]
        
        priority = 2
        if(up_msg.if_reverse):
            out = self.hosts[dpid][f.dst] if(dpid == dplast) else self.neighbors[dpid][dplast]
            out_reverse = self.hosts[dpid][f.src] if(dpid==dpnext) else self.neighbors[dpid][dpnext]
            self.logger.info("reverse add tag")
            actions = [parser.OFPActionPushVlan(),
                       parser.OFPActionSetField(vlan_vid =(f.version_tag|0x1000)),
                       parser.OFPActionOutput(out_reverse)]
            
            action_pop = [parser.OFPActionPopVlan(),
                          parser.OFPActionOutput(out)]
            self.add_flow(datapath,priority,match_reverse,actions)#for the <--flow to add tag
            self.add_flow(datapath,priority,match_pop,action_pop)#when the dp is end-node pop the tag
        else:
            out = self.hosts[dpid][f.dst] if(dpid == dpnext) else self.neighbors[dpid][dpnext]
            out_reverse = self.hosts[dpid][f.src] if(dpid==dplast) else self.neighbors[dpid][dplast]
            self.logger.info("normal add tag")
            actions = [parser.OFPActionPushVlan(),
                       parser.OFPActionSetField(vlan_vid =(f.version_tag|0x1000)),
                       parser.OFPActionOutput(out)]
            action_pop = [parser.OFPActionPopVlan(),
                          parser.OFPActionOutput(out_reverse)]
            self.add_flow(datapath,priority,match,actions)
            self.add_flow(datapath,priority,match_pop_reverse,action_pop)
        self.send_barrier(datapath,f.up_step,f.flow_id)
        self.logger.info("sent a barrier for tag pks")
    
    

#methods for raw
    def any_up_msg_RAW(self,f,up_msg):
        f.up_step = up_msg.up_step
        to_barr_dp = []
        self.logger.info("----------in any up msg raw-------------")
        self.logger.info(str(up_msg))
        for d in up_msg.to_del: 
            dplast,dpid,dpnext = d
            datapath = self.datapaths[dpid]
            if (dpid not in to_barr_dp):
                to_barr_dp.append(dpid)
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match,match_reverse = self.make_match(parser,f,version_tag=None)
            priority = 2
            self.remove_flow(datapath,priority,match)
            self.remove_flow(datapath,priority,match_reverse)

        for a in up_msg.to_add:
            dplast,dpid,dpnext = a
            print(dpid)
            if (dpid not in to_barr_dp):
                to_barr_dp.append(dpid)
            print("haha" + str(self.datapaths))
            datapath = self.datapaths[dpid]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match,match_reverse = self.make_match(parser,f,version_tag=None)
            self.logger.info(str(match))
            self.logger.info(str(match_reverse))
            out = self.hosts[dpid][f.dst] if(dpid == dpnext) else self.neighbors[dpid][dpnext]
            out_reverse = self.hosts[dpid][f.src] if(dpid==dplast) else self.neighbors[dpid][dplast]
            actions = [parser.OFPActionOutput(out)]
            actions_reverse = [parser.OFPActionOutput(out_reverse)]
            priority = 2
            self.add_flow(datapath,priority,match,actions)
            self.add_flow(datapath,priority,match_reverse,actions_reverse)
        
        for dpid in to_barr_dp:
            self.send_barrier(self.datapaths[dpid],f.up_step,f.flow_id)
#methods for control
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id     

        if(dpid in self.datapaths.keys()):
            return
        self.datapaths[dpid]=datapath
        self.logger.info(self.datapaths)
        print(ofproto.OFPP_CONTROLLER)
        actions = [parser.OFPActionOutput(port=ofproto.OFPP_CONTROLLER,max_len=ofproto.OFPCML_NO_BUFFER)]
        # actions = [parser.OFPActionOutput(port=0 ,max_len=ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(type_=ofproto.OFPIT_APPLY_ACTIONS,actions=actions)]
        mod = parser.OFPFlowMod(datapath=datapath,priority=0,match=parser.OFPMatch(),instructions=inst)
        datapath.send_msg(mod) 

        self.disable_dhcp(datapath)
        
        # self.install(datapath)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, MAIN_DISPATCHER)
    def _features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id     
        self.logger.info("------------in features----------")
        self.logger.info(str(msg))


    @set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
    def _barrier_reply_handler(self,ev):
        print("---------------------------------------------------------")
        self.logger.info("hello this is reply for xid" +str(ev.msg.xid))
        xid = ev.msg.xid
        flows_move_on = self.get_flows_move_on(xid)
        self.logger.info("here's move on")
        self.logger.info(flows_move_on)
        self.logger.info(self.xid_find_flow)
        # self.logger.info(self.flows["10.0.0.110.0.0.25001"].barrs_wait)
        self.logger.info(flows_move_on)
        for f in flows_move_on:
            self.clear_xid_flow(f.flow_id)
            f.barrs_wait = []
            f.barrs_ok = 0
            # self.xid_find_flow[xid].remove(f.flow_id)
            fb_msg = FeedbackMessge(f.flow_id,self.local_id)
            self.send_fb_to_global(fb_msg)
            self.logger.info("sent a fb msg ")
    
    def clear_xid_flow(self,flow_id):
        xids = self.flows[flow_id].barrs_wait
        for xid in xids:
            self.xid_find_flow[xid].remove(flow_id)

    #get the flows move on to send fb to global
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
            self.logger.info(nf)
            self.flows.update({nf.flow_id:nf})

    def make_match(self,parser,f,version_tag=None):
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
        if(version_tag):
            match_dict['vlan_vid'] = (version_tag|0x1000)
            reverse_dict['vlan_vid'] = (version_tag|0x1000)
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
        return match,match_reverse

    
    def any_up_msg(self,up_msg):
        f = self.flows[up_msg.flow_id]
        up_type,up_step = f.up_type,f.up_step
        f.up_step = up_msg.up_step
        if(up_type == consts.BUF):
            if(f.up_step != consts.BUF_RLS):
                self.logger.info("in buf del or add")
                self.any_up_msg_BUF(f,up_msg)
            else:
                self.logger.info("in rls")
                self.any_up_msg_RLS_BUF(f,up_msg)
        elif(up_type == consts.TAG):
            self.any_up_msg_TAG_new(f,up_msg)
        elif(up_type == consts.RAW):
            self.any_up_msg_RAW(f,up_msg)

    def process_info_msg(self,info_msg):
        if(info_msg.statusAsk):
            self.logger.info("---------get an Ask")
            fb_msg = FeedbackMessge(-1,self.local_id)
            fb_msg.statusAnswer = True
            a = {}
            for dp,tcam in self.dp_tcam_size.items():
                a[dp] = tcam if tcam > 0 else 0
            fb_msg.status = ({
                "buffer_remain":self.buf_size,
                "tcam_remain":a
            })
            self.logger.info(fb_msg)
            self.send_fb_to_global(fb_msg)
            self.logger.info("sent to global")
            return
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
        parser = datapath.ofproto_parser
        in_port = pkt_in.match["in_port"]
        print(in_port)
        src,dst,dst_port,dpid,pkg = self.identify_pkg(pkt_in)
        key = src + dst + str(dst_port)
        if(self.flows.has_key(key) and self.flows[key].up_type == consts.BUF):
            self.logger.info("buffffffffffff")
            self.save_to_buffer(pkt_in)
        # self.logger.info("--------------in packet in---------------") 
        # self.logger.info(self.flows[key].up_type)
        # self.logger.info(self.flows[key].up_step)   

        # if(self.flows.has_key(key) and self.flows[key].up_type == consts.TAG and self.flows[key].up_step > consts.TAG_ADD):
        #     self.logger.info("yes tagged now go back and enjoy your tour")
        #     actions = [parser.OFPActionOutput(port=ofproto.OFPP_TABLE)]
        #     req = parser.OFPPacketOut(datapath,in_port=in_port,buffer_id=ofproto.OFP_NO_BUFFER,actions=actions,data=pkg)
        #     datapath.send_msg(req)
        
        #for simulating the latency of updateing
        # self.packts_buffed += 1
        # if(self.packts_buffed == 30):
        #     # self.install(self.datapaths[1])
        #     self.install()

        # hub.spawn(self.save_to_buffer,pkt_in)
            

#methods for update
    def send_barrier(self,datapath,up_step,flow_id):
        if(not self.xid_find_flow):
            xid = 1
        else:
            xid = max(self.xid_find_flow.keys()) + 1

        parser = datapath.ofproto_parser
        req = parser.OFPBarrierRequest(datapath,xid)
        datapath.send_msg(req)
        self.logger.info("i've sent xid barrier" + str(xid) + "for tag " + str(up_step))

        if(not self.xid_find_flow or (not self.xid_find_flow.get(xid))):
            self.xid_find_flow[xid] = [flow_id]
        else:
            self.xid_find_flow[xid].append(flow_id)

        self.flows[flow_id].barrs_wait.append(xid)
        print(self.flows)
        # print(self.xid_find_flow)

    def remove_flow(self, datapath, priority, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE,
                                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                                match=match, priority=priority)
        datapath.send_msg(mod)
        dpid = {value: key for key, value in self.datapaths.items()}[datapath]
        self.dp_tcam_size[dpid] = int(self.dp_tcam_size[dpid]) + 1

    def add_flow(self,datapath,priority,match,actions):
        self.logger.info(match)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        buffer_id = ofproto.OFP_NO_BUFFER
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
        dpid = {value: key for key, value in self.datapaths.items()}[datapath]
        self.dp_tcam_size[dpid] = int(self.dp_tcam_size[dpid]) - 1


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
        while True:
            fd, addr = server.accept()  #accept returns (conn,address) so fd is a connection
            self.logger.info("receive a connection")
            self.connection_handler(fd)            





    
