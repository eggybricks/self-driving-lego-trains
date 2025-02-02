# Scenario 5x:
# - one hub attached to one train (broadcasting position as color patterns, taking commands as color patterns)
# - one hub acting as the leader (receiving position updates as color patterns, sending commands as color patterns)

from pybricks.hubs import InventorHub
from pybricks.parameters import Port, Color
from pybricks.tools import wait

# Broadcast channels
COMMAND_CHANNEL = 1 # Leader -> Switch/train hubs
SWITCH_STATUS_1 = 11    # Switch hub 1 -> leader
SWITCH_STATUS_2 = 12    # Switch hub 2 -> leader
SWITCH_STATUS_3 = 13    # Switch hub 3 -> leader
SWITCH_STATUS_4 = 14    # Switch hub 4 -> leader
SWITCH_STATUS_5 = 15    # Switch hub 5 -> leader
TRAIN_STATUS_CSX = 21   # CSX train hub -> leader

# Switch positions
SWITCH_POSITION = {
    "STRAIGHT": 0,
    "DIVERGING": 1
}

# Train commands
TRAIN_COMMAND = {
    "STOP": 0,
    "FORWARD_UNTIL_PATTERN": 1,
    "BACKWARD_UNTIL_PATTERN": 2
}

# Color codes
TRAIN_COLOR_CODES = {
    Color.NONE: 0,
    Color.RED: 1,
    Color.YELLOW: 2, 
    Color.GREEN: 3,
    Color.BLUE: 4,
    Color.GRAY: 5,
    Color.WHITE: 6
}
TRAIN_COLOR_FROM_CODE = {code: color for color, code in TRAIN_COLOR_CODES.items()}

# Movement codes
TRAIN_MOVEMENT_CODES = {
    "STOPPED": 0,
    "FORWARD": 1,
    "BACKWARD": 2
}
TRAIN_MOVEMENT_FROM_CODE = {code: movement for movement, code in TRAIN_MOVEMENT_CODES.items()}

# Valid colors for patterns
VALID_PATTERN_COLORS = {
    "RED": Color.RED,
    "YELLOW": Color.YELLOW,
    "GREEN": Color.GREEN,
    "BLUE": Color.BLUE
}

# Clear terminal output
print("\x1b[H\x1b[2J", end="")

# Initialize hub
hub = InventorHub(broadcast_channel=COMMAND_CHANNEL,
                  observe_channels=[SWITCH_STATUS_1, SWITCH_STATUS_2, 
                                    SWITCH_STATUS_3, SWITCH_STATUS_4, 
                                    SWITCH_STATUS_5, TRAIN_STATUS_CSX])
print("Leader hub initialized!")

# Initialize state
switch_states = {}
train_states = {}
command_number = 0
processed_statuses = set()

def send_switch_command(switch_name, position):
    """Send a command to the specified switch: tell it to switch to specified position"""
    global command_number
    command_number += 1
    position_str = 'DIVERGING' if position else 'STRAIGHT'
    print(f"Sending command #{command_number}: {switch_name} -> {position_str}")
    hub.ble.broadcast((command_number, switch_name, position))

def send_train_command(train_name, command_type, pattern=None):
    """Send command to train"""
    global command_number
    command_number += 1

    if command_type in [TRAIN_COMMAND["FORWARD_UNTIL_PATTERN"], 
                       TRAIN_COMMAND["BACKWARD_UNTIL_PATTERN"]]:
        # Send pattern length followed by color codes
        pattern_codes = [TRAIN_COLOR_CODES[color] for color in pattern]
        command = (command_number, train_name, command_type, 
                  len(pattern_codes)) + tuple(pattern_codes)
    else:
        command = (command_number, train_name, command_type)

    print(f"Sending command #{command_number}: {train_name} -> {command_type} " +
          (f"pattern={pattern}" if pattern else ""))
    hub.ble.broadcast(command)

def parse_pattern(pattern_str):
    """Convert hyphen-separated color names to color objects"""
    colors = pattern_str.split('-')
    pattern = []

    for color_name in colors:
        color_name = color_name.upper()
        if color_name not in VALID_PATTERN_COLORS:
            print(f"Invalid color: {color_name}")
            print("Valid colors are: RED, YELLOW, GREEN, BLUE")
            return None
        pattern.append(VALID_PATTERN_COLORS[color_name])

    return pattern

def check_status_updates():
    """Check for status updates from all hubs"""
    for channel in [SWITCH_STATUS_1, SWITCH_STATUS_2, SWITCH_STATUS_3, 
                   SWITCH_STATUS_4, SWITCH_STATUS_5, TRAIN_STATUS_CSX]:
        status = hub.ble.observe(channel)

        if status and len(status) >= 2:
            status_number = status[0]
            status_id = (channel, status_number)

            if status_id not in processed_statuses:
                print(f"Processing new status #{status_number} from channel {channel}")

                if channel in [SWITCH_STATUS_1, SWITCH_STATUS_2, SWITCH_STATUS_3, 
                             SWITCH_STATUS_4, SWITCH_STATUS_5]:
                    # Process pairs of (switch_letter, position)
                    for i in range(1, len(status), 2):
                        switch_letter = status[i]
                        position = status[i+1]
                        switch_name = "SWITCH_" + switch_letter
                        switch_states[switch_name] = position
                        print(f"Updated {switch_name} to {'DIVERGING' if position else 'STRAIGHT'}")

                elif channel == TRAIN_STATUS_CSX:
                    train_name = status[1]
                    color_code = status[2]
                    movement_code = status[3]

                    train_states[train_name] = {
                        'movement': TRAIN_MOVEMENT_FROM_CODE[movement_code],
                        'color': TRAIN_COLOR_FROM_CODE[color_code]
                    }

                    # If train is seeking a pattern, save it
                    if len(status) > 4:
                        pattern_length = status[4]
                        pattern = [TRAIN_COLOR_FROM_CODE[code] 
                                 for code in status[5:5+pattern_length]]
                        train_states[train_name]['target_pattern'] = pattern

                    print(f"Updated {train_name} status")

                processed_statuses.add(status_id)

            # Clean up old statuses if we have too many
            if len(processed_statuses) > 100:
                processed_statuses.clear()

def show_status():
    """Display current train status"""
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

    print("\nCurrent train position:")
    if not train_states:
        print("No train reporting")
    else:
        for name, state in train_states.items():
            base_str = f"{name}: {state['movement']}, at {state['color']}"
            if state.get('target_pattern'):
                pattern_str = "-".join(str(c).split('.')[-1] for c in state['target_pattern'])
                base_str += f", seeking pattern {pattern_str}"
            print(base_str)

print("Leader hub ready!")
print("Commands:")
print("Switches:")
print("  s a 0 - Set LA switch (A) to straight")
print("  s a 1 - Set LA switch (A) to diverging")
print("  (same for switches B-J)")
print("Train:")
print("  t csx f red-yellow   - Move CSX train forward until RED-YELLOW pattern")
print("  t csx b yellow-green - Move CSX train backward until YELLOW-GREEN pattern")
print("  t csx s              - Stop CSX train")
print("    Valid colors for patterns:")
print("    RED, YELLOW, GREEN, BLUE")
print("Status:")
print("  st                   - Show all device status")
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
    elif cmd.startswith('t '):
        # Train commands: t csx f red-yellow
        parts = cmd.split()
        if len(parts) >= 3:
            train_name = f"TRAIN_{parts[1].upper()}"
            if parts[2] == 's':
                send_train_command(train_name, TRAIN_COMMAND["STOP"])
            elif len(parts) == 4 and parts[2] in ['f', 'b']:
                pattern = parse_pattern(parts[3])
                if pattern:
                    command_type = (TRAIN_COMMAND["FORWARD_UNTIL_PATTERN"] 
                                   if parts[2] == 'f' else 
                                   TRAIN_COMMAND["BACKWARD_UNTIL_PATTERN"])
                    if parts[2] == 'b':
                        pattern = list(reversed(pattern))
                    send_train_command(train_name, command_type, pattern)
                else:
                    print("Invalid color pattern")
            else:
                print("Invalid train command")
        else:
            print("Invalid train command format")
    else:
        print("Invalid command")

    wait(50) # Short delay so we don't busy-loop
