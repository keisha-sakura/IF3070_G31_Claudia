"""
Menjalankan Genetic Algorithm dan menyimpan hasilnya.

Struktur folder:
    src/
    ├── algoritma/
    │   └── genetic_algorithm.py
    ├── data.json
    ├── evaluation.py
    └── main.py
    output/                   ← hasil (di root repository)

Cara menjalankan (dari root repository):
    python src/main.py

Eksperimen sesuai spesifikasi:
    1. jumlah populasi sebagai kontrol, 3 variasi banyak iterasi, masing-masing 3 run
    2. banyak iterasi sebagai kontrol, 3 variasi jumlah populasi, masing-masing 3 run
Konfigurasinya diatur lewat konstanta GA_... di src/algoritma/genetic_algorithm.py.
Hasil disimpan di output/ga/.
"""

import json
import os
import random

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from algoritma.genetic_algorithm import (GA_CONTROL_ITERATION, GA_CONTROL_POPULATION,
                                         GA_ITERATION_VARIATIONS, GA_MUTATION_RATE,
                                         GA_POPULATION_VARIATIONS, genetic_algorithm)
from evaluation import get_size, load_data

# lokasi folder src/ dan root repository, agar path tidak bergantung pada
# folder tempat perintah dijalankan
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)

# spesifikasi: setiap konfigurasi dijalankan 3 kali; satu seed per run agar hasil
# dapat diulang persis (seed yang sama dipakai untuk semua algoritma)
SEEDS = [42, 56, 78]

LINE = "=" * 60


# =============================================================================
# Menampilkan dan menggambar state
# =============================================================================

def describe_state(state, ship):
    # ringkasan state (untuk JSON dan laporan)
    placed = state["placed_vehicles"]
    return {
        "inside": [{"id": v["id"], "x": v["x"], "y": v["y"], "Orientation": v["Orientation"]}
                   for v in placed],
        "outside": [v["id"] for v in state["outside_vehicles"]],
        "total_fee": sum(v["ShippingFee"] for v in placed),
        "total_weight": sum(v["Weight"] for v in placed),
        "max_capacity": ship["MaxCapacity"],
    }


def plot_state(state, ship, fitness, title, path):
    # gambar geladak: sumbu horizontal = y (panjang kapal), sumbu vertikal = x (lebar)
    ship_w, ship_l = ship["Dimensions"]["w"], ship["Dimensions"]["l"]
    fig = plt.figure(figsize=(12, 5))
    ax = fig.add_axes([0.05, 0.12, 0.62, 0.72])
    side = fig.add_axes([0.70, 0.05, 0.29, 0.85])
    side.axis("off")

    ax.add_patch(Rectangle((0, 0), ship_l, ship_w, facecolor="#f1f3f5", edgecolor="#343a40", lw=2))
    cmap = plt.get_cmap("tab20")
    for k, v in enumerate(state["placed_vehicles"]):
        sx, sy = get_size(v, v["Orientation"])
        ax.add_patch(Rectangle((v["y"] + 0.05, v["x"] + 0.05), sy - 0.1, sx - 0.1,
                               facecolor=cmap(k % 20), edgecolor="#212529", alpha=0.8))
        ax.text(v["y"] + sy / 2, v["x"] + sx / 2,
                f"#{v['id']}\n{v['Orientation'][0]} | {v['ShippingFee']}",
                ha="center", va="center", fontsize=7)

    ax.set_xlim(-0.3, ship_l + 0.3)
    ax.set_ylim(-0.3, ship_w + 0.3)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, ship_l + 1, 2))
    ax.set_yticks(range(0, ship_w + 1, 2))
    ax.grid(True, color="#dee2e6", lw=0.5)
    ax.set_xlabel("y (panjang geladak)")
    ax.set_ylabel("x (lebar geladak)")
    ax.set_title(title, loc="left", fontsize=11)

    d = describe_state(state, ship)
    info = (f"Objective     : {fitness}\n"
            f"ShippingFee   : {d['total_fee']}\n"
            f"Berat         : {d['total_weight']} / {d['max_capacity']}\n"
            f"Di kapal      : {len(d['inside'])}\n"
            f"Di luar kapal : {len(d['outside'])}")
    side.text(0, 1, info, va="top", family="monospace", fontsize=9)
    side.text(0, 0.6, "Kendaraan di luar kapal:\n" + (", ".join(d["outside"]) or "-"),
              va="top", fontsize=8, wrap=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_fitness(results, title, path):
    # plot nilai objective maksimum (garis penuh) dan rata-rata populasi (garis
    # putus-putus) terhadap iterasi, untuk semua run dalam satu konfigurasi
    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for k, r in enumerate(results):
        c = colors[k % len(colors)]
        ax.plot(r["fitness_list"], color=c, lw=1.4, label=f"Run {k + 1} maksimum")
        ax.plot(r["avg_fitness_list"], color=c, lw=0.9, ls="--", label=f"Run {k + 1} rata-rata")
    ax.set_xlabel("Iterasi (generasi)")
    ax.set_ylabel("Nilai objective function")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


# =============================================================================
# Menjalankan GA
# =============================================================================

def rel(path):
    # path relatif terhadap root repository, agar ringkas saat dicetak
    return os.path.relpath(path, ROOT_DIR)


def run_ga(vehicles, ship, population_size, max_iteration, mutation_rate, out_dir, tag):
    # menjalankan GA sekali untuk setiap seed dengan konfigurasi yang sama, menampilkan
    # hasil tiap run di terminal, lalu menyimpan gambar state awal/akhir, plot, dan data
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n{LINE}")
    print(f"GENETIC ALGORITHM | populasi = {population_size}, iterasi = {max_iteration}, "
          f"mutation rate = {mutation_rate}")
    print(LINE)

    results, rows = [], []
    for run, seed in enumerate(SEEDS, start=1):
        random.seed(seed)
        res = genetic_algorithm(vehicles, ship, population_size=population_size,
                                max_iteration=max_iteration, mutation_rate=mutation_rate)
        results.append(res)

        initial_path = os.path.join(out_dir, f"{tag}_run{run}_initial.png")
        final_path = os.path.join(out_dir, f"{tag}_run{run}_final.png")
        plot_state(res["initial_state"], ship, res["initial_fitness"],
                   f"GA pop={population_size} iter={max_iteration} run {run} - state awal", initial_path)
        plot_state(res["final_state"], ship, res["final_fitness"],
                   f"GA pop={population_size} iter={max_iteration} run {run} - state akhir", final_path)

        final = describe_state(res["final_state"], ship)
        n_total = len(vehicles)
        print(f"RUN {run}  (seed {seed})")
        print(f"  Objective awal   : {res['initial_fitness']}")
        print(f"  Objective akhir  : {res['final_fitness']}")
        print(f"  Kendaraan masuk  : {len(final['inside'])} / {n_total}   "
              f"(di luar: {', '.join(final['outside']) or '-'})")
        print(f"  Berat            : {final['total_weight']} / {final['max_capacity']}")
        print(f"  Durasi           : {res['duration']:.3f} detik")
        print(f"  Gambar           : {rel(initial_path)}")
        print(f"                     {rel(final_path)}")
        print()

        rows.append({
            "config": tag,
            "population_size": population_size,
            "max_iteration": max_iteration,
            "mutation_rate": mutation_rate,
            "run": run,
            "seed": seed,
            "initial_fitness": res["initial_fitness"],
            "final_fitness": res["final_fitness"],
            "duration_s": round(res["duration"], 4),
            "initial_state": describe_state(res["initial_state"], ship),
            "final_state": final,
            "fitness_list": res["fitness_list"],
            "avg_fitness_list": res["avg_fitness_list"],
        })

    plot_path = os.path.join(out_dir, f"{tag}_plot.png")
    plot_fitness(results, f"GA populasi={population_size}, iterasi={max_iteration}", plot_path)
    print(f"Plot: {rel(plot_path)}")
    return rows


def run_ga_experiments(vehicles, ship, out_dir):
    # eksperimen GA sesuai spesifikasi
    rows = []
    print(f"\n### SKENARIO 1: populasi = {GA_CONTROL_POPULATION} (kontrol), variasi banyak iterasi ###")
    for iteration in GA_ITERATION_VARIATIONS:
        tag = f"kontrolpop_pop{GA_CONTROL_POPULATION}_iter{iteration}"
        rows += run_ga(vehicles, ship, GA_CONTROL_POPULATION, iteration, GA_MUTATION_RATE,
                       out_dir, tag)
    print(f"\n### SKENARIO 2: banyak iterasi = {GA_CONTROL_ITERATION} (kontrol), variasi jumlah populasi ###")
    for population in GA_POPULATION_VARIATIONS:
        tag = f"kontroliter_pop{population}_iter{GA_CONTROL_ITERATION}"
        rows += run_ga(vehicles, ship, population, GA_CONTROL_ITERATION, GA_MUTATION_RATE,
                       out_dir, tag)
    return rows


def write_summary(rows, path):
    # tabel ringkasan per konfigurasi: dicetak di terminal dan disimpan sebagai markdown
    groups = {}
    for r in rows:
        groups.setdefault(r["config"], []).append(r)

    print(f"\n{'=' * 26} RINGKASAN {'=' * 26}")
    header = f"{'Skenario':<14}{'Konfigurasi':<20}{'Rata-rata':>10}{'Terbaik':>9}{'Terburuk':>10}{'Durasi (s)':>12}"
    print(header)
    print("-" * len(header))
    md = ["| Skenario | Populasi | Iterasi | Run | Seed | Objective awal | Objective akhir | Durasi (s) |",
          "|---|---|---|---|---|---|---|---|"]
    md_summary = ["| Skenario | Populasi | Iterasi | Rata-rata akhir | Terbaik | Terburuk | Rata-rata durasi (s) |",
                  "|---|---|---|---|---|---|---|"]
    for config, rs in groups.items():
        scenario = "kontrol pop" if config.startswith("kontrolpop") else "kontrol iter"
        label = f"pop {rs[0]['population_size']}, iter {rs[0]['max_iteration']}"
        values = [r["final_fitness"] for r in rs]
        avg_value = sum(values) / len(values)
        avg_duration = sum(r["duration_s"] for r in rs) / len(rs)
        print(f"{scenario:<14}{label:<20}{avg_value:>10.1f}{max(values):>9}{min(values):>10}{avg_duration:>12.3f}")
        md_summary.append(f"| {scenario} | {rs[0]['population_size']} | {rs[0]['max_iteration']} | "
                          f"{avg_value:.1f} | {max(values)} | {min(values)} | {avg_duration:.3f} |")
        for r in rs:
            md.append(f"| {scenario} | {r['population_size']} | {r['max_iteration']} | {r['run']} | "
                      f"{r['seed']} | {r['initial_fitness']} | {r['final_fitness']} | {r['duration_s']:.3f} |")

    with open(path, "w") as f:
        f.write("## Ringkasan per konfigurasi\n\n" + "\n".join(md_summary) +
                "\n\n## Detail per run\n\n" + "\n".join(md) + "\n")


def main():
    ship, vehicles = load_data(os.path.join(SRC_DIR, "data.json"))
    out_dir = os.path.join(ROOT_DIR, "output", "ga")
    os.makedirs(out_dir, exist_ok=True)

    rows = run_ga_experiments(vehicles, ship, out_dir)

    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(rows, f, indent=1)
    write_summary(rows, os.path.join(out_dir, "summary.md"))
    print(f"\nSemua hasil disimpan di {rel(out_dir)}/ (gambar, plot, summary.md, results.json)")


if __name__ == "__main__":
    main()
