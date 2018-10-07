import os
import sys

from getContainerInfo import getContainerInfo


def getNetStats(service, timeout = 10):
    sys.stdout = os.fdopen(sys.stdout.fileno(), "wb", 0)
    sys.stderr = os.fdopen(sys.stderr.fileno(), "wb", 0)

    _, srvcIp, _, cntPid = getContainerInfo(service)

    i = 0
    startTime = time.time()
    while True:
        cmd = "ssh ubuntu@{ip} \"cat /proc/{cnt}/net/dev\"".format(ip=srvcIp, cnt=cntPid)
        p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
        netIo, _ = p.communicate()

        netIn = 0
        netOut = 0
        i += 1
        for net in netIo.splitlines()[2:]:
            net = net.strip()
            if len(net) == 0: continue

            netIn += int(net.split()[1])
            netOut += int(net.split()[9])
        print("#{}: {}\t{}".format(i, netIn, netOut))
        time.sleep(startTime + i*timeout - time.time())

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <service_name>".format(__file__))
        raise SystemExit

    getNetStats(sys.argv[1])
