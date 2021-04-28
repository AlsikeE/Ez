#!/bin/bash
N="test"


tmux new-session -d -s $N

tmux ls

mn -c
tmux new-window -t $N:99 -n "mn" 
# tmux send-keys -t $N:99 "mn --topo=single,4 --arp --controller=remote,ip=127.0.0.1,port=6666" Enter
# tmux send-keys -t $N:99 "python topo.py --iperf 1 --filepath ./data/flowdes.intra" Enter
tmux send-keys -t $N:99 "python topo.py " Enter
sleep 1

tmux new-window -t $N:1 -n "controller" 

# tmux send-keys -t $N:1 "ryu-manager --verbose --ofp-tcp-listen-port 6666 buf.py" Enter
# tmux send-keys -t $N:1 "ryu-manager --verbose --ofp-tcp-listen-port 6666 localthread.py ryu.app.ofctl_rest" Enter
tmux send-keys -t $N:1 "ryu-manager --verbose --ofp-tcp-listen-port 6666 localthread.py" Enter
sleep 1
# tmux send-keys -t $N:99 "h1 ping h2 -s 1460 -i 0.01 -c 100 " Enter
# tmux send-keys -t $N:99 "h1 ping h2 -s 64 -i 0.01 -c 100 " Enter
# tmux send-keys -t $N:99 "iperf h3 h4 " Enter

tmux a -t $N