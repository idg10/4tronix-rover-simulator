import sys
import json

from PyQt6.QtCore import QThread, QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPixmap, QTransform

from flask import Flask, request

class ServerWorker(QObject):
    mysignal = pyqtSignal(str)
    http_server = Flask("RoverSimUi")

    def run(self):
        self.http_server.route('/', methods=['POST'])(self.result)
        self.http_server.run(port=8523)

    #@http_server.route('/', methods=['POST'])
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
