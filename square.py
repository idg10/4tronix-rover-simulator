import roversimulator as rover
import time

FORWARD_SPEED = 100  # Full speed
TURN_SPEED = 100     # Full speed
SIDE_LENGTH_CM = 100

# At 9 cm/s and full speed, time needed to travel 100cm
TIME_FOR_SIDE = SIDE_LENGTH_CM / 9.0  # ~11.11 seconds

# At 36 degrees/s at full speed, time needed to turn 90 degrees
TIME_FOR_TURN = 90.0 / 36.0  # 2.5 seconds

def drive_forward():
    print("Driving forward 100cm...")
    rover.forward(100)
    time.sleep(TIME_FOR_SIDE)
    rover.stop()

def turn_right():
    print("Turning right 90 degrees...")
    # Right motor reverse, left motor forward for spin
    rover.spinRight(100)
    time.sleep(TIME_FOR_TURN)
    rover.stop()
    # Stop

print("Starting square pattern...")
# Drive in a square pattern - 4 sides with right turns
for i in range(4):
    print(f"Side {i+1} of 4")
    drive_forward()
    time.sleep(0.5)  # Small pause between movements
    turn_right()
    time.sleep(0.5)  # Small pause between movements
print("Square pattern completed!")

