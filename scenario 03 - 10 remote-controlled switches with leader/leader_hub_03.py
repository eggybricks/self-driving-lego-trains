# Scenario 3:
# - five Technic hubs attached to ten switches (broadcasting position and taking commands)
#    - hub 1 (close to LA): switch A (left switch, DCMotor) at Port A, switch B (right switch, Motor) at Port B
#    - hub 2 (close to Calgary) : switch C (right switch, DCMotor) at Port A, switch D (left switch, DCMotor) at Port B
#    - hub 3 (close to Kansas City): switch E (left switch reversed, Motor) at Port A, switch F (right switch, DCMotor), switch G (right switch reversed, Motor)
#    - hub 4 (close to NYC): switch H (left switch, DCMotor), switch I (right switch, Motor)
#    - hub 5 (close to Atlanta): switch J (left switch, DCMotor)
# - one Inventor hub acting as the leader (receiving position updates, sending commands to switches)

# This code is meant to run on the leader hub

from pybricks.hubs import InventorHub
from pybricks.parameters import Port, Color
from pybricks.tools import wait, Matrix

# Broadcast channels
COMMAND_CHANNEL = 1     # Leader broadcasts, all switch hubs listen
SWITCH_STATUS_1 = 11    # Switch hub 1 broadcasts, leader listens
SWITCH_STATUS_2 = 12    # Switch hub 2 broadcasts, leader listens
SWITCH_STATUS_3 = 13    # Switch hub 3 broadcasts, leader listens
SWITCH_STATUS_4 = 14    # Switch hub 4 broadcasts, leader listens
SWITCH_STATUS_5 = 15    # Switch hub 5 broadcasts, leader listens

# Switch positions
SWITCH_POSITION = {
    "STRAIGHT": 0,
    "DIVERGING": 1
}

# Clear terminal output
print("\x1b[H\x1b[2J", end="")

# Initialize hub
hub = InventorHub(broadcast_channel=COMMAND_CHANNEL,
                  observe_channels=[SWITCH_STATUS_1, SWITCH_STATUS_2, 
                                    SWITCH_STATUS_3, SWITCH_STATUS_4, 
                                    SWITCH_STATUS_5])
print("Leader hub initialized!")

# Initialize state
switch_states = {}
command_number = 0
processed_statuses = set()

def send_switch_command(switch_name, position):
    """Send command to switch"""
    global command_number
    command_number += 1
    position_str = 'DIVERGING' if position else 'STRAIGHT'
    print(f"Sending command #{command_number}: {switch_name} -> {position_str}")
    hub.ble.broadcast((command_number, switch_name, position))

def check_status_updates():
    """Check for status updates from all switch hubs"""
    for channel in [SWITCH_STATUS_1, SWITCH_STATUS_2, SWITCH_STATUS_3, 
                   SWITCH_STATUS_4, SWITCH_STATUS_5]:
        status = hub.ble.observe(channel)
        if status and status[0] not in processed_statuses:
            status_number = status[0]
            
            # Process pairs of (switch_letter, position)
            for i in range(1, len(status), 2):
                switch_letter = status[i]
                position = status[i+1]
                switch_name = "SWITCH_" + switch_letter
                switch_states[switch_name] = position
            
            processed_statuses.add(status_number)

def show_status():
    """Display current status of all devices"""
    check_status_updates()

    print("\nCurrent switch positions:")
    if not switch_states:
        print("No switches reporting")
    else:
        for switch_name in sorted(switch_states.keys()):
            position = switch_states[switch_name]
            print("{0}: {1}".format(
                switch_name,
                "DIVERGING" if position == SWITCH_POSITION["DIVERGING"] else "STRAIGHT"
            ))

TINY_EGG = Matrix(
    [
        [0, 0, 0, 0, 0],
        [0, 0, 100, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 100, 0, 0],
        [0, 0, 0, 0, 0],
    ]
)
SMALL_EGG = Matrix(
    [
        [0, 0, 0, 0, 0],
        [0, 0, 100, 0, 0],
        [0, 100, 0, 100, 0],
        [0, 0, 100, 0, 0],
        [0, 0, 0, 0, 0],
    ]
)
MEDIUM_EGG = Matrix(
    [
        [0, 0, 100, 0, 0],
        [0, 50, 0, 50, 0],
        [0, 100, 100, 100, 0],
        [0, 100, 0, 100, 0],
        [0, 0, 100, 0, 0],
    ]
)
LARGE_EGG = Matrix(
    [
        [0, 70, 100, 70, 0],
        [70, 100, 0, 100, 70],
        [100, 100, 100, 100, 100],
        [100, 100, 0, 100, 100],
        [0, 100, 100, 100, 0],
    ]
)

def animate_startup():
    """Show expanding egg animation"""
    animations = [TINY_EGG, SMALL_EGG, MEDIUM_EGG, SMALL_EGG, MEDIUM_EGG, LARGE_EGG]
    for egg in animations:
        hub.display.icon(egg)
        wait(400)
    hub.light.on(Color.YELLOW)  # Ready indicator

print("Leader hub starting up...")
animate_startup()
print("Leader hub ready!")
print("Commands:")
print("Switches:")
print("  s a 0 - Set switch A to straight")
print("  s a 1 - Set switch A to diverging")
print("  (same for switches B-J)")
print("Status:")
print("  st                   - Show status of all devices")
print("  q                    - Quit")

while True:
    cmd = input("Enter command: ").strip().lower()

    if cmd == 'q':
        print("Quitting...")
        break
    elif cmd in ['st', 'status']:
        show_status()
    elif cmd.startswith('s ') and len(cmd) == 5:
        # Switch commands: s a 0
        switch = f"SWITCH_{cmd[2].upper()}"
        position = int(cmd[4])
        if position in [0, 1]:
            send_switch_command(switch, position)
        else:
            print("Invalid switch position")
    else:
        print("Invalid command")

    wait(50) # Short delay so we don't busy-loop
