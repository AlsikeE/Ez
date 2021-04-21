import redis
import socket
import logging
import threading
import multiprocessing
import time
import cPickle as pickle
import logger as logger
from ryu.lib.packet import *

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

        # self.run()

    def run(self):
        if(self.conn):
            print("i have a conn")
        while(True):
            # print("but in the list" + str(len(self.pkg_to_save)))
            try:
                data = self.conn.recv()
                print(data)
                self.save_to_buffer(0,data)
            except Exception as err:
                print("No No No No No")
                time.sleep(1)

        # while(True):
        #     tosave = len(self.pkg_to_save)
        #     if(tosave>0):
        #         pkg = self.pkg_to_save[0]
        #         self.save_to_buffer(0,pkg)
        #         self.pkg_to_save.pop(0)
        #     else:
        #         print("sleep")
        #         time.sleep(1)

            
  

    def save_to_buffer(self,key,v):
        # r = redis.Redis(connection_pool=self.pool)
        # value = pickle.dumps(v.data)
        self.rds.rpush(key,v)
    
    def get_from_buffer(self,key):
        # r = redis.Redis(connection_pool=self.pool)
        return self.rds.lpop(key)

    def read_cmd(self,data):
        pass

def main():
    bm = BufferManager()
    bm.save_to_buffer("emm",'hah')
    print(bm.get_from_buffer('emm'))

if __name__ == '__main__':
    main()
    