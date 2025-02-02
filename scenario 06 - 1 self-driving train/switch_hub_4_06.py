# Scenario 6: path planning for automated navigation between cities
# - five hubs attached to ten switches (broadcasting position and taking commands)
#    - hub 1 (close to LA): switch A (left switch, M motor) at Port A, switch B (right switch, L motor) at Port B
#    - hub 2 (close to Calgary) : switch C (right switch, M motor) at Port A, switch D (left switch, M motor) at Port B
#    - hub 3 (close to Kansas City): switch E (left switch reversed, L motor) at Port A, switch F (right switch, M motor), switch G (right switch reversed, L motor)
#    - hub 4 (close to NYC): switch H (left switch, M motor), switch I (right switch, L motor)
#    - hub 5 (close to Atlanta): switch J (left switch, M motor)
# - one hub attached to one train (broadcasting position as color patterns, taking commands)
# - one hub acting as the leader (computing full paths using breadth-first search, receiving position updates, sending commands)

# This code is meant to run on switch hub 4 (the hub closest to NYC)

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import DCMotor, Motor  # DCMotor for M, Motor for L
from pybricks.parameters import Port
from pybricks.tools import wait

# Broadcast channels
COMMAND_CHANNEL = 1   # Leader -> All switch hubs
SWITCH_STATUS_4 = 14  # This switch hub's status channel

# Switch positions
SWITCH_POSITION = {
    "STRAIGHT": 0,
    "DIVERGING": 1
}

# Motor constants
MOTOR_POWER = 100  # Power in %
M_MOVE_TIME = 80   # Time in ms for M motors (DCMotor)
L_MOVE_TIME = 85   # Time in ms for L motors (Motor)

# Initialize constants
switch_states = {
    "SWITCH_H": SWITCH_POSITION["STRAIGHT"],
    "SWITCH_I": SWITCH_POSITION["STRAIGHT"]
}
processed_commands = set()
status_number = 0

# Initialize hub and motors
hub = TechnicHub(broadcast_channel=SWITCH_STATUS_4, 
                 observe_channels=[COMMAND_CHANNEL])
switch_H = DCMotor(Port.A)  # Left switch, M motor
switch_I = Motor(Port.B)    # Right switch, L motor
print("Hub and motors initialized!")

def move_switch(switch_name, position):
    """Move switch and broadcast its new position"""
    global status_number
    print("Moving {0} to {1} position!".format(
        switch_name,
        "DIVERGING" if position else "STRAIGHT"
    ))

    if switch_name == "SWITCH_H":
        motor = switch_H
        power = MOTOR_POWER  # Left switch
        move_time = M_MOVE_TIME  # M motor
    else:  # SWITCH_I
        motor = switch_I
        power = -MOTOR_POWER  # Right switch
        move_time = L_MOVE_TIME  # L motor

    if position == SWITCH_POSITION["DIVERGING"]:
        motor.dc(power)
    else:
        motor.dc(-power)
    wait(move_time)
    motor.brake()

    # Update state and broadcast status as name-position pairs
    switch_states[switch_name] = position
    status_number += 1
    hub.ble.broadcast((status_number, 
                      "H", switch_states["SWITCH_H"],
                      "I", switch_states["SWITCH_I"]))

def check_commands():
    """Check for and handle any incoming commands"""
    cmd = hub.ble.observe(COMMAND_CHANNEL)
    if cmd and len(cmd) >= 2:
        command_number = cmd[0]
        switch_name = cmd[1]
        
        if (switch_name in ["SWITCH_H", "SWITCH_I"] and 
            command_number not in processed_commands and 
            len(cmd) == 3):
            
            position = cmd[2]
            move_switch(switch_name, position)
            processed_commands.add(command_number)
            
            if len(processed_commands) > 100:
                oldest = min(processed_commands)
                processed_commands.remove(oldest)

# Initialize switches to STRAIGHT
for name in switch_states:
    print("Initializing {0} to STRAIGHT...".format(name))
    move_switch(name, SWITCH_POSITION["STRAIGHT"])

print("Switches ready! Press button to stop.")

while True:
    if hub.buttons.pressed():
        print("Detected button press: stopped.")
        break
        
    check_commands()
    wait(50)
