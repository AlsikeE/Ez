import networkx as nx
import matplotlib
import numpy as np
matplotlib.use("Agg")
from matplotlib import pyplot as plt

import itertools
def read_matrix_from_file(topo_file,type):
    result = []
    with open(topo_file) as f:
        for line in f:
            result.append([type(x) for x in line.strip().split(' ')])
    return result

def read_mapping_from_file(file):
    result = {}
    with open(file) as f:
        for line in f:
            a,b = line.split(':')
            objs = b.split(',')
            result.update({int(a):map(lambda x: int(x),objs)})
    return result

# def multilayered_graph(*subset_sizes):
#     extents = pairwise(itertools.accumulate((0,) + subset_sizes))
#     layers = [range(start, end) for start, end in extents]
#     G = nx.Graph()
#     for (i, layer) in enumerate(layers):
#         G.add_nodes_from(layer, layer=i)
#     for layer1, layer2 in pairwise(layers):
#         G.add_edges_from(itertools.product(layer1, layer2))
#     return G

def draw(topofile,hostfile,localfile):
    topo = read_matrix_from_file(topofile,int)
    dp_hosts = read_mapping_from_file(hostfile)
    ctrl_dps = read_mapping_from_file(localfile)
    hosts = []
    ctrls = []

    dp_host_lines = []
    ctrl_dp_lines = []
    for (dp,hs) in dp_hosts.items():
        for h in hs:
            hosts.append('h' + str(h))
            dp_host_lines.append(('s'+str(dp),'h'+str(h)))

    for (ctrl,dps) in ctrl_dps.items():
        ctrls.append('c' + str(ctrl))
        for s in dps:
            ctrl_dp_lines.append(('c'+str(ctrl),'s'+str(s)))

    G = nx.Graph()
    matrix = np.array(topo)

    sws = ['s' + str(i) for i in range(1,len(topo) + 1)]

    G.add_nodes_from(sws,layer=2)
    G.add_nodes_from(ctrls,layer=1)
    G.add_nodes_from(hosts,layer=3)

    lins = []
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            if(topo[i][j] == 1):
                lins.append(('s'+str(i+1),'s'+str(j+1)))
    print(lins)


    G.add_edges_from(dp_host_lines,edge_color='grey')
    G.add_edges_from(lins,edgecolor='red')
    G.add_edges_from(ctrl_dp_lines,style='dashdot')

    position = nx.spring_layout(G)
    # position2 = nx.random_layout(G)
    nx.draw_networkx_nodes(G,position, nodelist=sws, node_color="#cc3333")
    nx.draw_networkx_nodes(G,position, nodelist=hosts, node_color="#A0CBE2",size=30)
    nx.draw_networkx_nodes(G,position, nodelist=ctrls, node_color="#7CCD7C")

    nx.draw_networkx_edges(G,position, edgelist = lins, width =1.2, color = 'g')
    nx.draw_networkx_edges(G,position, edgelist = dp_host_lines, color = 'black')
    nx.draw_networkx_edges(G,position, edgelist = ctrl_dp_lines, color = 'black',style='dashdot')
    nx.draw_networkx_labels(G,position)
    plt.savefig('../../../front/static/topo.png', bbox_inches='tight')


if __name__ == "__main__":
    draw('../topo.intra','../dp_host.intra','../local_dp.intra')