#!/bin/bash


array=( `ovs-vsctl --columns=_uuid list controller |awk -F ":" '{print $2}'` )
len=${#array[@]}
echo $len
# echo ${array[@]}

for i in ${array[@]}; do
    ovs-vsctl set manager $i inactivity_probe=30000
done