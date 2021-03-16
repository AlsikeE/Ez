#!/bin/bash

cd /root/ez-segway/simulator;

python flow_change_gen.py  \
	--logFolder logs\
	--logFile data-generator.log\
	--logLevel DEBUG\
	--data_folder data\
	--topology randomhaha\
	--topology_type adjacency\
	--generating_method random\
	--number_of_tests 10\
	--number_of_flows 10\
    --seed 19831126
