import sys
import os
import subprocess


def getContainerInfo(service):
	# node ID
	cmd = "docker service ps --format '{{{{.Node}}}} {{{{.DesiredState}}}}' --no-resolve {srvc}".format(srvc=service)
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	nodeId, _ = p.communicate()
	nodeId = nodeId.split("\n", 1)[0]
	if nodeId.split()[1] != "Running":
		return None
	nodeId = nodeId.split()[0].strip()

	# node IP
	cmd = "docker node inspect --format '{{{{.Status.Addr}}}}' {node}".format(node=nodeId.strip())
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	nodeIp, _ = p.communicate()
	nodeIp = nodeIp.strip()

	# container ID
	cmd = "ssh ubuntu@{ip} \"docker container ls --format '{{{{.ID}}}} {{{{.Names}}}}'\" | grep {node}".format(ip=nodeIp, node=service)
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	cnts, _ = p.communicate()
	cnts = cnts.strip()
	if len(cnts) == 0:
		return None
	cntId, _ = cnts.split()
	cntId = cntId.strip()

	# container PID
	cmd = "ssh ubuntu@{ip} \"docker inspect {cnt} --format {{{{.State.Pid}}}}\"".format(ip=nodeIp, cnt=cntId)
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	cntPid, _ = p.communicate()
	cntPid = cntPid.strip()

	return nodeId, nodeIp, cntId, cntPid


if __name__ == "__main__":
	if len(sys.argv)!= 2:
		print("Usage: {} <peer_name>".format(__file__))
		raise SystemExit

	print(getContainerInfo(sys.argv[1]))

