import threading
import multiprocessing
import time
from gevent import monkey
monkey.patch_all(Process=False)

class Father(object):
    def __init__(self):
        self.son = None
        self.conn = None
        self.init_my_son()

    def init_my_son(self):
        self.conn, son_conn = multiprocessing.Pipe()
        self.son = Son(name='zaizai',conn = son_conn)
        self.son.start()

    def father_run(self):
        while(True):
            self.conn.send("you are my son")
            print ("father is running")
            time.sleep(2)
            print(self.conn.recv())



class Son(multiprocessing.Process):
    def __init__(self, name,conn):
        multiprocessing.Process.__init__(self,name=name)
        self.conn = conn

    def run(self):
        while(True):
            print (self.name + " is running")
            print(self.conn.recv())
            self.conn.send("i know i know i know")
            time.sleep(2)
        
f= Father()
f.father_run()


