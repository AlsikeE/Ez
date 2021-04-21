#!/bin/sh


mn -c
N="test"
tmux new-session -d -s $N


tmux new-window -t $N:1 -n "server" "python server_muc.py"
tmux new-window -t $N:2 -n "c1" "ryu-manager --observe-links --verbose local_muc.py"
tmux new-window -t $N:3 -n "c2" "ryu-manager --observe-links --verbose --ofp-tcp-listen-port 6654 local_muc.py"
tmux new-window -t $N:100 -n 'mininet' "python topo.py"

tmux a -t $N
