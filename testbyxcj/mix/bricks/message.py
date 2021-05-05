class InfoMessage(object):
    def __init__(self,ctrl_id=1):
        self.ctrl_id = ctrl_id
        self.new_flows = [] # tell local new flows occure
        # self.del_flows = [] # tell local some flows go
        self.ums = []


class UpdateMessageByFlow(object):
    def __init__(self,flow_id,up_type,up_step):
        self.flow_id = flow_id
        self.up_type = up_type
        self.up_step = up_step
        self.to_add = [] #dplast,dp,dpnext
        self.to_del = []#dp_last_old,dp,dp_next_old
        self.version_tag = None
        self.if_reverse =False#fanxiang tag for <-- flows

class FeedbackMessge(object):
    def __init__(self,flow_id,ctrl_id):
        self.flow_id = flow_id
        self.ctrl_id = ctrl_id
