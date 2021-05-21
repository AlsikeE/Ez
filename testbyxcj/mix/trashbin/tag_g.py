    #more to do for find a version tag such as for conflicts
    def find_version_tag(self,f):
        # if(f.new_version_tag == 2 and f.old_version_tag == 1):
        #     return 3,4
        return 1,2


    def send_mod_packet_vid_cmd(self,f,dp_tup,ifr):
        self.logger.info("--------------in send mod vid ----------------")
        info = InfoMessage(f.ctrl_tag)
        l,dpid,n = dp_tup
        um = UpdateMessageByFlow(f.flow_id,f.up_type,f.up_step)
        
        # um.version_tag = f.old_version_tag if old else f.new_version_tag
        um.version_tag = 2
        self.logger.info(um.up_step)
        send_ctrl = self.dp_to_local[dpid]
        if(ifr):
            um.if_reverse = True
            um.to_add.append((n,dpid,l))
            self.logger.info(um.to_add)
            f.ctrl_tag_reverse = send_ctrl
        else:
            um.to_add.append(dp_tup)
            f.ctrl_tag = send_ctrl
        info.ums.append(um)
        self.send_to_local(send_ctrl,info)
        if(send_ctrl not in f.ctrl_wait):
            f.ctrl_wait.append(send_ctrl)

# def send_mod_packet_vid_cmd(self,f,dp_tup,old,ifr):
#         self.logger.info("--------------in send mod vid ----------------")
#         info = InfoMessage(f.ctrl_tag)
#         l,dpid,n = dp_tup
#         um = UpdateMessageByFlow(f.flow_id,f.up_type,f.up_step)
        
#         # um.version_tag = f.old_version_tag if old else f.new_version_tag
#         um.version_tag = 2
#         self.logger.info(um.up_step)
#         send_ctrl = self.dp_to_local[dpid]
#         if(ifr):
#             um.if_reverse = True
#             um.to_add.append((n,dpid,l))
#             self.logger.info(um.to_add)
#             f.ctrl_tag_reverse = send_ctrl
#         else:
#             um.to_add.append(dp_tup)
#             f.ctrl_tag = send_ctrl
#         info.ums.append(um)
#         self.send_to_local(send_ctrl,info)
#         if(send_ctrl not in f.ctrl_wait):
#             f.ctrl_wait.append(send_ctrl)
    #TAG NEW step 0: tell every local flows come
    def tag0(self,flows={}):
        aggre_dict = {}
        for f_id, f in flows.items():
            f.up_type = consts.TAG
            f.up_step = 0
            # f.old_version_tag,f.new_version_tag = self.find_version_tag(f)
            to_add,to_del = tools.diff_old_new(f.old,f.new)
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,to_del)
            # self.make_and_send_info(aggre_dict,False)
            left,right = {},{}
            try:
                right.update({'old':to_del[-1]})
                to_del.pop(-1)
            except:
                self.logger.info("right old wrong")
            
            try:
                right.update({'new':to_add[-1]})
                to_add.pop(-1)
            except:
                self.logger.info("right new wrong")
            
            try:
                left.update({'old':to_del[0]})
                to_del.pop(0)
            except:
                self.logger.info("left old wrong")
            
            try:
                left.update({'new':to_add[0]})
                to_add.pop(0)
            except:
                self.logger.info("left new wrong")
            
            self.tag_flows_temp.update({f_id:{'to_add':to_add,'to_del':to_del,'left':left,'right':right}})

        self.logger.info(" tag0")
        self.logger.info(self.tag_flows_temp)
        self.make_and_send_info(aggre_dict,False)
        for f_id, f in flows.items():
            self.started_update_to_flows_new(f)

    #TAG new step 1: add popvlan id in start for reverse and end for normal

    def tag1_pop_add(self,f):    
        f.up_step = consts.TAG_POP_ADD
        up_infos = self.tag_flows_temp[f.flow_id]
        nothing_flag = True
        # if(up_infos['left'].has_key('old')):
        #     self.send_mod_packet_vid_cmd(f,up_infos['left']['old'],False)
        #     nothing_flag = False
        if(up_infos['left'].has_key('new')):
            self.send_mod_packet_vid_cmd(f,up_infos['left']['new'],False)
            nothing_flag = False
        # if(up_infos['right'].has_key('old')):
        #     self.send_mod_packet_vid_cmd(f,up_infos['right']['old'],True)
        #     nothing_flag = False
        if(up_infos['right'].has_key('new')):
            self.send_mod_packet_vid_cmd(f,up_infos['right']['new'],True)
            nothing_flag = False
        
        # if(nothing_flag):
        #     self.tag2_push_old(f)
        

    # def tag2_push_old(self,f):
    #     f_id = f.flow_id
    #     f.up_step = consts.TAG_PUSH_OLD
    #     up_info = self.tag_flows_temp[f_id]
    #     try:
    #         self.send_mod_packet_vid_cmd(f,up_info['left']['old'],True,False)
    #     except:
    #         self.logger.info("no old")
    #     try:
    #         self.send_mod_packet_vid_cmd(f,up_info['right']['old'],True,True)
    #     except:
    #         self.logger.info("no old")
    #         self.tag3_tag_old(f)
    
    # def tag3_tag_old(self,f):
    #     aggre_dict = {}
    #     f.up_step = consts.TAG_OLD_TAG
    #     to_del = self.tag_flows_temp[f.flow_id]['to_del']
    #     if(len(to_del) == 0):
    #         self.tag4_tag_new(f)
    #         return
    #     aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f.flow_id,to_del,[])
    #     self.make_and_send_info(aggre_dict,True)
    
    def tag2_tag_new(self,f):
        aggre_dict = {}
        f.up_step = consts.TAG_NEW_TAG
        to_add = self.tag_flows_temp[f.flow_id]['to_add']
        if(len(to_add) == 0):
            self.tag3_push_new(f)
            return
        aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f.flow_id,to_add,[])
        self.make_and_send_info(aggre_dict,False)

    def tag3_push_new(self,f):
        self.logger.info("!!!!!!!!!!!!!!!!!!in tag 5")
        f.up_step = consts.TAG_PUSH_NEW
        up_infos = self.tag_flows_temp[f.flow_id]
        if('new' not in up_infos['right'].keys() and 'new' not in up_infos['left'].keys()):
            self.logger.info("no new")
            self.tag6_del_old(f)
            return 
        try:
            self.send_mod_packet_vid_cmd(f,up_infos['left']['new'],False)
        except:
            self.logger.info("no new")
        try:
            self.send_mod_packet_vid_cmd(f,up_infos['right']['new'],True)
        except:
            self.logger.info("no new")
    
    def tag4_del_old(self,f):
        f.up_step = consts.TAG_DEL_OLD
        aggre_dict = {}
        to_del = self.tag_flows_temp[f.flow_id]['to_del']
        if(len(to_del) == 0):
            self.tag7_mod_new(f)
            return
        aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f.flow_id,[],to_del)
        self.make_and_send_info(aggre_dict,True)

    def tag5_mod_new(self,f):
        f.up_step = consts.TAG_MOD_NEW
        aggre_dict = {}
        to_add = self.tag_flows_temp[f.flow_id]['to_add']
        if(len(to_add) == 0):
            self.tag8_push_old_del(f)
            
            return
        aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f.flow_id,to_add,[])
        self.make_and_send_info(aggre_dict,False)

    def tag6_push_old_del(self,f):
        pass

    def tag7_pop_del(self,f):
        pass

    def tag_fb_process_new(self,f_id):
        self.logger.info("in tag fb")
        f = self.flows_new[f_id]
        f.ctrl_ok += 1
        self.logger.info(f.up_step)
        aggre_dict = {}
        if(len(f.ctrl_wait) == f.ctrl_ok):
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(f.up_step == 0):
                self.logger.info(f_id + "tag info telled every one")
                self.tag1_pop_add(f)
            # elif(f.up_step == consts.TAG_POP_ADD):
            #     self.logger.info("tag pop add finished")
            #     self.tag2_push_old(f)
            # elif(f.up_step == consts.TAG_PUSH_OLD):
            #     self.logger.info("tag push old finished")
            #     self.tag3_tag_old(f)
            elif(f.up_step == consts.TAG_POP_ADD):
                self.logger.info(f_id + "tag pop add finished")
                self.tag2_tag_new(f)
            elif(f.up_step == consts.TAG_NEW_TAG):
                self.logger.info( f_id + "tag new tag finished")
                self.tag3_push_new(f)
            elif(f.up_step == consts.TAG_PUSH_NEW):
                self.logger.info(f_id + "tag push new finished")
                self.logger.info("update over by tag")
                self.logger.info(nowTime())
                # self.tag4_del_old(f)
            # elif(f.up_step == consts.TAG_DEL_OLD):
            #     self.logger.info("update over by tag")
            #     self.logger.info(nowTime())
            #     self.tag7_mod_new(f)
            # elif(f.up_step == consts.TAG_MOD_NEW):
            #     self.logger.info("tag mod new finished")
            #     self.tag8_push_old_del(f)
            # elif(f.up_step == consts.TAG_PUSH_OLD_DEL):
            #     self.logger.info("tag push old del finished")
            #     self.tag9_pop_del(f)
            # elif(f.up_step == consts.TAG_POP_DEL):
            #     self.logger.info("update over by tag")
            # elif(f.up_step == consts.TAG_PUSH_NEW):
            #     self.logger.info("tag push new finished")
            #     self.tag6_del_old(f)
 ################################################################           
    #TAG step 1
    def tag_add(self, flows={}):
        aggre_dict = {}
        # for f_id,f in self.flows_new.items():
        for f_id,f in flows.items():
            f.up_type = consts.TAG
            f.up_step = consts.TAG_ADD
            f.version_tag = self.find_version_tag(f)
            to_add, to_del = tools.diff_old_new(f.old,f.new)
           
            aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,to_add,[])
            self.started_update_to_flows_new(f)
        # self.logger.info(aggre_dict)
        self.make_and_send_info(aggre_dict,False)

    def find_packet_tag_dp(self,f):
        to_add, to_del = tools.diff_old_new(f.old,f.new)
        to_add_bak,to_del_bak = tools.diff_old_new(f.new,[])
        dp_tup =  to_del[0] if to_del else to_del_bak[0]
        to_add, to_del = tools.diff_old_new(list(reversed(f.old)),list(reversed(f.new)))
        to_add_bak,to_del_bak = tools.diff_old_new(list(reversed(f.new)),[])
        dp_tup_reverse = to_del[0] if to_del else to_del_bak[0]
        return dp_tup,dp_tup_reverse

    def send_pkg_tag_cmd(self,f,dp_tup,ifr):
        info = InfoMessage(f.ctrl_tag)
        l,dpid,n = dp_tup
        um = UpdateMessageByFlow(f.flow_id,f.up_type,f.up_step)
        um.to_add.append(dp_tup)
        um.version_tag = f.version_tag
        send_ctrl = self.dp_to_local[dpid]
        if(ifr):
            um.if_reverse = True
            f.ctrl_tag_reverse = send_ctrl
        else:
            f.ctrl_tag = send_ctrl
        info.ums.append(um)
        self.send_to_local(send_ctrl,info)
        if(send_ctrl not in f.ctrl_wait):
            f.ctrl_wait.append(send_ctrl)

    def tag_fb_process(self,f_id):
        self.logger.info("in tag fb")
        f = self.flows_new[f_id]
        f.ctrl_ok += 1
        self.logger.info(f.up_step)
        aggre_dict = {}
        if(len(f.ctrl_wait) == f.ctrl_ok):
            f.ctrl_wait = []
            f.ctrl_ok = 0
            if(f.up_step == consts.TAG_ADD):
                self.logger.info("tag add finished")
                f.up_step = consts.TAG_TAG
                dp_tup, dp_tup_reverse = self.find_packet_tag_dp(f)
                # l,dpid,n =dp_tup
                # l,dpid_reverse,n = dp_tup_reverse
                # self.send_pkg_tag_cmd(f,dpid,False)
                # self.send_pkg_tag_cmd(f,dpid_reverse,True)
                self.send_pkg_tag_cmd(f,dp_tup,False)
                self.send_pkg_tag_cmd(f,dp_tup_reverse,True)
                self.logger.info(f.ctrl_wait)

            elif(f.up_step == consts.TAG_TAG):
                self.logger.info("tag tag finished")
                f.up_step = consts.TAG_DEL
                to_add, to_del = tools.diff_old_new(f.old,f.new)
                self.logger.info(to_add)
                self.logger.info(to_del)
                if(len(to_del) > 0):
                    aggre_dict = tools.flowkey_to_ctrlkey(aggre_dict,self.dp_to_local,f_id,[],to_del)
                    self.make_and_send_info(aggre_dict,False)
                else:
                    info = InfoMessage(f.ctrl_tag)
                    um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                    info.ums.append(um)
                    self.send_to_local(f.ctrl_tag,info)
                    f.ctrl_wait.append(f.ctrl_tag)
                self.logger.info("tag_del sent")
            elif(f.up_step == consts.TAG_DEL):
                self.logger.info("tag del finished")
                self.logger.info(nowTime())
                f.up_step = consts.TAG_MOD
                # l,dpid,n = self.find_packet_tag_dp(f)
                # f.ctrl_tag = self.dp_to_local[dpid]
                info = InfoMessage(f.ctrl_tag)
                um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                info.ums.append(um)
                self.send_to_local(f.ctrl_tag,info)

                info = InfoMessage(f.ctrl_tag_reverse)
                um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                um.if_reverse =True
                info.ums.append(um)
                self.send_to_local(f.ctrl_tag_reverse,info)

                f.ctrl_wait.append(f.ctrl_tag)
                f.ctrl_wait.append(f.ctrl_tag_reverse)
    #from here should be rewrited
            elif(f.up_step == consts.TAG_MOD):
                pass
                return
                self.logger.info("tag notag finished")
                f.up_step = consts.TAG_UNTAG
                # l,dpid,n = self.find_packet_tag_dp(f)
                # f.ctrl_tag = self.dp_to_local[dpid]
                info = InfoMessage(f.ctrl_tag)
                um = UpdateMessageByFlow(f_id,f.up_type,f.up_step)
                info.ums.append(um)
                self.send_to_local(f.ctrl_tag,info)
                f.ctrl_wait.append(f.ctrl_buf)

            elif(f.up_step == consts.TAG_UNTAG):
                f.up_step = None
                f.up_type = None
                f.ctrl_tag =None
                self.logger.info(f.flow_id)
                self.logger.info("updated over by tag")
                self.finished_update_to_flows(f)
            else:
                self.logger.info("what type?")