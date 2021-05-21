#!/bin/bash

dir='/root/ez-segway/logs/iperflogs/server/'
echo $dir+'server10.0.0.110.0.0.65001.txt'
python draw_all.py --file $dir'server10.0.0.110.0.0.65001.txt' -n jitter
python draw_all.py --file $dir'server10.0.0.110.0.0.65001.txt' -n bw
python draw_all.py --file $dir'server10.0.0.110.0.0.65001.txt' -n loss