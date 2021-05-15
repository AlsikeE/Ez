import eventlet
import json
import struct
import cPickle as pickle
from eventlet import wsgi,GreenPool
from eventlet.green import socket

from bricks.flow_des import FlowDesGlobal,FlowDes
from bricks.message import InfoMessage,UpdateMessageByFlow
from scheduler.scheduler import Scheduler,PolicyUtil
from multi_controller_topo import read_mapping_from_file,get_reverse_mapping_from_file,get_link_bw,get_link_ltcy
import consts
import tools
import argparse
import logging
import logger as logger
import time

BW_NUM = 100
nowTime = lambda:int(round(time.time() * 1000))

class GlobalController(object):
    # def __init__(self,topo):
    def __init__(self,local_mapping_file):
        logger.init('./globalhapi.log',logging.INFO)
        self.logger=logger.getLogger('global',logging.INFO)
        # self.topo = topo
        # self.locals = [0,1] #{0:"bala"}
        # self.dp_to_local = {1:0,2:1}
        self.locals = read_mapping_from_file(local_mapping_file).keys()
        self.dp_to_local = get_reverse_mapping_from_file(local_mapping_file)
        self.logger.info(self.locals)
        self.logger.info(self.dp_to_local)
        self.sockets = {}
        
        self.link_bw = {}#outer layer 
        self.link_ltcy = {}
        self.local_to_buf_size = {}
        self.dp_to_tcam_size = {}
        # self.dp_to_local = {1:0,2:0,3:1,4:1}#for lineartopo2
        self.flows = {}# all flows now
        self.flows_new = {} #flows updating
        self.flows_to_schedule = {} #flow to update
        self.status_num = 0 #for start update
        # self.flows_new = {"10.0.0.110.0.0.25001":flowdes0}

        self.scheduler = Scheduler()
        self.tag_flows_temp = {}
        self.schedule_result = {}
        eventlet.spawn(self.run_fd_server)

# tools
    def finished_update_to_flows(self,f):
        self.logger.info("---in move updating flow in flows")
        self.flows_new.pop(f.flow_id)
        self.flows.update({f.flow_id:f})
        
        self.logger.info(self.flows)
        self.logger.info(self.flows_new)
        self.cal_remain_bw()
        self.logger.info(self.link_bw)
    
    def started_update_to_flows_new(self,f):
        self.logger.info("---in move to scd flow to flows_new")
        self.logger.info("before")
        self.logger.info(self.flows_new)
        self.logger.info(self.flows_to_schedule)
        self.flows_to_schedule.pop(f.flow_id)
        self.flows_new.update({f.flow_id:f})
        self.logger.info("after")
        self.logger.info(self.flows_new)
        self.logger.info(self.flows_to_schedule)

    def make_schedule_topo_for_schedule(self):
        topo = {}
        for dpid,nbr_info in self.link_bw.items():
            dpentry = {}
            for dpnext,bw in nbr_info.items():
                dpentry[dpnext] = {}
                dpentry.update({dpnext:{"bandwidth":bw,"latency":self.link_ltcy[dpid][dpnext]}})
            topo.update({dpid:dpentry})
        return topo
    
    def make_dp_dict_for_schedule(self):
        dp_dict = {}
        for dpid,local_id in self.dp_to_local.items():
            dpentry = {"flowspace":self.dp_to_tcam_size[dpid],"ctrl":self.dp_to_local[dpid]}
            dp_dict.update({dpid:dpentry})
        return dp_dict

#for calculating updates    

    def schedule_and_update(self):
        self.logger.info("________in schedule--------------")
        topo = self.make_schedule_topo_for_schedule()
        flows = self.flows_to_schedule
        ctrl_dict = self.local_to_buf_size
        dp_dict = self.make_dp_dict_for_schedule()
        self.logger.info("topo:")
        self.logger.info(topo)
        self.logger.info("flows:")
        self.logger.info(flows)
        self.logger.info("ctrl_dict:")
        self.logger.info(ctrl_dict)
        self.logger.info("dp_dict:")
        self.logger.info(dp_dict)
        flows_method,prices = self.scheduler.schedule(topo,flows,ctrl_dict,dp_dict)
        self.schedule_result = {'methods':flows_method,'prices':prices}
        flows_buf = {}
        flows_tag = {}
        flows_raw = {}
        self.logger.info("hahahahha let's see jason bug")
        self.logger.info(flows_method)
        self.logger.info("prices")
        self.logger.info(prices)
        for f_id,method in flows_method.items():
            if method  == PolicyUtil.TAG:
                flows_tag.update({f_id:self.flows_to_schedule[f_id]})
            elif method == PolicyUtil.BUFFER:
                flows_buf.update({f_id:self.flows_to_schedule[f_id]})
            elif method == PolicyUtil.RAW:
                flows_raw.update({f_id:self.flows_to_schedule[f_id]})
        
        self.raw_update(flows_raw)
        self.buf_del(flows_buf)
        self.tag0(flows_tag)

    
    #cal_remain_bandwidth
    def cal_remain_bw(self):
        for dp,linkto in self.link_bw.items():
            for dpnext,v in linkto.items():
                self.link_bw[dp][dpnext] = BW_NUM
        for f in self.flows.values():
            path = f.new
            if(path):
                for i in range(0,len(path)-1):
                    self.logger.info(i)
                    self.logger.info(self.link_bw)
                    self.logger.info(path[i])
                    self.link_bw[path[i]][path[i+1]] -= f.bw

    #from aggre_dict to InfoMessage
    def make_and_send_info(self,aggre_dict,old):
        self.logger.info("here is aggre_dict")
        self.logger.info(aggre_dict)
        for (ctrl_id,ups) in aggre_dict.items():
            info = InfoMessage(ctrl_id)
            for (flow_id,up) in ups.items():
                # self.logger.info(up)
                try:
                    f = self.flows_to_schedule[flow_id]
                except:
                    f = self.flows_new[flow_id]
                f.ctrl_wait.append(ctrl_id)
                up_msg = UpdateMessageByFlow(flow_id,f.up_type,f.up_step)
                up_msg.to_add = up['to_add']
                up_msg.to_del = up['to_del']
                up_msg.version_tag = f.old_version_tag if old else f.new_version_tag
                info.ums.append(up_msg)
                self.logger.info(up_msg)
                f_des = FlowDes(f.src,f.dst,f.dst_port,f.old,f.new,f.up_type,f.trans_type)
                info.new_flows.append(f_des)
            self.send_to_local(ctrl_id,info)
#for buf
    #more where-to-buf can be accomplished here
    def find_buf_dp(self,f):
        to_add, to_del = tools.diff_old_new(f.old,f.new)
        self.logger.info(to_del)
        to_add_bak,to_del_bak = tools.diff_old_new(f.new,[])
        self.logger.info("where to buf")
        
        where_to_buf =  to_del[0] if to_del else to_del_bak[0]  
        self.logger.info(where_to_buf)  
        return where_to_buf
    
    #BUF  step 1
    def buf_del(self,flows={}):
        aggre_dict = {}
        # for f_id,f in self.flows_new.items():
        for f_id,f in flows.items():
            f.up_type = consts.BUF
            f.up_step = consts.BUF_DEL
            to_buf = self.find_buf_dp(f)
            l,dp,n = to_buf
            f.ctrl_buf = self.dp_to_local[dp]
            self.logger.info("flow_id"+str(f.flow_id))
            self.logger.info("ctrl_buf" + str(f.ctrl_buf))
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,[],[to_buf])
            self.logger.info("her is buf del")
            self.logger.info(self.flows_to_schedule)
            self.started_update_to_flows_new(f)

        self.logger.info(aggre_dict)
        self.make_and_send_info(aggre_dict,False)
 
    #BUF step 2 and 3
    def buf_fb_process(self,f_id):
        aggre_dict = {}
        f = self.flows_new[f_id]
        f.ctrl_ok += 1
        self.logger.info("-------in buf fb process")
        self.logger.info(f.up_step)
        self.logger.info("ctrl_ok" + str(f.ctrl_ok))
        self.logger.info("ctrl_wait" + str(f.ctrl_wait))
        if(len(f.ctrl_wait) == f.ctrl_ok):
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(f.up_step == consts.BUF_DEL):
                self.logger.info("buf del over")
                f.up_step = consts.BUF_ADD
                to_add, to_del = tools.diff_old_new(f.old,f.new)
                aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,to_del)
                # self.logger.info(aggre_dict)
                self.make_and_send_info(aggre_dict,False)
                
            elif(f.up_step == consts.BUF_ADD):
                self.logger.info("buf add over")
                f.up_step = consts.BUF_RLS
                #firstly we send cmd to the ctrls who bufed,but why?? why some buffed from other dps?
                # info = InfoMessage(f.ctrl_buf)
                # um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                # info.ums.append(um)
                # self.send_to_local(f.ctrl_buf,info)
                # f.ctrl_wait.append(f.ctrl_buf)
                #now we let all ctrls to sendback,but why????
                for ctrl in self.locals:
                    info = InfoMessage(ctrl)
                    um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                    info.ums.append(um)
                    self.send_to_local(ctrl,info)
                    f.ctrl_wait.append(ctrl)

            elif(f.up_step == consts.BUF_RLS):
                f.up_step = None
                f.up_type = None
                f.ctrl_buf = None
                self.logger.info(f.flow_id)
                self.logger.info("updated over by buf")
                self.finished_update_to_flows(f)
                self.logger.info("------------------------buf over time--------------")
                self.logger.info(nowTime())


#for tag
    #more to do for find a version tag such as for conflicts
    def find_version_tag(self,f):
        # if(f.new_version_tag == 2 and f.old_version_tag == 1):
        #     return 3,4
        return 1,2


    def send_mod_packet_vid_cmd(self,f,dp_tup,old,ifr):
        self.logger.info("--------------in send mod vid ----------------")
        info = InfoMessage(f.ctrl_tag)
        l,dpid,n = dp_tup
        um = UpdateMessageByFlow(f.flow_id,f.up_type,f.up_step)
        
        um.version_tag = f.old_version_tag if old else f.new_version_tag
        self.logger.info(um.up_step)
        send_ctrl = self.dp_to_local[dpid]
        if(ifr):
            um.if_reverse = True
            um.to_add.append((n,dpid,l))
            self.logger.info(um.to_add)
            f.ctrl_tag_reverse = send_ctrl
        else:
            um.to_add.append(dp_tup)
            f.ctrl_tag = send_ctrl
        info.ums.append(um)
        self.send_to_local(send_ctrl,info)
        if(send_ctrl not in f.ctrl_wait):
            f.ctrl_wait.append(send_ctrl)

    #TAG NEW step 0: tell every local flows come
    def tag0(self,flows={}):
        aggre_dict = {}
        for f_id, f in flows.items():
            f.up_type = consts.TAG
            f.up_step = 0
            f.old_version_tag,f.new_version_tag = self.find_version_tag(f)
            to_add,to_del = tools.diff_old_new(f.old,f.new)
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,to_del)
            # self.make_and_send_info(aggre_dict,False)
            left,right = {},{}
            try:
                right.update({'old':to_del[-1]})
                to_del.pop(-1)
            except:
                self.logger.info("right old wrong")
            
            try:
                right.update({'new':to_add[-1]})
                to_add.pop(-1)
            except:
                self.logger.info("right new wrong")
            
            try:
                left.update({'old':to_del[0]})
                to_del.pop(0)
            except:
                self.logger.info("left old wrong")
            
            try:
                left.update({'new':to_add[0]})
                to_add.pop(0)
            except:
                self.logger.info("left new wrong")
            
            self.tag_flows_temp.update({f_id:{'to_add':to_add,'to_del':to_del,'left':left,'right':right}})
            
        self.make_and_send_info(aggre_dict,False)
        self.started_update_to_flows_new(f)

    #TAG new step 1: add popvlan id in start for reverse and end for normal

    def tag1_pop_add(self,f):    
        f.up_step = consts.TAG_POP_ADD
        up_infos = self.tag_flows_temp[f.flow_id]
        nothing_flag = True
        if(up_infos['left'].has_key('old')):
            self.send_mod_packet_vid_cmd(f,up_infos['left']['old'],True,False)
            nothing_flag = False
        
        if(up_infos['left'].has_key('new')):
            self.send_mod_packet_vid_cmd(f,up_infos['left']['new'],False,False)
            nothing_flag = False
        
        if(up_infos['right'].has_key('old')):
            self.send_mod_packet_vid_cmd(f,up_infos['right']['old'],True,True)
            nothing_flag = False
        
        if(up_infos['right'].has_key('new')):
            self.send_mod_packet_vid_cmd(f,up_infos['right']['new'],False,True)
            nothing_flag = False
        
        if(nothing_flag):
            self.tag2_push_old(f)
        

    def tag2_push_old(self,f):
        f_id = f.flow_id
        f.up_step = consts.TAG_PUSH_OLD
        up_info = self.tag_flows_temp[f_id]
        try:
            self.send_mod_packet_vid_cmd(f,up_info['left']['old'],True,False)
        except:
            self.logger.info("no old")
        try:
            self.send_mod_packet_vid_cmd(f,up_info['right']['old'],True,True)
        except:
            self.logger.info("no old")
            self.tag3_tag_old(f)
    
    def tag3_tag_old(self,f):
        aggre_dict = {}
        f.up_step = consts.TAG_OLD_TAG
        to_del = self.tag_flows_temp[f.flow_id]['to_del']
        if(len(to_del) == 0):
            self.tag4_tag_new(f)
            return
        aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f.flow_id,to_del,[])
        self.make_and_send_info(aggre_dict,True)
    
    def tag4_tag_new(self,f):
        aggre_dict = {}
        f.up_step = consts.TAG_NEW_TAG
        to_add = self.tag_flows_temp[f.flow_id]['to_add']
        if(len(to_add) == 0):
            self.tag5_push_new(f)
            return
        aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f.flow_id,to_add,[])
        self.make_and_send_info(aggre_dict,False)

    def tag5_push_new(self,f):
        self.logger.info("!!!!!!!!!!!!!!!!!!in tag 5")
        f.up_step = consts.TAG_PUSH_NEW
        up_infos = self.tag_flows_temp[f.flow_id]
        if('new' not in up_infos['right'].keys() and 'new' not in up_infos['left'].keys()):
            self.logger.info("no new")
            self.tag6_del_old(f)
            return 
        try:
            self.send_mod_packet_vid_cmd(f,up_infos['left']['new'],False,False)
        except:
            self.logger.info("no new")
        try:
            self.send_mod_packet_vid_cmd(f,up_infos['right']['new'],False,True)
        except:
            self.logger.info("no new")
    
    def tag6_del_old(self,f):
        f.up_step = consts.TAG_DEL_OLD
        aggre_dict = {}
        to_del = self.tag_flows_temp[f.flow_id]['to_del']
        if(len(to_del) == 0):
            self.tag7_mod_new(f)
            return
        aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f.flow_id,[],to_del)
        self.make_and_send_info(aggre_dict,True)

    def tag7_mod_new(self,f):
        f.up_step = consts.TAG_MOD_NEW
        aggre_dict = {}
        to_add = self.tag_flows_temp[f.flow_id]['to_add']
        if(len(to_add) == 0):
            self.tag8_push_old_del(f)
            return
        aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f.flow_id,to_add,[])
        self.make_and_send_info(aggre_dict,False)

    def tag8_push_old_del(self,f):
        pass

    def tag9_pop_del(self,f):
        pass

    def tag_fb_process_new(self,f_id):
        self.logger.info("in tag fb")
        f = self.flows_new[f_id]
        f.ctrl_ok += 1
        self.logger.info(f.up_step)
        aggre_dict = {}
        if(len(f.ctrl_wait) == f.ctrl_ok):
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(f.up_step == 0):
                self.logger.info("tag info telled every one")
                self.tag1_pop_add(f)
            elif(f.up_step == consts.TAG_POP_ADD):
                self.logger.info("tag pop add finished")
                self.tag2_push_old(f)
            elif(f.up_step == consts.TAG_PUSH_OLD):
                self.logger.info("tag push old finished")
                self.tag3_tag_old(f)
            elif(f.up_step == consts.TAG_OLD_TAG):
                self.logger.info("tag old tag finished")
                self.tag4_tag_new(f)
            elif(f.up_step == consts.TAG_NEW_TAG):
                self.logger.info("tag new tag finished")
                self.tag5_push_new(f)
            elif(f.up_step == consts.TAG_PUSH_NEW):
                self.logger.info("tag push new finished")
                self.logger.info("update over by tag")
                self.logger.info(nowTime())
                # self.tag6_del_old(f)
            # elif(f.up_step == consts.TAG_DEL_OLD):
            #     self.logger.info("update over by tag")
            #     self.logger.info(nowTime())
            #     self.tag7_mod_new(f)
            # elif(f.up_step == consts.TAG_MOD_NEW):
            #     self.logger.info("tag mod new finished")
            #     self.tag8_push_old_del(f)
            # elif(f.up_step == consts.TAG_PUSH_OLD_DEL):
            #     self.logger.info("tag push old del finished")
            #     self.tag9_pop_del(f)
            # elif(f.up_step == consts.TAG_POP_DEL):
            #     self.logger.info("update over by tag")
            # elif(f.up_step == consts.TAG_PUSH_NEW):
            #     self.logger.info("tag push new finished")
            #     self.tag6_del_old(f)
 ################################################################           
    #TAG step 1
    def tag_add(self, flows={}):
        aggre_dict = {}
        # for f_id,f in self.flows_new.items():
        for f_id,f in flows.items():
            f.up_type = consts.TAG
            f.up_step = consts.TAG_ADD
            f.version_tag = self.find_version_tag(f)
            to_add, to_del = tools.diff_old_new(f.old,f.new)
           
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,[])
            self.started_update_to_flows_new(f)
        # self.logger.info(aggre_dict)
        self.make_and_send_info(aggre_dict,False)

    def find_packet_tag_dp(self,f):
        to_add, to_del = tools.diff_old_new(f.old,f.new)
        to_add_bak,to_del_bak = tools.diff_old_new(f.new,[])
        dp_tup =  to_del[0] if to_del else to_del_bak[0]
        to_add, to_del = tools.diff_old_new(list(reversed(f.old)),list(reversed(f.new)))
        to_add_bak,to_del_bak = tools.diff_old_new(list(reversed(f.new)),[])
        dp_tup_reverse = to_del[0] if to_del else to_del_bak[0]
        return dp_tup,dp_tup_reverse

    def send_pkg_tag_cmd(self,f,dp_tup,ifr):
        info = InfoMessage(f.ctrl_tag)
        l,dpid,n = dp_tup
        um = UpdateMessageByFlow(f.flow_id,f.up_type,f.up_step)
        um.to_add.append(dp_tup)
        um.version_tag = f.version_tag
        send_ctrl = self.dp_to_local[dpid]
        if(ifr):
            um.if_reverse = True
            f.ctrl_tag_reverse = send_ctrl
        else:
            f.ctrl_tag = send_ctrl
        info.ums.append(um)
        self.send_to_local(send_ctrl,info)
        if(send_ctrl not in f.ctrl_wait):
            f.ctrl_wait.append(send_ctrl)

    def tag_fb_process(self,f_id):
        self.logger.info("in tag fb")
        f = self.flows_new[f_id]
        f.ctrl_ok += 1
        self.logger.info(f.up_step)
        aggre_dict = {}
        if(len(f.ctrl_wait) == f.ctrl_ok):
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(f.up_step == consts.TAG_ADD):
                self.logger.info("tag add finished")
                f.up_step = consts.TAG_TAG
                dp_tup, dp_tup_reverse = self.find_packet_tag_dp(f)
                # l,dpid,n =dp_tup
                # l,dpid_reverse,n = dp_tup_reverse
                # self.send_pkg_tag_cmd(f,dpid,False)
                # self.send_pkg_tag_cmd(f,dpid_reverse,True)
                self.send_pkg_tag_cmd(f,dp_tup,False)
                self.send_pkg_tag_cmd(f,dp_tup_reverse,True)
                self.logger.info(f.ctrl_wait)

            elif(f.up_step == consts.TAG_TAG):
                self.logger.info("tag tag finished")
                f.up_step = consts.TAG_DEL
                to_add, to_del = tools.diff_old_new(f.old,f.new)
                self.logger.info(to_add)
                self.logger.info(to_del)
                if(len(to_del) > 0):
                    aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,[],to_del)
                    self.make_and_send_info(aggre_dict,False)
                else:
                    info = InfoMessage(f.ctrl_tag)
                    um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                    info.ums.append(um)
                    self.send_to_local(f.ctrl_tag,info)
                    f.ctrl_wait.append(f.ctrl_tag)
                self.logger.info("tag_del sent")
            elif(f.up_step == consts.TAG_DEL):
                self.logger.info("tag del finished")
                self.logger.info(nowTime())
                f.up_step = consts.TAG_MOD
                # l,dpid,n = self.find_packet_tag_dp(f)
                # f.ctrl_tag = self.dp_to_local[dpid]
                info = InfoMessage(f.ctrl_tag)
                um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                info.ums.append(um)
                self.send_to_local(f.ctrl_tag,info)

                info = InfoMessage(f.ctrl_tag_reverse)
                um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                um.if_reverse =True
                info.ums.append(um)
                self.send_to_local(f.ctrl_tag_reverse,info)

                f.ctrl_wait.append(f.ctrl_tag)
                f.ctrl_wait.append(f.ctrl_tag_reverse)
    #from here should be rewrited
            elif(f.up_step == consts.TAG_MOD):
                pass
                return
                self.logger.info("tag notag finished")
                f.up_step = consts.TAG_UNTAG
                # l,dpid,n = self.find_packet_tag_dp(f)
                # f.ctrl_tag = self.dp_to_local[dpid]
                info = InfoMessage(f.ctrl_tag)
                um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                info.ums.append(um)
                self.send_to_local(f.ctrl_tag,info)
                f.ctrl_wait.append(f.ctrl_buf)

            elif(f.up_step == consts.TAG_UNTAG):
                f.up_step = None
                f.up_type = None
                f.ctrl_tag =None
                self.logger.info(f.flow_id)
                self.logger.info("updated over by tag")
                self.finished_update_to_flows(f)
            else:
                self.logger.info("what type?")

#for raw
    def raw_update(self,flows={}):
        aggre_dict = {}
        for f_id,f in flows.items():
            f.up_type = consts.RAW
            f.up_step = consts.RAW_INSTALL
            to_add, to_del = tools.diff_old_new(f.old,f.new)
            self.logger.info("let's see raw update bug")
            self.logger.info(to_add)
            self.logger.info(to_del)
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,to_del)
            self.make_and_send_info(aggre_dict,False)
            self.started_update_to_flows_new(f)

    def raw_fb_process(self,f_id):
        f = self.flows_new[f_id]
        f.ctrl_ok += 1
        self.logger.info(f.up_step)
        if(len(f.ctrl_wait) == f.ctrl_ok):
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(f.up_step == consts.RAW_INSTALL):
                self.logger.info("up over by raw")
                self.logger.info(nowTime())
                self.finished_update_to_flows(f)

           
#for communicate with local
    def init_socks(self):
        for local_id in self.locals:
            c = socket.socket()
            host = socket.gethostbyname('127.0.0.1')
            c.connect((host,6000 + local_id))
            self.sockets[local_id] = c
    
    def send_to_local(self,local_id,msg):
        # self.logger.info("-------------in send to local")
        str_message = pickle.dumps(msg)
        msg_len = len(str_message)
        data = struct.pack('L', msg_len) + str_message
        # self.logger.info(str_message)
        self.sockets[local_id].sendall(data)
    
    def global_conn(self,fd):
        self.logger.info("--------------a connection-------------------")
        while True:
            data = fd.recv(8)
            if(len(data) == 0):
                fd.close()
                return
            msg_len = struct.unpack('L',data)[0]
            self.logger.info("global get the fb len")
            self.logger.info(msg_len)
            more_msg = tools.recv_size(fd,msg_len)
            self.logger.info(more_msg)
            msg = pickle.loads(more_msg)
            eventlet.spawn(self.process_fd_msg,msg)
            # print(msg)

    def run_fd_server(self):
        server = eventlet.listen(('127.0.0.1', consts.GLOBAL_FB_PORT))
        pool = GreenPool(10000)
        while True:
            fd, addr = server.accept()  #accept returns (conn,address) so fd is a connection
            self.logger.info("global receives a connection")
            # self.global_conn(fd)  
            pool.spawn_n(self.global_conn, fd)

    #here to start next step
    def process_fd_msg(self,fd_msg):
        print(fd_msg)
        if(fd_msg.statusAnswer):
            status = fd_msg.status
            self.status_num += 1
            self.logger.info(status)
            self.local_to_buf_size.update({fd_msg.ctrl_id:status["buffer_remain"]})
            self.dp_to_tcam_size.update(status["tcam_remain"])
            self.logger.info("---------get a statusAnswer")
            self.logger.info(self.local_to_buf_size)
            self.logger.info(self.dp_to_tcam_size)
            if(self.status_num >= len(self.locals)):
                self.logger.info("---------------------schedule start")
                self.logger.info(nowTime())
                self.schedule_and_update()
                self.status_num = 0
            # self.scheduler.schedule(topo,self.flows_to_schedule,self.local_to_buf_size,self.dp_to_local,self.dp_to_tcam_size)
            return
        flow_id = fd_msg.flow_id
        ctrl_id = fd_msg.ctrl_id
        self.logger.info(flow_id)
        self.logger.info(ctrl_id)
        self.logger.info(fd_msg)
        self.logger.info("!!!!!!feedback to find flow")
        self.logger.info(self.flows_new)
        f = self.flows_new[flow_id]
        # try:
        #     f = self.flows_new[flow_id]
        #     self.logger.info("mingzhong")
        # except:
        #     self.logger.info(str(flow_id) + " was finished longlong ago")
        #     return
        if(f.up_type == consts.BUF):
            self.logger.info("hey buf feedback")
            self.buf_fb_process(flow_id)
        elif(f.up_type == consts.TAG):
            self.tag_fb_process_new(flow_id)
                #here should be next step
        elif(f.up_type == consts.RAW):
            self.raw_fb_process(flow_id)
        else:
            self.logger.info("what's up??")

    def if_flow_finished(self,f):
        if(f.up_type == consts.BUF and (f.up_step == consts.BUF_RLS)):
            return True
        elif(f.up_type == consts.TAG and (f.up_step == consts.TAG_UNTAG)):
            return True
        return False

#for experiment   
    #test0
    def install(self):
        flow_id = "10.0.0.110.0.0.25001"
        umbf =  UpdateMessageByFlow(flow_id,consts.BUF,consts.BUF_ADD)
        umbf.to_add = [(1,1,1)]
        ctrl_id = 0
        info = InfoMessage(ctrl_id)
        info.ums.append(umbf)
        self.flows_new[flow_id].ctrl_wait.append(ctrl_id)
        self.flows_new[flow_id].up_step = consts.BUF_ADD
        self.send_to_local(0,info)
    
    #test 1
    def auto_install(self,methname):
        #put something in flow_new
        if(methname == consts.ONLY_BUF):
            self.buf_del(self.flows_to_schedule)
        elif(methname == consts.ONLY_TAG):
            self.tag0(self.flows_to_schedule)
        elif(methname == consts.ONLY_RAW):
            self.raw_update(self.flows_to_schedule)
#for input
    def run_server(self):
        wsgi.server(eventlet.listen(('', 8800)), self.wsgi_app, max_size=50)

    def run_experiment(self):
        eventlet.monkey_patch(socket=True, thread=True)
        self.init_socks()
        self.run_server()
    
    def ana_input(self,input_data):
        self.logger.info("in ana_input")
        flows = input_data['flows']
        for flow in flows:
            args = flow.split(' ')
            src = args[0]
            dst = args[1]
            try:
                port = int(args[2])
            except:
                port = None
            old = tools.str_to_list(args[3])
            new = tools.str_to_list(args[4])
            self.logger.info(new)
            trans_type = args[5]
            ratio = float(args[6])
            bw = int(args[7])
            flow  = FlowDesGlobal(src,dst,port,old,new,None,trans_type)
            flow.ratio = ratio
            flow.bw = bw

            self.logger.info(flow.new)
            self.logger.info(flow.trans_type)
            self.flows_to_schedule.update({src+dst+str(port):flow})
        self.logger.info(self.flows_to_schedule)
        self.logger.info("---------------------start!---------------------")
        self.logger.info(nowTime())

    def fetch_status_info(self):
        for l in self.locals:
            info = InfoMessage(l)
            info.statusAsk = True
            self.send_to_local(l,info)
            self.logger.info("sent Ask to local" + str(l))
        
    def wsgi_app(self, env, start_response):
        # print "Get finished msg"
        input = env['wsgi.input']
        request_body = input.read(int(env.get("CONTENT_LENGTH",0)))#post
        print(request_body)
        input_data = None
        try:
            input_data = json.loads(request_body)
        except Exception as e:
            self.logger.info(e)
        
        self.logger.info(input_data)
        if (input_data):
            self.ana_input(input_data)
        
        self.fetch_status_info()

        #should be in feedback handler 
        # self.auto_install(consts.ONLY_BUF)
        # self.auto_install(consts.ONLY_TAG)
        # self.auto_install(consts.ONLY_RAW)

        response_headers = [('Content-type', 'application/json'),
                        ('Access-Control-Allow-Origin', '*'),
                        ('Access-Control-Allow-Methods', 'POST'),
                        ('Access-Control-Allow-Headers', 'x-requested-with,content-type'),
                        ]  # json
        start_response('200 OK', response_headers)
        return ['zuomieya\r\n']


if __name__ == "__main__":
    # gl_ctrl = GlobalController('FourHosts')
    parser = argparse.ArgumentParser(description='mix global')
    parser.add_argument('--localdp',nargs='?',
                        type = str,default='./data/local_dp.intra')
    parser.add_argument('--matrix',nargs='?',
                        type=str,default='./data/topo.intra')
    parser.add_argument('--latencies',nargs='?',
                        type=str,default='./data/latencies.intra')
    args = parser.parse_args()
    gl_ctrl = GlobalController(args.localdp)
    gl_ctrl.link_bw = get_link_bw(args.matrix)
    gl_ctrl.link_ltcy = get_link_ltcy(args.latencies)
    gl_ctrl.run_experiment()