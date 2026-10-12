import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process import (
    FIXED_CASES,
    compute_metrics,
    idle_gap_case,
    phase1_example,
    random_case,
    simultaneous_case,
    single_process_case,
    starvation_case,
)
from scheduler import ALGORITHMS, aphrrn_schedule, hrrn_schedule, sjf_schedule

SJF_TIMELINE = [(1, 0, 8), (3, 8, 10), (4, 10, 11), (5, 11, 12), (2, 12, 19)]
HRRN_TIMELINE = [(1, 0, 8), (3, 8, 10), (2, 10, 17), (4, 17, 18), (5, 18, 19)]
APHRRN_TIMELINE = [(1, 0, 3), (3, 3, 5), (2, 5, 12), (4, 12, 13), (5, 13, 14), (1, 14, 19)]


def close(a, b):
    return abs(a - b) < 1e-9


def check_invariants(original, procs, timeline):
    prev_end = None
    for pid, s, e in timeline:
        assert e > s
        if prev_end is not None:
            assert s >= prev_end
        prev_end = e
    for p in procs:
        segs = [(s, e) for pid, s, e in timeline if pid == p.pid]
        assert sum(e - s for s, e in segs) == p.burst
        assert min(s for s, _ in segs) >= p.arrival
        assert p.completion == max(e for _, e in segs)
        assert p.turnaround == p.completion - p.arrival
        assert p.waiting == p.turnaround - p.burst
        assert p.waiting >= 0
        assert p.response == p.start - p.arrival
        assert p.remaining == 0
    assert len(procs) == len(original)


def test_sjf_matches_manual():
    procs, tl = sjf_schedule(phase1_example())
    assert tl == SJF_TIMELINE
    m = compute_metrics(procs, tl)
    assert close(m["avg_waiting"], 3.8)
    assert close(m["avg_turnaround"], 7.6)
    assert close(m["avg_response"], 3.8)
    assert m["max_waiting"] == 11
    assert m["context_switches"] == 4


def test_hrrn_matches_manual():
    procs, tl = hrrn_schedule(phase1_example())
    assert tl == HRRN_TIMELINE
    m = compute_metrics(procs, tl)
    assert close(m["avg_waiting"], 6.2)
    assert close(m["avg_turnaround"], 10.0)
    assert close(m["avg_response"], 6.2)
    assert m["max_waiting"] == 9
    assert m["context_switches"] == 4


def test_aphrrn_matches_manual():
    procs, tl = aphrrn_schedule(phase1_example())
    assert tl == APHRRN_TIMELINE
    m = compute_metrics(procs, tl)
    assert close(m["avg_waiting"], 4.4)
    assert close(m["avg_turnaround"], 8.2)
    assert close(m["avg_response"], 2.2)
    assert m["max_waiting"] == 11
    assert m["context_switches"] == 5
    assert close(m["cpu_utilization"], 100.0)


def test_idle_gap():
    expected = [(1, 0, 3), (None, 3, 10), (2, 10, 12), (3, 12, 16)]
    for name, algo in ALGORITHMS.items():
        procs, tl = algo(idle_gap_case())
        assert tl == expected, name
        m = compute_metrics(procs, tl)
        assert close(m["cpu_utilization"], 100.0 * 9 / 16), name


def test_single_process():
    for name, algo in ALGORITHMS.items():
        procs, tl = algo(single_process_case())
        assert tl == [(1, 3, 8)], name
        p = procs[0]
        assert (p.start, p.completion, p.waiting, p.turnaround, p.response) == (3, 8, 0, 5, 0), name
        m = compute_metrics(procs, tl)
        assert m["context_switches"] == 0, name
        assert close(m["cpu_utilization"], 100.0), name


def test_simultaneous_arrivals():
    _, tl = sjf_schedule(simultaneous_case())
    assert tl == [(2, 0, 2), (4, 2, 4), (1, 4, 8), (3, 8, 14)]
    _, tl = hrrn_schedule(simultaneous_case())
    assert tl == [(1, 0, 4), (2, 4, 6), (4, 6, 8), (3, 8, 14)]
    _, tl = aphrrn_schedule(simultaneous_case())
    assert tl == [(1, 0, 1), (2, 1, 3), (4, 3, 5), (1, 5, 8), (3, 8, 14)]


def test_input_not_modified():
    original = phase1_example()
    for algo in ALGORITHMS.values():
        algo(original)
    assert all(p.remaining == p.burst and p.start is None for p in original)


def test_invariants_fixed_cases():
    for case_name, factory in FIXED_CASES.items():
        for name, algo in ALGORITHMS.items():
            original = factory()
            procs, tl = algo(original)
            check_invariants(original, procs, tl)


def test_invariants_random():
    for seed in range(60):
        for n in (1, 2, 5, 12):
            for name, algo in ALGORITHMS.items():
                original = random_case(n, seed)
                procs, tl = algo(original)
                check_invariants(original, procs, tl)
            original = random_case(n, seed)
            procs, tl = aphrrn_schedule(original, estimator="exp")
            check_invariants(original, procs, tl)


def test_long_job_not_starved():
    p_sjf, _ = sjf_schedule(starvation_case())
    p_ap, _ = aphrrn_schedule(starvation_case())
    long_sjf = next(p for p in p_sjf if p.pid == 2)
    long_ap = next(p for p in p_ap if p.pid == 2)
    assert long_sjf.waiting == 41
    assert long_ap.waiting == 25
    assert long_ap.completion < long_sjf.completion


def test_exp_estimator_runs():
    original = phase1_example()
    procs, tl = aphrrn_schedule(original, estimator="exp")
    check_invariants(original, procs, tl)


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
