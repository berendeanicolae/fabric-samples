import sys
import os
import subprocess


if len(sys.argv)!= 2:
	print("Usage: {} <peer_name>".format(__file__))
	raise SystemExit

srvcName = sys.argv[1]

def getContainerInfo(service):
	# node ID
	cmd = "docker service ps --format '{{{{.Node}}}} {{{{.DesiredState}}}}' --no-resolve {srvc}".format(srvc=service)
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	srvcId, _ = p.communicate()
	srvcId = srvcId.split("\n", 1)[0]
	if srvcId.split()[1]!="Running":
		return None
	srvcId = srvcId.split()[0].strip()

	# node IP
	cmd = "docker node inspect --format '{{{{.Status.Addr}}}}' {srvc}".format(srvc=srvcId.strip())
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	srvcIp, _ = p.communicate()
	srvcIp = srvcIp.strip()

	# container ID
	cmd = "ssh ubuntu@{ip} \"docker container ls --format '{{{{.ID}}}} {{{{.Names}}}}'\" | grep {srvc}".format(ip=srvcIp, srvc=service)
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	cnts, _ = p.communicate()
	cnts = cnts.strip()
	cntId, _ = cnts.split()
	cntId = cntId.strip()

	# container PID
	cmd = "ssh ubuntu@{ip} \"docker inspect {cnt} --format {{{{.State.Pid}}}}\"".format(ip=srvcIp, cnt=cntId)
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	cntPid, _ = p.communicate()
	cntPid = cntPid.strip()

	return srvcId, srvcIp, cntId, cntPid


print(getContainerInfo(srvcName))

