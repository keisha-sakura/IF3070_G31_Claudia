import copy, math, random, time

from evaluation import evaluate_state, generate_random_state, random_neighbor, objective_function, decode_state


def penurunan_suhu(iterasi, T_awal, cooling_rate):
    return T_awal * (cooling_rate ** iterasi)

def simulated_annealing(vehicles, ship, T_awal, cooling_rate, max_iterasti, stuck_threshold):
    
    start_time = time.perf_counter()

    current = generate_random_state(vehicles, ship, p_inside=0)

    urutan_kendaraan = list(range(len(vehicles)))

    random.shuffle(urutan_kendaraan)

    # periksa apkh overlap
    for i in urutan_kendaraan:
        current[i]["inside"] = True

        if evaluate_state(current, vehicles, ship) == -1:
            current[i]["inside"] = False

    current_value = evaluate_state(current, vehicles, ship)

    initial = copy.deepcopy(current)
    initial_value = current_value

    best = copy.deepcopy(current)
    best_value = current_value  

    history_iterasi = []
    no_improvement_iterasi_count = 0
    stuck_count = 0
    accepted_count = 0

    for iterasi in range(max_iterasti):
        T = penurunan_suhu(iterasi, T_awal, cooling_rate)

        if T <= 1e-12: break

        neighbor = random_neighbor(current, vehicles, ship)
        neighbor_value = evaluate_state(neighbor, vehicles, ship)

        accepted = False
        peluang = 0.0
        exp_value = None

        if neighbor_value != -1:
            try:
                exp_value = math.exp((neighbor_value - current_value) / T)
            except OverflowError:
                exp_value = None

            if neighbor_value < current_value:
                peluang = exp_value
                accepted = random.random() < peluang
            else:
                peluang = 1.0
                accepted = True

        if accepted:
            current = neighbor
            current_value = neighbor_value
            accepted_count += 1

        if current_value > best_value:
            best = copy.deepcopy(current)
            best_value = current_value
            no_improvement_iterasi_count = 0
        else:
            no_improvement_iterasi_count += 1

        if no_improvement_iterasi_count >= stuck_threshold:
            stuck_count += 1
            no_improvement_iterasi_count = 0

        history_iterasi.append((iterasi + 1, current_value, T, peluang, accepted))
    
    return best, best_value, history_iterasi, initial, initial_value, accepted_count, stuck_count, time.perf_counter() - start_time, exp_value