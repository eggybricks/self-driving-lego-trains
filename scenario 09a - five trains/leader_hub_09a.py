# Scenario 9a: full multi-train control with path planning using A*
# - five hubs attached to ten switches (broadcasting position and taking commands)
#    - hub 1 (close to LA): switch A (left switch, M motor) at Port A, switch B (right switch, L motor) at Port B
#    - hub 2 (close to Calgary) : switch C (right switch, M motor) at Port A, switch D (left switch, M motor) at Port B
#    - hub 3 (close to Kansas City): switch E (left switch reversed, L motor) at Port A, switch F (right switch, M motor), switch G (right switch reversed, L motor)
#    - hub 4 (close to NYC): switch H (left switch, M motor), switch I (right switch, L motor)
#    - hub 5 (close to Atlanta): switch J (left switch, M motor)
# - five hubs attached to five trains (broadcasting position as color patterns, taking commands)
# - one hub acting as the leader (computing full paths for multiple trains and switches using A*, receiving position updates, sending commands)

from pybricks.hubs import InventorHub
from pybricks.parameters import Port, Color
from pybricks.tools import wait

###########################################
# 1. CONSTANTS AND CONFIGURATIONS
###########################################

# Broadcast channels
COMMAND_CHANNEL = 1     # Leader -> All hubs
SWITCH_STATUS_1 = 11    # Switch hub 1 -> leader
SWITCH_STATUS_2 = 12    # Switch hub 2 -> leader
SWITCH_STATUS_3 = 13    # Switch hub 3 -> leader
SWITCH_STATUS_4 = 14    # Switch hub 4 -> leader
SWITCH_STATUS_5 = 15    # Switch hub 5 -> leader
TRAIN_STATUS_CSX = 21   # CSX train -> leader
TRAIN_STATUS_UP = 22    # UP train -> leader
TRAIN_STATUS_CN = 23    # CN train -> leader
TRAIN_STATUS_BNSF = 24  # BNSF train -> leader
TRAIN_STATUS_NS = 25    # NS train -> leader

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

# Train movement codes (for status messages)
TRAIN_MOVEMENT_CODES = {
    "STOPPED": 0,
    "FORWARD": 1,
    "BACKWARD": 2
}
TRAIN_MOVEMENT_FROM_CODE = {
    0: "STOPPED",
    1: "FORWARD",
    2: "BACKWARD"
}

# Color codes (for status messages)
TRAIN_COLOR_CODES = {
    Color.NONE: 0,
    Color.RED: 1,
    Color.YELLOW: 2, 
    Color.GREEN: 3,
    Color.BLUE: 4,
    Color.GRAY: 5,
    Color.WHITE: 6
}
TRAIN_COLOR_FROM_CODE = {
    0: Color.NONE,
    1: Color.RED,
    2: Color.YELLOW,
    3: Color.GREEN,
    4: Color.BLUE,
    5: Color.GRAY,
    6: Color.WHITE
}

# Location types and orientations
LOCATION_CITY = "CITY"
LOCATION_SEGMENT = "SEGMENT"
ORIENTATION_FORWARD = "FORWARD"
ORIENTATION_BACKWARD = "BACKWARD"

###########################################
# 2. TRACK LAYOUT DEFINITION
###########################################

# City connectivity for pathfinding
city_connectivity = {
    "LA": ["LAS_VEGAS", "CALGARY", "KANSAS_CITY"],
    "LAS_VEGAS": ["LA", "KANSAS_CITY"],
    "CALGARY": ["LA", "KANSAS_CITY", "NYC"],
    "KANSAS_CITY": ["LA", "LAS_VEGAS", "CALGARY", "NYC", "ATLANTA"],
    "NYC": ["CALGARY", "KANSAS_CITY", "ATLANTA"],
    "ATLANTA": ["KANSAS_CITY", "NYC"]
}

# Complete track layout with patterns and switch configurations
track = {
    ("LA", "LAS_VEGAS"): {
        "switches": {
            "SWITCH_A": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_B": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near Las Vegas
            "approach": (Color.RED, Color.YELLOW, Color.GREEN),
            "at_city": (Color.BLUE, Color.RED)
        },
        "distance": 100,
        "reverse_for": ["LA"]
    },
    ("LAS_VEGAS", "LA"): {
        "switches": {},
        "patterns": {  # Patterns near LA
            "approach": (Color.GREEN, Color.YELLOW, Color.RED),
            "at_city": (Color.YELLOW, Color.RED)
        },
        "distance": 100,
        "reverse_for": ["CALGARY", "LAS_VEGAS", "KANSAS_CITY"]
    },
    ("LA", "CALGARY"): {
        "switches": {
            "SWITCH_A": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near Calgary
            "approach": (Color.RED, Color.BLUE, Color.YELLOW),
            "at_city": (Color.YELLOW, Color.BLUE)
        },
        "distance": 224,
        "reverse_for": ["NYC", "KANSAS_CITY", "LA"]
    },
    ("CALGARY", "LA"): {
        "switches": {
            "SWITCH_C": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near LA
            "approach": (Color.BLUE, Color.YELLOW, Color.RED),
            "at_city": (Color.YELLOW, Color.RED)
        },
        "distance": 224,
        "reverse_for": ["CALGARY", "LAS_VEGAS", "KANSAS_CITY"]
    },
    ("CALGARY", "KANSAS_CITY"): {
        "switches": {
            "SWITCH_C": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_D": SWITCH_POSITION["STRAIGHT"]
        },
        "patterns": {  # Patterns near Kansas City
            "approach": (Color.YELLOW, Color.GREEN, Color.BLUE),
            "at_city": (Color.GREEN, Color.RED)
        },
        "distance": 212,
        "reverse_for": ["LAS_VEGAS", "LA"]
    },
    ("KANSAS_CITY", "CALGARY"): {
        "switches": {
            "SWITCH_F": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near Calgary
            "approach": (Color.GREEN, Color.BLUE, Color.YELLOW),
            "at_city": (Color.YELLOW, Color.BLUE)
        },
        "distance": 212,
        "reverse_for": ["NYC", "KANSAS_CITY", "LA"]
    },
    ("LA", "KANSAS_CITY"): {
        "switches": {
            "SWITCH_A": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_B": SWITCH_POSITION["STRAIGHT"]
        },
        "patterns": {  # Patterns near Kansas City
            "approach": (Color.RED, Color.BLUE, Color.GREEN),
            "at_city": (Color.GREEN, Color.RED)
        },
        "distance": 200,
        "reverse_for": ["LAS_VEGAS", "LA"]
    },
    ("KANSAS_CITY", "LA"): {
        "switches": {
            "SWITCH_F": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_E": SWITCH_POSITION["STRAIGHT"]
        },
        "patterns": {  # Patterns near LA
            "approach": (Color.GREEN, Color.BLUE, Color.RED),
            "at_city": (Color.YELLOW, Color.RED)
        },
        "distance": 200,
        "reverse_for": ["CALGARY", "LAS_VEGAS", "KANSAS_CITY"]
    },
    ("LAS_VEGAS", "KANSAS_CITY"): {
        "switches": {},
        "patterns": {  # Patterns near Kansas City
            "approach": (Color.RED, Color.GREEN, Color.YELLOW),
            "at_city": (Color.GREEN, Color.RED)
        },
        "distance": 108,
        "reverse_for": ["LAS_VEGAS", "LA"]
    },
    ("KANSAS_CITY", "LAS_VEGAS"): {
        "switches": {
            "SWITCH_F": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_E": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near Las Vegas
            "approach": (Color.YELLOW, Color.GREEN, Color.RED),
            "at_city": (Color.RED, Color.BLUE)
        },
        "distance": 108,
        "reverse_for": ["LA"]
    },
    ("CALGARY", "NYC"): {
        "switches": {
            "SWITCH_C": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_D": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near NYC
            "approach": (Color.RED, Color.YELLOW, Color.BLUE, Color.GREEN),
            "at_city": (Color.BLUE, Color.GREEN)
        },
        "distance": 328,
        "reverse_for": ["KANSAS_CITY", "ATLANTA", "CALGARY"]
    },
    ("NYC", "CALGARY"): {
        "switches": {
            "SWITCH_H": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_I": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near Calgary
            "approach": (Color.BLUE, Color.GREEN, Color.YELLOW, Color.RED),
            "at_city": (Color.YELLOW, Color.BLUE)
        },
        "distance": 328,
        "reverse_for": ["NYC", "KANSAS_CITY", "LA"]
    },
    ("KANSAS_CITY", "NYC"): {
        "switches": {
            "SWITCH_G": SWITCH_POSITION["STRAIGHT"]
        },
        "patterns": {  # Patterns near NYC
            "approach": (Color.RED, Color.GREEN, Color.BLUE),
            "at_city": (Color.BLUE, Color.GREEN)
        },
        "distance": 128,
        "reverse_for": ["KANSAS_CITY", "ATLANTA", "CALGARY"]
    },
    ("NYC", "KANSAS_CITY"): {
        "switches": {
            "SWITCH_H": SWITCH_POSITION["STRAIGHT"],
            "SWITCH_I": SWITCH_POSITION["STRAIGHT"]
        },
        "patterns": {  # Patterns near Kansas City
            "approach": (Color.BLUE, Color.GREEN, Color.RED),
            "at_city": (Color.RED, Color.GREEN)
        },
        "distance": 128,
        "reverse_for": ["NYC", "ATLANTA"]
    },
    ("KANSAS_CITY", "ATLANTA"): {
        "switches": {
            "SWITCH_G": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near Atlanta
            "approach": (Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW),
            "at_city": (Color.YELLOW, Color.GREEN)
        },
        "distance": 192,
        "reverse_for": ["KANSAS_CITY", "ATLANTA"]
    },
    ("ATLANTA", "KANSAS_CITY"): {
        "switches": {
            "SWITCH_J": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near Kansas City
            "approach": (Color.BLUE, Color.YELLOW, Color.GREEN, Color.RED),
            "at_city": (Color.RED, Color.GREEN)
        },
        "distance": 192,
        "reverse_for": ["NYC", "ATLANTA"]
    },
    ("NYC", "ATLANTA"): {
        "switches": {
            "SWITCH_H": SWITCH_POSITION["DIVERGING"]
        },
        "patterns": {  # Patterns near Atlanta
            "approach": (Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW),
            "at_city": (Color.YELLOW, Color.GREEN)
        },
        "distance": 188,
        "reverse_for": ["KANSAS_CITY", "ATLANTA"]
    },
    ("ATLANTA", "NYC"): {
        "switches": {
            "SWITCH_J": SWITCH_POSITION["STRAIGHT"]
        },
        "patterns": {  # Patterns near NYC
            "approach": (Color.GREEN, Color.YELLOW, Color.BLUE, Color.RED),
            "at_city": (Color.BLUE, Color.GREEN)
        },
        "distance": 188,
        "reverse_for": ["KANSAS_CITY", "ATLANTA", "CALGARY"]
    }
}

###########################################
# 3. BASIC CLASSES AND HELPER FUNCTIONS
###########################################

class Location:
    """A train can be either at a city or on a track segment"""
    def __init__(self, type, value):
        self.type = type  # LOCATION_CITY or LOCATION_SEGMENT
        self.value = value  # city name or (city1, city2) segment tuple
        
    def __eq__(self, other):
        return self.type == other.type and self.value == other.value
        
    def __hash__(self):
        return hash((self.type, self.value if self.type == LOCATION_CITY 
                    else tuple(sorted(self.value))))

class TrainState:
    """State of a single train"""
    def __init__(self, location, orientation=ORIENTATION_FORWARD):
        self.location = location
        self.orientation = orientation
        
    def __eq__(self, other):
        return self.location == other.location
        
    def __hash__(self):
        return hash(self.location)

class TrackState:
    """Complete state of all trains and switches"""
    def __init__(self, trains, switches):  # Removed move_number parameter
        self.trains = trains  # Dict mapping train names to TrainState
        self.switches = switches  # Dict mapping switch names to positions
        
    def __eq__(self, other):
        return (self.trains == other.trains and 
                self.switches == other.switches)
        
    def __hash__(self):
        trains_tuple = tuple(sorted(
            (name, state.location.type, 
             state.location.value if state.location.type == LOCATION_CITY
             else tuple(sorted(state.location.value)))
            for name, state in self.trains.items()
        ))
        switches_tuple = tuple(sorted(self.switches.items()))
        return hash((trains_tuple, switches_tuple))

class PriorityQueue:
    """Simple priority queue for A* search"""
    def __init__(self):
        self._items = []  # List of (priority, count, state, cost, path) tuples
        self._count = 0  # Unique count for same-priority ordering
    
    def push(self, item, priority):
        """
        Push an item with given priority.
        Lower priority numbers are handled first.
        """
        # item is (g, state, path)
        g, state, path = item
        entry = (priority, self._count, g, state, path)
        self._count += 1
        self._items.append(entry)
        self._items.sort()  # Sort by priority (first element of tuple)
    
    def pop(self):
        """Remove and return the lowest priority item."""
        if self.empty():
            raise IndexError("Queue is empty")
        # Return (g, state, path) from the stored tuple
        _, _, g, state, path = self._items.pop(0)
        return g, state, path
    
    def empty(self):
        """Return True if queue is empty."""
        return len(self._items) == 0

def compute_all_distances():
    distances = {}
    cities = set()

    # Collect all cities
    for city1, neighbors in city_connectivity.items():
        cities.add(city1)
        for city2 in neighbors:
            cities.add(city2)

    # Initialize distances with direct segment lengths
    for (city1, city2), segment_info in track.items():
        dist = segment_info["distance"]
        distances[(city1, city2)] = dist
        distances[(city2, city1)] = dist

    print("Initial distances:")
    for (c1, c2), dist in sorted(distances.items()):
        print(f"{c1}->{c2}: {dist}")

    # Floyd-Warshall algorithm to find all shortest paths
    for k in cities:
        for i in cities:
            for j in cities:
                dist_ik = distances.get((i, k), float('inf'))
                dist_kj = distances.get((k, j), float('inf'))
                dist_ij = distances.get((i, j), float('inf'))
                if dist_ik + dist_kj < dist_ij:
                    distances[(i, j)] = dist_ik + dist_kj

    print("\nFinal distances:")
    for (c1, c2), dist in sorted(distances.items()):
        print(f"{c1}->{c2}: {dist}")

    return distances

def get_min_distance(city1, city2):
    """Get actual minimum distance between cities using precomputed distances"""
    global all_distances

    if city1 == city2:
        return 0
    return all_distances.get((city1, city2), float('inf'))

def get_connected_segments(city):
    """Get all segments that START at this city"""
    connected = []
    for (city1, city2), segment_info in track.items():
        if city1 == city:
            connected.append((city1, city2))
        # Only add reverse direction if explicitly present
        if city2 == city and (city2, city1) in track:
            connected.append((city2, city1))
    return connected

###########################################
# 4. PATHFINDING IMPLEMENTATION
###########################################

def get_valid_moves(state, train, goals):
    """Get valid moves for a single train"""
    valid_moves = []
    train_state = state.trains[train]

    if train_state.location.type == LOCATION_CITY:
        # Moving from city to segment
        city = train_state.location.value

        for segment in get_connected_segments(city):
            # Check if segment is safely usable
            can_use = True
            for other_train, other_state in state.trains.items():
                if other_train != train:
                    # Can't use segment if:
                    # 1. Another train is on this segment
                    # 2. Another train is in a city we need
                    if (other_state.location.type == LOCATION_SEGMENT and 
                        other_state.location.value == segment):
                        can_use = False
                        break

                    if (other_state.location.type == LOCATION_CITY and
                        other_state.location.value in segment):
                        can_use = False
                        break

                    # Check if other train is on a segment connected to either of our endpoints
                    if other_state.location.type == LOCATION_SEGMENT:
                        other_cities = other_state.location.value
                        # If other train's segment shares any city with our desired segment
                        if (other_cities[0] in segment or 
                            other_cities[1] in segment):
                            can_use = False
                            break

            if can_use:
                new_switches = {}
                for switch, position in track[segment]["switches"].items():
                    new_switches[switch] = position

                # Get actual segment distance from track layout
                segment_distance = track[segment]["distance"]

                valid_moves.append({
                    'location': Location(LOCATION_SEGMENT, segment),
                    'switches': new_switches,
                    'cost': segment_distance / 100.0
                })
    
    else:  # Moving from segment to city
        segment = train_state.location.value
        for end_city in segment:
            # Can move to a city if:
            # 1. No train is there
            # 2. No train is on a segment connected to this city (except us)
            can_use = True
            for other_train, other_state in state.trains.items():
                if other_train != train:
                    if (other_state.location.type == LOCATION_CITY and
                        other_state.location.value == end_city):
                        can_use = False
                        break

                    # Check if other train is on any segment connected to this city
                    if other_state.location.type == LOCATION_SEGMENT:
                        other_cities = other_state.location.value
                        if end_city in other_cities:
                            can_use = False
                            break

            if can_use:
                valid_moves.append({
                    'location': Location(LOCATION_CITY, end_city),
                    'switches': {},
                    'cost': 0.0
                })

    return valid_moves

def heuristic(state, goals):
    """Heuristic based on actual minimum distances to goals"""
    total = 0

    for train, goal in goals.items():
        train_state = state.trains[train]
        if train_state.location.type == LOCATION_CITY:
            # Direct distance to goal from current city
            total += get_min_distance(train_state.location.value, goal)
        else:
            # If on segment, use distance from destination city to goal
            _, dest_city = train_state.location.value
            total += get_min_distance(dest_city, goal)

    return total

def get_move_cost(current_state, next_state, train, goals):
    """Calculate move cost based on actual distances and switch changes"""
    current_loc = current_state.trains[train].location
    next_loc = next_state.trains[train].location

    # Calculate distance cost
    if current_loc.type == LOCATION_CITY and next_loc.type == LOCATION_SEGMENT:
        # Moving from city onto segment - use actual track distance
        city1, city2 = next_loc.value
        cost = track[(city1, city2)]["distance"] / 100.0  # Scale to reasonable cost
    elif current_loc.type == LOCATION_SEGMENT and next_loc.type == LOCATION_CITY:
        # Moving from segment to city - cost already counted when entering segment
        cost = 0.0
    else:
        cost = 0.0

    # Add scaled switch change penalty
    switch_changes = sum(1 for switch, pos in next_state.switches.items()
                        if switch not in current_state.switches or 
                        current_state.switches[switch] != pos)
    cost += switch_changes * 0.1  # Small penalty for switch changes

    return cost

def find_paths(initial_state, goals, max_depth=100):
    """Find shortest paths using A* search with enhanced heuristics"""
    queue = PriorityQueue()

    g = 0
    h = heuristic(initial_state, goals)

    queue.push((g, initial_state, []), g + h)
    visited = set([initial_state])

    states_explored = 0
    while not queue.empty() and states_explored < max_depth:
        g, current_state, path = queue.pop()
        states_explored += 1

        print(f"\nExploring state {states_explored} (cost {g:.1f}):")
        for train_name, train_state in current_state.trains.items():
            if train_name in goals:
                print(f"  {train_name}: {train_state.location.value}")

        # Check if we've reached goals
        all_at_goals = True
        for train, goal in goals.items():
            train_state = current_state.trains[train]
            if (train_state.location.type != LOCATION_CITY or
                train_state.location.value != goal):
                all_at_goals = False
                break

        if all_at_goals:
            print(f"Found solution after exploring {states_explored} states")
            return path + [current_state]

        # Try moving each train that isn't at its goal
        for train in goals:
            train_state = current_state.trains[train]
            if (train_state.location.type == LOCATION_CITY and 
                train_state.location.value == goals[train]):
                continue

            moves = get_valid_moves(current_state, train, goals)

            for move in moves:
                new_trains = current_state.trains.copy()
                new_trains[train] = TrainState(
                    move['location'],
                    current_state.trains[train].orientation
                )

                next_state = TrackState(new_trains, move['switches'])

                if next_state not in visited:
                    visited.add(next_state)
                    new_g = g + get_move_cost(current_state, next_state, train, goals)
                    new_h = heuristic(next_state, goals)
                    new_f = new_g + new_h

                    print(f"  Adding move (f={new_f:.1f}, h={new_h:.1f}):")
                    print(f"    {train}: moves to {move['location'].value}")

                    queue.push((new_g, next_state, path + [current_state]), new_f)

    print(f"Search stopped after exploring {states_explored} states")
    return None

def process_path_for_reversals(path, train, goal):
    """Process a path to determine where reversals are needed"""
    commands = []
    orientation = path[0].trains[train].orientation
    print(f"\nDEBUG: Starting path processing for {train} with orientation {orientation}")
    
    for i in range(len(path) - 1):
        current_state = path[i]
        next_state = path[i + 1]
        
        curr_train = current_state.trains[train]
        next_train = next_state.trains[train]
        
        print(f"\nDEBUG: Step {i}: Train {train} orientation={orientation}")
        print(f"DEBUG: Current location: {curr_train.location.value}")
        print(f"DEBUG: Next location: {next_train.location.value}")
        
        # Only process if train actually moved
        if curr_train == next_train:
            print("DEBUG: Train didn't move this step, continuing...")
            continue
        
        # Handle switch changes first
        if next_train.location.type == LOCATION_SEGMENT:
            segment = next_train.location.value
            print(f"DEBUG: Moving onto segment {segment}")
            for switch, pos in track[segment]["switches"].items():
                if switch not in current_state.switches or current_state.switches[switch] != pos:
                    commands.append({
                        'type': 'switch',
                        'switch': switch,
                        'position': pos
                    })
        
        # Now handle train movement
        if next_train.location.type == LOCATION_SEGMENT:
            # Moving onto segment
            segment = next_train.location.value
            print(f"DEBUG: Orientation when starting segment: {orientation}")
            commands.append({
                'type': 'train',
                'train': train,
                'action': ("FORWARD_UNTIL_PATTERN" 
                          if orientation == ORIENTATION_FORWARD
                          else "BACKWARD_UNTIL_PATTERN"),
                'pattern': track[segment]["patterns"]["approach"]
            })

        else:  # Moving to city
            if curr_train.location.type != LOCATION_SEGMENT:
                continue
                
            # Moving to city - get current segment and pattern
            current_segment = curr_train.location.value
            last_segment = current_segment  # Store it before we lose it
            print(f"DEBUG: Moving to city {next_train.location.value} from segment {current_segment}")
            pattern = track[current_segment]["patterns"]["at_city"]

            # First, add command to reach the city
            commands.append({
                'type': 'train',
                'train': train,
                'action': ("FORWARD_UNTIL_PATTERN"
                          if orientation == ORIENTATION_FORWARD
                          else "BACKWARD_UNTIL_PATTERN"),
                'pattern': pattern
            })

            # Now look ahead to find the next segment
            print(f"DEBUG: About to start look-ahead scan from i={i}, path length={len(path)}")
            next_segment_found = False
            scan_idx = i + 2  # Start looking 2 states ahead
            while scan_idx < len(path):
                print(f"DEBUG: Scanning state {scan_idx}")
                scan_state = path[scan_idx].trains[train]
                print(f"DEBUG: Found location type: {scan_state.location.type}")
                if scan_state.location.type == LOCATION_SEGMENT:
                    next_segment_found = True
                    next_segment = scan_state.location.value
                    print(f"DEBUG: Found next segment: {next_segment}")
                    # Get where we're ultimately going in this next segment
                    current_city = next_train.location.value
                    destination_city = (next_segment[1] if next_segment[0] == current_city 
                                      else next_segment[0])
                    print(f"DEBUG: Last segment {last_segment} reverse_for list: {track[last_segment]['reverse_for']}")
                    print(f"DEBUG: Next segment {next_segment} goes from {next_segment[0]} to {next_segment[1]}")
                    print(f"DEBUG: Current city is {current_city}, next destination is {destination_city}")
                    needs_reversal = destination_city in track[last_segment]["reverse_for"]
                    print(f"DEBUG: {destination_city} in reverse_for list? {needs_reversal}")
                    print(f"DEBUG: Current orientation is {orientation}")
                    print(f"DEBUG: Will need reversal? {needs_reversal != (orientation == ORIENTATION_BACKWARD)}")
                    if needs_reversal != (orientation == ORIENTATION_BACKWARD):
                        print("DEBUG: Adding reverse command")
                        commands.append({'type': 'reverse'})
                        orientation = ORIENTATION_BACKWARD if needs_reversal else ORIENTATION_FORWARD
                        next_state.trains[train].orientation = orientation
                        print(f"DEBUG: New orientation is {orientation}")
                    break
                scan_idx += 1

            if not next_segment_found:
                print("DEBUG: No next segment found - this must be the last move")

    return commands

###########################################
# 5. COMMAND EXECUTION
###########################################

def send_switch_command(switch_name, position):
    """Send command to switch"""
    global command_number
    command_number += 1
    position_str = 'DIVERGING' if position else 'STRAIGHT'
    print(f"Sending command #{command_number}: {switch_name} -> {position_str}")
    hub.ble.broadcast((command_number, switch_name, position))

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

def send_train_command(train_name, command_type, pattern=None):
    """Send command to train"""
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

def check_status_updates():
    """Check for status updates from all hubs"""
    for channel in [SWITCH_STATUS_1, SWITCH_STATUS_2, SWITCH_STATUS_3, 
                   SWITCH_STATUS_4, SWITCH_STATUS_5, TRAIN_STATUS_CSX,
                   TRAIN_STATUS_UP, TRAIN_STATUS_CN, TRAIN_STATUS_BNSF,
                   TRAIN_STATUS_NS, TRAIN_STATUS_CM]:
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
                
                elif channel in [TRAIN_STATUS_CSX, TRAIN_STATUS_UP, TRAIN_STATUS_CN, TRAIN_STATUS_BNSF, TRAIN_STATUS_NS, TRAIN_STATUS_CM]:
                    train_name = status[1]
                    color_code = status[2]
                    movement_code = status[3]
                    
                    train_states[train_name] = {
                        'movement': TRAIN_MOVEMENT_FROM_CODE[movement_code],
                        'color': TRAIN_COLOR_FROM_CODE[color_code]
                    }
                    
                    print(f"Updated {train_name} status")
                
                processed_statuses.add(status_id)
            
            if len(processed_statuses) > 100:
                processed_statuses.clear()

def merge_train_commands(commands_by_train, path):
    """Merge commands from multiple trains into a single ordered sequence"""
    # Map each command to its path step
    command_steps = {}  # Maps (train, command_index) -> path_step
    
    for train, commands in commands_by_train.items():
        step = 0
        for i, cmd in enumerate(commands):
            command_steps[(train, i)] = step
            # Only increment step after movement commands that are "approach" patterns
            # (i.e., start of segment movement)
            if (cmd['type'] == 'train' and 
                i + 1 < len(commands) and
                commands[i + 1]['type'] == 'train'):  # If there's a following train command
                step += 1
    
    # Create merged sequence
    merged_commands = []
    execution_order = []
    unprocessed = {train: list(range(len(commands))) 
                  for train, commands in commands_by_train.items()}
    
    while any(unprocessed.values()):
        candidates = []
        for train, indices in unprocessed.items():
            if not indices:
                continue
            cmd_idx = indices[0]
            candidates.append((train, cmd_idx))
        
        if not candidates:
            raise Exception("Deadlock detected in command ordering!")
        
        # Choose command with earliest path step
        chosen = min(candidates, key=lambda x: command_steps[x])
        train, cmd_idx = chosen
        
        # Add to execution order
        execution_order.append(chosen)
        unprocessed[train].pop(0)
    
    # Convert execution order to merged command list with global numbering
    command_number = 1
    for train, cmd_idx in execution_order:
        cmd = commands_by_train[train][cmd_idx]
        merged_dict = {'number': command_number, 'train': train}
        merged_dict.update(cmd)
        merged_commands.append(merged_dict)
        command_number += 1
    
    return merged_commands

def print_merged_commands(merged_commands):
    """Print the complete sequence of moves for all trains"""
    print("\nComplete sequence of moves:")
    for cmd in merged_commands:
        if cmd['type'] == 'switch':
            print(f"{cmd['number']}. Set {cmd['switch']} to {'DIVERGING' if cmd['position'] else 'STRAIGHT'}")
        elif cmd['type'] == 'reverse':
            print(f"{cmd['number']}. {cmd['train']}: Reverse orientation")
        elif cmd['type'] == 'train':
            pattern_str = '-'.join(str(c).split('.')[-1] for c in cmd['pattern'])
            print(f"{cmd['number']}. {cmd['train']}: Move {cmd['action'].split('_')[0].lower()} until pattern {pattern_str}")

def execute_multi_train_path(initial_positions, goals):
    """Find and execute paths for multiple trains"""
    print(f"Planning routes for {len(goals)} trains...")
    for train, goal in goals.items():
        current = (initial_positions[train] if train in initial_positions 
                  else "unknown position")
        print(f"- {train}: {current} -> {goal}")
    
    # Create initial state
    initial_state = TrackState(
        trains={
            train: TrainState(
                Location(LOCATION_CITY, pos) if isinstance(pos, str)
                else Location(LOCATION_SEGMENT, pos)
            )
            for train, pos in initial_positions.items()
        },
        switches=switch_states.copy()  # Removed move_number=0
    )
    
    # Find shortest paths ignoring orientation
    path = find_paths(initial_state, goals)
    
    if not path:
        print("No valid path found!")
        return
        
    # Process path for each train to determine reversals
    print("\nGenerating commands...")
    commands_by_train = {}
    for train in goals:
        commands = process_path_for_reversals(path, train, goals[train])
        if commands:
            commands_by_train[train] = commands
    
    # Merge commands into properly ordered sequence
    merged_commands = merge_train_commands(commands_by_train, path)
    print_merged_commands(merged_commands)
    
    if input("\nExecute route? (y/n): ").lower() != 'y':
        return
    
    # Execute merged commands in order
    for cmd in merged_commands:
        print(f"\nExecuting command {cmd['number']}/{len(merged_commands)}")
        
        if cmd['type'] == 'switch':
            if not execute_switch_command(cmd['switch'], cmd['position']):
                print(f"Failed to set {cmd['switch']} after all retries!")
                if input("Continue anyway? (y/n): ").lower() != 'y':
                    return
        
        elif cmd['type'] == 'train':
            pattern = cmd['pattern']
            print(f"Looking for pattern: {'-'.join(str(c).split('.')[-1] for c in pattern)}")
            send_train_command(cmd['train'], TRAIN_COMMAND[cmd['action']], pattern)
            
            # Wait for movement to complete
            print("Waiting for train to complete movement...")
            wait(1000)  # Initial wait to let train start moving

            timeout = 30000  # 30 second timeout
            interval = 100   # Check every 100ms
            elapsed = 0

            movement_complete = False
            while elapsed < timeout:
                check_status_updates()
                if (cmd['train'] in train_states and 
                    train_states[cmd['train']]["movement"] == "STOPPED"):
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

###########################################
# 6. INITIALIZATION AND MAIN LOOP
###########################################

# Initialize hub
print("\x1b[H\x1b[2J", end="")  # Clear terminal
hub = InventorHub(broadcast_channel=COMMAND_CHANNEL,
                  observe_channels=[SWITCH_STATUS_1, SWITCH_STATUS_2, 
                                  SWITCH_STATUS_3, SWITCH_STATUS_4, 
                                  SWITCH_STATUS_5, TRAIN_STATUS_CSX,
                                  TRAIN_STATUS_UP, TRAIN_STATUS_CN,
                                  TRAIN_STATUS_BNSF, TRAIN_STATUS_NS,
                                  TRAIN_STATUS_CM])

# Initialize state
switch_states = {}
train_states = {}
command_number = 0
processed_statuses = set()

# Precompute distances
print("Precomputing shortest path distances...")
all_distances = compute_all_distances()
print("Distance computation complete!")

# Validate track definition
print("Validating track layout...")
validation_errors = []
for segment, info in track.items():
    # Check that we have both patterns
    if "approach" not in info["patterns"]:
        validation_errors.append(f"Missing approach pattern for segment {segment}")
    if "at_city" not in info["patterns"]:
        validation_errors.append(f"Missing at_city pattern for segment {segment}")

if validation_errors:
    print("Track validation errors:")
    for error in validation_errors:
        print(f"- {error}")
    print("Please fix track definition!")
else:
    print("Track layout valid!")

# Main command loop
print("\nLeader hub ready!")
print("Commands:")
print("Multi-train pathfinding:")
print("  m - Start multi-train movement")
print("Switches:")
print("  s a 0 - Set switch A to straight")
print("  s a 1 - Set switch A to diverging")
print("  (same for switches B-J)")
print("Single train commands:")
print("  t csx f red-yellow    - Move CSX train forward until RED-YELLOW pattern")
print("  t csx b yellow-green  - Move CSX train backward until YELLOW-GREEN pattern")
print("  t csx s              - Stop CSX train")
print("  (same for up and cn)")
print("Status:")
print("  st                   - Show all device status")
print("  q                    - Quit")

def show_status():
    """Display current status of all devices"""
    # Poll for updates
    for _ in range(10):
        check_status_updates()
        wait(50)
        
    print("\nSwitch positions:")
    if not switch_states:
        print("No switches reporting")
    else:
        for switch_name in sorted(switch_states.keys()):
            position = switch_states[switch_name]
            print(f"{switch_name}: {'DIVERGING' if position else 'STRAIGHT'}")
    
    print("\nTrain status:")
    if not train_states:
        print("No trains reporting")
    else:
        for train_name in sorted(train_states.keys()):
            state = train_states[train_name]
            status = f"{train_name}: {state['movement']}, sees {state['color']}"
            if 'target_pattern' in state:
                pattern_str = '-'.join(str(c).split('.')[-1] for c in state['target_pattern'])
                status += f", seeking {pattern_str}"
            print(status)

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
            if train_name not in ["TRAIN_CSX", "TRAIN_UP", "TRAIN_CN", "TRAIN_BNSF", "TRAIN_NS", "TRAIN_CM"]:
                print("Invalid train name. Use: CSX, UP, CN, BNSF, NS, or CM")
                continue
                
            if parts[2] == 's':
                send_train_command(train_name, TRAIN_COMMAND["STOP"])
            elif len(parts) == 4 and parts[2] in ['f', 'b']:
                pattern_str = parts[3]
                colors = pattern_str.split('-')
                pattern = []
                valid = True
                for color_name in colors:
                    if color_name.upper() == 'RED':
                        pattern.append(Color.RED)
                    elif color_name.upper() == 'YELLOW':
                        pattern.append(Color.YELLOW)
                    elif color_name.upper() == 'GREEN':
                        pattern.append(Color.GREEN)
                    elif color_name.upper() == 'BLUE':
                        pattern.append(Color.BLUE)
                    else:
                        valid = False
                        break
                
                if valid:
                    command_type = (TRAIN_COMMAND["FORWARD_UNTIL_PATTERN"] 
                                  if parts[2] == 'f' else 
                                  TRAIN_COMMAND["BACKWARD_UNTIL_PATTERN"])
                    if parts[2] == 'b':
                        pattern = list(reversed(pattern))
                    send_train_command(train_name, command_type, pattern)
                else:
                    print("Invalid color pattern")
                    print("Valid colors are: RED, YELLOW, GREEN, BLUE")
            else:
                print("Invalid train command")
        else:
            print("Invalid train command format")
    elif cmd == 'm':
        # Multi-train pathfinding
        print("\nStarting multi-train movement planning")
        print("For each train, enter current position and goal")
        print("Positions can be cities or segments, e.g.:")
        print("  NYC")
        print("  CALGARY,LA (segment)")
        print("Enter blank line when done")
        
        initial_positions = {}
        goals = {}
        
        while True:
            train = input("\nTrain name (CSX/UP/CN/BNSF/NS/CM or blank to finish): ").strip().upper()
            if not train:
                break
                
            if train not in ["CSX", "UP", "CN", "BNSF", "NS", "CM"]:
                print("Invalid train name. Use: CSX, UP, CN, BNSF, NS, or CM")
                continue
                
            train = "TRAIN_" + train
            pos = input("Current position: ").strip().upper()
            if ',' in pos:
                city1, city2 = pos.split(',')
                initial_positions[train] = (city1.strip(), city2.strip())
            else:
                initial_positions[train] = pos
                
            goal = input("Goal city: ").strip().upper()
            goals[train] = goal
        
        if initial_positions and goals:
            execute_multi_train_path(initial_positions, goals)
        else:
            print("No trains specified!")
    else:
        print("Invalid command")
    
    wait(50)  # Short delay to prevent busy loop
