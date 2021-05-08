# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
from scheduler import Scheduler


class BaseFlow(object):
    def  __init__(self,src,dst,dst_port,new,old,rate,latency,loss, up_type=None,trans_type='UDP'):
        self.trans_type = trans_type
        self.new = new
        self.old = old
        self.up_type = up_type
        self.up_step = None

        self.rate = rate
        self.latency = latency
        self.loss = loss

        self.src = src
        self.dst = dst
        # self.src_port = src_port
        self.dst_port = dst_port
        self.flow_id = str(src) + str(dst) + str(dst_port)


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')


    # def schedule(self, flow_info, l_controller_info, switch_info):
    info1 = {"latency":10,"rate":100,"loss":0.01}
    info2 = {"latency": 1, "rate": 10, "loss": 0.01}
    # flow1 = {1: info1}
    # flow2 = {2: info2}
    flows = {1: info1,2: info2}
    s = Scheduler()
    # s.schedule(flows,None,None)

    s1 = 1
    s2 = 2
    s3 = 3
    s4 = 4
    flowspace = 100
    ctrl1 = 1
    ctrl2 = 2
    bufferspace = 1000
    dp_dict = {s1: {"flowspace":flowspace, "ctrl":ctrl1}, s2: {"flowspace":flowspace, "ctrl":ctrl1},
               s3: {"flowspace":flowspace, "ctrl":ctrl2}, s4: {"flowspace":flowspace, "ctrl":ctrl2}}
    ctrl_dict = {ctrl1: bufferspace, ctrl2: bufferspace}


    f1 = BaseFlow(s1, s3, 1, [s1, s4, s3], [s1, s2, s3], 10, 10, 10)
    f2 = BaseFlow(s2, s4, 1, [s2, s1, s4], [s2, s3, s4], 20, 10, 10)

    s1s2_bw = 100
    s1s4_bw = 100
    s1s2_ltc = 1
    s1s4_ltc = 1

    s2s3_bw = 100
    s3s4_bw = 100
    s2s3_ltc = 1
    s3s4_ltc = 1

    s1_topo_entry = {s2: {"bandwidth": s1s2_bw, "latency": s1s2_ltc}, s4 :{"bandwidth": s1s4_bw, "latency": s1s4_ltc}}
    s2_topo_entry = {s1: {"bandwidth": s1s2_bw, "latency": s1s2_ltc}, s3: {"bandwidth": s2s3_bw, "latency": s2s3_ltc}}
    s3_topo_entry = {s2: {"bandwidth": s2s3_bw, "latency": s2s3_ltc}, s4: {"bandwidth": s3s4_bw, "latency": s3s4_ltc}}
    s4_topo_entry = {s1: {"bandwidth": s1s4_bw, "latency": s1s4_ltc}, s3: {"bandwidth": s3s4_bw, "latency": s3s4_ltc}}

    topo = {}
    topo[s1] = s1_topo_entry
    topo[s2] = s2_topo_entry
    topo[s3] = s3_topo_entry
    topo[s4] = s4_topo_entry

    flows = [f1,f2]

    s.schedule(topo, flows, ctrl_dict, dp_dict)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
