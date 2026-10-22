import copy, io, json, math, queue, threading, tkinter as tk
from datetime import datetime, timedelta, timezone
from contextlib import redirect_stdout
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from evaluation import decode_state, get_size, load_data
from algoritma.genetic_alrgorithm import genetic_algorithm
from algoritma.hc_random_restart import random_restart
from algoritma.hc_sideways import hc_sideways
from algoritma.hc_steepest_ascent import steepest_ascent
from algoritma.hc_stochastic import stochastic
from algoritma.simulated_annealing import simulated_annealing


ALGORITHMS = {
    "HC: Steepest Ascent": (steepest_ascent, [
        ("max_iterations", "Maksimum iterasi", int, 300),
    ]),
    "HC: Sideways Move": (hc_sideways, [
        ("max_sideways", "Maksimum sideways", int, 10),
        ("max_iterasi", "Maksimum iterasi", int, 300),
    ]),
    "HC: Stochastic": (stochastic, [
        ("max_iterations", "Maksimum iterasi", int, 300),
    ]),
    "HC: Random Restart": (random_restart, [
        ("max_restarts", "Jumlah restart", int, 10),
        ("max_iterations", "Iterasi per restart", int, 300),
    ]),
    "SA: Simulated Annealing": (simulated_annealing, [
        ("T_awal", "Suhu awal", float, 1000),
        ("cooling_rate", "Cooling rate (0 < nilai < 1)", float, 0.995),
        ("max_iterasti", "Maksimum iterasi", int, 300),
        ("stuck_threshold", "Stuck threshold", int, 100),
    ]),
    "GA: Genetic Algorithm": (genetic_algorithm, [
        ("population_size", "Jumlah populasi", int, 50),
        ("max_iteration", "Jumlah generasi", int, 300),
        ("mutation_rate", "Mutation rate (0 sampai 1)", float, 0.1),
    ]),
}

def read_parameters(algorithm, values):
    parameters = {}
    for key, label, convert, _ in ALGORITHMS[algorithm][1]:
        try:
            value = convert(values[key])
        except ValueError:
            raise ValueError(f"{label} harus berupa angka {convert.__name__}.") from None
        if key == "mutation_rate":
            valid = 0 <= value <= 1
        elif key == "cooling_rate":
            valid = 0 < value < 1
        elif key == "max_sideways":
            valid = value >= 0
        else:
            valid = value > 0
        if not valid:
            raise ValueError(f"Nilai {label} di luar batas yang diperbolehkan.")
        parameters[key] = value
    return parameters


def run_algorithm(algorithm, vehicles, ship, parameters):
    function = ALGORITHMS[algorithm][0]
    result = function(vehicles, ship, **parameters)

    if isinstance(result, dict):
        if function is steepest_ascent:
            result["fitness_list"] += [result["final_fitness"]] * max(
                0, result["iterations"] + 1 - len(result["fitness_list"]))
        return result
    
    if function is hc_sideways:
        final, score, initial, initial_score, history, iterations, sideways, duration = result
        extra = {"iterations": iterations, "sideways_total": sideways}
    else:
        final, score, history, initial, initial_score, accepted, stuck, duration, _ = result
        extra = {"iterations": len(history), "accepted_count": accepted, "stuck_count": stuck,
                 "exp_history": [(row[0], row[5]) for row in history]}
    fitness = [initial_score] + [row[1] for row in history]
    fitness += [score] * max(0, extra["iterations"] + 1 - len(fitness))

    return {"initial_state": decode_state(initial, vehicles), "initial_fitness": initial_score, "final_state": decode_state(final, vehicles), "final_fitness": score, "fitness_list": fitness, "history_iterasi": history, "duration": duration, **extra}

def experiment_plan(name, parameters, generation_text, population_text):
    if name != "GA: Genetic Algorithm":
        return [("Konfigurasi utama", run, dict(parameters)) for run in range(1, 4)]

    def variations(text):
        try:
            values = [int(value.strip()) for value in text.split(",")]
        except ValueError:
            raise ValueError("Variasi GA harus berupa 3 bilangan bulat, dipisahkan koma.") from None
        if len(values) != 3 or len(set(values)) != 3 or min(values) <= 0:
            raise ValueError("Isi tepat 3 variasi GA yang berbeda dan positif.")
        return values

    generations, populations = variations(generation_text), variations(population_text)
    plan = []
    for key, values, group in (("max_iteration", generations, "Populasi tetap"),
                               ("population_size", populations, "Generasi tetap")):
        for value in values:
            config = {**parameters, key: value}
            for run in range(1, 4):
                plan.append((group, run, dict(config)))
    return plan


def create_experiment_folder(name):
    algorithm = ALGORITHMS[name][0].__name__
    timestamp = datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d_%H-%M-%S")
    parent = Path(__file__).resolve().parent.parent / "output" / algorithm
    folder_name = f"eksperimen_{timestamp}"
    folder = parent / folder_name
    suffix = 2
    while True:
        try:
            folder.mkdir(parents=True, exist_ok=False)
            return folder
        except FileExistsError:
            folder = parent / f"{folder_name}_{suffix:02d}"
            suffix += 1


def run_output_folder(batch_path, name, group, repeat, parameters):
    folder = batch_path
    if name == "GA: Genetic Algorithm":
        folder = folder / group.lower().replace(" ", "_")
        folder = folder / f"populasi_{parameters['population_size']}_generasi_{parameters['max_iteration']}"
    return folder / f"run_{repeat:02d}"


def result_figure(result):
    figure = Figure(figsize=(8, 3.5), dpi=100, constrained_layout=True)
    sa = "exp_history" in result
    ax = figure.add_subplot(1, 2 if sa else 1, 1)
    if "iteration_history" in result:
        for restart in sorted({row[0] for row in result["iteration_history"]}):
            rows = [row for row in result["iteration_history"] if row[0] == restart]
            ax.plot([row[1] for row in rows], [row[2] for row in rows], label=f"Restart {restart}")
        ax.legend(fontsize=8)
    else:
        values = result["fitness_list"]
        ax.plot(range(len(values)), values, label="Maksimum populasi" if "avg_fitness_list" in result else "Objective")
        if "avg_fitness_list" in result:
            averages = result["avg_fitness_list"]
            ax.plot(range(len(averages)), averages, label="Rata-rata populasi")
        ax.legend(fontsize=8)
    ax.set(title="Objective: Total Shipping Fee", xlabel="Generasi" if "avg_fitness_list" in result else "Iterasi",
           ylabel="Shipping Fee (juta rupiah; -1 = invalid)")
    ax.grid(True, alpha=0.3)
    if sa:
        exp_ax = figure.add_subplot(1, 2, 2)
        history = result["exp_history"]
        exp_ax.plot([row[0] for row in history],
                    [row[1] if row[1] is not None and math.isfinite(row[1]) else float("nan") for row in history])
        exp_ax.set(title=r"$e^{\Delta E/T}$", xlabel="Iterasi", ylabel="Nilai eksponensial (symlog)")
        exp_ax.set_yscale("symlog", linthresh=1)
        exp_ax.grid(True, alpha=0.3)
    return figure

def total_shipping_fee(state):
    return sum(vehicle["ShippingFee"] for vehicle in state["placed_vehicles"])


def state_description(state):
    lines = []
    for key, title in (("placed_vehicles", "DI DALAM KAPAL"), ("outside_vehicles", "DI LUAR KAPAL")):
        lines.append(f"{title} ({len(state[key])} kendaraan):")
        for vehicle in state[key]:
            identity = vehicle.get("id", vehicle.get("ID", "?"))
            position = f"({vehicle['x']}, {vehicle['y']})" if key == "placed_vehicles" else "di luar"
            lines.append(f"  ID {identity}: {position}, {vehicle.get('Orientation', '-')}, "
                         f"dimensi={vehicle['Dimensions']['w']}x{vehicle['Dimensions']['l']}, "
                         f"berat={vehicle['Weight']}, fee={vehicle['ShippingFee']}")
    return "\n".join(lines)


def state_figure(result, ship):
    figure = Figure(figsize=(10, 7), dpi=100, constrained_layout=True)
    width, length = ship["Dimensions"]["w"], ship["Dimensions"]["l"]
    from matplotlib.patches import Rectangle
    for index, (key, title) in enumerate((("initial_state", "Awal"), ("final_state", "Akhir")), 1):
        ax = figure.add_subplot(1, 2, index)
        ax.set(xlim=(0, width), ylim=(length, 0),
               title=f"{title}: Shipping Fee {total_shipping_fee(result[key]):g} juta rupiah\n"
                     f"Objective: {result[key.replace('state', 'fitness')]}")
        ax.set_aspect("equal")
        ax.set_xticks(range(width + 1), minor=True)
        ax.set_yticks(range(length + 1), minor=True)
        ax.grid(which="both", alpha=0.3)
        ax.set_facecolor("#ffd6e8")
        for v in result[key]["placed_vehicles"]:
            w, l = get_size(v, v["Orientation"])
            ax.add_patch(Rectangle((v["x"], v["y"]), w, l, fill=False, linewidth=2))
            ax.text(v["x"] + w / 2, v["y"] + l / 2, str(v.get("id", v.get("ID", "?"))), ha="center", va="center")
        outside = ", ".join(str(v.get("id", v.get("ID", "?"))) for v in result[key]["outside_vehicles"]) or "Tidak ada"
        ax.set_xlabel(f"Di luar kapal: {outside}", wrap=True)
    return figure


class ShipLoadingApp:
    def __init__(self, root):
        self.root = root
        self.ship = self.vehicles = None
        self.messages = queue.Queue()
        self.pending = 0
        self.chart_canvases = []
        root.title("Penempatan Kendaraan di Kapal")
        pink = "#e11584"
        light_pink = "#fff0f7"
        root.configure(background=pink)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", background=pink, foreground="black")
        style.configure("TLabelframe", background=pink, bordercolor="#9d0f5c")
        style.configure("TLabelframe.Label", background=pink, foreground="black")
        style.configure("TLabel", background=pink, foreground="black")
        style.configure("TButton", background="#ff94ce", foreground="black")
        style.map("TButton", background=[("active", "#ffc6e5"), ("disabled", "#f5abcF")])
        style.configure("TEntry", fieldbackground=light_pink, foreground="black")
        style.configure("TCombobox", fieldbackground=light_pink, foreground="black")
        style.map("TCombobox", fieldbackground=[("readonly", light_pink)],
                  selectbackground=[("readonly", light_pink)], selectforeground=[("readonly", "black")])
        root.option_add("*TCombobox*Listbox.background", light_pink)
        root.option_add("*TCombobox*Listbox.foreground", "black")
        root.geometry("950x780")
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)
        root.rowconfigure(3, weight=1)

        setup = ttk.LabelFrame(root, text="Setup")
        setup.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        setup.columnconfigure(0, weight=1)
        self.file_path = tk.StringVar(value=str(Path(__file__).with_name("data.json")))
        ttk.Entry(setup, textvariable=self.file_path).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(setup, text="Load Data", command=self.load).grid(row=0, column=1, padx=5)
        self.data_status = ttk.Label(setup, text="Data belum dimuat", wraplength=430)
        self.data_status.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.algorithm = tk.StringVar(value=next(iter(ALGORITHMS)))
        menu = ttk.Combobox(setup, textvariable=self.algorithm, values=list(ALGORITHMS), state="readonly", width=30)
        menu.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        menu.bind("<<ComboboxSelected>>", self.update_parameters)
        self.generation_variations = tk.StringVar(value="100,300,600")
        self.population_variations = tk.StringVar(value="20,50,100")

        self.parameter_frame = ttk.LabelFrame(root, text="Parameter Algoritma")
        self.parameter_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.update_parameters()
        controls = ttk.Frame(root)
        controls.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.run_button = ttk.Button(controls, text="Run Experiment", command=self.run)
        self.run_button.grid(row=0, column=0, padx=3)

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="Hasil")
        self.chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_frame, text="Grafik")
        self.chart_frame.columnconfigure(0, weight=1)
        self.chart_frame.rowconfigure(0, weight=1)
        chart_scroll = tk.Canvas(self.chart_frame, background=light_pink, highlightthickness=0)
        chart_scroll.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.chart_frame, orient="vertical", command=chart_scroll.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        chart_scroll.config(yscrollcommand=scrollbar.set)
        self.chart_list = ttk.Frame(chart_scroll)
        chart_window = chart_scroll.create_window((0, 0), window=self.chart_list, anchor="nw")
        self.chart_list.bind("<Configure>", lambda event: chart_scroll.config(scrollregion=chart_scroll.bbox("all")))
        chart_scroll.bind("<Configure>", lambda event: chart_scroll.itemconfigure(chart_window, width=event.width))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        self.output = ScrolledText(output_frame, height=12, wrap="word", state="disabled",
                                   background=light_pink, foreground="black", insertbackground="black")
        self.output.frame.configure(background=pink)
        self.output.grid(row=0, column=0, sticky="nsew")
        self.grids = {}
        self.grid_results = []
        for column, (key, title) in enumerate((("initial_state", "Susunan awal"), ("final_state", "Susunan akhir"))):
            frame = ttk.LabelFrame(root, text=title)
            frame.grid(row=3, column=column, padx=5, pady=5, sticky="nsew")
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)
            canvas = tk.Canvas(frame, background=light_pink, highlightbackground=pink, width=300, height=300)
            canvas.grid(row=0, column=0, sticky="nsew")
            vertical = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            vertical.grid(row=0, column=1, sticky="ns")
            horizontal = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
            horizontal.grid(row=1, column=0, sticky="ew")
            canvas.config(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
            canvas.bind("<Configure>", self.resize_grids)
            self.grids[key] = canvas

        root.after(100, self.poll_result)

    def update_parameters(self, event=None):
        for widget in self.parameter_frame.winfo_children():
            widget.destroy()
        self.parameters = {}
        for row, (key, label, _, default) in enumerate(ALGORITHMS[self.algorithm.get()][1]):
            ttk.Label(self.parameter_frame, text=label).grid(row=row, column=0, padx=5, pady=3, sticky="w")
            variable = tk.StringVar(value=str(default))
            ttk.Entry(self.parameter_frame, textvariable=variable, width=12).grid(row=row, column=1, padx=5, pady=3)
            self.parameters[key] = variable
        if self.algorithm.get() == "GA: Genetic Algorithm":
            for row, (label, variable) in enumerate((
                ("3 variasi generasi", self.generation_variations),
                ("3 variasi populasi", self.population_variations),
            ), start=len(self.parameters)):
                ttk.Label(self.parameter_frame, text=label).grid(row=row, column=0, padx=5, pady=3, sticky="w")
                ttk.Entry(self.parameter_frame, textvariable=variable, width=18).grid(row=row, column=1, padx=5, pady=3)

    def load(self):
        try:
            ship, vehicles = load_data(self.file_path.get())
        except Exception as error:
            self.ship = self.vehicles = None
            self.data_status.config(text="Data belum dimuat")
            messagebox.showerror("Gagal memuat data", str(error))
            return
        self.ship, self.vehicles = ship, vehicles
        self.data_status.config(text=f"{Path(self.file_path.get()).name}: {len(vehicles)} kendaraan | "
                                f"Kapal {ship['Dimensions']['w']} x {ship['Dimensions']['l']} | "
                                f"Kapasitas {ship['MaxCapacity']}")

    def log(self, text):
        self.output.config(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.config(state="disabled")

    def run(self):
        if self.ship is None:
            messagebox.showerror("Data belum dimuat", "Klik Load Data terlebih dahulu.")
            return
        name = self.algorithm.get()
        try:
            parameters = read_parameters(name, {key: var.get() for key, var in self.parameters.items()})
            plan = experiment_plan(name, parameters, self.generation_variations.get(), self.population_variations.get())
            batch_path = create_experiment_folder(name)
        except (ValueError, OSError) as error:
            messagebox.showerror("Gagal menyiapkan eksperimen", str(error))
            return
        ship, vehicles = self.ship, self.vehicles
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")
        for canvas in self.chart_canvases:
            canvas.get_tk_widget().destroy()
            canvas.figure.clear()
        self.chart_canvases.clear()
        for widget in self.chart_list.winfo_children():
            widget.destroy()
        self.run_button.config(state="disabled")
        self.pending = len(plan)
        self.batch_path = batch_path
        self.show_grids()
        threading.Thread(target=self.batch_worker, args=(name, vehicles, ship, plan), daemon=True).start()

    def batch_worker(self, name, vehicles, ship, plan):
        for number, (group, repeat, parameters) in enumerate(plan, 1):
            folder = run_output_folder(self.batch_path, name, group, repeat, parameters)
            self.worker(name, copy.deepcopy(vehicles), copy.deepcopy(ship), parameters,
                        {"algorithm": name, "group": group, "repeat": repeat, "number": number,
                         "parameters": parameters, "output_path": str(folder)})

    def worker(self, name, vehicles, ship, parameters, metadata):
        console = io.StringIO()
        try:
            with redirect_stdout(console):
                result = run_algorithm(name, vehicles, ship, parameters)
            self.messages.put((result, ship, console.getvalue(), None, metadata))
        except Exception as error:
            self.messages.put((None, ship, console.getvalue(), f"{type(error).__name__}: {error}", metadata))

    def poll_result(self):
        try:
            result, ship, console, error, metadata = self.messages.get_nowait()
        except queue.Empty:
            pass
        else:
            record = {"result": result, "ship": ship, "console": console, "error": error, **metadata}
            try:
                self.save_record(record)
            except Exception as save_error:
                record["save_error"] = str(save_error)
            self.show_result(record)
            self.pending = max(0, self.pending - 1)
            if self.pending == 0:
                self.run_button.config(state="normal")
        self.root.after(100, self.poll_result)

    def save_record(self, record):
        if "output_path" not in record:
            return
        folder = Path(record["output_path"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "hasil.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        (folder / "console.txt").write_text(record["console"], encoding="utf-8")
        if record["result"] is not None:
            figure = result_figure(record["result"])
            figure.savefig(folder / "grafik.png")
            figure.clear()
            figure = state_figure(record["result"], record["ship"])
            figure.savefig(folder / "state.png")
            figure.clear()

    def show_result(self, record):
        heading = f"{record['algorithm']} | Run {record.get('number', record['repeat'])}"
        if record["algorithm"] == "GA: Genetic Algorithm":
            heading += f" | {record['group']} | Pengulangan {record['repeat']}"
        self.log(f"\n{'=' * 45}\n{heading}\n{'=' * 45}")
        if record.get("save_error"):
            self.log(f"Gagal menyimpan sebagian hasil: {record['save_error']}")
        result = record["result"]
        if record["error"]:
            self.log(f"Proses gagal: {record['error']}\n{record['console']}")
            return
        self.log(f"\nTotal Shipping Fee akhir: {total_shipping_fee(result['final_state']):g} juta rupiah"
                 f"\nTotal Shipping Fee awal: {total_shipping_fee(result['initial_state']):g} juta rupiah"
                 f"\nObjective awal: {result['initial_fitness']}\nObjective akhir: {result['final_fitness']}"
                 f"\nDurasi pencarian: {result['duration']:.6f} detik")
        fields = {"iterations": "Jumlah iterasi", "max_restart": "Jumlah restart",
                  "iterations_per_restart": "Iterasi per restart", "population_size": "Jumlah populasi",
                  "max_iteration": "Jumlah generasi" if "avg_fitness_list" in result else "Batas iterasi",
                  "sideways_total": "Total sideways", "accepted_count": "Perpindahan diterima",
                  "stuck_count": "Frekuensi stuck"}
        for key, label in fields.items():
            if key in result:
                self.log(f"{label}: {result[key]}")
       
        if result["final_fitness"] == -1:
            self.log("Objective -1, ada melanggar constraints")
        for key, title in (("initial_state", "STATE AWAL"), ("final_state", "STATE AKHIR")):
            self.log(f"\n{title}\n{state_description(result[key])}")
        self.show_grids(result, record["ship"], heading)
        ttk.Label(self.chart_list, text=heading).pack(anchor="w", padx=5, pady=(10, 0))
        chart_canvas = FigureCanvasTkAgg(result_figure(result), master=self.chart_list)
        chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        chart_canvas.draw()
        self.chart_canvases.append(chart_canvas)

    def show_grids(self, result=None, ship=None, heading=""):
        if result is None:
            self.grid_results.clear()
        else:
            self.grid_results.append((result, ship, heading))
        self.resize_grids()

    def resize_grids(self, event=None):
        for key, canvas in self.grids.items():
            position = canvas.yview()[0]
            canvas.delete("all")
            canvas.config(scrollregion=(0, 0, 0, 0))
            offset = 10
            for result, ship, heading in self.grid_results:
                width, length = ship["Dimensions"]["w"], ship["Dimensions"]["l"]
                cell_size = max(12, min((max(canvas.winfo_width(), 300) - 20) / width,
                                        (max(canvas.winfo_height(), 250) - 20) / length))
                left = max(10, (canvas.winfo_width() - width * cell_size) / 2)
                canvas.create_text(10, offset, anchor="nw", text=heading,
                                   width=max(canvas.winfo_width(), 300) - 20, tags="run_title")
                top = offset + 85
                canvas.create_text(left, top - 40, anchor="w",
                                   text=f"Shipping Fee: {total_shipping_fee(result[key]):g} juta rupiah")
                canvas.create_text(left, top - 20, anchor="w", text=f"Objective: {result[key.replace('state', 'fitness')]}")
                right, bottom = left + width * cell_size, top + length * cell_size
                canvas.create_rectangle(left, top, right, bottom, fill="#ffd6e8",
                                        outline="", tags="ship_background")
                for x in range(width + 1):
                    position = left + x * cell_size
                    canvas.create_line(position, top, position, bottom, fill="#c98aa5")
                for y in range(length + 1):
                    position = top + y * cell_size
                    canvas.create_line(left, position, right, position, fill="#c98aa5")
                canvas.create_rectangle(left, top, right, bottom, outline="black")
                for number, vehicle in enumerate(result[key]["placed_vehicles"]):
                    w, l = get_size(vehicle, vehicle["Orientation"])
                    x, y = left + vehicle["x"] * cell_size, top + vehicle["y"] * cell_size
                    canvas.create_rectangle(x, y, x + w * cell_size, y + l * cell_size,
                                            outline="black", width=2, tags="vehicle")
                    canvas.create_text(x + w * cell_size / 2, y + l * cell_size / 2,
                                       text=str(vehicle.get("id", vehicle.get("ID", number + 1))),
                                       fill="black", font=("Consolas", 10), tags="vehicle_id")
                outside = result[key]["outside_vehicles"]
                canvas.create_text(left, bottom + 20, anchor="nw", text=f"Di luar kapal ({len(outside)}):")
                for number, vehicle in enumerate(outside):
                    canvas.create_text(left, bottom + 40 + number * 18, anchor="nw",
                                       text=f"ID {vehicle.get('id', vehicle.get('ID', '?'))} | "
                                       f"{vehicle['Dimensions']['w']}x{vehicle['Dimensions']['l']} | "
                                       f"berat {vehicle['Weight']} | fee {vehicle['ShippingFee']}")
                outside_count = max(len(result[state]["outside_vehicles"])
                                    for state in ("initial_state", "final_state"))
                offset = bottom + 75 + outside_count * 18
            canvas.config(scrollregion=canvas.bbox("all") or (0, 0, 0, 0))
            canvas.yview_moveto(position if self.grid_results else 0)


if __name__ == "__main__":
    root = tk.Tk()
    ShipLoadingApp(root)
    root.mainloop()
