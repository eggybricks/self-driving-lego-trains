# Scenario 4: one hub, one train (with motor and color sensor):
# Run at 45% of top power until seeing RED, then stop, then run backwards until BLUE, then stop.

from pybricks.hubs import CityHub
from pybricks.pupdevices import ColorDistanceSensor, DCMotor
from pybricks.parameters import Color, Port
from pybricks.tools import wait

# Constants
MOTOR_SPEED = 45     # Power in %
CHECK_INTERVAL = 50  # Time between color checks in ms

# Clear terminal output
print("\x1b[H\x1b[2J", end="")

# Initialize hub and devices
hub = CityHub()
motor = DCMotor(Port.A)
sensor = ColorDistanceSensor(Port.B)
print("Hub and devices initialized!")

TRAIN_NAME = "TRAIN_CSX"

# Limit color palette because the color sensor is unreliable otherwise
Color.BLUE = Color(h=240, s=43, v=5)
Color.GREEN = Color(h=120, s=60, v=5)
Color.YELLOW = Color(h=40, s=70, v=9)
Color.RED = Color(h=17, s=78, v=7)
Color.GRAY = Color(h=0, s=29, v=3)
sensor.detectable_colors((Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE, Color.GRAY, Color.WHITE, Color.NONE))

def move_until_color(direction, target_color):
    """
    Move train in specified direction until target color is found
    direction: 1 for forward, -1 for backward
    target_color: Color.RED, Color.YELLOW, etc.
    """
    print(f"{TRAIN_NAME}: Moving {'forward' if direction > 0 else 'backward'} until {target_color} detected...")

    # Start moving
    motor.dc(direction * MOTOR_SPEED)

    # Keep checking color until we find the target
    while True:
        current_color = sensor.color()
        print(f"{TRAIN_NAME}: Saw color: {current_color}")
        print(f"{TRAIN_NAME}: HSV: {sensor.hsv()}")
        if current_color == target_color and sensor.distance() < 15:
            print(f"Found {target_color}!")
            motor.brake()
            return True

        wait(CHECK_INTERVAL)

print(f"{TRAIN_NAME}: Starting up: moving forward until RED is detected...")
move_until_color(1, Color.RED)
print(f"{TRAIN_NAME}: Now moving backwards until BLUE is detected...")
move_until_color(-1, Color.BLUE)
print("Done!")
