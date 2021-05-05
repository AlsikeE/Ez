#for up_type
BUF = 1
TAG = 0
RAW = 2
#for buf up_step
BUF_CYCLE = [0,1,2]
BUF_DEL = 0
BUF_ADD = 1
BUF_RLS = 2

#for tag up_step
TAG_CYCLE = [3,4,5,6,7]
TAG_ADD = 3
TAG_TAG = 4
TAG_DEL = 5
TAG_MOD = 6
TAG_UNTAG = 7

#for raw up_step
RAW_INSTALL = 8
#for choose update name
ONLY_BUF = 0
ONLY_TAG = 1
ONLY_RAW = 2
MIX = 3

#for ports occupied
GLOBAL_FB_PORT = 9999