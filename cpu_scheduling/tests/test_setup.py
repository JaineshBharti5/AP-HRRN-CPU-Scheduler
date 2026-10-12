import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process import (
    FIXED_CASES,
    clone,
    compute_metrics,
    finalize,
    phase1_example,
    random_case,
)

SJF_TIMELINE = [(1, 0, 8), (3, 8, 10), (4, 10, 11), (5, 11, 12), (2, 12, 19)]
HRRN_TIMELINE = [(1, 0, 8), (3, 8, 10), (2, 10, 17), (4, 17, 18), (5, 18, 19)]
APHRRN_TIMELINE = [(1, 0, 3), (3, 3, 5), (2, 5, 12), (4, 12, 13), (5, 13, 14), (1, 14, 19)]


def run(timeline):
    procs = phase1_example()
    finalize(procs, timeline)
    return compute_metrics(procs, timeline)


def close(a, b):
    return abs(a - b) < 1e-9


def test_sjf_manual():
    m = run(SJF_TIMELINE)
    assert close(m["avg_waiting"], 3.8)
    assert close(m["avg_turnaround"], 7.6)
    assert close(m["avg_response"], 3.8)
    assert m["max_waiting"] == 11
    assert m["context_switches"] == 4
    assert close(m["cpu_utilization"], 100.0)


def test_hrrn_manual():
    m = run(HRRN_TIMELINE)
    assert close(m["avg_waiting"], 6.2)
    assert close(m["avg_turnaround"], 10.0)
    assert close(m["avg_response"], 6.2)
    assert m["max_waiting"] == 9
    assert m["context_switches"] == 4


def test_aphrrn_manual():
    m = run(APHRRN_TIMELINE)
    assert close(m["avg_waiting"], 4.4)
    assert close(m["avg_turnaround"], 8.2)
    assert close(m["avg_response"], 2.2)
    assert m["max_waiting"] == 11
    assert m["context_switches"] == 5


def test_clone_is_independent():
    a = phase1_example()
    b = clone(a)
    b[0].remaining = 0
    assert a[0].remaining == 8


def test_random_is_reproducible():
    a = [(p.arrival, p.burst) for p in random_case(10, seed=7)]
    b = [(p.arrival, p.burst) for p in random_case(10, seed=7)]
    c = [(p.arrival, p.burst) for p in random_case(10, seed=8)]
    assert a == b
    assert a != c


def test_fixed_cases_valid():
    for name, factory in FIXED_CASES.items():
        procs = factory()
        pids = [p.pid for p in procs]
        assert len(pids) == len(set(pids)), name
        assert all(p.burst > 0 and p.arrival >= 0 for p in procs), name


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"{len(tests)} tests passed")
