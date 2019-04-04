import sys
import signal
import time
import subprocess

from getContainerInfo import getContainerInfo


url_cpu = 'https://raw.githubusercontent.com/CloudLargeScale-UCLouvain/nicolae_thesis/master/stats/cpuProbe.py?token=ADmo4erb-rORlrmB6gpw2hClj2rfrS9Fks5crkFZwA%3D%3D'
url_net = 'https://raw.githubusercontent.com/CloudLargeScale-UCLouvain/nicolae_thesis/master/stats/netProbe.py?token=ADmo4YE4IKGLbSS5eIwEqomG2OSXhLOjks5crkFzwA%3D%3D'

containers = get_containers_info()

def get_containers_info():
    containersCount = 100
    containers = {}

    for i in range(containersCount):
        cnt = "fabric_peer{}_org1".format(i)
        containers[cnt] = getContainerInfo(cnt)

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
    stop_monitor()
    get_logs()

if __name__ == "__main__":
    signal.signal(signal.SIGKILL, signal_handler)

    start_monitor()
    while True: time.sleep(1)
