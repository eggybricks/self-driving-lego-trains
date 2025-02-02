# Scenario 1:
# - one hub attached to one switch: just toggle between states every 3 seconds

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import DCMotor  # DCMotor for M motor, Motor for L motor
from pybricks.parameters import Port
from pybricks.tools import wait

# Switch positions
SWITCH_POSITION = {
    "STRAIGHT": 0,
    "DIVERGING": 1
}
SWITCH_NAME = "A"

# Motor constants
MOTOR_POWER = 100      # Power in %
M_MOVE_TIME = 70       # Time in ms for M motors (DCMotor)

# Clear terminal output
print("\x1b[H\x1b[2J", end="")

# Initialize hub and motor
hub = TechnicHub()
motor = DCMotor(Port.A)  # Left switch, M motor
print("Hub and motor initialized!")

def move_switch(position):
    if position == SWITCH_POSITION["DIVERGING"]:
        print(f"Switch {SWITCH_NAME}: Moving to diverging position!")
        motor.dc(MOTOR_POWER)
    else:  # STRAIGHT
        print(f"Switch {SWITCH_NAME}: Moving to straight position!")
        motor.dc(-MOTOR_POWER)
    wait(M_MOVE_TIME)
    motor.brake()

# Always reset the switch to STRAIGHT when starting
move_switch(SWITCH_POSITION["STRAIGHT"])
current_position = SWITCH_POSITION["STRAIGHT"]

print(f"Switch {SWITCH_NAME}: Starting automatic test. Press button to stop.")
print("Will toggle position every 3 seconds...")
wait(500)  # Wait 0.5s before starting

while True:
    if hub.buttons.pressed():
        print("Detected button press: stopped.")
        break

    # Toggle position
    current_position = (
        SWITCH_POSITION["DIVERGING"] if current_position == SWITCH_POSITION["STRAIGHT"]
        else SWITCH_POSITION["STRAIGHT"]
    )
    move_switch(current_position)

    # Wait 3 seconds before next toggle, but check for button press every 50ms
    for _ in range(60): # 60 * 50ms = 3 seconds
        if hub.buttons.pressed():
            break
        wait(50)
