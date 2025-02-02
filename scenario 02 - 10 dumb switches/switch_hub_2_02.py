# Scenario 2:
# - five hubs attached to ten switches: just toggle between states every 3 seconds
#    - hub 1 (close to LA): switch A (left switch, M motor) at Port A, switch B (right switch, L motor) at Port B
#    - hub 2 (close to Calgary) : switch C (right switch, M motor) at Port A, switch D (left switch, M motor) at Port B
#    - hub 3 (close to Kansas City): switch E (left switch reversed, L motor) at Port A, switch F (right switch, M motor), switch G (right switch reversed, L motor)
#    - hub 4 (close to NYC): switch H (left switch, M motor), switch I (right switch, L motor)
#    - hub 5 (close to Atlanta): switch J (left switch, M motor)

# This code is meant to run on switch hub 2 (the hub closest to Calgary)

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import DCMotor
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

# Clear terminal output
print("\x1b[H\x1b[2J", end="")

# Initialize constants
switch_states = {
    "SWITCH_C": SWITCH_POSITION["STRAIGHT"],
    "SWITCH_D": SWITCH_POSITION["STRAIGHT"]
}

# Initialize hub and motors
hub = TechnicHub()
switch_C = DCMotor(Port.A)  # Right switch, reverse power, M motor
switch_D = DCMotor(Port.B)  # Left switch, M motor
print("Hub and motors initialized!")

def move_switch(switch_name, position):
    print("Moving {0} to {1} position!".format(
        switch_name,
        "DIVERGING" if position else "STRAIGHT"
    ))
    
    if switch_name == "SWITCH_C":
        motor = switch_C
        power = -MOTOR_POWER  # Right switch
    else:  # SWITCH_D
        motor = switch_D
        power = MOTOR_POWER  # Left switch
    move_time = M_MOVE_TIME  # Both are M motors

    if position == SWITCH_POSITION["DIVERGING"]:
        motor.dc(power)
    else:
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
    switch_states["SWITCH_C"] = (
        SWITCH_POSITION["DIVERGING"] if switch_states["SWITCH_C"] == SWITCH_POSITION["STRAIGHT"]
        else SWITCH_POSITION["STRAIGHT"]
    )
    move_switch("SWITCH_C", switch_states["SWITCH_C"])
    wait(500)
    switch_states["SWITCH_D"] = (
        SWITCH_POSITION["DIVERGING"] if switch_states["SWITCH_D"] == SWITCH_POSITION["STRAIGHT"]
        else SWITCH_POSITION["STRAIGHT"]
    )
    move_switch("SWITCH_D", switch_states["SWITCH_D"])

    # Wait 2.5 seconds before next toggles, but check for button press every 50ms
    for _ in range(50): # 50 * 50ms = 2.5 seconds
        if hub.buttons.pressed():
            break
        wait(50)
