import copy
import json
import random

def load_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    ship = data['Ship']
    vehicles = data['Vehicles']

    return ship, vehicles

def check_overlap(placed_vehicles):

    occupied_cells = set()
    for v in placed_vehicles:
        w = v['Dimensions']['w'] if v['Orientation'] == 'Horizontal' else v['Dimensions']['l']
        l = v['Dimensions']['l'] if v['Orientation'] == 'Horizontal' else v['Dimensions']['w']

        x_start, y_start = v['x'], v['y']

        for x in range(x_start, x_start + w):
            for y in range(y_start, y_start + l):
                if (x, y) in occupied_cells:
                    return True
                occupied_cells.add((x, y))
    return False

def check_boundary_violation(placed_vehicles, ship_dim):

    ship_w, ship_l = ship_dim['w'], ship_dim['l']
    for v in placed_vehicles:
        w = v['Dimensions']['w'] if v['Orientation'] == 'Horizontal' else v['Dimensions']['l']
        l = v['Dimensions']['l'] if v['Orientation'] == 'Horizontal' else v['Dimensions']['w']

        if v['x'] < 0 or v['y'] < 0 or (v['x'] + w) > ship_w or (v['y'] + l) > ship_l:
            return True
    return False

def check_weight_violation(placed_vehicles, max_capacity):
    total_weight = sum(v['Weight'] for v in placed_vehicles)
    return max(0, total_weight - max_capacity)

def objective_function(state, ship):

    placed_vehicles = state['placed_vehicles']

    total_fee = sum(v['ShippingFee'] for v in placed_vehicles)

    penalty = 0

    if check_overlap(placed_vehicles):
        penalty += 10000

    if check_boundary_violation(placed_vehicles, ship['Dimensions']):
        penalty += 10000

    weight_overflow = check_weight_violation(placed_vehicles, ship['MaxCapacity'])
    if weight_overflow > 0:
        penalty += weight_overflow * 1000

    return total_fee - penalty

ORIENTATIONS = ("Horizontal", "Vertical")

def get_size(vehicle, orientation):
    w, l = vehicle["Dimensions"]["w"], vehicle["Dimensions"]["l"]
    return (w, l) if orientation == "Horizontal" else (l, w)

def fits(vehicle, orientation, ship):
    size_x, size_y = get_size(vehicle, orientation)
    return size_x <= ship["Dimensions"]["w"] and size_y <= ship["Dimensions"]["l"]

def random_position(vehicle, orientation, ship):
    size_x, size_y = get_size(vehicle, orientation)
    x = random.randint(0, ship["Dimensions"]["w"] - size_x)
    y = random.randint(0, ship["Dimensions"]["l"] - size_y)
    return x, y

def clamp_placement(placement, vehicle, ship):
    if not fits(vehicle, placement["Orientation"], ship):
        placement["Orientation"] = "Vertical" if placement["Orientation"] == "Horizontal" else "Horizontal"
    size_x, size_y = get_size(vehicle, placement["Orientation"])
    placement["x"] = min(max(0, placement["x"]), ship["Dimensions"]["w"] - size_x)
    placement["y"] = min(max(0, placement["y"]), ship["Dimensions"]["l"] - size_y)

def generate_random_state(vehicles, ship, p_inside=0.5):
    state = []
    for v in vehicles:
        orientation = random.choice(ORIENTATIONS)
        if not fits(v, orientation, ship):
            orientation = "Vertical" if orientation == "Horizontal" else "Horizontal"
        x, y = random_position(v, orientation, ship)
        state.append({
            "inside": random.random() < p_inside,
            "x": x,
            "y": y,
            "Orientation": orientation,
        })
    return state

def decode_state(state, vehicles):
    placed, outside = [], []
    for placement, v in zip(state, vehicles):
        if placement["inside"]:
            placed_v = copy.deepcopy(v)
            placed_v["x"] = placement["x"]
            placed_v["y"] = placement["y"]
            placed_v["Orientation"] = placement["Orientation"]
            placed.append(placed_v)
        else:
            outside.append(copy.deepcopy(v))
    return {"placed_vehicles": placed, "outside_vehicles": outside}

def evaluate_state(state, vehicles, ship):
    return objective_function(decode_state(state, vehicles), ship)

def swap_vehicles(state, i, j, vehicles, ship):
    a, b = state[i], state[j]
    a["inside"], b["inside"] = b["inside"], a["inside"]
    a["x"], b["x"] = b["x"], a["x"]
    a["y"], b["y"] = b["y"], a["y"]
    clamp_placement(a, vehicles[i], ship)
    clamp_placement(b, vehicles[j], ship)

def move_vehicle(state, i, vehicles, ship, p_out=0.2):
    placement = state[i]
    if placement["inside"] and random.random() < p_out:
        placement["inside"] = False
        return
    placement["inside"] = True
    placement["x"], placement["y"] = random_position(vehicles[i], placement["Orientation"], ship)

def rotate_vehicle(state, i, vehicles, ship):
    placement = state[i]
    new_orientation = "Vertical" if placement["Orientation"] == "Horizontal" else "Horizontal"
    if fits(vehicles[i], new_orientation, ship):
        placement["Orientation"] = new_orientation
        clamp_placement(placement, vehicles[i], ship)

def random_neighbor(state, vehicles, ship):
    neighbor = copy.deepcopy(state)
    n = len(neighbor)
    i = random.randrange(n)
    move = random.choice(("swap", "move", "rotate"))
    if move == "swap" and n > 1:
        j = random.choice([k for k in range(n) if k != i])
        swap_vehicles(neighbor, i, j, vehicles, ship)
    elif move == "rotate" and neighbor[i]["inside"]:
        rotate_vehicle(neighbor, i, vehicles, ship)
    else:
        move_vehicle(neighbor, i, vehicles, ship)
    return neighbor

def all_neighbors(state, vehicles, ship):
    neighbors = []
    n = len(state)
    ship_w, ship_l = ship["Dimensions"]["w"], ship["Dimensions"]["l"]

    for i in range(n):
        for j in range(i + 1, n):
            if state[i]["inside"] or state[j]["inside"]:
                neighbor = copy.deepcopy(state)
                swap_vehicles(neighbor, i, j, vehicles, ship)
                neighbors.append(neighbor)

    for i in range(n):
        size_x, size_y = get_size(vehicles[i], state[i]["Orientation"])
        for x in range(ship_w - size_x + 1):
            for y in range(ship_l - size_y + 1):
                if state[i]["inside"] and x == state[i]["x"] and y == state[i]["y"]:
                    continue
                neighbor = copy.deepcopy(state)
                neighbor[i].update({"inside": True, "x": x, "y": y})
                neighbors.append(neighbor)
        if state[i]["inside"]:
            neighbor = copy.deepcopy(state)
            neighbor[i]["inside"] = False
            neighbors.append(neighbor)

    for i in range(n):
        if state[i]["inside"]:
            new_orientation = "Vertical" if state[i]["Orientation"] == "Horizontal" else "Horizontal"
            if fits(vehicles[i], new_orientation, ship):
                neighbor = copy.deepcopy(state)
                rotate_vehicle(neighbor, i, vehicles, ship)
                neighbors.append(neighbor)

    return neighbors

def best_neighbor(state, vehicles, ship):
    best_value = float("-inf")
    best_candidates = []
    for neighbor in all_neighbors(state, vehicles, ship):
        value = evaluate_state(neighbor, vehicles, ship)
        if value > best_value:
            best_value = value
            best_candidates = [neighbor]
        elif value == best_value:
            best_candidates.append(neighbor)
    return random.choice(best_candidates), best_value