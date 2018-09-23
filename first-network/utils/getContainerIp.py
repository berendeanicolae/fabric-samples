import sys
import os
import subprocess


if len(sys.argv)!= 2:
	print("Usage: {} <peer_name>".format(__file__))
	raise SystemExit

srvcName = sys.argv[1]

def getContainerIP(service):
	# node ID
	cmd = "docker service ps --format '{{{{.Node}}}}' --no-resolve {srvc}".format(srvc=service)
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	srvcId, _ = p.communicate()

	# node IP
	cmd = "docker node inspect --format '{{{{.Status.Addr}}}}' {srvc}".format(srvc=srvcId.strip())
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	srvcIp, _ = p.communicate()

	return srvcIp.strip()


print(getContainerIP(srvcName))
