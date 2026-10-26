"""Tests for process.py (data, metrics, random workloads)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process import FIXED_CASES, clone, compute_metrics, finalize, phase1_example, random_case

# Same hand-calculated timelines as test_scheduler.py; here only the metric formulas are tested.
# name -> (timeline, avg waiting, avg turnaround, avg response, max waiting, context switches)
MANUAL = {
    "SJF": ([(1, 0, 8), (3, 8, 10), (4, 10, 11), (5, 11, 12), (2, 12, 19)], 3.8, 7.6, 3.8, 11, 4),
    "HRRN": ([(1, 0, 8), (3, 8, 10), (2, 10, 17), (4, 17, 18), (5, 18, 19)], 6.2, 10.0, 6.2, 9, 4),
    "AP-HRRN": ([(1, 0, 3), (3, 3, 5), (2, 5, 12), (4, 12, 13), (5, 13, 14), (1, 14, 19)], 4.4, 8.2, 2.2, 11, 5),
}


def test_metrics_from_manual_timelines():
    for name, (timeline, wt, tat, rt, max_wt, cs) in MANUAL.items():
        procs = phase1_example()
        finalize(procs, timeline)
        m = compute_metrics(procs, timeline)
        assert (m["max_waiting"], m["context_switches"], m["cpu_utilization"]) == (max_wt, cs, 100.0), name
        for got, want in ((m["avg_waiting"], wt), (m["avg_turnaround"], tat), (m["avg_response"], rt)):
            assert abs(got - want) < 1e-9, name


def test_clone_is_independent():
    a = phase1_example()
    b = clone(a)
    b[0].remaining = 0
    assert a[0].remaining == 8


def test_random_is_reproducible():
    pairs = lambda seed: [(p.arrival, p.burst) for p in random_case(10, seed)]
    assert pairs(7) == pairs(7)
    assert pairs(7) != pairs(8)


def test_fixed_cases_valid():
    for name, factory in FIXED_CASES.items():
        procs = factory()
        assert len({p.pid for p in procs}) == len(procs), name           # unique PIDs
        assert all(p.burst > 0 and p.arrival >= 0 for p in procs), name


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"{len(tests)} tests passed")
