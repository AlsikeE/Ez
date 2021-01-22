import cPickle as pickle
#import pickle 
import binascii
import sys
import six
sys.path.append('./simulator')
from domain.message import AggregatedMessage

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, udp
from ryu.lib.packet import ether_types
from ryu.ofproto import ether
from ryu.lib.packet.in_proto import IPPROTO_UDP
# #src=4,dst=3,Good_TO_MOVE:[]
# rcved = b"\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x05\x08\x00E\x00\x01|\x00\x00\x00\x00\xff\x11\xbah\x00\x00\x00\x05\x00\x00\x00\x04\x19\xdc\x19\xdc\x01h\xc9]\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00(idomain.message\nAggregatedMessage\np1\n(dp2\nS'src_id'\np3\nI4\nsS'receiving_time'\np4\nNsS'dst_id'\np5\nI3\nsS'seg_path_ids'\np6\n(dp7\nI0\n(lp8\n(I33\nI0\ntp9\na(I100\nI0\ntp10\na(I37\nI0\ntp11\na(I39\nI0\ntp12\na(I73\nI0\ntp13\na(I57\nI0\ntp14\na(I75\nI0\ntp15\na(I53\nI0\ntp16\na(I55\nI0\ntp17\na(I25\nI0\ntp18\na(I71\nI0\ntp19\nassS'update_id'\np20\nI0\nsS'sending_time'\np21\nF1611211334769.9412\nsb."
# rc = b"(idomain.message\nAggregatedMessage\np1\n(dp2\nS'src_id'\np3\nI4\nsS'receiving_time'\np4\nNsS'dst_id'\np5\nI3\nsS'seg_path_ids'\np6\n(dp7\nI0\n(lp8\n(I33\nI0\ntp9\na(I100\nI0\ntp10\na(I37\nI0\ntp11\na(I39\nI0\ntp12\na(I73\nI0\ntp13\na(I57\nI0\ntp14\na(I75\nI0\ntp15\na(I53\nI0\ntp16\na(I55\nI0\ntp17\na(I25\nI0\ntp18\na(I71\nI0\ntp19\nassS'update_id'\np20\nI0\nsS'sending_time'\np21\nF1611211334769.9412\nsb."
# t = AggregatedMessage('3','2',0,[(150, 0), (152, 0)],10000)
# # a = t.decode('ascii')
# t.receiving_time = 19191919191991
# td = pickle.dumps(t)


# test = AggregatedMessage(3,4,'GOOD_TO_MOVE','[(33, 0), (100, 0), (37, 0), (39, 0), (73, 0), (57, 0), (75, 0), (53, 0), (55, 0), (25, 0), (71, 0)]',0)
# # # tdcpk = pk.dumps(t)
# # print(td)
# # # #print(binascii.hexlify(td))
# # print(pickle.loads(rc))
# # # # print(tdcpk)
# # print(str(pickle.loads(td)))
# # strpprcvd = rcved.strip(b'\x00')
# # spl = rcved.split('(')
# # spl[0] = ''
# # result = '('.join(spl)
# # print(spl)
# # print(result)
# # print(pickle.loads(result))

# ba = bytearray()
# sa =six.binary_type(ba)
# print(str(sa))

pkt = packet.Packet()

e = ethernet.ethernet(dst=2,
                              src=1,
                              ethertype=ether.ETH_TYPE_IP)
i = ipv4.ipv4(src=1,
                      dst=2,
                      proto=IPPROTO_UDP,
                      total_length=ipv4.ipv4._MIN_LEN + udp.udp._MIN_LEN + 5)
u = udp.udp(dst_port=6620,
                    src_port=6620,
                    total_length=udp.udp._MIN_LEN + 5)

pkt.add_protocol(e)
pkt.add_protocol(i)
pkt.add_protocol(u)
print(pkt.data)
pkt.serialize()
print(binascii.hexlify(pkt.data))