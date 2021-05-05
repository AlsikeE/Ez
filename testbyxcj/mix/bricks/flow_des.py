
class BaseFlow(object):
    def  __init__(self,src,dst,dst_port,old,new,up_type=None,trans_type='UDP'):
        self.trans_type = trans_type
        self.new = new
        self.old = old
        self.up_type = up_type
        self.up_step = None

        self.src = src
        self.dst = dst
        # self.src_port = src_port
        self.dst_port = dst_port
        self.flow_id = src + dst + str(dst_port)
        self.version_tag = None
        
    

#flow object in local controller
class FlowDes(BaseFlow):
    def __init__(self, src, dst, dst_port, old,new, up_type=None, trans_type='UDP'):
        super(FlowDes,self).__init__(src, dst, dst_port,old,new, up_type=up_type, trans_type=trans_type)
        self.barrs_wait = [] #the barriers for update
        self.barrs_ok = 0
        self.dp_tag = None
        self.dp_tag_reverse = None


class FlowDesGlobal(BaseFlow):
    def __init__(self, src, dst, dst_port,  old,new, up_type=None, trans_type='UDP'):
        super(FlowDesGlobal,self).__init__(src, dst, dst_port, old,new, up_type=up_type, trans_type=trans_type)
        self.ctrl_wait = []
        self.ctrl_ok = 0
        self.ctrl_tag = None #the local controller which tag the pkgs
        self.ctrl_tag_reverse = None
        self.ctrl_buf = None #the one buf pkgs

        
