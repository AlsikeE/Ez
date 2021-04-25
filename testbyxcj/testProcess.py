import threading
import multiprocessing
import time
# from gevent import monkey
# monkey.patch_all()
# from gevent import sleep
import eventlet
class Father(object):
    def __init__(self):
        self.son = None
        self.conn = None
        
        self.pkg_to_buf = multiprocessing.Array('i',3)
        self.msg_to_ana = multiprocessing.Array('i',3)

        self.init_my_son()

    def init_my_son(self):
        # self.conn, son_conn = multiprocessing.Pipe()
        self.son = Son(name='zaizai',pkgs=self.pkg_to_buf,msgs=self.msg_to_ana)
        self.son.start()
        # son_conn.close()

    def father_run(self):
        i = 0
        while True:
            # print("father is running")
            self.pkg_to_buf=[1,2,3]
            i += 1

            print(self.msg_to_ana[0])



class Son(multiprocessing.Process):
    def __init__(self, name,pkgs,msgs):
        multiprocessing.Process.__init__(self,name=name)
        self.pkg_to_buf = pkgs
        self.msg_to_ana = msgs
        self.daemon = True

    def run(self):
        i = 0
        while True:
            # print(self.name +" is running")
            self.msg_to_ana=['str'+str(i),'str'+str(i+1),'str'+str(i+2)]
            i += 1
            if(self.pkg_to_buf[0]):
                for i in self.pkg_to_buf:
                    print(i)
                self.pkg_to_buf=[None,None,None]

            # time.sleep(0.01)
    # def a_small_func(self):
    #     i = 1
    #     while(i > 0):
    #         self.conn.send("small_fun" + str(i))
    #         i-=1
        # self.conn.close()
f= Father()
f.father_run()




# import time
# from multiprocessing import Pipe, Process
 
 
# def sed_fun(p_conn):
#     all_sed = 0
#     s, r = p_conn
#     send_num = 0
 
#     while True:
#         time.sleep(1)
#         all_sed += 1
#         print('sending...', all_sed)
#         try:
#             send_num += 1
#             print('try to send', send_num)
 
#             if send_num < 10:
#                 msg = 1111
#                 small_fun(s)
#                 s.send([msg])
 
#             elif send_num > 30:
#                 msg = 2222
#                 print('sending', msg)
#                 s.send([msg])
 
#             else:
#                 print('no send any more')
#                 # sed.close() # uncomment will cause the sed proc not to be resurrected after 30
 
#         except Exception as e:
#             print(e)
#             print('can not send')
 

# def small_fun(s):
#     i = 10
#     while(i > 0):
#         s.send("haha" + str(i))
#         i-=1

# def rec_fun(p_conn):
#     all_rec = 0
#     s, r = p_conn
 
#     while True:
#         time.sleep(1)
#         all_rec += 1
#         print('\nreceiving.....', all_rec)
 
#         try:
#             print('\n', r.recv())  # If there is no data in pipe, it will be stuck here with no notification!!!
#         except Exception as e:  # this except has no use when stucked above!
#             print(e)
#             print('can not recv')
 
 
# if __name__ == '__main__':
 
#     sed, rec = Pipe()
 
#     sed_proc = Process(target=sed_fun, args=((sed, rec), ))
#     rec_proc = Process(target=rec_fun, args=((sed, rec), ))
 
#     sed_proc.start()
#     rec_proc.start()
 
#     # sed_proc.join()
#     # rec_proc.join()
