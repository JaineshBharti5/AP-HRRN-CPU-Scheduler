import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

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
    return [Process(p.pid, p.arrival, p.burst) for p in processes]


def phase1_example() -> List[Process]:
    return [
        Process(1, 0, 8),
        Process(2, 1, 7),
        Process(3, 2, 2),
        Process(4, 9, 1),
        Process(5, 10, 1),
    ]


def starvation_case() -> List[Process]:
    procs = [Process(1, 0, 2), Process(2, 1, 20)]
    for i in range(3, 23):
        procs.append(Process(i, i - 1, 2))
    return procs


def many_short_case() -> List[Process]:
    procs = []
    for i in range(1, 16):
        procs.append(Process(i, (i - 1) * 2, 1 + (i % 3)))
    procs.append(Process(16, 3, 12))
    return procs


def mixed_case() -> List[Process]:
    data = [(0, 6), (1, 14), (2, 3), (4, 9), (5, 2), (7, 11), (9, 4), (12, 7), (15, 1), (18, 5)]
    return [Process(i + 1, a, b) for i, (a, b) in enumerate(data)]


def idle_gap_case() -> List[Process]:
    return [Process(1, 0, 3), Process(2, 10, 2), Process(3, 11, 4)]


def single_process_case() -> List[Process]:
    return [Process(1, 3, 5)]


def simultaneous_case() -> List[Process]:
    return [Process(1, 0, 4), Process(2, 0, 2), Process(3, 0, 6), Process(4, 0, 2)]


def random_case(n: int = 10, seed: int = 42, max_arrival: int = 30, max_burst: int = 15) -> List[Process]:
    rng = random.Random(seed)
    return [
        Process(i + 1, rng.randint(0, max_arrival), rng.randint(1, max_burst))
        for i in range(n)
    ]


FIXED_CASES = {
    "phase1": phase1_example,
    "mixed": mixed_case,
    "starvation": starvation_case,
    "many_short": many_short_case,
    "idle_gap": idle_gap_case,
    "single": single_process_case,
    "simultaneous": simultaneous_case,
}


def merge_timeline(timeline: Timeline) -> Timeline:
    merged: Timeline = []
    for pid, s, e in timeline:
        if e <= s:
            continue
        if merged and merged[-1][0] == pid and merged[-1][2] == s:
            merged[-1] = (pid, merged[-1][1], e)
        else:
            merged.append((pid, s, e))
    return merged


def finalize(processes: List[Process], timeline: Timeline) -> None:
    for p in processes:
        segs = [(s, e) for pid, s, e in timeline if pid == p.pid]
        p.start = min(s for s, _ in segs)
        p.completion = max(e for _, e in segs)
        p.remaining = 0
        p.turnaround = p.completion - p.arrival
        p.waiting = p.turnaround - p.burst
        p.response = p.start - p.arrival


def context_switches(timeline: Timeline) -> int:
    run = [pid for pid, _, _ in merge_timeline(timeline) if pid is not None]
    return sum(1 for a, b in zip(run, run[1:]) if a != b)


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


def print_process_table(processes: List[Process]) -> None:
    header = f"{'PID':>4} {'AT':>4} {'BT':>4} {'Start':>6} {'CT':>4} {'TAT':>5} {'WT':>4} {'RT':>4}"
    print(header)
    print("-" * len(header))
    for p in sorted(processes, key=lambda x: x.pid):
        print(
            f"{'P' + str(p.pid):>4} {p.arrival:>4} {p.burst:>4} {p.start:>6} "
            f"{p.completion:>4} {p.turnaround:>5} {p.waiting:>4} {p.response:>4}"
        )


def print_metrics(name: str, metrics: dict) -> None:
    print(f"[{name}]")
    print(f"  Avg waiting      : {metrics['avg_waiting']:.2f}")
    print(f"  Avg turnaround   : {metrics['avg_turnaround']:.2f}")
    print(f"  Avg response     : {metrics['avg_response']:.2f}")
    print(f"  Max waiting      : {metrics['max_waiting']}")
    print(f"  Context switches : {metrics['context_switches']}")
    print(f"  CPU utilization  : {metrics['cpu_utilization']:.1f}%")


def print_gantt(timeline: Timeline) -> None:
    parts = []
    for pid, s, e in merge_timeline(timeline):
        label = "idle" if pid is None else f"P{pid}"
        parts.append(f"{label} ({s}-{e})")
    print("| " + " | ".join(parts) + " |")
