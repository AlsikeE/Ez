import redis
import socket
import logging
import threading
import multiprocessing
import time
import cPickle as pickle
import logger as logger
from ryu.lib.packet import *

import consts
#Process

class BufferManager(multiprocessing.Process):
    def __init__(self,name,conn):
# class BufferManager(threading.Thread):
#     def __init__(self,name):
        super(BufferManager,self).__init__()
        self.conn = conn
        self.daemon = True
        # threading.Thread.__init__(self)
        self.pool = redis.ConnectionPool(host='localhost',port=6379)
        self.rds = redis.Redis(connection_pool=self.pool)
        self.name = name
        self.pkg_to_save = []
        logger.init('./buf.log',logging.INFO)
        self.logger=logger.getLogger('bm',logging.INFO)


    def run(self):
        if(self.conn):
            print("i have a conn")
        while(True):
            # print("but in the list" + str(len(self.pkg_to_save)))
            cmd_to_me = None
            try:
                cmd_to_me = self.conn.recv()
            except Exception as err:
                # print("Nothing sent to me, i'm boring")
                # time.sleep(0.01)
                pass
            if(cmd_to_me):
                # print("i can read!!!!")
                msg_type,key,dpid,pkg,in_port = self.read_and_make_key(cmd_to_me)
                if(msg_type == consts.BUF_PUSH):
                    value = self.make_value(dpid,pkg,in_port)
                    self.save_to_buffer(key,value)
                elif(msg_type == consts.BUF_POP):
                    self.get_from_buffer(key)


    def save_to_buffer(self,key,value):
        self.rds.rpush(key,value)
    
    def get_from_buffer(self,key):
        msg = self.rds.lpop(key)
        while(msg):
            self.conn.send(msg)
            msg = self.rds.lpop(key)

    def read_and_make_key(self,cmd_to_me):
        cmd_json = pickle.loads(cmd_to_me)
        msg_type = cmd_json["msg_type"]
        key = cmd_json["src"]+cmd_json["dst"]+str(cmd_json["dst_port"])
        dpid = cmd_json["dpid"]
        pkg = cmd_json["pkg"]
        in_port = cmd_json["in_port"]
        return msg_type,key,dpid,pkg,in_port
    
    def make_value(self,dpid,pkg,in_port):
        v = {
            "dpid":dpid,
            "pkg":pkg,
            "in_port":in_port
        }
        return pickle.dumps(v)


