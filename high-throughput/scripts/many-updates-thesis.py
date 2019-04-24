import subprocess
import random

peersCount = 10
incCount = 10

increments = []

for peer in range(peersCount):
    for inc in range(incCount):
        increments.append((peer, inc))

random.shuffle(increments)

for increment in increments:
    peer, value = increment
    subprocess.Popen(["./increment-thesis.sh {} {} {}".format(peer, 1, value)], shell=True).wait()