import time
import subprocess

from getContainerInfo import getContainerInfo

services = [
	"fabric_cli",
	"fabric_orderer",
	"fabric_peer0_org1",
	"fabric_peer1_org1",
	"fabric_peer0_org2",
	"fabric_peer1_org2",
]

for service in services:
	cnt = 0
	info = getContainerInfo(service)
	while info is None:
		if cnt>=10: break
		time.sleep(10)
		info = getContainerInfo(service)
		cnt += 1

	_, ip, id, _ = info

	cmd = "ssh ubuntu@{ip} \"docker inspect {cnt} --format {{{{.LogPath}}}}\"".format(ip=ip, cnt=id)
	p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
	logPath, _ = p.communicate()

	cmd = "ssh {ip}".format(ip=ip)
	p = subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, universal_newlines=True, bufsize=0)
	p.stdin.write("sudo chmod 777 {}\n".format(os.path.basename(os.path.basename(os.path.basename(os.path.basename(logPath))))))
	p.stdin.write("sudo chmod 777 {}\n".format(os.path.basename(os.path.basename(os.path.basename(logPath)))))
	p.stdin.write("sudo chmod 777 {}\n".format(os.path.basename(os.path.basename(logPath))))
	p.stdin.write("sudo chmod 777 {}\n".format(os.path.basename(logPath)))
	p.stdin.close()

	cmd = "scp ubuntu@{ip}:{srcFile} ./{dstFile}".format(ip=ip, srcFile=logPath, dstFile=service)
	p = subprocess.Popen([cmd], shell=True).wait()

