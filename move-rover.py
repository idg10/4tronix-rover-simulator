import sys
from time import sleep
import roversimulator as rover


rover.init(0)

print("Main thread sleeping")
sleep(100)
print("Main thread done")
