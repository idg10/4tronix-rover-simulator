#!/usr/bin/python
#
# rover.py
#
# Python Module to support 4tronix M.A.R.S. Rover
#
# Copyright 4tronix
#
# This code is in the public domain and may be freely copied and used
# No warranty is provided or implied
#
#======================================================================


#======================================================================
# General Functions
# (Both versions)
#
# init(brightness). Initialises GPIO pins, switches motors and LEDs Off. If brightness is 0, no LEDs are initialised
# cleanup(). Sets all motors and LEDs off and sets GPIO to standard values
# version(). Returns 4 for M.A.R.S. Rover. Invalid until after init() has been called
#======================================================================


#======================================================================
# Motor Functions
#
# stop(): Stops both motors
# forward(speed): Sets both motors to move forward at speed. 0 <= speed <= 100
# reverse(speed): Sets both motors to reverse at speed. 0 <= speed <= 100
# spinLeft(speed): Sets motors to turn opposite directions at speed. 0 <= speed <= 100
# spinRight(speed): Sets motors to turn opposite directions at speed. 0 <= speed <= 100
# turnForward(leftSpeed, rightSpeed): Moves forwards in an arc by setting different speeds. 0 <= leftSpeed,rightSpeed <= 100
# turnreverse(leftSpeed, rightSpeed): Moves backwards in an arc by setting different speeds. 0 <= leftSpeed,rightSpeed <= 100
#======================================================================


#======================================================================
# FIRELED Functions
#
# setColor(color): Sets all LEDs to color - requires show()
# setPixel(ID, color): Sets pixel ID to color - requires show()
# show(): Updates the LEDs with state of LED array
# clear(): Clears all LEDs to off - requires show()
# rainbow(): Sets the LEDs to rainbow colors - requires show()
# fromRGB(red, green, blue): Creates a color value from R, G and B values
# toRGB(color): Converts a color value to separate R, G and B
# wheel(pos): Generates rainbow colors across 0-255 positions
#======================================================================


#======================================================================
# UltraSonic Functions
#
# getDistance(). Returns the distance in cm to the nearest reflecting object. 0 == no object
#======================================================================


#======================================================================
# Servo Functions
#
# getLight(Sensor). Returns the value 0..1023 for the selected sensor, 0 <= Sensor <= 3
# getLightFL(). Returns the value 0..1023 for Front-Left light sensor
# getLightFR(). Returns the value 0..1023 for Front-Right light sensor
# getLightBL(). Returns the value 0..1023 for Back-Left light sensor
# getLightBR(). Returns the value 0..1023 for Back-Right light sensor
# getBattery(). Returns the voltage of the battery pack (>7.2V is good, less is bad)
#======================================================================


#======================================================================
# Keypad Functions
#
# getSwitch(). Returns the value of the tact switch: True==pressed
#======================================================================


# Import all necessary libraries
import RPi.GPIO as GPIO, sys, time, os
from rpi_ws281x import *
import pca9685
import smbus

# Define Model
PGNone = 0
PGFull = 1
PGLite = 2
PG2 = 3
ROVER = 4
PGType = PGNone # Set to None until we confirm during init()

# Pins 26, 19 Left Motor
# Pins 36, 40 Right Motor
# If using PiBit, then L1 and L2 are swapped
L1 = 16
L2 = 19
R1 = 12
R2 = 13
# Variables to track movements to prevent sudden forward/reverse current surges. -1 reverse, 0 stop, +1 forward
lDir = 0
rDir = 0

# Define RGB LEDs
leds = None
_brightness = 40
numPixels = 4

# Define Sonar Pin (same pin for both Ping and Echo)
sonar = 23    # mast sonar

# Pins used for keypad
keypadOut = 5
keypadIn = 25

# EEROM
EEROM = 0x50
bus = smbus.SMBus(1)
offsets = [0]*16

#======================================================================
# General Functions
#
# init(). Initialises GPIO pins, switches motors and LEDs Off, etc
def init(brightness, PiBit=False):
    global p, q, a, b, pwm, pcfADC, PGType
    global irFL, irFR, irMID, lineLeft, lineRight
    global leds, L1, L2

    GPIO.setwarnings(False)

    PGType = PG2

    #use physical pin numbering
    GPIO.setmode(GPIO.BCM)
    
    # Initialise LEDs
    if (leds == None and brightness>0):
        _brightness = brightness
        leds = Adafruit_NeoPixel(numPixels, 18, 800000, 5, False, _brightness)
        leds.begin()

    pca9685.init()

    if PiBit:
        t = L1
        L1 = L2
        L2 = t

    #use pwm for motor outputs
    GPIO.setup(L1, GPIO.OUT)
    p = GPIO.PWM(L1, 20)
    p.start(0)

    GPIO.setup(L2, GPIO.OUT)
    q = GPIO.PWM(L2, 20)
    q.start(0)

    GPIO.setup(R1, GPIO.OUT)
    a = GPIO.PWM(R1, 20)
    a.start(0)

    GPIO.setup(R2, GPIO.OUT)
    b = GPIO.PWM(R2, 20)
    b.start(0)

    # set Keypad Clock as an Output and Data as an input
    GPIO.setup(keypadOut, GPIO.OUT)
    GPIO.setup(keypadIn, GPIO.IN)

    loadOffsets()


# cleanup(). Sets all motors and LEDs off and sets GPIO to standard values
def cleanup():
    global running
    running = False
    stop()
    if (leds != None):
        clear()
        show()
    time.sleep(0.1)
    GPIO.cleanup()


# version(). Returns 3 for Pi2Go2. Invalid until after init() has been called
def version():
    return PGType

# End of General Functions
#======================================================================


#======================================================================
# Motor Functions
#
# stop(): Stops both motors - coasts slowly to a stop
def stop():
    global lDir, rDir
    p.ChangeDutyCycle(0)
    q.ChangeDutyCycle(0)
    a.ChangeDutyCycle(0)
    b.ChangeDutyCycle(0)
    lDir = 0
    rDir = 0

# brake(): Stops both motors - regenrative braking to stop quickly
def brake():
    global lDir, rDir
    p.ChangeDutyCycle(100)
    q.ChangeDutyCycle(100)
    a.ChangeDutyCycle(100)
    b.ChangeDutyCycle(100)
    lDir = 0
    rDir = 0

# forward(speed): Sets both motors to move forward at speed. 0 <= speed <= 100
def forward(speed):
    global lDir, rDir
    if (lDir == -1 or rDir == -1):
        brake()
        time.sleep(0.2)
    p.ChangeDutyCycle(speed)
    q.ChangeDutyCycle(0)
    a.ChangeDutyCycle(speed)
    b.ChangeDutyCycle(0)
    p.ChangeFrequency(max(speed/2, 10))
    a.ChangeFrequency(max(speed/2, 10))
    lDir = 1
    rDir = 1

# reverse(speed): Sets both motors to reverse at speed. 0 <= speed <= 100
def reverse(speed):
    global lDir, rDir
    if (lDir == 1 or rDir == 1):
        brake()
        time.sleep(0.2)
    p.ChangeDutyCycle(0)
    q.ChangeDutyCycle(speed)
    a.ChangeDutyCycle(0)
    b.ChangeDutyCycle(speed)
    q.ChangeFrequency(max(speed/2, 10))
    b.ChangeFrequency(max(speed/2, 10))
    lDir = -1
    rDir = -1

# spinLeft(speed): Sets motors to turn opposite directions at speed. 0 <= speed <= 100
def spinLeft(speed):
    global lDir, rDir
    if (lDir == 1 or rDir == -1):
        brake()
        time.sleep(0.2)
    p.ChangeDutyCycle(0)
    q.ChangeDutyCycle(speed)
    a.ChangeDutyCycle(speed)
    b.ChangeDutyCycle(0)
    q.ChangeFrequency(min(speed+5, 20))
    a.ChangeFrequency(min(speed+5, 20))
    lDir = -1
    rDir = 1

# spinRight(speed): Sets motors to turn opposite directions at speed. 0 <= speed <= 100
def spinRight(speed):
    global lDir, rDir
    if (lDir == -1 or rDir == 1):
        brake()
        time.sleep(0.2)
    p.ChangeDutyCycle(speed)
    q.ChangeDutyCycle(0)
    a.ChangeDutyCycle(0)
    b.ChangeDutyCycle(speed)
    p.ChangeFrequency(min(speed+5, 20))
    b.ChangeFrequency(min(speed+5, 20))
    lDir = 1
    rDir = -1

# turnForward(leftSpeed, rightSpeed): Moves forwards in an arc by setting different speeds. 0 <= leftSpeed,rightSpeed <= 100
def turnForward(leftSpeed, rightSpeed):
    global lDir, rDir
    if (lDir == -1 or rDir == -1):
        brake()
        time.sleep(0.2)
    p.ChangeDutyCycle(leftSpeed)
    q.ChangeDutyCycle(0)
    a.ChangeDutyCycle(rightSpeed)
    b.ChangeDutyCycle(0)
    p.ChangeFrequency(min(leftSpeed+5, 20))
    a.ChangeFrequency(min(rightSpeed+5, 20))
    lDir = 1
    rDir = 1

# turnReverse(leftSpeed, rightSpeed): Moves backwards in an arc by setting different speeds. 0 <= leftSpeed,rightSpeed <= 100
def turnReverse(leftSpeed, rightSpeed):
    global lDir, rDir
    if (lDir == 1 or rDir == 1):
        brake()
        time.sleep(0.2)
    p.ChangeDutyCycle(0)
    q.ChangeDutyCycle(leftSpeed)
    a.ChangeDutyCycle(0)
    b.ChangeDutyCycle(rightSpeed)
    q.ChangeFrequency(min(leftSpeed+5, 20))
    b.ChangeFrequency(min(rightSpeed+5, 20))
    lDir = -1
    rDir = -1

# End of Motor Functions
#======================================================================


#======================================================================
# Wheel Sensor Functions

def stopL():
    p.ChangeDutyCycle(100)
    q.ChangeDutyCycle(100)

def stopR():
    a.ChangeDutyCycle(100)
    b.ChangeDutyCycle(100)

def lCounter(pin):
    global countL, targetL
    countL += 1
    if countL == targetL:
        stopL()
        targetL = -1

def rCounter(pin):
    global countR, targetR
    countR += 1
    if countR == targetR:
        stopR()
        targetR = -1

# stepForward(speed, steps): Moves forward specified number of counts, then stops
def stepForward(speed, counts):
    global countL, countR, targetL, targetR
    countL = 0
    countR = 0
    targetL = counts-(speed/20)
    targetR = counts-(speed/20)
    forward(speed)
    while (targetL != -1) or (targetR != -1):
        time.sleep(0.002)

# stepReverse(speed, steps): Moves backward specified number of counts, then stops
def stepReverse(speed, counts):
    global countL, countR, targetL, targetR
    countL = 0
    countR = 0
    targetL = counts-(speed/20)
    targetR = counts-(speed/20)
    reverse(speed)
    while (targetL != -1) or (targetR != -1):
        time.sleep(0.002)

# stepSpinL(speed, steps): Spins left specified number of counts, then stops
def stepSpinL(speed, counts):
    global countL, countR, targetL, targetR
    countL = 0
    countR = 0
    targetL = counts-(speed/20)
    targetR = counts-(speed/20)
    spinLeft(speed)
    while (targetL != -1) or (targetR != -1):
        time.sleep(0.002)

# stepSpinR(speed, steps): Spins right specified number of counts, then stops
def stepSpinR(speed, counts):
    global countL, countR, targetL, targetR
    countL = 0
    countR = 0
    targetL = counts-(speed/20)
    targetR = counts-(speed/20)
    spinRight(speed)
    while (targetL != -1) or (targetR != -1):
        time.sleep(0.002)


# End of Wheel Sensor Functions
#======================================================================


#======================================================================
# IR Sensor Functions
#
# irLeft(): Returns state of Left IR Obstacle sensor
def irLeft():
    if GPIO.input(irFL)==0:
        return True
    else:
        return False

# irRight(): Returns state of Right IR Obstacle sensor
def irRight():
    if GPIO.input(irFR)==0:
        return True
    else:
        return False

# irAll(): Returns true if either of the Obstacle sensors are triggered
def irAll():
    if GPIO.input(irFL)==0 or GPIO.input(irFR)==0:
        return True
    else:
        return False

# irLeftLine(): Returns state of Left IR Line sensor
def irLeftLine():
    if GPIO.input(lineLeft)==0:
        return True
    else:
        return False

# irRightLine(): Returns state of Right IR Line sensor
def irRightLine():
    if GPIO.input(lineRight)==0:
        return True
    else:
        return False

# End of IR Sensor Functions
#======================================================================


#======================================================================
# UltraSonic Functions
#
# getDistance(). Returns the distance in cm to the nearest reflecting object. 0 == no object
#
def getDistance(): # default to front sensor
    GPIO.setup(sonar, GPIO.OUT)
    # Send 10us pulse to trigger
    GPIO.output(sonar, True)
    time.sleep(0.00001)
    GPIO.output(sonar, False)
    start = time.time()
    count=time.time()
    GPIO.setup(sonar,GPIO.IN)
    while GPIO.input(sonar)==0 and time.time()-count<0.1:
        start = time.time()
    count=time.time()
    stop=count
    while GPIO.input(sonar)==1 and time.time()-count<0.1:
        stop = time.time()
    # Calculate pulse length
    elapsed = stop-start
    # Distance pulse travelled in that time is time
    # multiplied by the speed of sound 34000(cm/s) divided by 2
    distance = elapsed * 17000
    return distance

# End of UltraSonic Functions
#======================================================================


#======================================================================
# RGB LED Functions
#
def setColor(color):
    for i in range(numPixels):
        setPixel(i, color)

def setPixel(ID, color):
    if (ID <= numPixels):
        leds.setPixelColor(ID, color)

def show():
    leds.show()

def clear():
    for i in range(numPixels):
        setPixel(i, 0)

def rainbow():
    i = 0
    for x in range(numPixels):
        setPixel(x, int(wheel(x * 256 / numPixels)))

def fromRGB(red, green, blue):
        return ((int(red)<<16) + (int(green)<<8) + blue)

def toRGB(color):
        return (((color & 0xff0000) >> 16), ((color & 0x00ff00) >> 8), (color & 0x0000ff))

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return fromRGB(255 - pos * 3, pos * 3, 0) # Red -> Green
    elif pos < 170:
        pos -= 85
        return fromRGB(0, 255 - pos * 3, pos * 3) # Green -> Blue
    else:
        pos -= 170
        return fromRGB(pos * 3, 0, 255 - pos * 3) # Blue -> Red

#
# End of RGB LED Functions
#======================================================================

#======================================================================
# Servo Functions

def setServo(Servo, Degrees):
    pca9685.setServo(Servo, Degrees + offsets[Servo])

def stopServos():
    for i in range(16):
        pca9685.stopServo(i)
    
# End of Servo Functions
#======================================================================

#======================================================================
# Keypad Functions

def getKey():
    keys = 0
    count = 0
    fred = 0
    
    GPIO.output(keypadOut, 0)
    while (keys == 0):
        #GPIO.output(keypadOut, 1)
        time.sleep(0.00001)
        while (GPIO.input(keypadIn) == 1):
            count += 1
            if (count > 1000):
                count = 0
                time.sleep(0.001)
        while (GPIO.input(keypadIn) == 0):
            pass
        for index in range(16):
            GPIO.output(keypadOut, 0)
            fred += 1 # dummy
            keys = (keys << 1) + GPIO.input(keypadIn)
            GPIO.output(keypadOut, 1)
            fred -= 1 # dummy
        keys = 65535 - keys
    return keys

            
# End of Keypad Functions
#======================================================================


#======================================================================
# EEROM Functions
# First 16 bytes are used for servo offsets (signed bytes)

# Low level read function. Reads data from actual Address
def rdEEROM(Address):
    bus.write_i2c_block_data(EEROM, Address >> 8, [Address & 0xff])
    return ((bus.read_byte(EEROM) + 0x80) & 0xff) - 0x80  # sign extend

# Low level write function. Writes Data to actual Address
def wrEEROM(Address, Data):
    bus.write_i2c_block_data(EEROM, Address >> 8, [Address & 0xff, Data])
    time.sleep(0.01)

# General Read Function. Ignores first 16 bytes
def readEEROM(Address):
    return rdEEROM(Address + 16)

# General Write Function. Ignores first 16 bytes
def writeEEROM(Address, Data):
    wrEEROM(Address + 16, Data)

# Load all servo Offsets
def loadOffsets():
    for idx in range(16):
        offsets[idx] = rdEEROM(idx)

# Save all servo Offsets
def saveOffsets():
    for idx in range(16):
        wrEEROM(idx, offsets[idx])

            
# End of EEROM Functions
#======================================================================


  
