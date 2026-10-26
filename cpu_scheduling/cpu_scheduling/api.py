"""Small Flask API: the React frontend calls our SJF / HRRN / AP-HRRN code through it.
Run:  python api.py   ->  http://127.0.0.1:5000
"""
import random

from flask import Flask, jsonify, request

from compare import METRICS, RANDOM_FIRST_SEED, RANDOM_KW, RANDOM_RUNS, evaluate
from process import FIXED_CASES, Process, compute_metrics, random_case
from scheduler import ALGORITHMS, ALPHA, BOOST, K, TAU0, WAIT_LIMIT

app = Flask(__name__)
app.json.sort_keys = False  # keep order: SJF, HRRN, AP-HRRN

LIMITS = {"processes": 60, "burst": 200, "arrival": 1000}
DEFAULTS = {"alpha": ALPHA, "tau0": TAU0, "k": K, "wait_limit": WAIT_LIMIT, "boost": BOOST, "estimator": "exact"}
RANGES = {"alpha": (0, 1), "tau0": (1, 200), "k": (1, 100), "wait_limit": (1, 10**6), "boost": (0, 1000)}

# Example buttons: key -> (title, tooltip)
PRESETS = {
    "phase1": ("Phase 1 example (5 processes)", "The basic example used to verify all three algorithms."),
    "mixed": ("Normal mixed load", "Ten processes with mixed bursts and arrivals."),
    "starvation": ("Starvation-prone", "One long job (P2, burst 20) while short jobs keep arriving - SJF starves P2."),
    "many_short": ("Many short jobs", "Fifteen short jobs plus one long job arriving at t=3."),
    "idle_gap": ("Idle gap", "CPU sits idle between t=3 and t=10."),
    "single": ("Single process", "Edge case: only one process, arrives at t=3."),
    "simultaneous": ("Simultaneous arrival", "All four processes arrive at t=0."),
}


class BadRequest(Exception):
    """Invalid input -> sent back to the frontend as {"error": ...}."""


@app.errorhandler(BadRequest)
def bad_request(err):
    return jsonify({"error": str(err)}), 400


def number(value, name, low, high, whole=True):
    """Convert to int/float and check low <= value <= high."""
    try:
        v = int(value) if whole else float(value)
    except (TypeError, ValueError):
        raise BadRequest(f"{name} must be a number")
    if not low <= v <= high:
        raise BadRequest(f"{name} must be between {low} and {high}")
    return v


def serialize(procs):
    return [{"pid": p.pid, "arrival": p.arrival, "burst": p.burst} for p in procs]


def read_processes(rows):
    """Validate the process table sent by the frontend."""
    if not isinstance(rows, list) or not rows:
        raise BadRequest("Add at least one process")
    if len(rows) > LIMITS["processes"]:
        raise BadRequest(f"At most {LIMITS['processes']} processes are allowed")
    procs = []
    for r in rows:
        pid = number(r.get("pid"), "PID", 1, 10**6)
        if any(p.pid == pid for p in procs):
            raise BadRequest(f"PID P{pid} is used twice")
        procs.append(Process(pid, number(r.get("arrival"), f"P{pid}: arrival", 0, LIMITS["arrival"]),
                             number(r.get("burst"), f"P{pid}: burst", 1, LIMITS["burst"])))
    return procs


def read_params(raw):
    """AP-HRRN parameters; anything missing falls back to the defaults."""
    raw = {**DEFAULTS, **(raw or {})}
    if raw["estimator"] not in ("exact", "exp"):
        raise BadRequest("estimator must be 'exact' or 'exp'")
    params = {k: number(raw[k], k, lo, hi, whole=k in ("wait_limit", "boost")) for k, (lo, hi) in RANGES.items()}
    return {**params, "estimator": raw["estimator"]}


def run(name, procs, params):
    """Only AP-HRRN takes the extra parameters."""
    return ALGORITHMS[name](procs, **params) if name == "AP-HRRN" else ALGORITHMS[name](procs)


@app.get("/api/meta")
def meta():
    return jsonify({
        "metrics": [{"key": k, "label": label} for k, label in METRICS],
        "defaults": DEFAULTS,
        "algorithms": list(ALGORITHMS),
        "limits": LIMITS,
        "benchmark": {"runs": RANDOM_RUNS, "first_seed": RANDOM_FIRST_SEED, **RANDOM_KW},
    })


@app.get("/api/presets")
def presets():
    """The built-in example cases from process.py."""
    return jsonify([{"key": key, "title": PRESETS[key][0], "description": PRESETS[key][1],
                     "processes": serialize(make())} for key, make in FIXED_CASES.items()])


@app.post("/api/random")
def random_workload():
    """Random processes via random_case() (same seed -> same processes)."""
    b = request.get_json(silent=True) or {}
    n = number(b.get("n", 10), "Processes", 1, LIMITS["processes"])
    max_arrival = number(b.get("max_arrival", 30), "Max arrival", 0, LIMITS["arrival"])
    max_burst = number(b.get("max_burst", 15), "Max burst", 1, LIMITS["burst"])
    seed = number(b["seed"], "Seed", 0, 10**9) if b.get("seed") not in (None, "") else random.randint(0, 10**6)
    return jsonify({"seed": seed, "processes": serialize(random_case(n, seed, max_arrival, max_burst))})


@app.post("/api/simulate")
def simulate():
    """Run SJF, HRRN and AP-HRRN on the same processes."""
    b = request.get_json(silent=True) or {}
    procs, params = read_processes(b.get("processes")), read_params(b.get("params"))
    results = {}
    for name in ALGORITHMS:
        done, timeline = run(name, procs, params)
        results[name] = {
            "processes": [{"pid": p.pid, "arrival": p.arrival, "burst": p.burst, "start": p.start,
                           "completion": p.completion, "turnaround": p.turnaround,
                           "waiting": p.waiting, "response": p.response}
                          for p in sorted(done, key=lambda p: p.pid)],
            "timeline": [{"pid": pid, "start": s, "end": e} for pid, s, e in timeline],
            "metrics": compute_metrics(done, timeline),
        }
    return jsonify({"processes": serialize(procs), "params": params, "results": results})


@app.post("/api/benchmark")
def benchmark():
    """Average the metrics over many random workloads."""
    b = request.get_json(silent=True) or {}
    runs = number(b.get("runs", RANDOM_RUNS), "Runs", 1, 200)
    n = number(b.get("n", RANDOM_KW["n"]), "Processes per run", 1, 30)
    max_arrival = number(b.get("max_arrival", RANDOM_KW["max_arrival"]), "Max arrival", 0, LIMITS["arrival"])
    max_burst = number(b.get("max_burst", RANDOM_KW["max_burst"]), "Max burst", 1, 50)
    params = read_params(b.get("params"))
    workloads = [random_case(n, s, max_arrival, max_burst)
                 for s in range(RANDOM_FIRST_SEED, RANDOM_FIRST_SEED + runs)]
    metrics = {name: evaluate(lambda p, name=name: run(name, p, params), workloads) for name in ALGORITHMS}
    return jsonify({"runs": runs, "n": n, "metrics": metrics})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
