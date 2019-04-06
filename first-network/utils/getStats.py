import os
import sys
import signal
import time
import subprocess
import multiprocessing.pool

from getContainerInfo import getContainerInfo


url_cpu = 'https://raw.githubusercontent.com/CloudLargeScale-UCLouvain/nicolae_thesis/master/stats/cpuProbe.py?token=ADmo4erb-rORlrmB6gpw2hClj2rfrS9Fks5crkFZwA%3D%3D'
url_net = 'https://raw.githubusercontent.com/CloudLargeScale-UCLouvain/nicolae_thesis/master/stats/netProbe.py?token=ADmo4YE4IKGLbSS5eIwEqomG2OSXhLOjks5crkFzwA%3D%3D'

containersCount = 100
containers = None

def get_container_info(cnt):
    return (cnt, getContainerInfo(cnt))

def get_containers_info():
    containers = {}

    cnts = []
    for i in range(containersCount):
        cnt = "fabric_peer{}_org1".format(i)
        cnts.append(cnt)

    pool = multiprocessing.pool.ThreadPool(containersCount)
    containersList = pool.map(get_container_info, cnts)

    for cnt in containersList:
        containers[cnt[0]] = cnt[1]

    return containers

def start_monitor(cnt_info):
    _, ip, id, _ = cnt_info
    subprocess.Popen(["ssh {ip} \"docker exec {cnt_id} curl -sSL '{url}' -o {output}\"".format(ip=ip, cnt_id=id, url=url_cpu, output='cpuProbe.py')], shell=True).wait()
    subprocess.Popen(["ssh {ip} \"docker exec {cnt_id} curl -sSL '{url}' -o {output}\"".format(ip=ip, cnt_id=id, url=url_net, output='netProbe.py')], shell=True).wait()
    subprocess.Popen(["ssh {ip} \"docker exec {cnt_id} rm -f CPUProbe.csv NetProbe.csv\"".format(ip=ip, cnt_id=id)], shell=True).wait()
    subprocess.Popen(["ssh {ip} \"docker exec -d {cnt_id} python cpuProbe.py 1 1 CPUProbe.csv\"".format(ip=ip, cnt_id=id)], shell=True).wait()
    subprocess.Popen(["ssh {ip} \"docker exec -d {cnt_id} python netProbe.py 1 1 NetProbe.csv\"".format(ip=ip, cnt_id=id)], shell=True).wait()


def start_monitors():
    cnts = []
    for cnt in containers:
        cnts.append((containers[cnt]))

    pool = multiprocessing.pool.ThreadPool(containersCount)
    pool.map(start_monitor, cnts)

def stop_monitor(cnt_info):
    _, ip, id, _ = cnt_info
    subprocess.Popen(["ssh {ip} \"docker exec {cnt_id} pkill python\"".format(ip=ip, cnt_id=id)], shell=True).wait()


def stop_monitors():
    cnts = []
    for cnt in containers:
        cnts.append((containers[cnt]))

    pool = multiprocessing.pool.ThreadPool(containersCount)
    pool.map(stop_monitor, cnts)

def get_stat(cnt_info):
    fHandle = open(os.devnull, "wb")
    cnt, _, ip, id, _ = cnt_info
    subprocess.Popen(["ssh {ip} \"docker cp {cnt_id}:/go/src/github.com/hyperledger/fabric/peer/CPUProbe.csv {cnt}_CPUProbe.csv\"".format(ip=ip, cnt_id=id, cnt=cnt)], shell=True).wait()
    subprocess.Popen(["ssh {ip} \"docker cp {cnt_id}:/go/src/github.com/hyperledger/fabric/peer/NetProbe.csv {cnt}_NetProbe.csv\"".format(ip=ip, cnt_id=id, cnt=cnt)], shell=True).wait()
    subprocess.Popen(["scp {ip}:/home/ubuntu/{cnt}_CPUProbe.csv {cnt}_CPUProbe.csv".format(ip=ip, cnt_id=id, cnt=cnt)], shell=True, stdout=fHandle).wait()
    subprocess.Popen(["scp {ip}:/home/ubuntu/{cnt}_NetProbe.csv {cnt}_NetProbe.csv".format(ip=ip, cnt_id=id, cnt=cnt)], shell=True, stdout=fHandle).wait()
    subprocess.Popen(["awk '{{print \"1 1 1 \" $0}}' {cnt}_CPUProbe.csv > {cnt}_NodeCPU.csv".format(cnt=cnt)], shell=True).wait()
    subprocess.Popen(["sed -i \"s/1 1 1 time/expRun col1 col2 time/g\" {cnt}_NodeCPU.csv".format(cnt=cnt)], shell=True).wait()
    os.unlink("{cnt}_CPUProbe.csv".format(cnt=cnt))
    subprocess.Popen(["awk '{{print \"1 1 1 \" $0}}' {cnt}_NetProbe.csv > {cnt}_NodeNet.csv".format(cnt=cnt)], shell=True).wait()
    subprocess.Popen(["sed -i \"s/1 1 1 time/expRun col1 col2 time/g\" {cnt}_NodeNet.csv".format(cnt=cnt)], shell=True).wait()
    os.unlink("{cnt}_NetProbe.csv".format(cnt=cnt))
    fHandle.close()

def get_stats():
    cnts = []
    for cnt in containers:
        cnts.append((cnt,)+(containers[cnt]))

    pool = multiprocessing.pool.ThreadPool(containersCount)
    pool.map(get_log, cnts)

def get_log(cnt_info):
    fHandle = open(os.devnull, "wb")
    cnt, _, ip, id, _ = cnt_info

    proc = subprocess.Popen(["ssh {ip} \"docker inspect {cnt} --format {{{{.LogPath}}}}\"".format(ip=ip, cnt=id)], shell=True, stdout=subprocess.PIPE)
	logPath, _ = p.communicate()
	logPath = logPath.strip()

    subprocess.Popen(["ssh {ip} \"sudo chmod 777 {path}\""].format(ip=ip, path=os.path.dirname(os.path.dirname(os.path.dirname(logPath)))), shell=True).wait()
    subprocess.Popen(["ssh {ip} \"sudo chmod 777 {path}\""].format(ip=ip, path=os.path.dirname(os.path.dirname(logPath))), shell=True).wait()
    subprocess.Popen(["ssh {ip} \"sudo chmod 777 {path}\""].format(ip=ip, path=os.path.dirname(logPath)), shell=True).wait()
    subprocess.Popen(["ssh {ip} \"sudo chmod 777 {path}\""].format(ip=ip, path=logPath), shell=True).wait()
    subprocess.Popen(["scp {ip}:{srcFile} ./{dstFile}".format(ip=ip, srcFile=logPath, dstFile=cnt)], shell=True, stdout=fHandle).wait()
    fHandle.close()

def get_logs():
    cnts = []
    for cnt in containers:
        cnts.append((cnt,)+(containers[cnt]))

    pool = multiprocessing.pool.ThreadPool(containersCount)
    pool.map(get_log, cnts)

def signal_handler(sig, frame):
    print('stopping monitoring...')
    stop_monitors()
    print('stopped monitoring!')

    print('saving stats...')
    get_stats()
    print('stats saved!')

    print('saving logs...')
    get_logs()
    print('logs saved!')

    sys.exit(0)

if __name__ == "__main__":
    containers = get_containers_info()
    signal.signal(signal.SIGINT, signal_handler)

    print('start monitoring...')
    start_monitors()
    print('started monitoring!')
    while True: time.sleep(1)
