# Mars Rover Simple Drive Mode
# Similar to motortest.py but integrates servo steering
# Moves: Forward, Reverse, turn Right, turn Left, Stop
# Press Ctrl-C to stop

from __future__ import print_function
import time

# choose between real rover and simulator
import roversimulator as rover
#import rover


# Servo numbers
servo_FL = 9
servo_RL = 11
servo_FR = 15
servo_RR = 13
servo_MA = 0


# this turns out not to work on Windows.
# #======================================================================
# # Reading single character by forcing stdin to raw mode
# import sys
# import tty
# import termios

# def readchar():
#     fd = sys.stdin.fileno()
#     old_settings = termios.tcgetattr(fd)
#     try:
#         tty.setraw(sys.stdin.fileno())
#         ch = sys.stdin.read(1)
#     finally:
#         termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
#     if ch == '0x03':
#         raise KeyboardInterrupt
#     return ch

# only works on Windows...
import msvcrt
def readchar():
    key = msvcrt.getch()
    val = 0
    for v in key:
        val = v + (val << 8)
    return chr(val)

def readkey(getchar_fn=None):
    getchar = getchar_fn or readchar
    c1 = getchar()
    if ord(c1) == 0xe0:
        # On Windows, we get this with arrow keys
        # and it's followed by a number indicating
        # direction
        d = getchar()
        if d == 'K': return chr(19) # Left
        if d == 'M': return chr(18) # Right
        if d == 'H': return chr(16) # Up
        if d == 'P': return chr(17) # Left
    if ord(c1) != 0x1b:
        return c1
    c2 = getchar()
    if ord(c2) != 0x5b:
        return c1
    c3 = getchar()
    return chr(0x10 + ord(c3) - 65)  # 16=Up, 17=Down, 18=Right, 19=Left arrows

    

# End of single character reading
#======================================================================

def goForward():
    rover.setServo(servo_FL, 0)
    rover.setServo(servo_FR, 0)
    rover.setServo(servo_RL, 0)
    rover.setServo(servo_RR, 0)
    rover.forward(speed)

def goReverse():
    rover.setServo(servo_FL, 0)
    rover.setServo(servo_FR, 0)
    rover.setServo(servo_RL, 0)
    rover.setServo(servo_RR, 0)
    rover.reverse(speed)

def goLeft():
    rover.setServo(servo_FL, -20)
    rover.setServo(servo_FR, -20)
    rover.setServo(servo_RL, 20)
    rover.setServo(servo_RR, 20)

def goRight():
    rover.setServo(servo_FL, 20)
    rover.setServo(servo_FR, 20)
    rover.setServo(servo_RL, -20)
    rover.setServo(servo_RR, -20)



speed = 60

print ("Drive M.A.R.S. Rover around")
print ("Use arrow keys to steer")
print ("Use , or < to slow down")
print ("Use . or > to speed up")
print ("Press space bar to coast to stop")
print ("Press b to brake and stop quickly")
print ("Press Ctrl-C to end")
print

rover.init(0)

# main loop
try:
    while True:
        keyp = readkey()
        if keyp == 'w' or ord(keyp) == 16:
            goForward()
            print ('Forward', speed)
        elif keyp == 'z' or ord(keyp) == 17:
            goReverse()
            print ('Reverse', speed)
        elif keyp == 's' or ord(keyp) == 18:
            goRight()
            print ('Go Right', speed)
        elif keyp == 'a' or ord(keyp) == 19:
            goLeft()
            print ('Go Left', speed)
        elif keyp == '.' or keyp == '>':
            speed = min(100, speed+10)
            print ('Speed+', speed)
        elif keyp == ',' or keyp == '<':
            speed = max (0, speed-10)
            print ('Speed-', speed)
        elif keyp == ' ':
            rover.stop()
            print ('Stop')
        elif keyp == 'b':
            rover.brake()
            rover.setServo(servo_FL, 0)
            rover.setServo(servo_FR, 0)
            rover.setServo(servo_RL, 0)
            rover.setServo(servo_RR, 0)
            print ('Brake')
        elif ord(keyp) == 3:
            break

except KeyboardInterrupt:
    pass

finally:
    rover.cleanup()