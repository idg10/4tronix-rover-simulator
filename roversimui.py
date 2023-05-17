# 4tronix M.A.R.S. Rover Simulator UI
#
# This displays a window representing the rover. It keeps track of its position
# and speed, and the orientation of its wheels. It models this in real time -
# if the virtual rover is set in motion, it will continue to move until further
# instructions are sent telling it to stop.
#
# This receives incoming HTTP requests to control the rover. Incoming messages
# are in JSON form. The following properties may be set in the top-level
# message:
#   wheelMotors
#   servos
#   rgbLeds
#
# A request setting both might look like this:
# {
#   "wheelMotors": {
#     "l": [ 100, 0 ],
#     "r": [ 0, 100 ]
#   },
#   "servos": {
#     "0": 0,
#     "9": -10
#     "10": -10  
#   },
#   "rgbLeds": {
#     "0": [255, 0, 0],
#     "3": [0, 255, 255]
#   }
# }
#
# The wheelMotors settings reflect the way the board itself is designed: it
# seems that there are separate PWM outputs for each direction. The duty
# cycle is set directly to the speed. More cryptically, the frequency is also
# adjusted with the speed. Maximum speed is 100, and the frequency is the speed
# divided by 2 in Hz. So at maximum speed, the PWM frequency is 50Hz. At half
# speed it's 25Hz, and so on until we get to a floor of 10Hz. However, we're
# not simulating at that level of detail. We're just accepting the speeds in
# each direction, and setting the speed to 100 in both directions actively
# brakes the wheels (whereas setting both speeds to zero lets the motor coast
# naturally to a halt, which it does pretty quickly).
# There are 16 servo outputs, although with a standard setup only 5 are used.
# Any servos not specified in the message will not have their positions
# changed.
#
# The response is always of the same format (even if the request is empty):
# {
#   "ultrasonicRange": 80
# }
#
# This reports the detected range from the ultrasonic sensor.
   
import sys
import math
from time import time
import json

from PyQt6.QtCore import QThread, QObject, QTimer, pyqtSignal, QRectF, Qt
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsScene, QGraphicsView,QGraphicsRectItem, QGraphicsItemGroup, QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap, QTransform, QColor, QPen, QBrush

from flask import Flask, request

# Servo assignments
servo_FL = 9
servo_FR = 15
servo_RL = 11
servo_RR = 13
servo_MA = 0


# Receives requests
class ServerWorker(QObject):
    mysignal = pyqtSignal(str)
    http_server = Flask("RoverSimUi")

    def run(self):
        self.http_server.route('/', methods=['POST'])(self.result)
        self.http_server.run(port=8523)

    def result(self): #, *args, **kwargs):
        bodyText = json.dumps(request.json)
        print(request.data)
        self.mysignal.emit(bodyText)
        return request.data

fullSpeedCmPerSecond = 10

class Rover:
    timeOfLastUpdate = time()
    posX = 0
    posY = 0
    headingInDegrees = 0
    speedL = 0
    speedR = 0
    servos = [0] * 16
    rgbLeds = [[0,0,0]] * 4

    def setServo(self, servoId, value):
        self.servos[servoId] = value

    def setWheelMotorLeft(self, fwd, rev):
        if fwd > 0 & rev > 0:
            self.speedL = 0
        else:
            self.speedL = fwd - rev

    def setWheelMotorRight(self, fwd, rev):
        if fwd > 0 & rev > 0:
            self.speedR = 0
        else:
            self.speedR = fwd - rev

    def setRgbLed(self, ledId, rgbValues):
        self.rgbLeds[ledId] = rgbValues
    
    def updateState(self):
        currentTime = time()
        timeSinceLastUpdate = currentTime - self.timeOfLastUpdate
        self.timeOfLastUpdate = currentTime

        # Working out the direction and distance of travel is surprisingly
        # complex, not least because there's no guarantee that all 4 steerable
        # wheels are working together - they could be fighting one another.
        # There are a few ways we could try to work it out:
        #   1. an idealised model in which we presume the wheels cannot slip
        #       sideways and work out the rotation and direction of travel
        #   2. determine the resultant force and moment on the rover by
        #       considering the forces from all 6 driven wheels.
        #   3. work out where each wheel is trying to travel and by how much,
        #       and then average these to work out the net motion and
        #       separately calculate the rotation
        # With 1, we can do this one steerable wheel at a time. If the
        # steerable wheel is pointing dead ahead, then it won't be attempting
        # to turn - it will just be trying to push forwards or backwards. But
        # if it is not dead ahead, then it will be attempting to steer. The two
        # fixed middle wheels constrain it to turn around a point somewhere
        # along the imaginary line joining those two wheels together. We need
        # to calculate the size of that turning circle, because from that, we
        # can calculate the rate of turn for a given speed.
        # We have the angle and also the length of the 'opposite' (the distance
        # between the middle and front wheel), and we want the radius.
        # r*sin(a) = opp, so r = opp/(sin(a))

        def calculateSteerAngle(left, front, wheelAngleRelativeToVehicleDegrees, wheelSpeed, dt):
            # The motor speed is just a number from 0 (not moving)
            # to 100 (full speed). We need to convert that to an
            # actual speed:
            wheelSpeedCmPerSecond = wheelSpeed / 100.0 * fullSpeedCmPerSecond

            if wheelAngleRelativeToVehicleDegrees == 0:
                # We're moving in a straight line, so we just need to work
                # out what that means given the way we're facing
                headingInRadians = (self.headingInDegrees / 180.0) * math.pi

                distanceMovedCmSinceLastUpdate = wheelSpeedCmPerSecond * dt 
                xChangeCm = -distanceMovedCmSinceLastUpdate * math.sin(headingInRadians)
                yChangeCm = distanceMovedCmSinceLastUpdate * math.cos(headingInRadians)
                headingChangeDegrees = 0
            else:
                # Trying to steer, so work out the turning circle radius
                distanceBetweenWheelsCm = 5 if front else -5
                wheelAngleRelativeToVehicleRadians = (wheelAngleRelativeToVehicleDegrees / 180.0) * math.pi
                radiusCm = distanceBetweenWheelsCm / math.sin(wheelAngleRelativeToVehicleRadians)

                # Now work out the rate of turn, then the amount of turn given the time difference
                diameterCm = 2*math.pi*radiusCm
                revolutionsPerSecond = wheelSpeedCmPerSecond / diameterCm
                revolutionsTurned = revolutionsPerSecond * dt
                headingChangeDegrees = revolutionsTurned * 360
                headingChangeRadians = revolutionsTurned * 2 * math.pi

                # Now work out the turning circle centre.
                # Start with the position of the wheel relative to the centre
                # of the vehicle, in a coordinate system aligned with the vehicle
                wheelXRelativeToVehicle = -5 if left else 5
                wheelYRelativeToVehicle = 5 if front else -5
                turningCentreX = 
                




        # This is a bit too basic. We need to take into
        # account wheel servo orientation to work out how
        # much each side moves, and in which direction,
        # and to deduce the rotation of the rover from that.
        # But it will do for now.
        averageSpeed = (self.speedL + self.speedR) / 2

        # The motor speed is just a number from 0 (not moving)
        # to 100 (full speed). We need to convert that to an
        # actual speed:
        averageSpeedCmPerSecond = averageSpeed / 100.0 * fullSpeedCmPerSecond

        # The program probably won't manage to update at exactly the
        # same interval - when the computer's busy or running slowly for
        # some reason, there might be longer gaps between updates. So we
        # need to work out how far the rover will have travelled based
        # not just on its speed, but also on how long it has been since the
        # last update.
        distanceMovedCmSinceLastUpdate = averageSpeedCmPerSecond * timeSinceLastUpdate 
        
        # Of course, the rover probably isn't heading exactly up/down/left/right,
        # so we can't just add the distance moved to posX or posY. We need to
        # work out how to split the distance between those two directions based on
        # the direction the rover is pointing. For this, we use trigonometry! Yay!
        # First, computers always want things in Radians, not Degrees, because reasons
        headingInRadians = (self.headingInDegrees / 180) * math.pi
        xChangeCm = -distanceMovedCmSinceLastUpdate * math.sin(headingInRadians)
        yChangeCm = distanceMovedCmSinceLastUpdate * math.cos(headingInRadians)
        self.posX += xChangeCm
        self.posY += yChangeCm
        print("X,Y: " + str(self.posX) + ", " + str(self.posY))


class MainWindow(QWidget):
    rover = Rover()
    updateTimer = QTimer()

    # Visualized Rover parts

    # This is the whole Rover. All the parts (wheel, head) are attached to
    # this, and will move with it.
    visRoverGroup = QGraphicsItemGroup()

    # Rotatable wheels
    visRoverWheelFL = QGraphicsItemGroup()
    visRoverWheelFR = QGraphicsItemGroup()
    visRoverWheelBL = QGraphicsItemGroup()
    visRoverWheelBR = QGraphicsItemGroup()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.setWindowTitle("M.A.R.S. Rover")
        self.setGeometry(100, 100, 750, 750)
        self.helloMsg = QLabel("<h1>Hello, World!</h1>", parent=self)
        self.helloMsg.move(60, 0)

        roverImage = QPixmap("rover.png")
        self.visRoverGroup.addToGroup(QGraphicsPixmapItem(roverImage))
        body = QGraphicsRectItem(QRectF(-50, -50, 100, 100))
        body.setPen(Qt.GlobalColor.black)
        body.setBrush(Qt.GlobalColor.lightGray)
        self.visRoverGroup.addToGroup(body)

        # For each wheel, we create a QGraphicsItemGroup container that
        # is at a fixed position relative to the rover. This does not
        # rotate as the wheel rotates but it contains an object that does
        # rotate, to visualize the wheel itself.

        def makeWheel(front, left, wheelRotatingContainer):
            wheelNonRotatingContainer = QGraphicsItemGroup(self.visRoverGroup)
            x = -70 if left else 70
            y = -50 if front else 50
            wheel = QGraphicsRectItem(QRectF(-8, -12, 16, 24))
            wheel.setPen(Qt.GlobalColor.lightGray)
            wheel.setBrush(Qt.GlobalColor.black)
            wheelRotatingContainer.addToGroup(wheel)

            wheelNonRotatingContainer.addToGroup(wheelRotatingContainer)
            wheelNonRotatingContainer.setTransform(QTransform.fromTranslate(x, y))
            return wheelNonRotatingContainer
        
        makeWheel(True, True, self.visRoverWheelFL)
        makeWheel(True, False, self.visRoverWheelFR)
        makeWheel(False, True, self.visRoverWheelBL)
        makeWheel(False, False, self.visRoverWheelBR)

        # tx = QTransform()
        # tx.rotate(90)
        # self.visRoverGroup.setTransform(tx)

        scene = QGraphicsScene()
        scene.setSceneRect(QRectF(-200, -200, 400, 400))
        scene.addRect(QRectF(0, 0, 100, 100), QPen(QColor(255,0,0)), QBrush(QColor(255,255,0)))
        #self.scRover = scene.addPixmap(roverImage)
        scene.addItem(self.visRoverGroup)
        #self.scRover.setTransform(tx)
        self.roverIcon = QGraphicsView(scene, parent=self)
        self.roverIcon.move(0, 120)
        self.roverIcon.resize(410, 410)

        # self.roverIcon = QLabel(parent=self)
        # self.roverIcon.setPixmap(roverImage.transformed(tx))
        # self.roverIcon.resize(roverImage.width(), roverImage.height())

        self.server = ServerWorker()
        self.serverThread = QThread()
        self.server.moveToThread(self.serverThread)
        self.serverThread.started.connect(self.server.run)

        self.server.mysignal.connect(self.on_change) #, Qt.QueuedConnection)

        self.serverThread.start()

        self.updateTimer.timeout.connect(self.on_update_timer)
        self.updateTimer.start(1000)

    def on_change(self, s):
        data = json.loads(s)
        if 'servos' in data:
            servos = data['servos']
            for servo in servos:
                servoId = int(servo)
                self.rover.setServo(servoId, servos[servo])

        if 'wheelMotors' in data:
            wheelMotors = data['wheelMotors']
            if 'l' in wheelMotors:
                [fwd, rev] = wheelMotors['l']
                self.rover.setWheelMotorLeft(fwd, rev)
            if 'r' in wheelMotors:
                [fwd, rev] = wheelMotors['r']
                self.rover.setWheelMotorRight(fwd, rev)

        if 'rgbLeds' in data:
            rgbLeds = data['rgbLeds']
            for led in rgbLeds:
                ledId = int(led)
                self.rover.setRgbLed(ledId, rgbLeds[led])


        self.helloMsg.setText(s)
        # self.scRover.setPos(data['location']['x'], data['location']['y'])
        # tx = QTransform()
        # tx.rotate(data['rotation'])
        # self.scRover.setTransform(tx)
        # #self.roverIcon.move(data['location']['x'], data['location']['y'])

    def on_update_timer(self):
        self.rover.updateState()
        tx = QTransform();
        tx.translate(self.rover.posX, self.rover.posY)
        self.visRoverGroup.setTransform(tx)

        self.visRoverWheelFL.setTransform(QTransform().rotate(self.rover.servos[servo_FL]))
        self.visRoverWheelFR.setTransform(QTransform().rotate(self.rover.servos[servo_FR]))
        self.visRoverWheelBL.setTransform(QTransform().rotate(self.rover.servos[servo_RL]))
        self.visRoverWheelBR.setTransform(QTransform().rotate(self.rover.servos[servo_RR]))

app = QApplication([])

window = MainWindow()
window.show()
sys.exit(app.exec())
