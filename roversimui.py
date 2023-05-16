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
#     "15": -10
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
import json

from PyQt6.QtCore import QThread, QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPixmap, QTransform

from flask import Flask, request

# Receives requ
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


class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.setWindowTitle("M.A.R.S. Rover")
        self.setGeometry(100, 100, 750, 750)
        self.helloMsg = QLabel("<h1>Hello, World!</h1>", parent=self)
        self.helloMsg.move(60, 0)

        roverImage = QPixmap("rover.png")
        tx = QTransform()
        tx.rotate(20)

        scene = QGraphicsScene()
        self.scRover = scene.addPixmap(roverImage)
        self.scRover.setTransform(tx)
        self.roverIcon = QGraphicsView(scene, parent=self)
        self.roverIcon.move(0, 120)
        self.roverIcon.resize(400, 400)

        # self.roverIcon = QLabel(parent=self)
        # self.roverIcon.setPixmap(roverImage.transformed(tx))
        # self.roverIcon.resize(roverImage.width(), roverImage.height())

        self.server = ServerWorker()
        self.serverThread = QThread()
        self.server.moveToThread(self.serverThread)
        self.serverThread.started.connect(self.server.run)

        self.server.mysignal.connect(self.on_change) #, Qt.QueuedConnection)

        self.serverThread.start()

    def on_change(self, s):
        data = json.loads(s)
        self.helloMsg.setText(s)
        self.scRover.setPos(data['location']['x'], data['location']['y'])
        tx = QTransform()
        tx.rotate(data['rotation'])
        self.scRover.setTransform(tx)
        #self.roverIcon.move(data['location']['x'], data['location']['y'])


app = QApplication([])

window = MainWindow()
window.show()
sys.exit(app.exec())
