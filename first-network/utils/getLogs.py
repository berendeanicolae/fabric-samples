import os
import time
import subprocess

from getContainerInfo import getContainerInfo

peersCount = [100]
services = []
for org in range(len(peersCount)):
	for peer in range(peersCount[org]):
		services.append("fabric_peer{}_org{}".format(peer, org+1))

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
	logPath = logPath.strip()

	cmd = "ssh {ip}".format(ip=ip)
	p = subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, universal_newlines=True, bufsize=0)
	p.stdin.write("sudo chmod 777 {}\n".format(os.path.dirname(os.path.dirname(os.path.dirname(logPath)))))
	p.stdin.write("sudo chmod 777 {}\n".format(os.path.dirname(os.path.dirname(logPath))))
	p.stdin.write("sudo chmod 777 {}\n".format(os.path.dirname(logPath)))
	p.stdin.write("sudo chmod 777 {}\n".format(logPath))
	p.stdin.write("exit\n")
	p.stdin.close()
	p.wait()

	cmd = "scp ubuntu@{ip}:{srcFile} ./{dstFile}".format(ip=ip, srcFile=logPath, dstFile=service)
	print(cmd)
	p = subprocess.Popen([cmd], shell=True).wait()

