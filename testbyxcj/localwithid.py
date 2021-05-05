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
from ryu.app import wsgi as ryuwsgi
from eventlet.green import socket


class TestId(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(TestId, self).__init__(*args, **kwargs)
        self.local_id = 0 #remember change me !
    
    def hah(self):
        print("haha" + str(self.local_id))

class TestId1(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(TestId1, self).__init__(*args, **kwargs)
        self.local_id = 1 #remember change me !   
        self.hah()

    def hah(self):
        print("haha" + str(self.local_id)) 

class TestId2(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
 
    def __init__(self, *args, **kwargs):
        super(TestId2, self).__init__(*args, **kwargs)
        self.local_id = 2 #remember change me !
        self.hah()
    
    def hah(self):
        print("haha" + str(self.local_id))

def main():
    app_lists = ['ryu.controller.ofp_handler','TestId1','TestId2']

    app_mgr = app_manager.AppManager.get_instance()
    # app_mgr.run_apps(app_lists)
    app_mgr.contexts_cls.update({
        'TestId1':TestId1,
        'TestId2':TestId2
    })
    contexts = app_mgr.create_contexts()
    services = app_mgr.instantiate_apps(**contexts)
    webapp = ryuwsgi.start_service(app_mgr)
    # app_mgr.load_apps(app_lists)
    # contexts = app_mgr.create_contexts()
    # services = []
    # services.extend(app_mgr.instantiate_apps(**contexts))

    # webapp = wsgi.start_service(app_mgr)
    # if webapp:
    #     thr = hub.spawn(webapp)
    #     services.append(thr)

    # try:
    #     hub.joinall(services)
    # except KeyboardInterrupt:
    #     logger.debug("Keyboard Interrupt received. "
    #                  "Closing RYU application manager...")
    # finally:
    #     app_mgr.close()


if __name__ == "__main__":
    main()
