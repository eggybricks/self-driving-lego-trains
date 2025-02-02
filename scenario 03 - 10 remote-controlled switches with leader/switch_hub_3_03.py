# Scenario 3:
# - five Technic hubs attached to ten switches (broadcasting position and taking commands)
#    - hub 1 (close to LA): switch A (left switch, DCMotor) at Port A, switch B (right switch, Motor) at Port B
#    - hub 2 (close to Calgary) : switch C (right switch, DCMotor) at Port A, switch D (left switch, DCMotor) at Port B
#    - hub 3 (close to Kansas City): switch E (left switch reversed, Motor) at Port A, switch F (right switch, DCMotor), switch G (right switch reversed, Motor)
#    - hub 4 (close to NYC): switch H (left switch, DCMotor), switch I (right switch, Motor)
#    - hub 5 (close to Atlanta): switch J (left switch, DCMotor)
# - one city hub acting as the leader (receiving position updates, sending commands to switches)

# This code is meant to run on switch hub 3 (the hub closest to Kansas City)

from pybricks.hubs import TechnicHub
from pybricks.pupdevices import DCMotor, Motor  # DCMotor for M, Motor for L
from pybricks.parameters import Port
from pybricks.tools import wait

# Broadcast channels
COMMAND_CHANNEL = 1   # Leader -> All switch hubs
SWITCH_STATUS_3 = 13  # This switch hub's status channel

# Switch positions
SWITCH_POSITION = {
    "STRAIGHT": 0,
    "DIVERGING": 1
}

# Motor constants
MOTOR_POWER = 100  # Power in %
M_MOVE_TIME = 70   # Time in ms for M motors (DCMotor)
L_MOVE_TIME = 85   # Time in ms for L motors (Motor)

# Initialize constants
switch_states = {
    "SWITCH_E": SWITCH_POSITION["STRAIGHT"],
    "SWITCH_F": SWITCH_POSITION["STRAIGHT"],
    "SWITCH_G": SWITCH_POSITION["STRAIGHT"]
}
processed_commands = set()
status_number = 0

# Initialize hub and motors
hub = TechnicHub(broadcast_channel=SWITCH_STATUS_3, 
                 observe_channels=[COMMAND_CHANNEL])
switch_E = Motor(Port.A)   # Left switch but flipped, L motor
switch_F = DCMotor(Port.B) # Right switch, M motor
switch_G = Motor(Port.C)   # Right switch but flipped, L motor
print("Hub and motors initialized!")

def move_switch(switch_name, position):
    global status_number
    print("Moving {0} to {1} position!".format(
        switch_name,
        "DIVERGING" if position else "STRAIGHT"
    ))
    
    if switch_name == "SWITCH_E":
        motor = switch_E
        power = -MOTOR_POWER  # Left switch but flipped
        move_time = L_MOVE_TIME  # L motor
    elif switch_name == "SWITCH_F":
        motor = switch_F
        power = -MOTOR_POWER  # Right switch
        move_time = M_MOVE_TIME  # M motor
    else:  # SWITCH_G
        motor = switch_G
        power = MOTOR_POWER  # Right switch but flipped
        move_time = L_MOVE_TIME  # L motor

    if position == SWITCH_POSITION["DIVERGING"]:
        motor.dc(power)
    else:
        motor.dc(-power)
    wait(move_time)
    motor.brake()

    switch_states[switch_name] = position
    status_number += 1
    hub.ble.broadcast((status_number,
                      "E", switch_states["SWITCH_E"],
                      "F", switch_states["SWITCH_F"],
                      "G", switch_states["SWITCH_G"]))

def check_commands():
    """Check for and handle any incoming commands"""
    cmd = hub.ble.observe(COMMAND_CHANNEL)
    if cmd and len(cmd) >= 2:
        command_number = cmd[0]
        switch_name = cmd[1]
        
        if (switch_name in ["SWITCH_E", "SWITCH_F", "SWITCH_G"] and 
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
