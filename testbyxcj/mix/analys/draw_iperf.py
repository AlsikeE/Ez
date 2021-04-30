
import sys
import argparse
import matplotlib.pyplot as plt
import os
import logging as log
import re
 
def iperf_data_graph(file):
    time_list = []
    rate_list = []
 
    with open(file, 'r') as f:
        row_data = f.readlines()
        for line in row_data:
            time = re.findall(r"-(.*) sec", line)
            rate = re.findall(r"MBytes  (.*) Mbits", line)
            if (len(time) > 0):
                log.debug(time)
                time_list.append(float(time[0]))
                rate_list.append(float(rate[0]))
 
    plt.figure()
    plt.plot(time_list, rate_list)
    plt.xlabel('Time(sec)')
    plt.ylabel('Bandwidth(Mbits/sec)')
    plt.grid()
    plt.savefig('test_iperf.png', bbox_inches='tight')
 
 
def main():
    parser = argparse.ArgumentParser(description="This is a example program")
    parser.add_argument('-f', '--file', default='iperf_test.data', required=True, help='the iperf test data')
    args = parser.parse_args()
 
    file = args.file
    if os.path.exists(file) is not True:
        log.error("the file not exist, please check!")
        sys.exit(1)
 
    # iperf data graph
    iperf_data_graph(file)
 
if __name__ == '__main__':
    main()
