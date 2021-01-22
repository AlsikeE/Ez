# -*- encoding: utf-8 -*- 
import random
DATADIR = '/root/ez-segway/data/randomhaha/'
def generate_random_graph(n):
    """
    Generate random graph with number of n
    :param n: graph's number of nodes
    :return: a dict of graph
    """
    number = n
    node_list = []
    graph = {}
    for node in range(0, n):  # 循环创建结点
        node_list.append(node)

    print(node_list)
    for node in node_list:
        graph[node] = []  # graph为dict结构，初始化为空列表

    for node in node_list:  # 创建连接无向图（无加权值）
        number = random.randint(1, n)  # 随机取1-n个结点 minmax 度
        l_tochoose = [i for i in range(0,n) if i not in [node]]

        for i in range(number):
            index = random.choice(l_tochoose)  # 某个结点的位置
            node_append = node_list[index]
            if node_append not in graph[node] and node != node_append:
                graph[node].append(node_append)
                graph[node_append].append(node)

    return graph


# def generate_edge(graph):
#     """
#     draw the edge of graph
#     :param graph: a dict of graph
#     :return: a list of edge
#     """
#     edges = []
#     for node in graph:
#         for neighbour in graph[node]:
#             edges.append((node, neighbour))
#     return edges

def gen_adj(n,graph):
    adj = [[0]*n for i in range(n)]
    for node in graph:
        for neighbour in graph[node]:
            adj[node][neighbour] = 1
            adj[neighbour][node] = 1
    
    f = open(DATADIR+'topo.intra','w')
    for row in adj:
        for item in row:
            s = str(item) + ' '
            f.write(s)
        f.write('\n')
    
    fc = open(DATADIR+'centroid.intra','w')
    fc.write(str(int(n/2)))
    return adj

def gen_distance(graph):
    distances = dict()
    for node in graph:
        for neighbor in graph[node]:
            key = (node,neighbor) if node < neighbor else (neighbor,node)
            if key not in distances.keys():
                distances[key] = round(random.random() * 20, 2)
    f = open(DATADIR + 'distance.intra','w')
    for key in distances.keys():
        f.write(str(key) + ':' + str(distances[key]) + '\n')
    return distances

def gen_latencies(n, distances):
    latencies = [[0]*n for i in range(n)]
    for (a,b) in distances.keys():
        latencies[a][b] = distances[(a,b)]
        latencies[b][a] = distances[(a,b)]
    
    f = open(DATADIR + 'latencies.intra','w')
    for row in latencies:
        for item in row:
            s = str(item) + ' '
            f.write(s)
        f.write('\n')
    return latencies

if __name__ == "__main__":
    # n = int(input())
    n = 6
    graph = generate_random_graph(n)
    adj = gen_adj(n,graph)
    distances = gen_distance(graph)
    latencies = gen_latencies(n, distances)
    print('adj:\n\r',adj)
    print("无向图",graph)
    print("无向图",distances)
    print('lat',latencies)