# Scenario 2:
# - five hubs attached to ten switches: just toggle between states every 3 seconds
#    - hub 1 (close to LA): switch A (left switch, M motor) at Port A, switch B (right switch, L motor) at Port B
#    - hub 2 (close to Calgary) : switch C (right switch, M motor) at Port A, switch D (left switch, M motor) at Port B
#    - hub 3 (close to Kansas City): switch E (left switch reversed, L motor) at Port A, switch F (right switch, M motor), switch G (right switch reversed, L motor)
#    - hub 4 (close to NYC): switch H (left switch, M motor), switch I (right switch, L motor)
#    - hub 5 (close to Atlanta): switch J (left switch, M motor)

# This code is meant to run on switch hub 1 (the hub closest to LA)

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import DCMotor, Motor  # DCMotor for M, Motor for L
from pybricks.parameters import Port
from pybricks.tools import wait

# Switch positions
SWITCH_POSITION = {
    "STRAIGHT": 0,
    "DIVERGING": 1
}

# Motor constants
MOTOR_POWER = 100  # Power in %
M_MOVE_TIME = 70   # Time in ms for M motors (DCMotor)
L_MOVE_TIME = 85   # Time in ms for L motors (Motor)

# Clear terminal output
print("\x1b[H\x1b[2J", end="")

# Initialize constants
switch_states = {
    "SWITCH_A": SWITCH_POSITION["STRAIGHT"],
    "SWITCH_B": SWITCH_POSITION["STRAIGHT"]
}

# Initialize hub and motors
hub = TechnicHub()
switch_A = DCMotor(Port.A)  # Left switch, M motor
switch_B = Motor(Port.B)    # Right switch, L motor
print("Hub and motors initialized!")

def move_switch(switch_name, position):
    print("Moving {0} to {1} position!".format(
        switch_name,
        "DIVERGING" if position else "STRAIGHT"
    ))

    if switch_name == "SWITCH_A":
        motor = switch_A
        power = MOTOR_POWER  # Left switch
        move_time = M_MOVE_TIME  # M motor
    else:  # SWITCH_B
        motor = switch_B
        power = -MOTOR_POWER  # Right switch
        move_time = L_MOVE_TIME  # L motor

    if position == SWITCH_POSITION["DIVERGING"]:
        motor.dc(power)
    else:  # STRAIGHT
        motor.dc(-power)
    wait(move_time)
    motor.brake()

# Initialize switches to STRAIGHT
for name in switch_states:
    print("Initializing {0} to STRAIGHT...".format(name))
    move_switch(name, SWITCH_POSITION["STRAIGHT"])

print("Switches ready: Starting automatic test. Press button to stop.")
print("Will toggle position every 3 seconds...")
wait(500)  # Wait 0.5s before starting

while True:
    if hub.buttons.pressed():
        print("Detected button press: stopped.")
        break

    # Toggle position
    switch_states["SWITCH_A"] = (
        SWITCH_POSITION["DIVERGING"] if switch_states["SWITCH_A"] == SWITCH_POSITION["STRAIGHT"]
        else SWITCH_POSITION["STRAIGHT"]
    )
    move_switch("SWITCH_A", switch_states["SWITCH_A"])
    wait(500)
    switch_states["SWITCH_B"] = (
        SWITCH_POSITION["DIVERGING"] if switch_states["SWITCH_B"] == SWITCH_POSITION["STRAIGHT"]
        else SWITCH_POSITION["STRAIGHT"]
    )
    move_switch("SWITCH_B", switch_states["SWITCH_B"])

    # Wait 2.5 seconds before next toggles, but check for button press every 50ms
    for _ in range(50): # 50 * 50ms = 2.5 seconds
        if hub.buttons.pressed():
            break
        wait(50)
