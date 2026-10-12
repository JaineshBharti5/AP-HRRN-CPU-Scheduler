from fractions import Fraction
from typing import Callable, List, Tuple

from process import (
    Process,
    Timeline,
    clone,
    compute_metrics,
    finalize,
    merge_timeline,
    phase1_example,
    print_gantt,
    print_metrics,
    print_process_table,
)

ALPHA = 0.5
TAU0 = 6
K = 1.5
WAIT_LIMIT = 24
BOOST = 10

Result = Tuple[List[Process], Timeline]


def _run_nonpreemptive(processes: List[Process], key: Callable) -> Result:
    procs = clone(processes)
    t = min(p.arrival for p in procs)
    timeline: Timeline = []
    finished = 0
    while finished < len(procs):
        ready = [p for p in procs if p.arrival <= t and p.remaining > 0]
        if not ready:
            nxt = min(p.arrival for p in procs if p.remaining > 0)
            timeline.append((None, t, nxt))
            t = nxt
            continue
        chosen = min(ready, key=lambda p: key(p, t))
        timeline.append((chosen.pid, t, t + chosen.burst))
        t += chosen.burst
        chosen.remaining = 0
        finished += 1
    timeline = merge_timeline(timeline)
    finalize(procs, timeline)
    return procs, timeline


def sjf_schedule(processes: List[Process]) -> Result:
    return _run_nonpreemptive(
        processes, lambda p, t: (p.burst, p.arrival, p.pid)
    )


def hrrn_schedule(processes: List[Process]) -> Result:
    return _run_nonpreemptive(
        processes,
        lambda p, t: (-Fraction(t - p.arrival + p.burst, p.burst), p.arrival, p.pid),
    )


def aphrrn_schedule(
    processes: List[Process],
    alpha: float = ALPHA,
    tau0: float = TAU0,
    k: float = K,
    wait_limit: int = WAIT_LIMIT,
    boost: int = BOOST,
    estimator: str = "exact",
) -> Result:
    if estimator not in ("exact", "exp"):
        raise ValueError("estimator must be 'exact' or 'exp'")

    procs = clone(processes)
    n = len(procs)
    k_ratio = Fraction(str(k))
    est = {}
    tau = float(tau0)
    ready: List[Process] = []
    running = None
    timeline: Timeline = []
    finished = 0
    t = min(p.arrival for p in procs)

    def waited(p):
        return t - p.arrival - (p.burst - p.remaining)

    def est_remaining(p):
        return max(est[p.pid] - (p.burst - p.remaining), 1)

    def score(p):
        rem = est_remaining(p)
        w = waited(p)
        return Fraction(w + rem, rem) + boost * (w // wait_limit)

    def best():
        return max(ready, key=lambda p: (score(p), -p.arrival, -p.pid))

    while finished < n:
        for p in procs:
            if p.arrival == t:
                est[p.pid] = p.burst if estimator == "exact" else max(1, int(tau + 0.5))
                ready.append(p)

        if running is None:
            if not ready:
                timeline.append((None, t, t + 1))
                t += 1
                continue
            running = best()
            ready.remove(running)
        elif ready and waited(running) < wait_limit:
            cand = best()
            if score(cand) >= k_ratio * score(running) and est_remaining(cand) < est_remaining(running):
                ready.remove(cand)
                ready.append(running)
                running = cand

        timeline.append((running.pid, t, t + 1))
        running.remaining -= 1
        t += 1

        if running.remaining == 0:
            finished += 1
            tau = alpha * running.burst + (1 - alpha) * tau
            running = None

    timeline = merge_timeline(timeline)
    finalize(procs, timeline)
    return procs, timeline


ALGORITHMS = {
    "SJF": sjf_schedule,
    "HRRN": hrrn_schedule,
    "AP-HRRN": aphrrn_schedule,
}


if __name__ == "__main__":
    for name, algo in ALGORITHMS.items():
        procs, timeline = algo(phase1_example())
        print(f"=== {name} ===")
        print_gantt(timeline)
        print_process_table(procs)
        print_metrics(name, compute_metrics(procs, timeline))
        print()
