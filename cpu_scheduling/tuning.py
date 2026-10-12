import csv
import os

import matplotlib  

matplotlib.use("Agg")
from matplotlib import pyplot as plt  

from compare import (
    COLORS,
    GRAPHS_DIR,
    INK_2,
    METRICS,
    RANDOM_FIRST_SEED,
    RANDOM_KW,
    RANDOM_RUNS,
    RESULTS_DIR,
    SURFACE,
    apply_style,
)
from process import FIXED_CASES, compute_metrics, random_case
from scheduler import aphrrn_schedule, hrrn_schedule, sjf_schedule

SWEEPS = {
    "k": ("Preemption threshold k", [1.0, 1.25, 1.5, 2.0, 3.0, 5.0], {}),
    "alpha": ("Smoothing factor alpha (estimated bursts)", [0.1, 0.3, 0.5, 0.7, 0.9], {"estimator": "exp"}),
    "wait_limit": ("Aging wait limit L", [4, 8, 12, 16, 24, 10**6], {}),
    "boost": ("Aging boost", [0, 5, 10, 20, 50], {}),
}

PLOT_METRICS = ["avg_waiting", "max_waiting", "context_switches"]
LABELS = dict(METRICS)


def workloads():
    sets = {
        "random_avg": [
            random_case(seed=s, **RANDOM_KW)
            for s in range(RANDOM_FIRST_SEED, RANDOM_FIRST_SEED + RANDOM_RUNS)
        ]
    }
    for key in ("mixed", "starvation", "many_short"):
        sets[key] = [FIXED_CASES[key]()]
    return sets


def evaluate(algo, plist, **kw):
    totals = {k: 0.0 for k, _ in METRICS}
    for procs in plist:
        done, timeline = algo(procs, **kw)
        m = compute_metrics(done, timeline)
        for k in totals:
            totals[k] += m[k]
    return {k: v / len(plist) for k, v in totals.items()}


def run_sweep(param, values, extra, sets):
    rows = []
    for v in values:
        for scenario, plist in sets.items():
            m = evaluate(aphrrn_schedule, plist, **{param: v}, **extra)
            rows.append({"param": param, "value": v, "scenario": scenario, **m})
    return rows


def plot_sweep(param, title, values, rows, baselines):
    labels = ["off" if v == 10**6 else str(v) for v in values]
    xs = range(len(values))
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9))
    for ax, mk in zip(axes, PLOT_METRICS):
        for name in ("SJF", "HRRN"):
            ax.plot(xs, [baselines[name][mk]] * len(values), color=COLORS[name], linewidth=2, label=name)
        ys = [next(r[mk] for r in rows if r["value"] == v and r["scenario"] == "random_avg") for v in values]
        ax.plot(
            xs,
            ys,
            color=COLORS["AP-HRRN"],
            linewidth=2,
            marker="o",
            markersize=7,
            markeredgecolor=SURFACE,
            markeredgewidth=1.5,
            label="AP-HRRN",
        )
        if mk == "context_switches":
            ax.set_ylim(0, max(ys + [baselines["SJF"][mk], baselines["HRRN"][mk]]) * 1.25)
        ax.set_xticks(list(xs))
        ax.set_xticklabels(labels)
        ax.set_title(LABELS[mk])
        ax.set_xlabel(title, fontsize=9)
        ax.grid(axis="x", visible=False)
    handles = axes[0].lines
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(
        f"Effect of: {title} (average of {RANDOM_RUNS} random workloads)",
        x=0.01,
        ha="left",
        fontsize=11.5,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(os.path.join(GRAPHS_DIR, f"tuning_{param}.png"), dpi=160)
    plt.close(fig)


def print_sweep(param, title, values, rows):
    print(f"\n{title}  (random_avg | starvation)")
    print(f"{'value':>8} | {'avgWT':>7} {'avgRT':>7} {'maxWT':>7} {'CS':>6} | {'avgWT':>7} {'maxWT':>7} {'CS':>4}")
    for v in values:
        a = next(r for r in rows if r["value"] == v and r["scenario"] == "random_avg")
        s = next(r for r in rows if r["value"] == v and r["scenario"] == "starvation")
        label = "off" if v == 10**6 else v
        print(
            f"{str(label):>8} | {a['avg_waiting']:7.2f} {a['avg_response']:7.2f} {a['max_waiting']:7.2f} "
            f"{a['context_switches']:6.2f} | {s['avg_waiting']:7.2f} {s['max_waiting']:7.0f} {s['context_switches']:4.0f}"
        )


def main():
    apply_style()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    sets = workloads()
    baselines = {
        "SJF": evaluate(sjf_schedule, sets["random_avg"]),
        "HRRN": evaluate(hrrn_schedule, sets["random_avg"]),
    }
    all_rows = []
    for param, (title, values, extra) in SWEEPS.items():
        rows = run_sweep(param, values, extra, sets)
        all_rows.extend(rows)
        print_sweep(param, title, values, rows)
        plot_sweep(param, title, values, rows, baselines)

    path = os.path.join(RESULTS_DIR, "tuning.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["param", "value", "scenario"] + [k for k, _ in METRICS])
        w.writeheader()
        for r in all_rows:
            w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
