"""Process data, test workloads and metric calculation (shared by all algorithms)."""
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Timeline = list of (pid, start, end); pid None means the CPU was idle.
Timeline = List[Tuple[Optional[int], int, int]]


@dataclass
class Process:
    pid: int
    arrival: int
    burst: int
    remaining: int = 0
    start: Optional[int] = None
    completion: Optional[int] = None
    waiting: Optional[int] = None
    turnaround: Optional[int] = None
    response: Optional[int] = None

    def __post_init__(self):
        if self.remaining == 0:
            self.remaining = self.burst


def clone(processes: List[Process]) -> List[Process]:
    """Fresh copies, so an algorithm never changes the caller's list."""
    return [Process(p.pid, p.arrival, p.burst) for p in processes]


def make(pairs) -> List[Process]:
    """Build processes P1, P2, ... from (arrival, burst) pairs."""
    return [Process(i + 1, a, b) for i, (a, b) in enumerate(pairs)]


# ---------- ready-made workloads ----------
def phase1_example():
    return make([(0, 8), (1, 7), (2, 2), (9, 1), (10, 1)])


def starvation_case():  # one long job (P2) while short jobs keep arriving
    return make([(0, 2), (1, 20)] + [(a, 2) for a in range(2, 22)])


def many_short_case():
    return make([((i - 1) * 2, 1 + i % 3) for i in range(1, 16)] + [(3, 12)])


def mixed_case():
    return make([(0, 6), (1, 14), (2, 3), (4, 9), (5, 2), (7, 11), (9, 4), (12, 7), (15, 1), (18, 5)])


def idle_gap_case():
    return make([(0, 3), (10, 2), (11, 4)])


def single_process_case():
    return make([(3, 5)])


def simultaneous_case():
    return make([(0, 4), (0, 2), (0, 6), (0, 2)])


def random_case(n=10, seed=42, max_arrival=30, max_burst=15):
    rng = random.Random(seed)  # same seed -> same workload
    return [Process(i + 1, rng.randint(0, max_arrival), rng.randint(1, max_burst)) for i in range(n)]


FIXED_CASES = {
    "phase1": phase1_example,
    "mixed": mixed_case,
    "starvation": starvation_case,
    "many_short": many_short_case,
    "idle_gap": idle_gap_case,
    "single": single_process_case,
    "simultaneous": simultaneous_case,
}


# ---------- timeline and metrics ----------
def merge_timeline(timeline: Timeline) -> Timeline:
    """Join back-to-back slices of the same process into one block."""
    merged = []
    for pid, s, e in timeline:
        if e <= s:
            continue
        if merged and merged[-1][0] == pid and merged[-1][2] == s:
            merged[-1] = (pid, merged[-1][1], e)
        else:
            merged.append((pid, s, e))
    return merged


def finalize(processes: List[Process], timeline: Timeline) -> None:
    """Fill start, completion, turnaround, waiting and response for every process."""
    for p in processes:
        segs = [(s, e) for pid, s, e in timeline if pid == p.pid]
        p.start = min(s for s, _ in segs)
        p.completion = max(e for _, e in segs)
        p.remaining = 0
        p.turnaround = p.completion - p.arrival  # TAT = CT - AT
        p.waiting = p.turnaround - p.burst        # WT  = TAT - BT
        p.response = p.start - p.arrival          # RT  = first start - AT


def context_switches(timeline: Timeline) -> int:
    run = [pid for pid, _, _ in merge_timeline(timeline) if pid is not None]
    return sum(a != b for a, b in zip(run, run[1:]))


def compute_metrics(processes: List[Process], timeline: Timeline) -> dict:
    n = len(processes)
    busy = sum(e - s for pid, s, e in timeline if pid is not None)
    span = max(p.completion for p in processes) - min(p.arrival for p in processes)
    return {
        "avg_waiting": sum(p.waiting for p in processes) / n,
        "avg_turnaround": sum(p.turnaround for p in processes) / n,
        "avg_response": sum(p.response for p in processes) / n,
        "max_waiting": max(p.waiting for p in processes),
        "context_switches": context_switches(timeline),
        "cpu_utilization": 100.0 * busy / span,
    }


# ---------- console output ----------
def print_process_table(processes: List[Process]) -> None:
    header = f"{'PID':>4} {'AT':>4} {'BT':>4} {'Start':>6} {'CT':>4} {'TAT':>5} {'WT':>4} {'RT':>4}"
    print(header + "\n" + "-" * len(header))
    for p in sorted(processes, key=lambda x: x.pid):
        print(f"{'P' + str(p.pid):>4} {p.arrival:>4} {p.burst:>4} {p.start:>6} "
              f"{p.completion:>4} {p.turnaround:>5} {p.waiting:>4} {p.response:>4}")


def print_metrics(name: str, m: dict) -> None:
    print(f"[{name}]")
    print(f"  Avg waiting      : {m['avg_waiting']:.2f}")
    print(f"  Avg turnaround   : {m['avg_turnaround']:.2f}")
    print(f"  Avg response     : {m['avg_response']:.2f}")
    print(f"  Max waiting      : {m['max_waiting']}")
    print(f"  Context switches : {m['context_switches']}")
    print(f"  CPU utilization  : {m['cpu_utilization']:.1f}%")


def print_gantt(timeline: Timeline) -> None:
    parts = [f"{'idle' if pid is None else f'P{pid}'} ({s}-{e})" for pid, s, e in merge_timeline(timeline)]
    print("| " + " | ".join(parts) + " |")
