"""Compare SJF, HRRN and AP-HRRN on several workloads: prints tables, saves CSVs and graphs."""
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

SURFACE, INK_2, GRID = "#fcfcfb", "#52514e", "#e1e0d9"
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
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "axes.axisbelow": True, "grid.color": GRID, "axes.titlelocation": "left",
        "axes.titleweight": "bold", "legend.frameon": False,
    })


def run_all(processes):
    """Run every algorithm on the same processes."""
    out = {}
    for name, algo in ALGORITHMS.items():
        procs, timeline = algo(processes)
        out[name] = {"procs": procs, "timeline": timeline, "metrics": compute_metrics(procs, timeline)}
    return out


def evaluate(algo, workloads, **kw):
    """Average every metric of one algorithm over a list of workloads."""
    totals = {k: 0.0 for k, _ in METRICS}
    for procs in workloads:
        m = compute_metrics(*algo(procs, **kw))
        for k in totals:
            totals[k] += m[k]
    return {k: v / len(workloads) for k, v in totals.items()}


def random_workloads():
    return [random_case(seed=s, **RANDOM_KW) for s in range(RANDOM_FIRST_SEED, RANDOM_FIRST_SEED + RANDOM_RUNS)]


def print_table(title, metrics_by_algo):
    print(f"\n{title}")
    header = f"{'Algorithm':<10}" + "".join(f"{label.split(' (')[0]:>24}" for _, label in METRICS)
    print(header + "\n" + "-" * len(header))
    for name, m in metrics_by_algo.items():
        print(f"{name:<10}" + "".join(f"{m[k]:>24.2f}" for k, _ in METRICS))


def draw_gantt(ax, name, result, pids, title):
    row = {pid: i for i, pid in enumerate(pids)}
    for pid, s, e in result["timeline"]:
        if pid is not None:
            ax.broken_barh([(s, e - s)], (row[pid] - 0.3, 0.6), facecolors=COLORS[name],
                           edgecolors=SURFACE, linewidth=1.2)
    ax.set_yticks(range(len(pids)))
    ax.set_yticklabels([f"P{p}" for p in pids], fontsize=8)
    ax.set_ylim(len(pids) - 0.5, -0.5)
    ax.grid(axis="y", visible=False)
    ax.set_title(title)


def plot_gantt(key, title, results, split=False):
    """One figure with 3 stacked Gantt charts, or (split=True) one figure per algorithm."""
    pids = sorted(p.pid for p in next(iter(results.values()))["procs"])
    label = lambda n: f"{n}   ·   {results[n]['metrics']['context_switches']} context switches"
    if split:
        for name, r in results.items():
            fig, ax = plt.subplots(figsize=(11, 0.2 * len(pids) + 1.5))
            draw_gantt(ax, name, r, pids, f"{label(name)}   ·   {title}")
            ax.set_xlabel("Time")
            fig.tight_layout()
            fig.savefig(os.path.join(GRAPHS_DIR, f"gantt_{key}_{name.lower().replace('-', '')}.png"), dpi=160)
            plt.close(fig)
        return
    panel_h = max(1.7, 0.21 * len(pids) + 0.7)
    fig, axes = plt.subplots(3, 1, figsize=(11, panel_h * 3 + 0.9), sharex=True)
    for ax, (name, r) in zip(axes, results.items()):
        draw_gantt(ax, name, r, pids, label(name))
    axes[-1].set_xlabel("Time")
    fig.suptitle(f"Gantt charts: {title}", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(GRAPHS_DIR, f"gantt_{key}.png"), dpi=160)
    plt.close(fig)


def plot_metric_bars(key, title, metrics_by_algo):
    """Six small bar charts, one per metric."""
    names = list(metrics_by_algo)
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.2))
    for ax, (mk, label) in zip(axes.flat, METRICS):
        vals = [metrics_by_algo[n][mk] for n in names]
        bars = ax.bar(names, vals, width=0.5, color=[COLORS[n] for n in names])
        ax.bar_label(bars, labels=[f"{v:.1f}" if v % 1 else f"{v:.0f}" for v in vals], color=INK_2, fontsize=8.5)
        ax.set_title(label, fontsize=10.5)
        ax.set_xticks([])
        ax.grid(axis="x", visible=False)
        ax.set_ylim(0, 110 if mk == "cpu_utilization" else max(max(vals) * 1.2, 1))
    fig.legend(handles=[Patch(facecolor=COLORS[n], label=n) for n in names], loc="lower center", ncol=3)
    fig.suptitle(title, x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    fig.savefig(os.path.join(GRAPHS_DIR, f"metrics_{key}.png"), dpi=160)
    plt.close(fig)


def plot_starvation(results):
    """Waiting time of every process (shows how the long job is treated) + CSV."""
    wait = {n: {p.pid: p.waiting for p in r["procs"]} for n, r in results.items()}
    procs = {p.pid: p for p in results["SJF"]["procs"]}
    pids = sorted(procs)
    long_pid = max(procs.values(), key=lambda p: p.burst).pid
    width = 0.26
    fig, ax = plt.subplots(figsize=(12.5, 4.8))
    for i, name in enumerate(results):
        xs = [j + (i - 1) * width for j in range(len(pids))]
        ax.bar(xs, [wait[name][p] for p in pids], width=width, color=COLORS[name], label=name)
        ax.text(xs[pids.index(long_pid)], wait[name][long_pid] + 0.8, str(wait[name][long_pid]),
                ha="center", color=INK_2, fontsize=9)
    ax.set_xticks(range(len(pids)))
    ax.set_xticklabels([f"P{p}" for p in pids], fontsize=8)
    ax.set_ylabel("Waiting time")
    ax.grid(axis="x", visible=False)
    ax.set_title(f"Waiting time per process, starvation-prone load (P{long_pid} is the long job, "
                 f"burst {procs[long_pid].burst})")
    ax.legend(loc="upper right", ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(GRAPHS_DIR, "starvation_waiting.png"), dpi=160)
    plt.close(fig)

    with open(os.path.join(RESULTS_DIR, "starvation_waiting.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pid", "arrival", "burst"] + list(results))
        for pid in pids:
            w.writerow([pid, procs[pid].arrival, procs[pid].burst] + [wait[n][pid] for n in results])


def main():
    apply_style()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    rows = []

    for key, title in SCENARIOS.items():                      # 1) fixed scenarios
        results = run_all(FIXED_CASES[key]())
        metrics = {n: r["metrics"] for n, r in results.items()}
        print_table(title, metrics)
        rows += [{"scenario": key, "algorithm": n, **{k: round(m[k], 2) for k, _ in METRICS}}
                 for n, m in metrics.items()]
        plot_gantt(key, title, results)
        if key != "mixed":
            plot_gantt(key, title, results, split=True)
        plot_metric_bars(key, title, metrics)
        if key == "starvation":
            plot_starvation(results)

    workloads = random_workloads()                            # 2) average of many random workloads
    avg = {name: evaluate(algo, workloads) for name, algo in ALGORITHMS.items()}
    title = f"Average over {RANDOM_RUNS} random workloads ({RANDOM_KW['n']} processes each)"
    print_table(title, avg)
    rows += [{"scenario": "random_avg", "algorithm": n, **{k: round(m[k], 2) for k, _ in METRICS}}
             for n, m in avg.items()]
    plot_metric_bars("random_avg", title, avg)

    with open(os.path.join(RESULTS_DIR, "comparison.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["scenario", "algorithm"] + [k for k, _ in METRICS])
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved tables to {RESULTS_DIR} and graphs to {GRAPHS_DIR}")


if __name__ == "__main__":
    main()
