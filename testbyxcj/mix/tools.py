import cPickle as pickle
def recv_size(fd, size):
    total_len=0
    total_data=[]
    while total_len < size:
        sock_data = fd.recv(size - total_len)
        total_data.append(sock_data)
        total_len = sum([len(i) for i in total_data ])
    
    tolog = pickle.loads(''.join(total_data))
    return ''.join(total_data)

def _put_all_in_tuple(path_to_deal):
    target = []
    length = len(path_to_deal)
    i = 0
    while(i < length):
        dp = path_to_deal[i]
        dplast = path_to_deal[i] if (i==0) else path_to_deal[i-1]
        dpnext = path_to_deal[i] if (i==length-1) else path_to_deal[i+1]
        target.append((dplast,dp,dpnext))
        i += 1
    return target

def _find_dif_str(path_old,path_new):
    i = 0
    lo = len(path_old)
    ln = len(path_new)
    while(i < lo and i < ln):
        if(path_old[i] == path_new[i]):
            i+=1
        else:
            break
    left = i-1
    i = 0
    while(i < lo and i < ln):
        if(path_old[-1-i] == path_new[-1-i]):
            i+=1
        else:
            break
    right = 0 - i 
    oright = lo + right + 1
    nright = ln + right + 1
    return path_old[left:oright], path_new[left:nright]

def diff_old_new(path_old,path_new):
    to_add = []
    to_del = []
    if(path_old == [] and path_new != []):
        to_add = _put_all_in_tuple(path_new)
    elif(path_new == [] and path_old != []):
        to_del = _put_all_in_tuple(path_old)
    elif(path_new!=[] and path_old!=[]):
        po,pn = _find_dif_str(path_new,path_old)
        to_add = _put_all_in_tuple(pn)
        to_del = _put_all_in_tuple(po)
    print(to_add,to_del)
    return to_add,to_del

def flowkey_to_dpkey(target,flow_id,to_add,to_del):
    for tup in to_add:
        dplast,dp,dpnext = tup
        if(target.has_key(dp)):
            if(not target[dp].has_key(flow_id)):
                target[dp].update({flow_id:{}})
                target[dp][flow_id].update({'to_del':[],'to_add':[]})
            target[dp][flow_id]['to_add'].append(tup)
        else:
            target.update({dp:{}})
            target[dp].update({flow_id:{}})
            target[dp][flow_id].update({'to_del':[],'to_add':[]})
            target[dp][flow_id]['to_add'].append(tup)
    for tup in to_del:
        dplast,dp,dpnext = tup
        if(target.has_key(dp)):
            if(not target[dp].has_key(flow_id)):
                target[dp].update({flow_id:{}})
                target[dp][flow_id].update({'to_del':[],'to_add':[]})
            target[dp][flow_id]['to_add'].append(tup)
        else:
            target.update({dp:{}})
            target[dp].update({flow_id:{}})
            target[dp][flow_id].update({'to_del':[],'to_add':[]})
            target[dp][flow_id]['to_del'].append(tup)
    return target

def flowkey_to_ctrlkey(target,dp_to_ctrl,flow_id,to_add,to_del):
    for tup in to_add:
        dplast,dp,dpnext = tup
        ctrl = dp_to_ctrl[dp]
        if(target.has_key(ctrl)):
            if(not target[ctrl].has_key(flow_id)):
                target[ctrl].update({flow_id:{}})
                target[ctrl][flow_id].update({'to_del':[],'to_add':[]})
            target[ctrl][flow_id]['to_add'].append(tup)
        else:
            target.update({ctrl:{}})
            target[ctrl].update({flow_id:{}})
            target[ctrl][flow_id].update({'to_del':[],'to_add':[]})
            target[ctrl][flow_id]['to_add'].append(tup)
    for tup in to_del:
        dplast,dp,dpnext = tup
        ctrl = dp_to_ctrl[dp]
        if(target.has_key(ctrl)):
            if(not target[ctrl].has_key(flow_id)):
                target[ctrl].update({flow_id:{}})
                target[ctrl][flow_id].update({'to_del':[],'to_add':[]})
            target[ctrl][flow_id]['to_add'].append(tup)
        else:
            target.update({ctrl:{}})
            target[ctrl].update({flow_id:{}})
            target[ctrl][flow_id].update({'to_del':[],'to_add':[]})
            target[ctrl][flow_id]['to_del'].append(tup)
    print(target)
    return target


if __name__ == "__main__":
    diff_old_new([1,2,3,4],[1,2,4])
    target1 = flowkey_to_ctrlkey({},{1:233,2:888},'flow1',[(1,1,1),(1,2,2)],[(2,1,3)])
    target2 = flowkey_to_ctrlkey(target1,{1:233,2:888},'flow1',[(3,1,5)],[(2,2,2)])
    target3 = flowkey_to_ctrlkey(target1,{1:233,2:888},'flow2',[(3,1,5)],[(2,2,2)])
    