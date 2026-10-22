from pathlib import Path

from evaluation import load_data, decode_state
from algoritma.simulated_annealing import simulated_annealing
from algoritma.hc_sideways import hc_sideways


path = Path(__file__).resolve().parent / "data.json"
ship, vehicles = load_data(path)

# # tiga percobaan
# for i in range(3):
#     (
#         best, best_value, history, initial, initial_value, accepted_count, stuck_count, duration, exp_value,
#     ) = simulated_annealing(vehicles, ship, T_awal=100, cooling_rate=0.995, max_iterasti=3000, stuck_threshold=100)

#     print(f"\n========== RUN {i + 1} ==========")

#     for judul, state, nilai in [
#         ("STATE AWAL", initial, initial_value),
#         ("STATE TERBAIK", best, best_value),
#     ]:
#         hasil = decode_state(state, vehicles)

#         print("\n" + judul)

#         for v in hasil["placed_vehicles"]:
#             print(v["id"], "| Posisi:", (v["x"], v["y"]), "| Orientasi:", v["Orientation"])

#         print("Di luar:", [v["id"] for v in hasil["outside_vehicles"]])

#         print("ShippingFee:", nilai)

#     print("\nJumlah iterasi:", len(history))
#     print("Langkah accepted:", accepted_count)
#     print("Count stagnasi:", stuck_count)
#     print("Durasi:", round(duration, 4), "detik")


for i in range(3):
    (current, current_value, initial, initial_value, history, iterasi_count, sideways_total, duration,
    ) = hc_sideways(vehicles, ship, max_sideways=100, max_iterasi=3000)

    print(f"\n========== RUN {i + 1} ==========")

    for judul, state, nilai in [
        ("STATE AWAL", initial, initial_value),
        ("STATE AKHIR", current, current_value),
    ]:
        hasil = decode_state(state, vehicles)

        print("\n" + judul)

        for v in hasil["placed_vehicles"]:
            print(v["id"],"| Posisi:", (v["x"], v["y"]), "| Orientasi:", v["Orientation"])

        print("Di luar:", [v["id"] for v in hasil["outside_vehicles"]])
        print("ShippingFee:", nilai)

    print("\nJumlah iterasi:", iterasi_count)
    print("Total sideways:", sideways_total)
    print("Durasi:", round(duration, 4), "detik")