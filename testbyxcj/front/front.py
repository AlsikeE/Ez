from flask import Flask,render_template,url_for,request
from flask_bootstrap import Bootstrap

import os
import multiprocessing

import requests
import json
app=Flask(__name__,template_folder='./templates',static_folder='./static')
bootstrap = Bootstrap(app)
print(bootstrap)


@app.route('/mix/')
@app.route('/mix/<name>')
def hello(name = None):
    return render_template('front.html', name=name)

@app.route('/index/')
def demo():
    return render_template('index.html')


def write_config(tcam,buff):
    f = open('../mix/data/dp_tcam.intra','r+')
    f.seek(0)
    f.truncate()
    for i in range(1,6):
        f.write(str(i)+':' + str(tcam) + '\n')
    f = open('../mix/data/local_bufsize.intra','r+')
    f.seek(0)
    f.truncate()
    f.write(str(buff))

def start_tests(tcam,buff):
    write_config(tcam,buff)
    os.system('./run_all.sh')
    os.system('exit')

def stop_test():
    os.system('tmux kill-session -t test')
    os.system('exit')

@app.route('/start_all/',methods=["GET","POST"])
def start_all():
    print("WO zaizhene ")
    # if request.method == "GET":
    #     mp1 = multiprocessing.Process(target=start_tests,args=())
    #     mp1.start()
    #     mp1.join()
    if request.method == "POST":
        print("post yes")
        tcam = request.form.get('tcam')
        buff = request.form.get('buff')
        mp1 = multiprocessing.Process(target=start_tests,args=(tcam,buff))
        mp1.start()
        # mp1.join()
    return 'success'


@app.route('/stop_all/',methods=["GET"])
def stop_all():
    print("guanle a woguanle  ")
    if request.method == "GET":
        mp1 = multiprocessing.Process(target=stop_test,args=())
        mp1.start()
    return 'stopped'

@app.route('/update/',methods=["POST"])
def update():
    if request.method == "POST":
        flows = request.form.get('flows')
        flow_list = flows.strip('\"').split('\",\n\"')
        data = {"flows":flow_list}
        headers = {'content-type': "application/json"}
        res = requests.post(url='http://192.168.0.33:8800',data=json.dumps(data),headers=headers)
    return 'update request sent'

@app.route('/methlogs/',methods=['GET'])
def get_methlogs():
    if request.method == 'GET':
        with open('./static/schedule.log') as f:
            lines = f.readlines()
            line = None
            try:
                line = lines[-1]
            except:
                print('why?')
            if(line):
                result = {}
                metlist = line[1:-2].split(', ')
                # return metlist
                for met in metlist:
                    k,v = met.split(': ')
                    print(k,v)
                    k = k.strip('u').strip('\'')
                    value = 'BUF' if v == '100' else 'TAG'
                    if v == '102':
                        value = 'RAW'
                    result.update({k:value})
                return json.dumps(result)
    return ''
if __name__=='__main__':

    app.run(host='0.0.0.0',debug=True,port=8100)