import time
import copy
import os
import sys
import random

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from evaluation import (
    load_data,
    generate_random_state,
    evaluate_state,
    random_neighbor,
    decode_state,
)


def stochastic(vehicles, ship, max_iterations=300):

    # 1. inisialisasi random generator
    random.seed()

    start_time = time.time()

    # 2. generate initial state
    initial_state = generate_random_state(
        vehicles,
        ship,
        p_inside=0.5
    )

    initial_fitness = evaluate_state(
        initial_state,
        vehicles,
        ship
    )

    current_state = copy.deepcopy(initial_state)
    current_fitness = initial_fitness

    best_state = copy.deepcopy(current_state)
    best_fitness = current_fitness

    fitness_list = [best_fitness]

    print("=" * 60)
    print("STOCHASTIC HILL CLIMBING")
    print("=" * 60)
    print(f"Initial fitness: {initial_fitness}")
    print(f"Max iterations : {max_iterations}")

    # 3. ambil satu neighbor acak pada setiap iterasi
    iterations = 0

    for iteration in range(1, max_iterations + 1):

        neighbor_state = random_neighbor(
            current_state,
            vehicles,
            ship
        )

        neighbor_fitness = evaluate_state(
            neighbor_state,
            vehicles,
            ship
        )

        iterations = iteration

        print(f"\nIteration       : {iteration}")
        print(f"Current fitness : {current_fitness}")
        print(f"Random neighbor : {neighbor_fitness}")

        # 4. tetap di state sekarang jika tidak ada peningkatan
        if neighbor_fitness <= current_fitness:
            print("Decision        : STAY, no improvement")
            fitness_list.append(best_fitness)
            continue

        # 5. pindah ke neighbor dengan fitness lebih tinggi
        current_state = copy.deepcopy(neighbor_state)
        current_fitness = neighbor_fitness

        if current_fitness > best_fitness:
            best_state = copy.deepcopy(current_state)
            best_fitness = current_fitness

        fitness_list.append(best_fitness)

        print("Decision        : MOVE to random neighbor")

    # 6. hitung durasi eksekusi
    duration = time.time() - start_time

    # 7. decode state awal dan akhir
    decoded_initial_state = decode_state(
        initial_state,
        vehicles
    )

    decoded_final_state = decode_state(
        best_state,
        vehicles
    )

    print("\n" + "=" * 60)
    print("HASIL AKHIR")
    print("=" * 60)
    print(f"Initial fitness : {initial_fitness}")
    print(f"Final fitness   : {best_fitness}")
    print(f"Iterations      : {iterations}")
    print(f"Duration        : {duration:.6f} seconds")
    print(
        f"Vehicles loaded : "
        f"{len(decoded_final_state['placed_vehicles'])}"
    )
    print(
        f"Vehicles outside: "
        f"{len(decoded_final_state['outside_vehicles'])}"
    )

    print("\nKendaraan yang dimuat:")

    for vehicle in decoded_final_state["placed_vehicles"]:
        vehicle_name = vehicle.get(
            "Name",
            vehicle.get("ID", "Vehicle")
        )

        print(
            f"* {vehicle_name}: "
            f"x={vehicle['x']}, "
            f"y={vehicle['y']}, "
            f"orientation={vehicle['Orientation']}, "
            f"fee={vehicle['ShippingFee']}"
        )

    # 8. return hasil
    return {
        "initial_state": decoded_initial_state,
        "initial_fitness": initial_fitness,
        "final_state": decoded_final_state,
        "final_fitness": best_fitness,
        "fitness_list": fitness_list,
        "duration": duration,
        "max_iteration": max_iterations,
        "iterations": iterations,
    }


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    ship, vehicles = load_data(
        os.path.join(BASE_DIR, "data.json")
    )

    result = stochastic(
        vehicles,
        ship,
        max_iterations=300
    )

    print("\n" + "=" * 60)
    print("RINGKASAN RETURN")
    print("=" * 60)
    print(f"Initial fitness: {result['initial_fitness']}")
    print(f"Final fitness  : {result['final_fitness']}")
    print(f"Iterations     : {result['iterations']}")
    print(f"Duration       : {result['duration']:.6f} seconds")
    print(f"Fitness history: {result['fitness_list']}")