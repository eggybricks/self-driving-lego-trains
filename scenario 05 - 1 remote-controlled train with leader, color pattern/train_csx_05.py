# Scenario 5:
# - one hub attached to one train (broadcasting position as color patterns, taking commands as color patterns)
# - one hub acting as the leader (receiving position updates as color patterns, sending commands as color patterns)

from pybricks.hubs import CityHub
from pybricks.pupdevices import ColorDistanceSensor, DCMotor
from pybricks.parameters import Color, Port
from pybricks.tools import StopWatch, wait

# Constants
MOTOR_SPEED = 40           # Power in %
CHECK_INTERVAL = 50        # Time between color checks in ms
BROADCAST_INTERVAL = 2000  # Time between status broadcasts in ms

# Broadcast channels
COMMAND_CHANNEL = 1  # Leader -> Switch/train hubs
STATUS_CHANNEL = 21  # CSX train hub -> Leader

# Train commands
TRAIN_COMMAND = {
    "STOP": 0,
    "FORWARD_UNTIL_PATTERN": 1,
    "BACKWARD_UNTIL_PATTERN": 2
}

# Clear terminal output
print("\x1b[H\x1b[2J", end="")

# Initialize hub and devices
hub = CityHub(broadcast_channel=STATUS_CHANNEL,
              observe_channels=[COMMAND_CHANNEL])
motor = DCMotor(Port.A)
sensor = ColorDistanceSensor(Port.B)
print("Hub and devices initialized!")

TRAIN_NAME = "TRAIN_CSX"
status_number = 0
processed_commands = set()
broadcast_timer = StopWatch()

# Limit color palette because the color sensor is unreliable otherwise
Color.BLUE = Color(h=216, s=79, v=5)
Color.GREEN = Color(h=90, s=60, v=3)
Color.YELLOW = Color(h=49, s=87, v=9)
Color.RED = Color(h=350, s=88, v=5)
Color.GRAY = Color(h=0, s=30, v=3)
our_colors = (Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE, Color.GRAY, Color.WHITE, Color.NONE)
sensor.detectable_colors(our_colors)

# Color codes (3 bits)
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

def broadcast_status(movement_state, pattern_codes=None):
    """Broadcast current status including target pattern"""
    global status_number
    status_number += 1
    current_color = sensor.color()
    current_code = TRAIN_COLOR_CODES[current_color]
    movement_code = TRAIN_MOVEMENT_CODES[movement_state]

    # Include pattern in status
    if pattern_codes:
        hub.ble.broadcast((status_number, TRAIN_NAME, current_code, movement_code, 
                          len(pattern_codes)) + tuple(pattern_codes))
    else:
        hub.ble.broadcast((status_number, TRAIN_NAME, current_code, movement_code, 0))

    # Print status in simpler way
    pattern_str = ""
    if pattern_codes:
        pattern_str = f", seeking pattern {[TRAIN_COLOR_FROM_CODE[c] for c in pattern_codes]}"
    print(f"{TRAIN_NAME}: Broadcasting status #{status_number}: {movement_state}, seeing {current_color}{pattern_str}")
    broadcast_timer.reset()

VALID_PATTERN_COLORS = {Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE}

def is_valid_color(color):
    """Check if a color is valid for pattern matching"""
    return color in VALID_PATTERN_COLORS

def consolidate_colors(color_history, min_repeats=2):
    """
    Convert a list of colors into a stable pattern by removing outliers.
    A color must be seen min_repeats times to be considered real.
    Returns list of colors with outliers removed.
    """
    if not color_history:
        return []

    # Group consecutive same colors
    groups = []
    current_color = color_history[0]
    current_count = 1

    for color in color_history[1:]:
        if color == current_color:
            current_count += 1
        else:
            groups.append((current_color, current_count))
            current_color = color
            current_count = 1
    groups.append((current_color, current_count))

    # Keep only colors that appear enough times
    stable_colors = []
    for color, count in groups:
        if count >= min_repeats:
            if not stable_colors or stable_colors[-1] != color:
                stable_colors.append(color)

    return stable_colors

def move_until_pattern(direction, pattern_codes):
    """
    Move train in specified direction until color pattern is found
    direction: 1 for forward, -1 for backward
    pattern_codes: list of color codes to look for in sequence
    """
    movement = "FORWARD" if direction > 0 else "BACKWARD"
    pattern = [TRAIN_COLOR_FROM_CODE[code] for code in pattern_codes]
    print(f"{TRAIN_NAME}: Moving {movement} until pattern {pattern} detected...")

    motor.dc(direction * MOTOR_SPEED)
    seen_colors = []
    broadcast_status(movement, pattern_codes)

    while True:
        # Check for new commands (especially STOP)
        cmd = hub.ble.observe(COMMAND_CHANNEL)
        if cmd:
            if handle_command(cmd):  # Returns True if we should stop
                return False

        if sensor.distance() < 15:
            current_color = sensor.color()
            if is_valid_color(current_color):
                seen_colors.append(current_color)
                if len(seen_colors) > len(pattern) * 4:
                    seen_colors.pop(0)

                stable_pattern = consolidate_colors(seen_colors)
                print(f"Stable pattern: {stable_pattern}")

                if len(stable_pattern) >= len(pattern):
                    if tuple(stable_pattern[-len(pattern):]) == tuple(pattern):
                        print(f"Found pattern {pattern}!")
                        motor.brake()
                        broadcast_status("STOPPED", pattern_codes)
                        return True

        if broadcast_timer.time() >= BROADCAST_INTERVAL:
            broadcast_status(movement, pattern_codes)

        wait(CHECK_INTERVAL)

def handle_command(cmd):
    """
    Process a command fully. Returns True if we should stop current movement.
    """
    if not cmd or len(cmd) < 2:
        return False

    command_number = cmd[0]
    device_name = cmd[1]

    # Only process commands for this train that we haven't seen before
    if device_name == TRAIN_NAME and command_number not in processed_commands:
        if len(cmd) >= 3:
            command_type = cmd[2]
            print(f"Received command #{command_number}: {command_type}")

            if command_type == TRAIN_COMMAND["STOP"]:
                motor.brake()
                broadcast_status("STOPPED")
                processed_commands.add(command_number)
                return True

            elif command_type in [TRAIN_COMMAND["FORWARD_UNTIL_PATTERN"], 
                                TRAIN_COMMAND["BACKWARD_UNTIL_PATTERN"]]:
                if len(cmd) >= 4:  # Has pattern length
                    pattern_length = cmd[3]
                    if len(cmd) >= 4 + pattern_length:  # Has full pattern
                        pattern = list(cmd[4:4+pattern_length])
                        direction = 1 if command_type == TRAIN_COMMAND["FORWARD_UNTIL_PATTERN"] else -1
                        processed_commands.add(command_number)
                        move_until_pattern(direction, pattern)

    return False

print(f"{TRAIN_NAME}: Ready! Listening for commands...")

# Main loop - just listen for commands
while True:
    cmd = hub.ble.observe(COMMAND_CHANNEL)
    if cmd:
        handle_command(cmd)
    wait(50) # Short delay so we don't busy-loop
