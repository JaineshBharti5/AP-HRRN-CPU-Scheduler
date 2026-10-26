"""SJF, HRRN (non-preemptive) and AP-HRRN (our improved, preemptive algorithm)."""
from fractions import Fraction

from process import (clone, compute_metrics, finalize, merge_timeline, phase1_example,
                     print_gantt, print_metrics, print_process_table)

# AP-HRRN settings
ALPHA = 0.5      # smoothing factor for the burst-time estimate
TAU0 = 6         # first burst estimate
K = 1.5          # a newcomer must score k times higher to preempt
WAIT_LIMIT = 24  # aging: every this many waited units ...
BOOST = 10       # ... adds this much to the score


def _run_nonpreemptive(processes, key):
    """Common loop: when the CPU is free, run the ready process with the smallest key to the end."""
    procs = clone(processes)
    t = min(p.arrival for p in procs)
    timeline, finished = [], 0
    while finished < len(procs):
        ready = [p for p in procs if p.arrival <= t and p.remaining > 0]
        if not ready:                                   # CPU idle until next arrival
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


def sjf_schedule(processes):
    """Shortest Job First: smallest burst goes first."""
    return _run_nonpreemptive(processes, lambda p, t: (p.burst, p.arrival, p.pid))


def hrrn_schedule(processes):
    """Highest Response Ratio Next: ratio = (waiting + burst) / burst, highest goes first."""
    return _run_nonpreemptive(
        processes, lambda p, t: (-Fraction(t - p.arrival + p.burst, p.burst), p.arrival, p.pid))


def aphrrn_schedule(processes, alpha=ALPHA, tau0=TAU0, k=K, wait_limit=WAIT_LIMIT,
                    boost=BOOST, estimator="exact"):
    """Adaptive Preemptive HRRN: decides every time unit, can preempt, ages long waiters."""
    if estimator not in ("exact", "exp"):
        raise ValueError("estimator must be 'exact' or 'exp'")

    procs = clone(processes)
    k_ratio = Fraction(str(k))
    est, ready, running, timeline, finished = {}, [], None, [], 0
    tau = float(tau0)                       # running average of finished bursts
    t = min(p.arrival for p in procs)

    def waited(p):
        return t - p.arrival - (p.burst - p.remaining)

    def est_remaining(p):
        return max(est[p.pid] - (p.burst - p.remaining), 1)

    def score(p):                           # response ratio + aging boost
        rem, w = est_remaining(p), waited(p)
        return Fraction(w + rem, rem) + boost * (w // wait_limit)

    def best():
        return max(ready, key=lambda p: (score(p), -p.arrival, -p.pid))

    while finished < len(procs):
        for p in procs:                     # new arrivals join the ready queue
            if p.arrival == t:
                est[p.pid] = p.burst if estimator == "exact" else max(1, int(tau + 0.5))
                ready.append(p)

        if running is None:                 # CPU free: pick the best process
            if not ready:
                timeline.append((None, t, t + 1))
                t += 1
                continue
            running = best()
            ready.remove(running)
        elif ready and waited(running) < wait_limit:   # preempt only if clearly better
            cand = best()
            if score(cand) >= k_ratio * score(running) and est_remaining(cand) < est_remaining(running):
                ready.remove(cand)
                ready.append(running)
                running = cand

        timeline.append((running.pid, t, t + 1))        # run for one time unit
        running.remaining -= 1
        t += 1

        if running.remaining == 0:
            finished += 1
            tau = alpha * running.burst + (1 - alpha) * tau
            running = None

    timeline = merge_timeline(timeline)
    finalize(procs, timeline)
    return procs, timeline


ALGORITHMS = {"SJF": sjf_schedule, "HRRN": hrrn_schedule, "AP-HRRN": aphrrn_schedule}


if __name__ == "__main__":
    for name, algo in ALGORITHMS.items():
        procs, timeline = algo(phase1_example())
        print(f"=== {name} ===")
        print_gantt(timeline)
        print_process_table(procs)
        print_metrics(name, compute_metrics(procs, timeline))
        print()
