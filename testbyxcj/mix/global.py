import eventlet
import json
import struct
import cPickle as pickle
from eventlet import wsgi,GreenPool
from eventlet.green import socket

from bricks.flow_des import FlowDesGlobal,FlowDes
from bricks.message import InfoMessage,UpdateMessageByFlow
import consts
import tools

import logging
import logger as logger
class GlobalController(object):
    def __init__(self,topo):
        logger.init('./globalhapi.log',logging.INFO)
        self.logger=logger.getLogger('global',logging.INFO)
        self.topo = topo
        self.locals = [0,1] #{0:"bala"}
        self.sockets = {}
        self.dp_to_local = {1:0,2:1}
        # self.dp_to_local = {1:0,2:0,3:1,4:1}#for lineartopo2
        self.flows = {}
        self.flows_new = {}
        # self.flows_new = {"10.0.0.110.0.0.25001":flowdes0}
        self.flows_move_on = {}

        eventlet.spawn(self.run_fd_server)
#for calculating updates    

    def schedule(self):
        for flow_id,f in self.flows_new.items():
            f.up_type = BUF
    

    #from aggre_dict to InfoMessage
    def make_and_send_info(self,aggre_dict):
        self.logger.info("here is aggre_dict")
        self.logger.info(aggre_dict)
        for (ctrl_id,ups) in aggre_dict.items():
            info = InfoMessage(ctrl_id)
            for (flow_id,up) in ups.items():
                self.logger.info(up)
                f = self.flows_new[flow_id]
                f.ctrl_wait.append(ctrl_id)
                up_msg = UpdateMessageByFlow(flow_id,f.up_type,f.up_step)
                up_msg.to_add = up['to_add']
                up_msg.to_del = up['to_del']
                up_msg.version_tag = f.version_tag
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
        return to_del[0] if to_del else to_del_bak[0]    
    
    #BUF  step 1
    def buf_del(self,flows={}):
        aggre_dict = {}
        # for f_id,f in self.flows_new.items():
        for f_id,f in flows.items():
            f.up_type = consts.BUF
            f.up_step = consts.BUF_DEL
            to_buf = self.find_buf_dp(f)
            self.logger.info("to buf is")
            self.logger.info(to_buf)
            l,dp,n = to_buf
            f.ctrl_buf = self.dp_to_local[dp]
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,[],[to_buf])
        self.logger.info(aggre_dict)
        self.make_and_send_info(aggre_dict)
 
    #BUF step 2 and 3
    def buf_fb_process(self,f_id):
        aggre_dict = {}
        f = self.flows_new[f_id]
        f.ctrl_ok += 1
        self.logger.info(f.up_step)
        if(len(f.ctrl_wait) == f.ctrl_ok):
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(f.up_step == consts.BUF_DEL):
                self.logger.info("buf del over")
                f.up_step = consts.BUF_ADD
                to_add, to_del = tools.diff_old_new(f.old,f.new)
                aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,to_del)
                self.logger.info(aggre_dict)
                self.make_and_send_info(aggre_dict)
                
            elif(f.up_step == consts.BUF_ADD):
                self.logger.info("buf add over")
                f.up_step = consts.BUF_RLS
                info = InfoMessage(f.ctrl_buf)
                um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                info.ums.append(um)
                self.send_to_local(f.ctrl_buf,info)
                f.ctrl_wait.append(f.ctrl_buf)

            elif(f.up_step == consts.BUF_RLS):
                f.up_step = None
                f.up_type = None
                f.ctrl_buf = None
                self.logger.info(f.flow_id)
                self.logger.info("updated over by buf")
        else:
            print("something wrong")

#for tag
    #more to do for find a version tag such as for conflicts
    def find_version_tag(self,f):
        return 2

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
        self.logger.info(aggre_dict)
        self.make_and_send_info(aggre_dict)

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
                if(len(to_del) > 0):
                    aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,[],to_del)
                    self.make_and_send_info(aggre_dict)
                else:
                    info = InfoMessage(f.ctrl_tag)
                    um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                    info.ums.append(um)
                    self.send_to_local(f.ctrl_tag,info)
                    f.ctrl_wait.append(f.ctrl_tag)
                self.logger.info("tag_del sent")
            elif(f.up_step == consts.TAG_DEL):
                self.logger.info("tag del finished")
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

            elif(f.up_step == consts.TAG_MOD):
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
            else:
                self.logger.info("what type?")

#for raw
    def raw_update(self,flows={}):
        aggre_dict = {}
        for f_id,f in flows.items():
            f.up_type = consts.RAW
            f.up_step = consts.RAW_INSTALL
            to_add, to_del = tools.diff_old_new(f.old,f.new)
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,to_del)
            self.make_and_send_info(aggre_dict)
    def raw_fb_process(self,f_id):
        f = self.flows_new[f_id]
        f.ctrl_ok += 1
        self.logger.info(f.up_step)
        if(len(f.ctrl_wait) == f.ctrl_ok):
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(f.up_step == consts.RAW_INSTALL):
                self.logger.info("up over by raw")

           
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
        flow_id = fd_msg.flow_id
        ctrl_id = fd_msg.ctrl_id
        f = self.flows_new[flow_id]
        if(f.up_type == consts.BUF):
            self.logger.info("hey buf feedback")
            self.buf_fb_process(flow_id)
        elif(f.up_type == consts.TAG):
            self.tag_fb_process(flow_id)
                # self.flows_move_on.append(f.flow_id)
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
            self.buf_del(self.flows_new)
        elif(methname == consts.ONLY_TAG):
            self.tag_add(self.flows_new)
        elif(methname == consts.ONLY_RAW):
            self.raw_update(self.flows_new)
#for input
    def run_server(self):
        wsgi.server(eventlet.listen(('', 8800)), self.wsgi_app, max_size=50)

    def run_experiment(self):
        eventlet.monkey_patch(socket=True, thread=True)
        self.init_socks()
        self.run_server()
    
    def ana_input(self,input_data):
        self.logger.info("in ana_input")
        args = input_data['flow'].split(' ')
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
        flow  = FlowDesGlobal(src,dst,port,old,new,None,trans_type)
        self.logger.info(flow.new)
        self.logger.info(flow.trans_type)
        self.flows_new.update({src+dst+str(port):flow})
        self.logger.info(self.flows_new)

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

        # self.auto_install(consts.ONLY_BUF)
        self.auto_install(consts.ONLY_TAG)
        # self.auto_install(consts.ONLY_RAW)


        response_headers = [('Content-type', 'application/json'),
                        ('Access-Control-Allow-Origin', '*'),
                        ('Access-Control-Allow-Methods', 'POST'),
                        ('Access-Control-Allow-Headers', 'x-requested-with,content-type'),
                        ]  # json
        start_response('200 OK', response_headers)
        return ["zuomieya\r\n"]


if __name__ == "__main__":
    gl_ctrl = GlobalController('FourHosts')
    gl_ctrl.run_experiment()