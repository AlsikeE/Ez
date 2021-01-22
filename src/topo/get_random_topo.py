from basetopo import BaseTopo
DATADIR = '/root/ez-segway/data/randomhaha/'
def read_matrix_from_file(file,type):
    result = []
    with open(file) as f:
        for line in f:
            result.append([type(x) for x in line.strip().split(' ')])
    return result


class Randomhaha(BaseTopo):
    "Random topology by me haha."

    def __init__( self, topo_file, latency_file):
        "Create custom topo."

        # Initialize topology
        BaseTopo.__init__( self )
        
        topo_matrix = read_matrix_from_file(topo_file,int)
        latency_matrix = read_matrix_from_file(latency_file, float)

        length = len(topo_matrix)
        # Add hosts and switches
        hs = [None]
        ss = [None]
        for i in range(0, length):
            hs.append(self.addHost(BaseTopo.get_host_name(i+1)))
            ss.append(self.addSwitch(BaseTopo.get_switch_name(i+1)))

        # Add links
        for i in range(0, length):
            self.addLink(hs[i+1], ss[i+1])
        
        for i in range(0, length):
            for j in range(i,length):
                if latency_matrix[i][j] != 0:
                    self.addLink(ss[i+1], ss[j+1], delay= latency_matrix[i][j], loss=0)

