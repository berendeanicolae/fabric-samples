import subprocess
import random

peersCount = 100
incCount = 100

increments = []

for peer in range(peersCount):
    for value in range(valueCount):
        increments.append((peer, value))

random.shuffle(increments)

for increment in increments:
    peer, value = increment
    subprocess.Popen(["./increment-thesis.sh {} {} {}".format(peer, 1, value)], shell=True).wait()
