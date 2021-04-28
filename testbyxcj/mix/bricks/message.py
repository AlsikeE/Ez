class InfoMessage(object):
    def __init__(self,ctrl_id=1):
        self.ctrl_id = ctrl_id
        self.ums = []


class UpdateMessageByFlow(object):
    def __init__(self,flow_id,up_type,up_step):
        self.flow_id = flow_id
        self.up_type = up_type
        self.up_step = up_step
        self.to_add = [] #dplast,dp,dpnext
        self.to_del = []#dp_last_old,dp,dp_next_old
