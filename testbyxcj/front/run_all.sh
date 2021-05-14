#!/bin/bash
cd ../mix
tmux kill-session -t test
sleep 1
./runbuf.sh