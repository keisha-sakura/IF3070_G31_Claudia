import copy, random, time

from evaluation import generate_random_state, all_neighbors, evaluate_state

def hc_sideways(vehicles, ship, max_sideways, max_iterasi):

    start_time = time.perf_counter()

    current = generate_random_state(vehicles, ship, p_inside = 0)

    urutan_kendaraan=list(range(len(vehicles)))
    random.shuffle(urutan_kendaraan)

    for i in urutan_kendaraan:
        current[i]["inside"] = True

        if evaluate_state(current, vehicles, ship) == -1:
            current[i]["inside"] = False
    
    current_value = evaluate_state(current, vehicles, ship)

    initial = copy.deepcopy(current)
    initial_value = current_value

    sideways_count = 0
    sideways_total = 0
    history_iterasi = []
    iterasi_count = 0

    for iterasi in range(max_iterasi):
        iterasi_count +=1

        neighbors = all_neighbors(current, vehicles, ship)

        best_value = float("-inf")
        best_kandidat = []

        for kandidat in neighbors:
            if kandidat == current:
                continue

            kandidat_value = evaluate_state(kandidat, vehicles, ship)

            if kandidat_value == -1:
                continue

            if kandidat_value > best_value:
                best_value = kandidat_value
                best_kandidat = [kandidat]

            elif kandidat_value == best_value:
                best_kandidat.append(kandidat)

        if not best_kandidat:
            break   

        neighbor = random.choice(best_kandidat)
        neighbor_value = evaluate_state(neighbor, vehicles, ship)

        if neighbor_value > current_value:
            current = neighbor
            current_value = neighbor_value
            sideways_count = 0

        elif neighbor_value == current_value:
            if sideways_count >= max_sideways:
                break

            current = neighbor
            current_value = neighbor_value
            sideways_count += 1
            sideways_total += 1

        if neighbor_value < current_value:
            break

        history_iterasi.append((iterasi + 1, current_value, sideways_count))

    return(current, current_value, initial, initial_value, history_iterasi, iterasi_count, sideways_total, time.perf_counter() - start_time)

