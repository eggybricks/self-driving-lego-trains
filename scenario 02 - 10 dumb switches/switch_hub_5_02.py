# Scenario 2:
# - five hubs attached to ten switches: just toggle between states every 3 seconds
#    - hub 1 (close to LA): switch A (left switch, M motor) at Port A, switch B (right switch, L motor) at Port B
#    - hub 2 (close to Calgary) : switch C (right switch, M motor) at Port A, switch D (left switch, M motor) at Port B
#    - hub 3 (close to Kansas City): switch E (left switch reversed, L motor) at Port A, switch F (right switch, M motor), switch G (right switch reversed, L motor)
#    - hub 4 (close to NYC): switch H (left switch, M motor), switch I (right switch, L motor)
#    - hub 5 (close to Atlanta): switch J (left switch, M motor)

# This code is meant to run on switch hub 5 (the hub closest to Atlanta)

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import DCMotor  # DCMotor for M motor, Motor for L motor
from pybricks.parameters import Port
from pybricks.tools import wait

# Switch positions
SWITCH_POSITION = {
    "STRAIGHT": 0,
    "DIVERGING": 1
}
SWITCH_NAME = "J"

# Motor constants
MOTOR_POWER = 100 # Power in %
M_MOVE_TIME = 70  # Time in ms for M motors (DCMotor)

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
