import eventlet
import json
import struct
import cPickle as pickle
from eventlet import wsgi
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
        self.logger=logger.getLogger('local',logging.INFO)
        self.topo = topo
        self.locals = [0] #{0:"bala"}
        self.sockets = {}
        self.dp_to_local = {1:0}
        flowdes0 = FlowDesGlobal("10.0.0.1","10.0.0.2",5001,[],[1],consts.BUF,'udp')
        self.flows = {"10.0.0.110.0.0.25001":flowdes0}
        self.flows_new = {"10.0.0.110.0.0.25001":flowdes0}
        self.flows_move_on = {}

        eventlet.spawn(self.run_fd_server)
#for calculating updates
    def only_buf(self):
        aggre_dict = {}
        for f_id,f in self.flows_new.items():
            f.up_type = consts.BUF
            to_add, to_del = tools.diff_old_new(f.new,f.old)
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,to_del)
        self.logger.info(aggre_dict)
        self.make_and_send_info(aggre_dict)
    
    #from aggre_dict to InfoMessage
    def make_and_send_info(self,aggre_dict):
        self.logger.info("here is aggre_dict")
        self.logger.info(aggre_dict)
        for (ctrl_id,ups) in aggre_dict.items():
            info = InfoMessage(ctrl_id)
            for (flow_id,up) in ups.items():
                self.logger.info(up)
                f = self.flows[flow_id]
                up_msg = UpdateMessageByFlow(flow_id,f.up_type,f.up_step)
                up_msg.to_add = up['to_add']
                up_msg.to_del = up['to_del']
                info.ums.append(up_msg)
                self.logger.info(up_msg)
                f_des = FlowDes(f.src,f.dst,f.dst_port,f.new,f.old,f.up_type,f.trans_type)
                info.new_flows.append(f_des)
            self.send_to_local(ctrl_id,info)
    
#for communicate with local
    def init_socks(self):
        for local_id in self.locals:
            c = socket.socket()
            host = socket.gethostbyname('127.0.0.1')
            c.connect((host,6000 + local_id))
            self.sockets[local_id] = c
    
    def send_to_local(self,local_id,msg):
        str_message = pickle.dumps(msg)
        msg_len = len(str_message)
        data = struct.pack('L', msg_len) + str_message
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
        while True:
            fd, addr = server.accept()  #accept returns (conn,address) so fd is a connection
            self.logger.info("global receives a connection")
            self.global_conn(fd)  

    #here to start next step
    def process_fd_msg(self,fd_msg):
        print(fd_msg)
        flow_id = fd_msg.flow_id
        ctrl_id = fd_msg.ctrl_id
        f = self.flows[flow_id]
        f.ctrl_ok += 1
        if(len(f.ctrl_wait) == f.ctrl_ok):
            self.logger.info("it's ok")
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(self.if_flow_finished(f)):
                self.logger.info(f.flow_id + " updated")
            else:
                pass
                # self.flows_move_on.append(f.flow_id)
                #here should be next step

    def if_flow_finished(self,f):
        if(f.up_type == consts.BUF and (f.up_step == consts.BUF_ADD)):
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
        self.flows[flow_id].ctrl_wait.append(ctrl_id)
        self.flows[flow_id].up_step = consts.BUF_ADD
        self.send_to_local(0,info)
    
    #test 1
    def auto_install(self,methname):
        #put something in flow_new
        if(methname == consts.ONLY_BUF):
            self.only_buf()
#for input
    def run_server(self):
        wsgi.server(eventlet.listen(('', 8800)), self.wsgi_app, max_size=50)

    def run_experiment(self):
        eventlet.monkey_patch(socket=True, thread=True)
        self.init_socks()
        self.run_server()
    

    def wsgi_app(self, env, start_response):
        # print "Get finished msg"
        input = env['wsgi.input']
        request_body = input.read(int(env.get("CONTENT_LENGTH",0)))#post
        print(request_body)
        data_feedback = "no request"
        try:
            data_feedback = json.loads(request_body)
        except Exception as e:
            data_feedback = "error"
        print(data_feedback)
        print(data_feedback['hah'])

        self.auto_install(consts.ONLY_BUF)
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