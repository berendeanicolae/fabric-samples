import subprocess
import random

peersCount = 100
incCount = 100

increments = []

for peer in range(peersCount):
    for inc in range(incCount):
        increments.append((peer, inc))

random.shuffle(increments)

for increment in increments:
    peer, value = increment
    subprocess.Popen(["./increment.sh {} {} {}".format(peer, 1, value)], shell=True).wait()
