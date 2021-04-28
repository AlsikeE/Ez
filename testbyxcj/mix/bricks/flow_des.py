
#flow object in local controller
class FlowDes(object):
    def __init__(self,src,dst,dst_port,new,old,up_type=None,trans_type='UDP'):

        self.trans_type = trans_type
        self.new = new
        self.old = old
        self.up_type = up_type
        self.up_step = None
        self.barrs_wait = [] #the barriers for update
        self.barrs_ok = 0

        self.src = src
        self.dst = dst
        # self.src_port = src_port
        self.dst_port = dst_port
        self.flow_id = src + dst + str(dst_port)

