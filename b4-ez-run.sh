#!/bin/bash

EZ_PATH=./src
N="ez-segway"
rm -rf ./logs/local/
mkdir -p ./logs/local/
cd $EZ_PATH

tmux new-session -d -s $N

# B4 has 11 switches
n=11

tmux new-window -t $N:100 -n 'mininet' "sudo ./topo.py --method p2p --topo b4"
sleep 1

for i in `seq 0 $n`; do
  OFP_PORT=$((6733+$i))
  WSAPI_PORT=$((8733+$i))

  tmux new-window -t $N:$(($i+1)) -n "sw$i" "EZSWITCH_ID=$i TOPO_INPUT=b4 ryu-manager --ofp-tcp-listen-port $OFP_PORT --wsapi-port $WSAPI_PORT --use-stderr --verbose ./local_ctrl.py"
done

tmux new-window -t $N:101 -n "controller"
tmux send-keys -t $N:101 "sleep 10 && ../b4-run-global-ctrl.sh" Enter

#tmux select-window -t $N:100
#tmux attach-session -t $N

sleep 15

CTRL_PID=`pgrep python`
while ps -p $CTRL_PID > /dev/null; do sleep 1; done;

tmux send-keys -t $N:100 'exit' Enter
sleep 10
tmux list-panes -s -F "#{pane_pid} #{pane_current_command}" | grep -v tmux | awk '{print $1}' | sudo xargs kill


