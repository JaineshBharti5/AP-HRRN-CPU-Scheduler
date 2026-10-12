import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from process import FIXED_CASES, compute_metrics, random_case
from scheduler import ALGORITHMS

ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(ROOT, "results")
GRAPHS_DIR = os.path.join(ROOT, "graphs")

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
COLORS = {"SJF": "#2a78d6", "HRRN": "#eb6834", "AP-HRRN": "#1baf7a"}

METRICS = [
    ("avg_waiting", "Average waiting time"),
    ("avg_turnaround", "Average turnaround time"),
    ("avg_response", "Average response time"),
    ("max_waiting", "Maximum waiting time"),
    ("context_switches", "Context switches"),
    ("cpu_utilization", "CPU utilization (%)"),
]

SCENARIOS = {
    "mixed": "Normal mixed load",
    "starvation": "Starvation-prone (long job, continuous short arrivals)",
    "many_short": "Many short jobs",
}

RANDOM_RUNS = 40
RANDOM_FIRST_SEED = 100
RANDOM_KW = {"n": 15, "max_arrival": 40, "max_burst": 15}


def apply_style():
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "font.family": "sans-serif",
            "text.color": INK,
            "axes.labelcolor": INK_2,
            "axes.edgecolor": AXIS,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.titlelocation": "left",
            "axes.titlesize": 10.5,
            "axes.titleweight": "bold",
            "axes.titlecolor": INK,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "legend.frameon": False,
            "legend.labelcolor": INK_2,
        }
    )


def run_all(processes):
    out = {}
    for name, algo in ALGORITHMS.items():
        procs, timeline = algo(processes)
        out[name] = {
            "procs": procs,
            "timeline": timeline,
            "metrics": compute_metrics(procs, timeline),
        }
    return out


def random_average():
    sums = {name: {k: 0.0 for k, _ in METRICS} for name in ALGORITHMS}
    for seed in range(RANDOM_FIRST_SEED, RANDOM_FIRST_SEED + RANDOM_RUNS):
        res = run_all(random_case(seed=seed, **RANDOM_KW))
        for name, r in res.items():
            for k, _ in METRICS:
                sums[name][k] += r["metrics"][k]
    return {name: {k: v / RANDOM_RUNS for k, v in m.items()} for name, m in sums.items()}


def fmt(key, value):
    if key in ("max_waiting", "context_switches"):
        return f"{value:.0f}" if float(value).is_integer() else f"{value:.1f}"
    return f"{value:.1f}"


def print_table(title, metrics_by_algo):
    print(f"\n{title}")
    header = f"{'Algorithm':<10}" + "".join(f"{label.split(' (')[0]:>24}" for _, label in METRICS)
    print(header)
    print("-" * len(header))
    for name, m in metrics_by_algo.items():
        print(f"{name:<10}" + "".join(f"{m[k]:>24.2f}" for k, _ in METRICS))


def plot_gantt(key, title, results):
    pids = sorted(p.pid for p in next(iter(results.values()))["procs"])
    row = {pid: i for i, pid in enumerate(pids)}
    panel_h = max(1.7, 0.21 * len(pids) + 0.7)
    fig, axes = plt.subplots(3, 1, figsize=(11, panel_h * 3 + 0.9), sharex=True)
    for ax, (name, r) in zip(axes, results.items()):
        for pid, s, e in r["timeline"]:
            if pid is None:
                continue
            ax.broken_barh(
                [(s, e - s)],
                (row[pid] - 0.3, 0.6),
                facecolors=COLORS[name],
                edgecolors=SURFACE,
                linewidth=1.2,
            )
        ax.set_yticks(range(len(pids)))
        ax.set_yticklabels([f"P{pid}" for pid in pids], fontsize=7.5 if len(pids) > 12 else 9)
        ax.set_ylim(len(pids) - 0.5, -0.5)
        ax.grid(axis="y", visible=False)
        ax.set_title(f"{name}   ·   {r['metrics']['context_switches']} context switches")
    axes[-1].set_xlabel("Time")
    fig.suptitle(f"Gantt charts: {title}", x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(GRAPHS_DIR, f"gantt_{key}.png"), dpi=160)
    plt.close(fig)


def plot_gantt_split(key, title, results):
    pids = sorted(p.pid for p in next(iter(results.values()))["procs"])
    row = {pid: i for i, pid in enumerate(pids)}
    fig_h = 0.2 * len(pids) + 1.5
    for name, r in results.items():
        fig, ax = plt.subplots(figsize=(11, fig_h))
        for pid, s, e in r["timeline"]:
            if pid is None:
                continue
            ax.broken_barh(
                [(s, e - s)],
                (row[pid] - 0.3, 0.6),
                facecolors=COLORS[name],
                edgecolors=SURFACE,
                linewidth=1.2,
            )
        ax.set_yticks(range(len(pids)))
        ax.set_yticklabels([f"P{pid}" for pid in pids], fontsize=8)
        ax.set_ylim(len(pids) - 0.5, -0.5)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("Time")
        ax.set_title(f"{name}   ·   {r['metrics']['context_switches']} context switches   ·   {title}")
        fig.tight_layout()
        fig.savefig(os.path.join(GRAPHS_DIR, f"gantt_{key}_{name.lower().replace('-', '')}.png"), dpi=160)
        plt.close(fig)


def plot_metric_bars(key, title, metrics_by_algo):
    names = list(metrics_by_algo)
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.2))
    for ax, (mk, label) in zip(axes.flat, METRICS):
        vals = [metrics_by_algo[n][mk] for n in names]
        ax.bar(
            range(len(names)),
            vals,
            width=0.26,
            color=[COLORS[n] for n in names],
            edgecolor=SURFACE,
            linewidth=1.5,
        )
        for i, v in enumerate(vals):
            ax.text(i, v, fmt(mk, v), ha="center", va="bottom", color=INK_2, fontsize=8.5)
        ax.set_xticks([])
        ax.set_title(label)
        ax.grid(axis="x", visible=False)
        top = 110 if mk == "cpu_utilization" else (max(vals) * 1.2 if max(vals) > 0 else 1)
        ax.set_ylim(0, top)
    fig.legend(
        handles=[Patch(facecolor=COLORS[n], label=n) for n in names],
        loc="lower center",
        ncol=3,
        bbox_to_anchor=(0.5, 0.0),
    )
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    fig.savefig(os.path.join(GRAPHS_DIR, f"metrics_{key}.png"), dpi=160)
    plt.close(fig)


def plot_starvation(results):
    by_algo = {n: {p.pid: p for p in r["procs"]} for n, r in results.items()}
    pids = sorted(next(iter(by_algo.values())))
    long_pid = max(next(iter(by_algo.values())).values(), key=lambda p: p.burst).pid
    long_idx = pids.index(long_pid)
    width = 0.26
    fig, ax = plt.subplots(figsize=(12.5, 4.8))
    for i, name in enumerate(results):
        xs = [j + (i - 1) * width for j in range(len(pids))]
        ys = [by_algo[name][pid].waiting for pid in pids]
        ax.bar(xs, ys, width=width, color=COLORS[name], edgecolor=SURFACE, linewidth=1, label=name)
        ax.text(
            xs[long_idx],
            ys[long_idx] + 0.8,
            str(ys[long_idx]),
            ha="center",
            va="bottom",
            color=INK_2,
            fontsize=9,
        )
    ax.set_xticks(range(len(pids)))
    ax.set_xticklabels([f"P{pid}" for pid in pids], fontsize=8)
    ax.set_ylabel("Waiting time")
    ax.grid(axis="x", visible=False)
    ax.set_title(
        f"Waiting time per process, starvation-prone load (P{long_pid} is the long job, burst "
        f"{by_algo['SJF'][long_pid].burst})"
    )
    ax.legend(loc="upper right", ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(GRAPHS_DIR, "starvation_waiting.png"), dpi=160)
    plt.close(fig)

    path = os.path.join(RESULTS_DIR, "starvation_waiting.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pid", "arrival", "burst"] + list(results))
        for pid in pids:
            p0 = by_algo["SJF"][pid]
            w.writerow([pid, p0.arrival, p0.burst] + [by_algo[n][pid].waiting for n in results])


def main():
    apply_style()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    rows = []

    for key, title in SCENARIOS.items():
        results = run_all(FIXED_CASES[key]())
        metrics_by_algo = {n: r["metrics"] for n, r in results.items()}
        print_table(title, metrics_by_algo)
        for n, m in metrics_by_algo.items():
            rows.append({"scenario": key, "algorithm": n, **{k: round(m[k], 2) for k, _ in METRICS}})
        plot_gantt(key, title, results)
        if key in ("starvation", "many_short"):
            plot_gantt_split(key, title, results)
        plot_metric_bars(key, title, metrics_by_algo)
        if key == "starvation":
            plot_starvation(results)

    avg = random_average()
    title = f"Average over {RANDOM_RUNS} random workloads ({RANDOM_KW['n']} processes each)"
    print_table(title, avg)
    for n, m in avg.items():
        rows.append({"scenario": "random_avg", "algorithm": n, **{k: round(m[k], 2) for k, _ in METRICS}})
    plot_metric_bars("random_avg", title, avg)

    path = os.path.join(RESULTS_DIR, "comparison.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["scenario", "algorithm"] + [k for k, _ in METRICS])
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved tables to {RESULTS_DIR} and graphs to {GRAPHS_DIR}")


if __name__ == "__main__":
    main()