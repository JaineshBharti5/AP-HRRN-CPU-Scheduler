"""Tests for the three algorithms. Run:  python -m pytest   (or  python tests/test_scheduler.py)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process import (FIXED_CASES, compute_metrics, idle_gap_case, phase1_example, random_case,
                     simultaneous_case, single_process_case, starvation_case)
from scheduler import ALGORITHMS, aphrrn_schedule, hrrn_schedule, sjf_schedule

# Hand-calculated results for the phase-1 example:
# algorithm -> (timeline, avg waiting, avg turnaround, avg response, max waiting, context switches)
MANUAL = {
    "SJF": ([(1, 0, 8), (3, 8, 10), (4, 10, 11), (5, 11, 12), (2, 12, 19)], 3.8, 7.6, 3.8, 11, 4),
    "HRRN": ([(1, 0, 8), (3, 8, 10), (2, 10, 17), (4, 17, 18), (5, 18, 19)], 6.2, 10.0, 6.2, 9, 4),
    "AP-HRRN": ([(1, 0, 3), (3, 3, 5), (2, 5, 12), (4, 12, 13), (5, 13, 14), (1, 14, 19)], 4.4, 8.2, 2.2, 11, 5),
}


def check_invariants(original, procs, timeline):
    """Rules every valid schedule must follow."""
    for (_, s, e), (_, s2, _) in zip(timeline, timeline[1:]):
        assert e > s and s2 >= e                          # slices are ordered, no overlap
    for p in procs:
        segs = [(s, e) for pid, s, e in timeline if pid == p.pid]
        assert sum(e - s for s, e in segs) == p.burst     # got exactly its burst time
        assert min(s for s, _ in segs) >= p.arrival       # never ran before arriving
        assert p.completion == max(e for _, e in segs)
        assert p.turnaround == p.completion - p.arrival
        assert p.waiting == p.turnaround - p.burst >= 0
        assert p.response == p.start - p.arrival
    assert len(procs) == len(original)


def test_matches_manual_calculation():
    for name, (timeline, wt, tat, rt, max_wt, cs) in MANUAL.items():
        procs, tl = ALGORITHMS[name](phase1_example())
        m = compute_metrics(procs, tl)
        assert tl == timeline, name
        assert (m["max_waiting"], m["context_switches"]) == (max_wt, cs), name
        for got, want in ((m["avg_waiting"], wt), (m["avg_turnaround"], tat), (m["avg_response"], rt)):
            assert abs(got - want) < 1e-9, name


def test_idle_gap():
    expected = [(1, 0, 3), (None, 3, 10), (2, 10, 12), (3, 12, 16)]
    for name, algo in ALGORITHMS.items():
        procs, tl = algo(idle_gap_case())
        assert tl == expected, name
        assert abs(compute_metrics(procs, tl)["cpu_utilization"] - 100 * 9 / 16) < 1e-9, name


def test_single_process():
    for name, algo in ALGORITHMS.items():
        procs, tl = algo(single_process_case())
        p = procs[0]
        assert tl == [(1, 3, 8)], name
        assert (p.start, p.completion, p.waiting, p.turnaround, p.response) == (3, 8, 0, 5, 0), name
        assert compute_metrics(procs, tl)["context_switches"] == 0, name


def test_simultaneous_arrivals():
    assert sjf_schedule(simultaneous_case())[1] == [(2, 0, 2), (4, 2, 4), (1, 4, 8), (3, 8, 14)]
    assert hrrn_schedule(simultaneous_case())[1] == [(1, 0, 4), (2, 4, 6), (4, 6, 8), (3, 8, 14)]
    assert aphrrn_schedule(simultaneous_case())[1] == [(1, 0, 1), (2, 1, 3), (4, 3, 5), (1, 5, 8), (3, 8, 14)]


def test_input_not_modified():
    original = phase1_example()
    for algo in ALGORITHMS.values():
        algo(original)
    assert all(p.remaining == p.burst and p.start is None for p in original)


def test_invariants_fixed_cases():
    for factory in FIXED_CASES.values():
        for algo in ALGORITHMS.values():
            original = factory()
            check_invariants(original, *algo(original))


def test_invariants_random():
    for seed in range(60):
        for n in (1, 2, 5, 12):
            original = random_case(n, seed)
            for algo in ALGORITHMS.values():
                check_invariants(original, *algo(original))
            check_invariants(original, *aphrrn_schedule(original, estimator="exp"))


def test_long_job_not_starved():
    sjf, _ = sjf_schedule(starvation_case())
    ap, _ = aphrrn_schedule(starvation_case())
    long_sjf, long_ap = (next(p for p in procs if p.pid == 2) for procs in (sjf, ap))
    assert (long_sjf.waiting, long_ap.waiting) == (41, 25)
    assert long_ap.completion < long_sjf.completion


def test_bad_estimator_rejected():
    try:
        aphrrn_schedule(phase1_example(), estimator="nope")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"{len(tests)} tests passed")
