from eventlet import wsgi
import eventlet

from ryu.lib import hub
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, udp
from ryu.lib.packet import ether_types

from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.controller import ofp_event


from mininet.util import ipAdd, ipStr


class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    LOGGER_NAME = "local_ctrl"
    # _CONTEXTS = {'wsgi': WSGIApplication}


#[]
    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.datapath = []


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        print("-----------------haha get a switch-------")
        datapath = ev.msg.datapath

        if datapath not in self.datapath:
            print("a new dp")
            self.datapath.append(datapath)

        # else:
        #     print("a new dp")
            

        # elif self.datapath.id == datapath.id:
        #     self.logger.info("reconnect")

        # else:
        #     self.logger.info("dp try to connect me is " + str(datapath.id))
        #     self.logger.info("dp i've connected is " + str(self.datapath.id))
        #     raise Exception('Only one switch can connect!')
        print("------------------my datapaths---------------")
        print(self.datapath)
        # self.logger.info(datapath)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(0,
                                           ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        match = parser.OFPMatch(in_port = 1)
        actions = [parser.OFPActionOutput(2)]

        self.add_flow(datapath, 1, match, actions)

        match = parser.OFPMatch(in_port = 2)
        actions = [parser.OFPActionOutput(1)]

        self.add_flow(datapath, 1, match, actions)
        # match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=ipAdd(datapath.id))
        # actions = [parser.OFPActionOutput(1)]
        # self.add_flow(datapath, 1, match, actions)
        # hub.spawn(self.run_server)
        self.ddbx()

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            # self.logger.info("-!!!--buffer id in add_flow----")
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)

        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def ddbx(self):
        # ofproto = self.datapath.ofproto
        # parser = self.datapath.ofproto_parser

        # # actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
        # #                                    ofproto.OFPCML_NO_BUFFER)]
        # actions = [parser.OFPActionOutput(0,
        #                                    ofproto.OFPCML_NO_BUFFER)]
        # match = parser.OFPMatch()
        # inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
        #                                      actions)]

        
        i = 0                                     
        while i < 100:
            for dp in self.datapath:
                ofproto = dp.ofproto
                parser = dp.ofproto_parser

        # actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
        #                                    ofproto.OFPCML_NO_BUFFER)]
                actions = [parser.OFPActionOutput(0,
                                           ofproto.OFPCML_NO_BUFFER)]
                match = parser.OFPMatch()
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
                mod = parser.OFPFlowMod(datapath=dp, priority=i,
                                    match=match, instructions=inst)
                
                dp.send_msg(mod)

            i += 1
    # def __init__(self, *args, **kwargs):
    #     super(SimpleSwitch13, self).__init__(*args, **kwargs)
    #     self.datapath = None


    # @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    # def switch_features_handler(self, ev):
    #     print("-----------------haha get a switch-------")
    #     datapath = ev.msg.datapath

    #     if self.datapath == None or datapath.id == self.datapath.id:
    #         self.datapath = datapath

    #     print("------------------my datapaths---------------")
    #     print(self.datapath)
    #     # self.logger.info(datapath)
    #     ofproto = self.datapath.ofproto
    #     parser = self.datapath.ofproto_parser

    #     match = parser.OFPMatch()
    #     actions = [parser.OFPActionOutput(0,
    #                                        ofproto.OFPCML_NO_BUFFER)]
    #     self.add_flow(self.datapath, 0, match, actions)

    #     # match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=ipAdd(datapath.id))
    #     # actions = [parser.OFPActionOutput(1)]
    #     # self.add_flow(datapath, 1, match, actions)
    #     # hub.spawn(self.run_server)
    #     self.ddbx(self.datapath)

    # def add_flow(self, datapath, priority, match, actions, buffer_id=None):
    #     ofproto = datapath.ofproto
    #     parser = datapath.ofproto_parser

    #     inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
    #                                          actions)]
    #     if buffer_id:
    #         # self.logger.info("-!!!--buffer id in add_flow----")
    #         mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
    #                                 priority=priority, match=match,
    #                                 instructions=inst)

    #     else:
    #         mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
    #                                 match=match, instructions=inst)
    #     datapath.send_msg(mod)

    # def ddbx(self,dp):
    #     # ofproto = self.datapath.ofproto
    #     # parser = self.datapath.ofproto_parser

    #     # # actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
    #     # #                                    ofproto.OFPCML_NO_BUFFER)]
    #     # actions = [parser.OFPActionOutput(0,
    #     #                                    ofproto.OFPCML_NO_BUFFER)]
    #     # match = parser.OFPMatch()
    #     # inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
    #     #                                      actions)]

        
    #     i = 0                                     
    #     while i < 100:
    #         ofproto = dp.ofproto
    #         parser = dp.ofproto_parser
    #         actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
    #                                        ofproto.OFPCML_NO_BUFFER)]
    #         match = parser.OFPMatch()
    #         inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
    #                                          actions)]
    #         mod = parser.OFPFlowMod(datapath=dp, priority=i,
    #                                 match=match, instructions=inst)
    #         dp.send_msg(mod)
    #         i += 1

    def run_server(self):
        print("here's runserver")
        server = eventlet.listen('127.0.0.1', 6800)
        while True:
            fd, addr = server.accept()
            print("--------------------")
            print(fd)
