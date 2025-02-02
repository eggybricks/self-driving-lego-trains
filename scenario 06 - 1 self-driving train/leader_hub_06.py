# Scenario 6: path planning for automated navigation between cities
# - five hubs attached to ten switches (broadcasting position and taking commands)
#    - hub 1 (close to LA): switch A (left switch, M motor) at Port A, switch B (right switch, L motor) at Port B
#    - hub 2 (close to Calgary) : switch C (right switch, M motor) at Port A, switch D (left switch, M motor) at Port B
#    - hub 3 (close to Kansas City): switch E (left switch reversed, L motor) at Port A, switch F (right switch, M motor), switch G (right switch reversed, L motor)
#    - hub 4 (close to NYC): switch H (left switch, M motor), switch I (right switch, L motor)
#    - hub 5 (close to Atlanta): switch J (left switch, M motor)
# - one hub attached to one train (broadcasting position as color patterns, taking commands)
# - one hub acting as the leader (computing full paths using breadth-first search, receiving position updates, sending commands)

from pybricks.hubs import InventorHub
from pybricks.parameters import Port, Color
from pybricks.tools import wait

# Broadcast channels
COMMAND_CHANNEL = 1     # Leader -> Switch/train hubs
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
    """Send command to train: forward/backward until color pattern or stop"""
    global command_number
    command_number += 1

    if command_type in [TRAIN_COMMAND["FORWARD_UNTIL_PATTERN"], 
                       TRAIN_COMMAND["BACKWARD_UNTIL_PATTERN"]]:
        pattern_codes = [TRAIN_COLOR_CODES[color] for color in pattern]
        command = (command_number, train_name, command_type, 
                  len(pattern_codes)) + tuple(pattern_codes)
    else:
        command = (command_number, train_name, command_type)

    pattern_str = f", pattern={pattern}" if pattern else ""
    print(f"Sending command #{command_number}: {train_name} -> {command_type}{pattern_str}")
    hub.ble.broadcast(command)

def parse_pattern(pattern_str):
    """Convert hyphen-separated color names to color objects"""
    colors = pattern_str.split('-')
    pattern = []

    for color_name in colors:
        color_name = color_name.upper()
        if color_name not in VALID_PATTERN_COLORS:
            print(f"Invalid color: {color_name}")
            print("Valid colors are:", ", ".join(VALID_PATTERN_COLORS.keys()))
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
    """Display current status of all devices"""
    print("\nPolling for status updates...")
    # Poll multiple times to catch updates that might otherwise be missed
    for _ in range(20):  # Poll for 1 second total (20 * 50ms)
        check_status_updates()
        wait(50)

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

# Track layout as a directed graph
# Each edge (track segment) has:
# - Basic graph properties: source, destination, distance
# - Train-specific properties: switches, color pattern, reversals needed after this segment
track = {
    ("LA", "LAS_VEGAS"): {
        "switches": {
            "SWITCH_A": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_B": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.BLUE, Color.RED),
        "reverse_for": ["LA"]  # After LAS_VEGAS
    },
    ("LAS_VEGAS", "LA"): {
        "switches": {},
        "pattern": (Color.YELLOW, Color.RED),
        "reverse_for": ["CALGARY", "LAS_VEGAS", "KANSAS_CITY"]  # After LA
    },
    ("LA", "CALGARY"): {
        "switches": {
            "SWITCH_A": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.YELLOW, Color.BLUE),
        "reverse_for": ["NYC", "KANSAS_CITY", "LA"]  # After CALGARY
    },
    ("CALGARY", "LA"): {
        "switches": {
            "SWITCH_C": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.YELLOW, Color.RED),
        "reverse_for": ["CALGARY", "LAS_VEGAS", "KANSAS_CITY"]  # After LA
    },
    ("CALGARY", "KANSAS_CITY"): {
        "switches": {
            "SWITCH_C": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_D": SWITCH_POSITION["STRAIGHT"]
        },
        "pattern": (Color.GREEN, Color.RED),
        "reverse_for": ["LAS_VEGAS", "LA"]  # After KANSAS_CITY
    },
    ("KANSAS_CITY", "CALGARY"): {
        "switches": {
            "SWITCH_F": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.YELLOW, Color.BLUE),
        "reverse_for": ["NYC", "KANSAS_CITY", "LA"]  # After CALGARY
    },
    ("LA", "KANSAS_CITY"): {
        "switches": {
            "SWITCH_A": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_B": SWITCH_POSITION["STRAIGHT"]
        },
        "pattern": (Color.GREEN, Color.RED),
        "reverse_for": ["LAS_VEGAS", "LA"]  # After KANSAS_CITY
    },
    ("KANSAS_CITY", "LA"): {
        "switches": {
            "SWITCH_F": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_E": SWITCH_POSITION["STRAIGHT"]
        },
        "pattern": (Color.YELLOW, Color.RED),
        "reverse_for": ["CALGARY", "LAS_VEGAS", "KANSAS_CITY"]  # After LA
    },
    ("LAS_VEGAS", "KANSAS_CITY"): {
        "switches": {},
        "pattern": (Color.GREEN, Color.RED),
        "reverse_for": ["LAS_VEGAS", "LA"]  # After KANSAS_CITY
    },
    ("KANSAS_CITY", "LAS_VEGAS"): {
        "switches": {
            "SWITCH_F": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_E": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.RED, Color.BLUE),
        "reverse_for": ["LA"]  # After LAS_VEGAS
    },
    ("CALGARY", "NYC"): {
        "switches": {
            "SWITCH_C": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_D": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.BLUE, Color.GREEN),
        "reverse_for": ["KANSAS_CITY", "ATLANTA", "CALGARY"]  # After NYC
    },
    ("NYC", "CALGARY"): {
        "switches": {
            "SWITCH_H": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_I": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.YELLOW, Color.BLUE),
        "reverse_for": ["NYC", "KANSAS_CITY", "LA"]  # After CALGARY
    },
    ("KANSAS_CITY", "NYC"): {
        "switches": {
            "SWITCH_G": SWITCH_POSITION["STRAIGHT"]
        },
        "pattern": (Color.BLUE, Color.GREEN),
        "reverse_for": ["KANSAS_CITY", "ATLANTA", "CALGARY"]  # After NYC
    },
    ("NYC", "KANSAS_CITY"): {
        "switches": {
            "SWITCH_H": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_I": SWITCH_POSITION["STRAIGHT"]
        },
        "pattern": (Color.RED, Color.GREEN),
        "reverse_for": ["NYC", "ATLANTA"]  # After KANSAS_CITY
    },
    ("KANSAS_CITY", "ATLANTA"): {
        "switches": {
            "SWITCH_G": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.YELLOW, Color.GREEN),
        "reverse_for": ["KANSAS_CITY", "ATLANTA"]  # After ATLANTA
    },
    ("ATLANTA", "KANSAS_CITY"): {
        "switches": {
            "SWITCH_J": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.RED, Color.GREEN),
        "reverse_for": ["NYC", "ATLANTA"]  # After KANSAS_CITY
    },
    ("NYC", "ATLANTA"): {
        "switches": {
            "SWITCH_H": SWITCH_POSITION["DIVERGING"]
        },
        "pattern": (Color.YELLOW, Color.GREEN),
        "reverse_for": ["KANSAS_CITY", "ATLANTA"]  # After ATLANTA
    },
    ("ATLANTA", "NYC"): {
        "switches": {
            "SWITCH_J": SWITCH_POSITION["STRAIGHT"]
        },
        "pattern": (Color.BLUE, Color.GREEN),
        "reverse_for": ["KANSAS_CITY", "ATLANTA", "CALGARY"]  # After NYC
    }
}

def find_path(start, end, initial_facing="FORWARD"):
    """
    Find path from start to end using Breadth-First Search (BFS).
    
    Core BFS concepts:
    1. Use a queue to explore nodes level by level
    2. Keep track of visited nodes to avoid cycles
    3. Build up the path as we go
    
    Train-specific additions:
    - Track train orientation at each node
    - Consider direction changes when determining valid next moves
    """
    # Get all cities (nodes) in the graph
    cities = set([x[0] for x in track.keys()] + [x[1] for x in track.keys()])

    # BFS queue: each entry is (city, path_so_far, train_facing)
    queue = [(start, [], initial_facing)]

    # Track visited states (need both city and train orientation to avoid cycles)
    visited = {(start, initial_facing)}

    # Core BFS loop
    while queue:
        # Get next node to explore
        current_city, path_so_far, train_facing = queue.pop(0)
        
        # If we've reached our destination, return the path
        if current_city == end:
            return path_so_far

        # Explore all possible next segments from current city
        for (src, dst), segment in track.items():
            if src == current_city:  # This segment starts at our current city
                # First handle core graph traversal
                new_path = path_so_far + [(src, dst)]

                # Then handle train-specific direction logic
                must_reverse = False
                if path_so_far:  # If we're not at the start
                    prev_segment = track[path_so_far[-1]]
                    must_reverse = dst in prev_segment["reverse_for"]

                new_facing = train_facing
                if must_reverse:
                    new_facing = "BACKWARD" if train_facing == "FORWARD" else "FORWARD"

                # Only explore this node if we haven't seen this city-orientation combination
                if (dst, new_facing) not in visited:
                    visited.add((dst, new_facing))
                    queue.append((dst, new_path, new_facing))

    # If we've explored everything and found no path, return empty list
    return []

def path_to_commands(path, initial_facing):
    """
    Convert a path (sequence of edges) into train and switch commands.
    This is separate from the core pathfinding - it handles the mechanics
    of actually moving the train along the found path.
    """
    commands = []
    current_facing = initial_facing

    # First set all switches to STRAIGHT for safety
    all_switches = set()
    for edge in track.values():
        all_switches.update(edge["switches"].keys())

    for switch in all_switches:
        commands.append({
            'type': 'switch',
            'switch': switch,
            'position': SWITCH_POSITION["STRAIGHT"]
        })

    # Convert each path segment into appropriate commands
    for i, (src, dst) in enumerate(path):
        segment = track[(src, dst)]
        
        # 1. Set required switches for this segment
        for switch, position in segment["switches"].items():
            commands.append({
                'type': 'switch',
                'switch': switch,
                'position': position
            })

        # 2. Determine if we need to reverse from previous segment
        must_reverse = False
        if i > 0:
            prev_segment = track[path[i-1]]
            must_reverse = dst in prev_segment["reverse_for"]

        if must_reverse:
            current_facing = "BACKWARD" if current_facing == "FORWARD" else "FORWARD"

        # 3. Create appropriate train movement command
        pattern = segment["pattern"]
        if current_facing == "BACKWARD":
            command_type = "BACKWARD_UNTIL_PATTERN"
            pattern = tuple(reversed(pattern))
        else:
            command_type = "FORWARD_UNTIL_PATTERN"

        commands.append({
            'type': 'train',
            'action': command_type,
            'pattern': pattern
        })

    return commands

def wait_for_switch_update(switch_name, target_position, command_number, timeout=5000):
    """Wait for switch status update confirming the switch reached desired position"""
    print(f"Waiting for {switch_name} to reach {'DIVERGING' if target_position else 'STRAIGHT'} position...")

    # Record current number of statuses we've processed
    initial_status_count = len(processed_statuses)

    interval = 100  # Check every 100ms
    elapsed = 0

    while elapsed < timeout:
        check_status_updates()

        # Check if we've received any new status updates since sending command
        if len(processed_statuses) > initial_status_count:
            if (switch_name in switch_states and
                switch_states[switch_name] == target_position):
                print(f"{switch_name} reached desired position!")
                return True

        wait(interval)
        elapsed += interval

    print(f"Warning: Timed out waiting for {switch_name} status update!")
    return False

def execute_switch_command(switch_name, position, max_retries=3):
    """Send switch command and verify it worked, with retries if needed"""
    global command_number

    for attempt in range(max_retries):
        if attempt > 0:
            print(f"Retry attempt {attempt}/{max_retries-1}...")

        # Send command
        send_switch_command(switch_name, position)
        command_num = command_number  # Save command number for verification
        wait(500)

        # Wait for status update from this specific command
        if wait_for_switch_update(switch_name, position, command_num):
            return True

        # If we reach here, the switch didn't report success
        if attempt < max_retries - 1:  # If we have retries left
            print(f"Switch {switch_name} didn't reach position, retrying...")
            wait(1000)  # Wait before retry

    return False

def execute_path(train_name, start, end, initial_facing="FORWARD"):
    """
    Main function to find and execute a path.
    Separates:
    1. Path finding (graph traversal)
    2. Command generation (train mechanics)
    3. Command execution (hardware control)
    """
    print(f"Planning route for {train_name} from {start} to {end} (initially facing {initial_facing})...")

    # First find the path using BFS
    path = find_path(start, end, initial_facing)

    if not path:
        print("No path found!")
        return

    # Then generate and display the plan
    print("\nPlanned route:")
    print("Initial move: Set all switches to STRAIGHT for safety")
    print(f"Train starts facing: {initial_facing}")

    current_facing = initial_facing
    for i, (src, dst) in enumerate(path):
        segment = track[(src, dst)]
        print(f"\nFrom {src} to {dst}:")

        # Show direction changes
        must_reverse = False
        if i > 0:
            prev_segment = track[path[i-1]]
            must_reverse = dst in prev_segment["reverse_for"]

        if must_reverse:
            current_facing = "BACKWARD" if current_facing == "FORWARD" else "FORWARD"
            print("- Must reverse direction at", src)

        print(f"- Train facing: {current_facing}")

        # Show switch settings
        if segment["switches"]:
            for switch, position in segment["switches"].items():
                print("- Set {0} to {1}".format(
                    switch,
                    "DIVERGING" if position == SWITCH_POSITION["DIVERGING"] else "STRAIGHT"
                ))

        # Show pattern to watch for
        pattern = segment["pattern"]
        if current_facing == "BACKWARD":
            pattern = tuple(reversed(pattern))

        colors = "-".join(str(c).split('.')[-1] for c in pattern)
        print("- Look for pattern: {0}".format(colors))

    # Finally, execute the commands if confirmed
    if input("\nExecute route? (y/n): ").lower() != 'y':
        return

    commands = path_to_commands(path, current_facing)

    for i, cmd in enumerate(commands):
        print("\nExecuting command {0}/{1}...".format(i + 1, len(commands)))

        if cmd['type'] == 'switch':
            if not execute_switch_command(cmd['switch'], cmd['position']):
                print(f"Failed to set {cmd['switch']} after all retries!")
                if input("Continue anyway? (y/n): ").lower() != 'y':
                    return

        elif cmd['type'] == 'train':
            pattern = cmd['pattern']
            print("Looking for pattern: {0}".format(
                "-".join(str(c).split('.')[-1] for c in pattern)
            ))

            send_train_command(train_name, TRAIN_COMMAND[cmd['action']], pattern)

            # Wait for movement to complete
            print("Waiting for train to complete movement...")
            wait(1000)  # Initial wait to let train start moving

            timeout = 30000  # 30 second timeout
            interval = 100   # Check every 100ms
            elapsed = 0

            movement_complete = False
            while elapsed < timeout:
                check_status_updates()
                if (train_name in train_states and 
                    train_states[train_name]["movement"] == "STOPPED"):
                    print("Movement completed!")
                    wait(1000)  # Extra wait to ensure train is fully stopped
                    movement_complete = True
                    break
                wait(interval)
                elapsed += interval
            
            if not movement_complete:
                print("Warning: Movement timed out after 30 seconds!")
                if input("Continue anyway? (y/n): ").lower() != 'y':
                    return

print("Leader hub ready!")
print("Commands:")
print("Pathfinding:")
print("  p train start end    - Find and execute path (e.g., p csx la nyc)")
print("  p train start end b  - Optionally, specify that the train is facing backwards")
print("                         Valid locations: LA, CALGARY, NYC, ATLANTA, LAS_VEGAS, KANSAS_CITY")
print("Switches:")
print("  s a 0 - Set LA switch (A) to straight")
print("  s a 1 - Set LA switch (A) to diverging")
print("  (same for switches B-J)")
print("Train:")
print("  t csx f red-yellow   - Move CSX train forward until RED-YELLOW pattern")
print("  t csx b yellow-green - Move CSX train backward until YELLOW-GREEN pattern")
print("  t csx s              - Stop CSX train")
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
    elif cmd.startswith('p '):  # p train start end [backwards]
        parts = cmd.split()
        if len(parts) >= 4:
            train = f"TRAIN_{parts[1].upper()}"
            start = parts[2].upper()
            end = parts[3].upper()
            # Check for optional 'backwards' flag
            initial_facing = "BACKWARD" if (len(parts) > 4 and parts[4].lower() in ['backwards', 'backward', 'b']) else "FORWARD"
            execute_path(train, start, end, initial_facing)
        else:
            print("Invalid path command. Use: p train start end [backwards]")
            print("Example: p csx la nyc")
            print("Example: p csx la nyc backwards")
    else:
        print("Invalid command")

    wait(50) # Short delay so we don't busy-loop
