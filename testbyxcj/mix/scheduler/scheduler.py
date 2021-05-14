# from mininet import Topo
from collections import defaultdict
import itertools
import sys
sys.path.append('../')
import logging
import logger as logger

class PolicyUtil():
    def __init__(self):
        pass
    INVALID = -1
    policy_count = 2
    BUFFER = 100
    TAG = 101
    RAW = 102

    BUFFER_PRICE = 10
    FLOW_ENTRY_PRICE = 1
    BANDWIDTH_PRICE = 1


    @classmethod
    def get_policy(cls,selector=0,multiplexr=1):
        divider = cls.policy_count * multiplexr
        if(selector % divider == 0):
            return cls.BUFFER
        elif(selector % divider ==1):
            return cls.TAG
        else:
            return cls.INVALID

def singleton(cls):
    _instance = {}
    def init_func():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]
    return init_func

# class Topo(object):
#     def __init__(self):
#         self.switches = []
#         self.links = {}
#
# {some_switch : { neighbour_switch : {"bandwidth":bw,"latency":latency}}}

@singleton
class Scheduler(object):

    def __init__(self):
        self.flows = None
        self.topo = None
        self.policies = {}
        self.flow_dict = {}

        flow_dict = {}  # {flow_id: info}  info{rate, loss, latency, instance}
        policies = {}  # {flow_id: PolicyConst}
        self.link2bw_dict = {}
        self.link2latency_dict = {} # not used yet
        self.link2flow_dict = defaultdict(list)

        self.dpid2flowspace_dict ={}
        self.dpid2ctrl_dict = {}
        # self.ctrl2buffspace_dict = {}
        self.ctrl2bufferspace_dict = None

        self.created_flow_index = []
        self.removed_flow_index = []

        logger.init('./globalhapi.log',logging.INFO)
        self.logger=logger.getLogger('scheduler',logging.INFO)

    def prepare_data(self, topo, flows, ctrl_dict, sw_dict):
        self.link2flow_dict.clear()
        self.link2bw_dict.clear()
        self.link2latency_dict.clear()
        self.dpid2flowspace_dict.clear()
        self.dpid2ctrl_dict.clear()
        # self.ctrl2buffspace_dict.clear()
        self.policies.clear()
        self.flow_dict.clear()
        self.created_flow_index = []
        self.removed_flow_index = []

        self.ctrl2bufferspace_dict = ctrl_dict

        for dpid, dp_info in sw_dict.items():
            ctrl_id = dp_info["ctrl"]
            assert ctrl_id
            flowspace = dp_info["flowspace"]
            assert flowspace >= 0
            self.dpid2ctrl_dict[dpid] = ctrl_id
            self.dpid2flowspace_dict[dpid] = flowspace
        # update the refs
        self.topo = topo
        self.flows = flows
        # prepare dpid2flowspace_dict {dpid : remaining flowspace}
        # prepare ctrl2buffspace_dict {ctr_id : remaining bufferspace}
        # prepare link2bw_dict
        for s1, others in topo.items():
            for s2, s1_s2_link in others.items():
                link_bw = s1_s2_link["bandwidth"]
                link_latency = s1_s2_link["latency"]
                self.link2bw_dict[(s1,s2)] = link_bw
                assert link_bw >= 0

        # prepare flow_dict & policies & link2flow_dict
        for f_id,f in flows.items():
            # flow_dict -> {id: info}
            info = {}
            assert f.ratio >= 0
            assert f.target_loss >= 0
            assert f.target_latency >= 0
            info["rate"] = f.ratio            
            info["loss"] = f.target_loss
            info["latency"] = f.target_latency
            info["instance"] = f
            info["old_path"] = f.old
            info["new_path"] = f.new
            self.flow_dict[f.flow_id] = info

            # prepare link2flow_dict
            for i in range(len(f.old)-2):
                switch_i = f.old[i]
                switch_j = f.old[i+1]
                self.link2flow_dict[(switch_i,switch_j)].append(f.flow_id)


    def find_common_diff_switch_for_flows(self):
        for fid,f_info in self.flow_dict.items():
            old_path = f_info["old_path"]
            new_path = f_info["new_path"]

            # find same and diff, assume no loop
            # todo: what if have loop?
            common, new, old = [],[],[]
            # for i in range(0,len(old_path)):
            i = 0

            # handle flow creation remove, empty old/new paths
            if(not old_path or not new_path):
                if(not old_path):
                    self.created_flow_index.append(fid)
                    # f_info[]
                else:
                    self.removed_flow_index.append(fid)

                continue


            while(old_path[i] == new_path[i]):
                # common.append(old_path[i])
                i += 1
            diverge_point = i - 1
            common.extend(old_path[:diverge_point+1])

            i = -1
            while(old_path[i] == new_path[i]):
                i -= 1
            i += 1
            converge_point = i
            common.extend(old_path[i:])
            # for i in old[diverge_point+1:converge_point]:

            new.extend(new_path[diverge_point+1:converge_point])
            old.extend(old_path[diverge_point+1:converge_point])

            # self.flow_dict[]
            f_info["common_nodes"] = common
            f_info["old_only_nodes"] = old
            f_info["new_only_nodes"] = new
            f_info["diverge_point"] = old_path[diverge_point]
            f_info["converge_point"] = old_path[converge_point]
            
            
            # f_info["old_links"] =  []
            # for i in range(0,len(old_path)-1):
            #     f_info["old_links"].append(old_path[i],old_path[i+1])
            # f_info["new_links"] = []
            # for i in range(0,len(old_path))


    def schedule(self, topo, flows, ctrl_dict, dp_dict):
        # flow_dict = {} #{flow_id: info}  info{rate, loss, latency, instance}
        # policies = {} #{flow_id: PolicyConst}
        # for lc_info in l_controller_info:
        #     # lc_info -> {id: cache,}
        #     lc_info.cache
        #
        # # s_info -> {dpid: {switich_info}}
        # return policies

        # prepare
        self.logger.info("mxd input parameters===")
        self.logger.info(flows)
        self.logger.info(ctrl_dict)
        self.logger.info(dp_dict)


        self.prepare_data(topo, flows, ctrl_dict, dp_dict)
        self.find_common_diff_switch_for_flows()

        # todo! get a random policy, and record the policy == done
        # generate policies
        potential_policies = []
        flow_count = len(flows)
        policy_space_size = pow(PolicyUtil.policy_count,flow_count)
        policy_space = [p for p in range(policy_space_size)]
        # for policy_id in policy_space:
        #     for flow_selector in range(1, flow_count+1):
        #         policy_selector = policy_id % flow_selector
        #         policy = PolicyUtil.get_policy(selector=policy_selector)

        policy_seed = [i for i in range(PolicyUtil.policy_count)]
        # policy_seed = []
        # lambda x : policy_seed.append(x)

        available_policies = [PolicyUtil.get_policy(selector=i) for i in policy_seed]

        generated_policies = itertools.product(available_policies, repeat=flow_count)
        # generated_policies = [PolicyUtil.get_policy(selector=i) for i in generated_policy_seeds]


        for policy in generated_policies:
            policy_entry = {} #{fid:policy}
            temp = zip(self.flow_dict.keys(), policy)
            for(fid,p) in temp:
                #handle flow creation or delete
                if(fid in self.created_flow_index or fid in self.removed_flow_index):
                    policy_entry[fid] = PolicyUtil.RAW
                else:
                    policy_entry[fid] = p
            potential_policies.append(policy_entry)
        # lambda: x,y: potential_policies[x] = y

        # todo! potential_policies should be evaluated in the following part

        best_choice = 0
        best_grade = -100.00
        best_violation_ratio = 100.00
        best_violation_count = 100
        # best_performance = [best_grade,best_violation_ratio,best_violation_count]
        best_performance = [best_violation_ratio, best_grade, best_violation_count]
        # policy_space_size = len(potential_policies)

        # for policy in potential_policies:
        for index_of_policy in range(len(potential_policies)):
            policy = potential_policies[index_of_policy]
            # calculate demanded_flow_space & demanded_buffer_space
            demanded_flowspace_dict = defaultdict(float)
            demanded_bufferspace_dict = defaultdict(float)
            demanded_bandwidth_dict = defaultdict(float)

            # case 1 : no dependency, i.e., no_common_node
            for fid, f_info in self.flow_dict.items():

                # 1.1 PolicyConst.TAG check switch flowspace

                # if(self.policies[fid] == PolicyUtil.TAG):

                # handle flow creation or remove
                if (policy[fid] == PolicyUtil.RAW):
                    if(fid in self.removed_flow_index):
                        # do nothing
                        pass
                    elif(fid in self.created_flow_index):
                        # calculate the bandwidth value
                        new_path = f_info["new_path"]
                        for i in range(0,len(new_path)-1):
                            demanded_bandwidth_dict[(new_path[i],new_path[i+1])] += f_info["rate"]
                        

                elif (policy[fid] == PolicyUtil.TAG):
                    # **diverge_point** **converge_point**
                    # denote **new_switch** as the ones appear only in new path.
                    # assume 4 extra flow entries on **diverge_point** / **converge_point** and 2 extra flow entries
                    # on **new_switch** for TAGGING
                    COMMONSWITCH_TAG_ENRTY = 4
                    NEWSWITCH_TAG_ENTRY = 2
                    diverge_point = f_info["diverge_point"]
                    converge_point = f_info["converge_point"]
                    demanded_flowspace_dict[diverge_point] += COMMONSWITCH_TAG_ENRTY
                    demanded_flowspace_dict[converge_point] += COMMONSWITCH_TAG_ENRTY

                    new_switch = f_info["new_only_nodes"]
                    for ns in new_switch:
                        demanded_flowspace_dict[ns] += NEWSWITCH_TAG_ENTRY

                    # for i in f_info["old_path"]
                    old_path = f_info["old_path"]
                    new_path = f_info["new_path"]
                    # update bandwidth demand
                    old_link_list = []
                    new_link_list = []
                    for i in range(0,len(old_path)-1):
                        old_link_list.append((old_path[i],old_path[i+1]))
                    for i in range(0,len(new_path)-1):
                        new_link_list.append((new_path[i],new_path[i+1]))
                    link_array = list(set(old_link_list + new_link_list))
                    for link in link_array:
                        demanded_bandwidth_dict[link] += f_info["rate"]

                    # for i in range(0,len(old_path)-1):
                    #     demanded_bandwidth_dict[(old_path[i],old_path[i+1])] += f_info["rate"]
                    # for i in range(0,len(new_path)-1):
                    #     demanded_bandwidth_dict[(new_path[i],new_path[i+1])] += f_info["rate"]

                # 1.2 PolicyConst.BUFFER check controller bufferspace

                # elif(self.policies[fid] == PolicyUtil.BUFFER):

                elif (policy[fid] == PolicyUtil.BUFFER):
                    flow_rate = f_info["rate"]
                    _TIME_TO_UPDATE_ONE_SWITCH = 0.005 #second
                    switch_count = len(f_info["new_path"])
                    # buffer_time = _TIME_TO_INSTALL_ONE_ENTRY * switch_count / 1000
                    # _TIME_TO_UPDATE_ONE_SWITCH
                    # buffer_time = _TIME_TO_UPDATE_ONE_SWITCH * switch_count
                    estimated_buffer_time = 30.00 / 1000 #ms

                    self.logger.info("estimated_buffer_time")
                    self.logger.info(estimated_buffer_time)

                    self.logger.info("flow_rate")
                    self.logger.info(flow_rate)

                    estimated_cache_size = 1.00 * flow_rate * estimated_buffer_time  #MB
                    
                    self.logger.info("estimated_cache_size")
                    self.logger.info(estimated_cache_size)

                    dpid = f_info["diverge_point"]
                    controller_id = self.dpid2ctrl_dict[dpid]
                    demanded_bufferspace_dict[controller_id] += estimated_cache_size

                # 1.3 todo: check latency? how?


            # 1.4 todo: evaluate policy
            grade, violation_ratio, violation_count =\
                self.evaluate_policy(demanded_flowspace_dict, demanded_bufferspace_dict, demanded_bandwidth_dict)
            if(violation_ratio <= best_performance[0]):
                if(grade > best_performance[1] or violation_count < best_performance[2]):
                    best_choice = index_of_policy
                    best_performance = [violation_ratio, grade, violation_count]
        self.logger.info("scheduling results ============")
        self.logger.info("potential_policies[best_choice]")
        self.logger.info(potential_policies[best_choice])
        self.logger.info("best_performance")
        self.logger.info(best_performance)
        return potential_policies[best_choice], best_performance


            # case 2 : todo: solve dependency !!


    def evaluate_policy(self, demanded_flowspace_dict, demanded_bufferspace_dict,demanded_bw_dict):

        # self.link2flow_dict
        # self.link2bw_dict
        # self.link2latency_dict

        total_buffer_demand = 0.00
        total_fs_demand = 0.00
        total_bw_demand = 0.00

        # 1 first_filtering : check remaining resources
        # 1.1 bandwidth
        violate_bw_count = 0
        violate_bw_percent = 0.00

        print(demanded_flowspace_dict)
        print(demanded_bw_dict)
        print(demanded_bufferspace_dict)

        for link,bandwidth_demand in demanded_bw_dict.items():
            total_bw_demand += bandwidth_demand
            assert bandwidth_demand > 0
            if(bandwidth_demand > self.link2bw_dict[link]):
                self.logger.info("bandwidth violation happens")
                violate_bw_count += 1
                violate_bw_percent += 1.00 * (bandwidth_demand -
                                                     self.link2bw_dict[link])/(self.link2bw_dict[link]+0.0001)

        # 1.2 flow_space
        violate_fs_count = 0
        violate_fs_percent = 0.00
        for dpid,flow_space_demand in demanded_flowspace_dict.items():
            total_fs_demand += flow_space_demand
            assert flow_space_demand > 0
            if(flow_space_demand > self.dpid2flowspace_dict[dpid]):
                self.logger.info("fs violation happens")
                violate_fs_count += 1
                violate_fs_percent += 1.00 * (flow_space_demand -
                                                     self.dpid2flowspace_dict[dpid])/(self.dpid2flowspace_dict[dpid]+0.0001)

        # 1.3 buffer_space
        violate_buffer_count = 0
        violate_buffer_percent = 0.00

        for ctrl_id, buffer_space_demand in demanded_bufferspace_dict.items():
            total_buffer_demand += buffer_space_demand
            # self.logger.info("in scheduler")
            self.logger.info(self.ctrl2bufferspace_dict[ctrl_id])
            self.logger.info("buffer_space_demand")
            self.logger.info(buffer_space_demand)
            assert buffer_space_demand > 0
            if(buffer_space_demand > float(self.ctrl2bufferspace_dict[ctrl_id])):
                self.logger.info("buffer violation happens")
                self.logger.info("total_buffer_demand")
                self.logger.info(total_buffer_demand)
                violate_buffer_count += 1
                violate_buffer_percent += 1.00 * (buffer_space_demand -
                                                       float(self.ctrl2bufferspace_dict[ctrl_id]))/(float(self.ctrl2bufferspace_dict[ctrl_id])+0.0001)

        total_violation_count = violate_buffer_count + violate_fs_count + violate_bw_count
        total_violation_ratio = violate_bw_percent + violate_fs_percent + violate_buffer_percent

        # 2. calculate the price
        total_buffer_price = total_buffer_demand * PolicyUtil.BUFFER_PRICE
        # BUFFER_PRICE = 1
        # FLOW_ENTRY_PRICE = 1
        # BANDWIDTH_PRICE = 1

        # total_demanded_bufferspace =
        # total_demanded_flowspace =
        # total_demanded_bandwidth =

        total_fs_price = total_fs_demand * PolicyUtil.FLOW_ENTRY_PRICE
        total_bw_price = total_bw_demand * PolicyUtil.BANDWIDTH_PRICE

        # 3. grade the policies :
        policy_price = total_buffer_price + total_fs_price + total_bw_price
        grade = 1.00 / (policy_price+0.0001)
        self.logger.info("when evaluation policies=================")
        self.logger.info("total_violation_ratio")
        self.logger.info("grade")
        self.logger.info(grade)
        self.logger.info("total_violation_count")
        self.logger.info(total_violation_count)

        return grade, total_violation_ratio, total_violation_count
    # def construct_topo(self, topo):
    #      #switches
    #     for s1, others in topo.keys():
    #         for s2 in others
