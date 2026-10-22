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
    best_neighbor,
    decode_state,
)


def random_restart(vehicles, ship, max_restarts=10, max_iterations=300):

    # 1. inisialisasi random generator
    random.seed()

    start_time = time.time()

    best_initial_state = None
    best_initial_fitness = None
    best_state = None
    best_fitness = None

    fitness_list = []
    iteration_history = [] 
    restart_fitness_list = []
    iterations_per_restart = []
    total_iterations = 0

    print("=" * 60)
    print("RANDOM RESTART HILL CLIMBING")
    print("=" * 60)
    print(f"Max restarts   : {max_restarts}")
    print(f"Max iterations : {max_iterations}")

    # 2. ulangi pencarian dari state awal yang baru
    for restart in range(1, max_restarts + 1):

        print("\n" + "=" * 60)
        print(f"RESTART {restart}")
        print("=" * 60)

        # 3. generate initial state untuk restart ini
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
        iteration_history.append((restart, 0, current_fitness))

        run_best_state = copy.deepcopy(current_state)
        run_best_fitness = current_fitness

        print(f"Initial fitness: {initial_fitness}")

        # 4. cari neighbor terbaik pada setiap iterasi
        iterations = 0

        for iteration in range(1, max_iterations + 1):

            neighbor_state, neighbor_fitness = best_neighbor(
                current_state,
                vehicles,
                ship
            )

            iterations = iteration

            print(f"\nIteration       : {iteration}")
            print(f"Current fitness : {current_fitness}")
            print(f"Best neighbor   : {neighbor_fitness}")

            # 5. berhenti jika tidak ada peningkatan
            if neighbor_fitness <= current_fitness:
                iteration_history.append((restart, iteration, current_fitness))
                print("Decision        : STOP, no improvement")
                break

            # 6. pindah ke neighbor dengan fitness lebih tinggi
            current_state = copy.deepcopy(neighbor_state)
            current_fitness = neighbor_fitness
            iteration_history.append((restart, iteration, current_fitness))

            if current_fitness > run_best_fitness:
                run_best_state = copy.deepcopy(current_state)
                run_best_fitness = current_fitness

            print("Decision        : MOVE to best neighbor")

        total_iterations += iterations
        iterations_per_restart.append(iterations)
        restart_fitness_list.append(run_best_fitness)

        print(f"\nRestart {restart} selesai")
        print(f"Final fitness   : {run_best_fitness}")
        print(f"Iterations      : {iterations}")

        # 7. simpan hasil terbaik dari semua restart
        if best_fitness is None or run_best_fitness > best_fitness:
            best_state = copy.deepcopy(run_best_state)
            best_fitness = run_best_fitness
            best_initial_state = copy.deepcopy(initial_state)
            best_initial_fitness = initial_fitness
            print("Decision        : NEW BEST across restarts")

        fitness_list.append(best_fitness)

    # 8. hitung durasi eksekusi
    duration = time.time() - start_time

    # 9. decode state awal dan akhir
    decoded_initial_state = decode_state(
        best_initial_state,
        vehicles
    )

    decoded_final_state = decode_state(
        best_state,
        vehicles
    )

    print("\n" + "=" * 60)
    print("HASIL AKHIR")
    print("=" * 60)
    print(f"Initial fitness : {best_initial_fitness}")
    print(f"Final fitness   : {best_fitness}")
    print(f"Restarts        : {max_restarts}")
    print(f"Iterations      : {total_iterations}")
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

    # 10. return hasil
    return {
        "initial_state": decoded_initial_state,
        "initial_fitness": best_initial_fitness,
        "final_state": decoded_final_state,
        "final_fitness": best_fitness,
        "fitness_list": fitness_list,
        "iteration_history": iteration_history,
        "restart_fitness_list": restart_fitness_list,
        "iterations_per_restart": iterations_per_restart,
        "duration": duration,
        "max_restart": max_restarts,
        "max_iteration": max_iterations,
        "iterations": total_iterations,
    }


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    ship, vehicles = load_data(
        os.path.join(BASE_DIR, "data.json")
    )

    result = random_restart(
        vehicles,
        ship,
        max_restarts=10,
        max_iterations=300
    )

    print("\n" + "=" * 60)
    print("RINGKASAN RETURN")
    print("=" * 60)
    print(f"Initial fitness: {result['initial_fitness']}")
    print(f"Final fitness  : {result['final_fitness']}")
    print(f"Restarts       : {result['max_restart']}")
    print(f"Iterations     : {result['iterations']}")
    print(f"Duration       : {result['duration']:.6f} seconds")
    print(f"Fitness history: {result['fitness_list']}")
    print(f"Per restart    : {result['restart_fitness_list']}")