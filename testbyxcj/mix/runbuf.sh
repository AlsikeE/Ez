#!/bin/bash
N="test"
bufsize=$(cat '/root/ez-segway/testbyxcj/mix/data/local_bufsize.intra')
echo $bufsize
tmux new-session -d -s $N

tmux ls

mn -c

tmux new-window -t $N:111 -n 'redis'
tmux send-keys -t $N:111 "redis-cli" Enter
tmux send-keys -t $N:111 "flushall" Enter

tmux new-window -t $N:112 -n 'redi2'
tmux send-keys -t $N:112 "redis-cli -p 6380" Enter
tmux send-keys -t $N:112 "flushall" Enter
# tmux new-window -t $N:222 -n "topogui" 
# tmux send-keys -t $N:222 "ryu-manager ~/ryucode/ryu-4.20/ryu/app/gui_topology/gui_topology.py" Enter

tmux new-window -t $N:99 -n "mn" 
# tmux send-keys -t $N:99 "mn --topo=single,4 --arp --controller=remote,ip=127.0.0.1,port=6666" Enter
# tmux send-keys -t $N:99 "python topo.py --iperf 1 --filepath ./data/flowdes.intra" Enter
tmux send-keys -t $N:99 "python ./multi_controller_topo.py --iperf 1" Enter
# tmux send-keys -t $N:99 "python ./multi_controller_topo.py" Enter
# tmux send-keys -t $N:99 "python topo3.py " Enter
sleep 1

tmux new-window -t $N:1 -n "controller1" 

# tmux send-keys -t $N:1 "ryu-manager --verbose --ofp-tcp-listen-port 6666 buf.py" Enter
# tmux send-keys -t $N:1 "ryu-manager --verbose --ofp-tcp-listen-port 6666 localthread.py ryu.app.ofctl_rest" Enter
tmux send-keys -t $N:1 "LOCAL_ID=1 BUF_SIZE=$bufsize REDIS_PORT=6379 ryu-manager --verbose --ofp-tcp-listen-port 6667 localthread.py" Enter

tmux new-window -t $N:2 -n "controller2" 
# tmux send-keys -t $N:2 "LOCAL_ID=1 ryu-manager --verbose --ofp-tcp-listen-port 6668 local2.py" Enter
tmux send-keys -t $N:2 "LOCAL_ID=2 BUF_SIZE=$bufsize REDIS_PORT=6380 ryu-manager --verbose --ofp-tcp-listen-port 6668 localthread.py" Enter
sleep 2
# tmux send-keys -t $N:99 "h1 ping h2 -s 1460 -i 0.01 -c 100 " Enter
# tmux send-keys -t $N:99 "h1 ping h2 -s 64 -i 0.01 -c 100 " Enter
# tmux send-keys -t $N:99 "iperf h3 h4 " Enter
tmux new-window -t $N:101 -n "global"
tmux send-keys -t $N:101 "python ./global.py " Enter

tmux a -t $N