
import sys
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import logging as log
import re

LOG_DIR = '/root/ez-segway/logs/iperflogs/server/'
IMG_DIR = '../../front/static/iperfimgs/'
def iperf_data_graph(file,name,save_path):
    time_list = []
    time_list2 = []
    time_list3 = []
    rate_list = []
    loss_list = []
    jitter_list = []
    filename = file.split('/')[-1].replace('.txt','').replace('server','')
    print(filename)
    with open(file, 'r') as f:
        row_data = f.readlines()
        for line in row_data:
            time = re.findall(r"-(.*) sec", line)
            rate = re.findall(r"MBytes  (.*) Mbits", line)
            loss = re.findall(r"\((.*)%",line)
            jitter = re.findall(r"sec   ([0-9]+\.[0-9]+) ms",line)
            if (len(time) > 0):
                log.debug(time)  
                if(len(rate) > 0):
                    time_list.append(float(time[0]))
                    rate_list.append(float(rate[0]))
                if(len(loss) > 0):
                    time_list2.append(float(time[0]))
                    loss_list.append(float(loss[0]))
                if(len(jitter) > 0):
                    # print(jitter[0])
                    time_list3.append(float(time[0]))
                    jitter_list.append(float(jitter[0]))
 
    plt.figure()
    # print(time_list)
    # print(jitter_list)
    if(name == 'bw'):
        plt.plot(time_list, rate_list[0:len(time_list)])
        plt.xlabel('Time(sec)')
        plt.ylabel('Bandwidth(Mbits/sec)')
    elif(name == 'loss'):
        plt.plot(time_list2,loss_list[0:len(time_list2)])
        plt.xlabel('Time(sec)')
        plt.ylabel('Loss(%)')
    elif(name == 'jitter'):
        plt.plot(time_list3,jitter_list[0:len(time_list3)])
        plt.xlabel('Time(sec)')
        plt.ylabel('Jitter(ms)')
    plt.grid()
    plt.savefig(save_path+ filename +'_' + name+'.png', bbox_inches='tight')


def draw_all_in_the_dir(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            f_name = f.replace('server','').replace('.txt','')
            save_path = IMG_DIR + f_name +'/'
            try:
                os.system('mkdir ' + save_path)
            except Exception as e:
                print(e)
            for name in ['bw','jitter','loss']:
                try:
                    iperf_data_graph(root+f,name,save_path)
                except Exception as e:
                    print(e)





def main():
    draw_all_in_the_dir(LOG_DIR)
# def main():
#     parser = argparse.ArgumentParser(description="This is a example program")
#     parser.add_argument('-f', '--file', default='../../../logs/iperflogs/server/server10.0.0.110.0.0.65001.txt', help='the iperf test data')
#     parser.add_argument('-n','--name',default = 'bw',help='what type to draw')
#     args = parser.parse_args()
 
#     file = args.file
#     if os.path.exists(file) is not True:
#         log.error("the file not exist, please check!")
#         sys.exit(1)
 
#     # iperf data graph
#     iperf_data_graph(file,args.name)
 
if __name__ == '__main__':
    main()
