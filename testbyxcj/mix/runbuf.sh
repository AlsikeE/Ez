#!/bin/bash
N="test"


tmux new-session -d -s $N

tmux ls

mn -c
tmux new-window -t $N:99 -n "mn" 
tmux send-keys -t $N:99 "python S4.py" Enter

sleep 1

tmux new-window -t $N:1 -n "controller" 

tmux send-keys -t $N:1 "ryu-manager --verbose --ofp-tcp-listen-port 6666 buf.py" Enter
sleep 1
tmux send-keys -t $N:99 "h3 ping h4 " Enter
tmux a -t $N