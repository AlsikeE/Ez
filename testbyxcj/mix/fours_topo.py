from mininet.topo import Topo

TOPOS = {'fourswitch':(lambda:fourswitch())}
class fourswitch(Topo):
    "Simple topology ex."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        hs = [None]
        ss = [None]
        for i in xrange(1, 5):
            hs.append(self.addHost(self.get_host_name(i)))
            ss.append(self.addSwitch(self.get_switch_name(i)))
        print(ss)
        # Add links
        for i in xrange(1, 5):
            self.addLink(hs[i], ss[i])
        self.addLink(ss[1], ss[2], delay='3.98ms', loss=0)
        self.addLink(ss[2], ss[3], delay='52.1ms', loss=0)
        self.addLink(ss[1], ss[4], delay='57.33ms', loss=0)
        self.addLink(ss[3], ss[4], delay='16ms', loss=0)

        c0 = self.addController(c0,controller=RemoteController,port=6666)
        c1 = self.addController(c1,controller=RemoteController,port=6667)
        # controller_list = [c0,c1]
        

    @staticmethod
    def get_switch_name(i):
        return "s%d" % i

    @staticmethod
    def get_controller_name(i):
        return "c%d" % i

    @staticmethod
    def get_host_name(i):
        return "h%d" % i