# 4tronix-rover-simulator

Simulator library to allow dev and test of code for the Raspberry Pi-based 4tronix M.A.R.S. Rover without being connected to the actual Rover.

## Getting things set up

We normally use the [Python](https://www.python.org) programming language to program the M.A.R.S. Rover, so this simulator is also all written in Python. The simulator uses a few Python libraries, so the first time you use this on a particular computer you'll need to take some steps to download those libraries.

### First Time (on any particular computer) Setup

1. Open a Windows Terminal window. (Press the Windows key, then type Terminal. If you don't have Terminal installed, [install it](https://www.microsoft.com/store/productId/9N0DX20HK701). If you don't want to, you can run Command Prompt instead.)
2. Find the path to the folder that this code is in. (If you're in VS Code, you can right click the README.md tab at the top of this page, and select **Reveal in File Explorer**. In the Windows File Explorer that opens, click in the address bar at the top to select the folder path then hit Ctrl-C.)

3. You need to get the terminal (or command) window into this directory. So type `cd` then a space, and then the path you just determined in the previous step (you can use Ctrl-V to paste it in if you copied it to the clipboard). So something like this:

```
cd \dev\4tronix-rover-simulator
```

4. Next, we create something called a Python _virtual environment_. That's essentially a place to put all the libraries this code uses. Run this command:

```
py -m venv env
```

5. Next, you need to activate this environment. (Activating it means telling the command window to use this Python environment.):

```
.\env\Scripts\activate
```

Once you've done this, the terminal or command window should change its prompt to show that the environment is activated by showing `(env)` at the start

6. Now that the environment has been activated, you need to tell Python to fetch all of the modules that this code uses:

```
pip install -r requirements.txt
```

This should show messages describing what modules it is downloading. It might show a `WARNING` starting with something like "You are using pip version 21.2.3; however..." You can ignore this. (You might also spot a reference to something called `itsdangerous`. This is a misleadingly named module, so you don't need to be alarmed.)

Once you've done the steps just described, you're now ready to use the simulator. The virtual environment you just created contains everything it needs.

So the next thing you'll probably want to do is run the simulator.

## Simulator User Interface (UI)

The [roversimui.py](roversimui.py) displays a simple representation of the Rover. This lets us see:

* Where the Rover is
* Which way the Rover is pointing
* Where the Rover's steerable wheels are pointing

This simulator runs as a standalone application. Programs that want to control the Rover run as separate applications, and send messages to the Simulator UI to tell it what to do. (This is because the system we're using to open a window and draw the Rover (called [Qt](https://doc.qt.io/qtforpython-6/)) wants to be in control of the program execution so that it can respond to clicks on the window, and repaint things as necessary. So you can't really run code that controls the robot in a normal way in a Qt application. That's why the Qt code is all in a separate program.)

You can run the simulator in the debugger, but you probably don't want to because you'll most likely want to debug the programs you're working on that are trying to control the Rover. You could actually run two copies of Visual Studio (or whatever you're using to debug your Python programs), one to run the simulator and one to debug your own program, but you don't have to. So here's how to run the Simulator UI on its own outside of a debugger.

If you've just finished the 'first time' steps from the preceding section, and you've still got your Terminal (or Command Prompt) open, you can skip straight to step N. But if you've rebooted since then, or closed that window, follow all of these steps.

1. Open a Windows Terminal window (or Command Prompt.)
2. Find the path to the folder that this code is in. (If you're in VS Code, you can right click the README.md tab at the top of this page, and select **Reveal in File Explorer**. In the Windows File Explorer that opens, click in the address bar at the top to select the folder path then hit Ctrl-C.)
3. You need to get the terminal (or command) window into this directory. So type `cd` then a space, and then the path you just determined in the previous step (you can use Ctrl-V to paste it in if you copied it to the clipboard). So something like this:

4. Activate the environment by running this command:

```
.\env\Scripts\activate
```

The terminal or command window should change its prompt to show that the environment is activated by showing `(env)` at the start.

6. Start the emulator UI with this command:

```
python .\roversimui.py
```

This should show a window with a small, simple representation of the Rover and its steerable wheels.


## Using the Simulator

Once the simulator UI is running, you can run Python programs to control it. Normally, programs that control the M.A.R.S. Rover have something like this near the top:

```py
import rover
```

If you change that to this:

```py
import roversimulator as rover
```

this tells Python that anything in the code that uses the `rover` module should use the simulator instead.

Here's a simple example (which you can run by opening the [very-simple-example.py](very-simple-example.py) file in VS Code, and then running it by pressing F5):

```py
import roversimulator as rover
import time

# Servo numbers (so we know which servos control which wheel)
servo_FL = 9
servo_RL = 11
servo_FR = 15
servo_RR = 13
servo_MA = 0


# Get the rover moving forward at full speed.
#
# First, make all the steerable wheels point forwards.
rover.setServo(servo_FL, 0)
rover.setServo(servo_FR, 0)
rover.setServo(servo_RL, 0)
rover.setServo(servo_RR, 0)
# And now it's full speed ahead.
rover.forward(100)


# Let it move for 3 seconds (3000 milliseconds)
time.sleep(3000)


# Now adjust the servo positions so that it's steering left
rover.setServo(servo_FL, -20)
rover.setServo(servo_FR, -20)
rover.setServo(servo_RL, 20)
rover.setServo(servo_RR, 20)


# Let it move for another 3 seconds
time.sleep(3000)

# Now steer right
rover.setServo(servo_FL, 20)
rover.setServo(servo_FR, 20)
rover.setServo(servo_RL, -20)
rover.setServo(servo_RR, -20)


# Let it move for another 3 seconds
time.sleep(3000)

# Straighten up.
rover.setServo(servo_FL, 0)
rover.setServo(servo_FR, 0)
rover.setServo(servo_RL, 0)
rover.setServo(servo_RR, 0)


# Let it move for another 3 seconds
time.sleep(3000)


# ...and rest.
rover.forward(0)
```

