import json

def load_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    ship = data['Ship']
    vehicles = data['Vehicles']
    
    return ship, vehicles

def check_overlap(placed_vehicles):
    # mengecek apakah ada grid pada kapal yang bertumpuk
    
    occupied_cells = set()
    for v in placed_vehicles:
        # menentukan dimensi berdasarkan orientasi horizontal atau vertikal
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
    # mengecek apakah ada kendaraan yang melebihi edge kapal

    ship_w, ship_l = ship_dim['w'], ship_dim['l']
    for v in placed_vehicles:
        w = v['Dimensions']['w'] if v['Orientation'] == 'Horizontal' else v['Dimensions']['l']
        l = v['Dimensions']['l'] if v['Orientation'] == 'Horizontal' else v['Dimensions']['w']
        
        if v['x'] < 0 or v['y'] < 0 or (v['x'] + w) > ship_w or (v['y'] + l) > ship_l:
            return True
    return False

def check_weight_violation(placed_vehicles, max_capacity):
    # mengecek apakah total berat kendaraan yang masuk ke dalam kapal melebihi berat maksimum kapal
    total_weight = sum(v['Weight'] for v in placed_vehicles)
    return max(0, total_weight - max_capacity)

def objective_function(state, ship):
    # state: daftar kendaraan apa saja yg masuk ke dalam kapal 
    # sudah termasuk koordinat (x, y) dan orientasi horizontal atau vertikalnya

    placed_vehicles = state['placed_vehicles']
    
    # 1. menghitung total keuntungan dari shipping fee
    total_fee = sum(v['ShippingFee'] for v in placed_vehicles)
    
    # 2. menghitung penalti ketika melanggar constraints
    penalty = 0
    
    # penambahan penalti ketika terjadi overlap
    if check_overlap(placed_vehicles):
        penalty += 10000
        
    # penambahan penalti ketika ada kendaraan melewati batas kapal
    if check_boundary_violation(placed_vehicles, ship['Dimensions']):
        penalty += 10000
        
    # penambahan penalti ketika total berat melebihi berat maksimum kapal
    weight_overflow = check_weight_violation(placed_vehicles, ship['MaxCapacity'])
    if weight_overflow > 0:
        penalty += weight_overflow * 1000
        
    # nilai objective function yang di-return adalah total keuntungan dikurangi penalti
    return total_fee - penalty