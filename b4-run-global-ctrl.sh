#!/bin/bash


python ./global_ctrl.py  \
	--logFolder logs\
	--logFile b4-global-ctrl.log\
	--logLevel INFO\
	--data_folder data\
	--topology b4 \
	--topology_type adjacency\
	--method p2p\
	--generating_method random\
	--number_of_flows 1000\
	--failure_rate 0.5\
	--repeat_time 1000\
	--skip_deadlock 0
