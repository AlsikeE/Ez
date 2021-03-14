#!/bin/bash
cd /root/ez-segway/src

python ./global_ctrl.py  \
	--logFolder logs\
	--logFile random-global-ctrl.log\
	--logLevel INFO\
	--data_folder data\
	--topology randomhaha \
	--topology_type adjacency\
	--method p2p\
	--generating_method random\
	--number_of_flows 1000\
	--failure_rate 0.5\
	--repeat_time 10\
	--skip_deadlock 0
