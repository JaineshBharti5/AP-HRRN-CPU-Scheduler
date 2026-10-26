# CPU Scheduling Simulator (SJF vs HRRN vs AP-HRRN)

Python simulators (`cpu_scheduling/`) + Flask API + React (Vite) frontend (`frontend/`).

## Run

Terminal 1 (backend, http://127.0.0.1:5000):

    pip install flask
    cd cpu_scheduling
    python api.py

Terminal 2 (frontend, http://localhost:5173):

    cd frontend
    npm install
    npm run dev

## What the UI does
- Enter processes manually (PID, arrival, burst), add/remove rows.
- Load the built-in examples (phase1, mixed, starvation, many_short, idle_gap, single, simultaneous).
- Generate random processes (count, max arrival, max burst, optional seed).
- Tune AP-HRRN parameters (k, wait limit, boost, alpha, tau0, estimator).
- Output: metrics table, 6 metric bar graphs, waiting-time-per-process graph,
  Gantt chart per algorithm, per-process tables (start/completion/TAT/WT/RT),
  and a random benchmark averaged over many workloads.

The existing scripts (scheduler.py, process.py, compare.py, tuning.py) are unchanged.
