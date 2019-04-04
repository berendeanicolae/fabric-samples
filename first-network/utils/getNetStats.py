import sys
import signal
import time
import subprocess
import multiprocessing

from getContainerInfo import getContainerInfo


url_cpu = 'https://raw.githubusercontent.com/CloudLargeScale-UCLouvain/nicolae_thesis/master/stats/cpuProbe.py?token=ADmo4erb-rORlrmB6gpw2hClj2rfrS9Fks5crkFZwA%3D%3D'
url_net = 'https://raw.githubusercontent.com/CloudLargeScale-UCLouvain/nicolae_thesis/master/stats/netProbe.py?token=ADmo4YE4IKGLbSS5eIwEqomG2OSXhLOjks5crkFzwA%3D%3D'

containers = None

def get_container_info(cnt):
    return (cnt, getContainerInfo(cnt))

def get_containers_info():
    containersCount = 10
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

def start_monitor():
    for cnt in containers:
        ip, _, id, _ = containers[cnt]
        subprocess.Popen(["ssh {ip} \"docker exec {cnt_id} curl -sSL '{url}' -o {output}\"".format(ip=ip, cnt_id=id, url=url_cpu, output='cpuProbe.py')], shell=True).wait()
        subprocess.Popen(["ssh {ip} \"docker exec {cnt_id} curl -sSL '{url}' -o {output}\"".format(ip=ip, cnt_id=id, url=url_net, output='netProbe.py')], shell=True).wait()
        subprocess.Popen(["ssh {ip} \"docker exec -d {cnt_id} python cpuProbe.py 1 1 CPUProbe.csv\"".format(ip=ip, cnt_id=id)], shell=True).wait()
        subprocess.Popen(["ssh {ip} \"docker exec -d {cnt_id} python netProbe.py 1 1 NetProbe.csv\"".format(ip=ip, cnt_id=id)], shell=True).wait()


def stop_monitor():
    for cnt in containers:
        ip, _, id, _ = containers[cnt]
        subprocess.Popen(["ssh {ip} \"docker exec {cnt_id} pkill python\"".format(ip=ip, cnt_id=id)], shell=True).wait()

def get_logs():
    for cnt in containers:
        ip, _, id, _ = containers[cnt]
        subprocess.Popen(["ssh {ip} \"docker cp {cnt_id}:/go/src/github.com/hyperledger/fabric/peer/CPUProbe.csv {cnt}_CPUProbe.csv".format(ip=ip, cnt_id=id, cnt=cnt)], shell=True).wait()
        subprocess.Popen(["ssh {ip} \"docker cp {cnt_id}:/go/src/github.com/hyperledger/fabric/peer/NetProbe.csv {cnt}_NetProbe.csv".format(ip=ip, cnt_id=id, cnt=cnt)], shell=True).wait()

def signal_handler(sig, frame):
    # stop_monitor()
    # get_logs()
    sys.exit(0)

if __name__ == "__main__":
    containers = get_containers_info()
    signal.signal(signal.SIGINT, signal_handler)

    print('Start monitoring...')
    # start_monitor()
    while True: time.sleep(1)
