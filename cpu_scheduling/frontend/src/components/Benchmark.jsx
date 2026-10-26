import { useState } from 'react'
import { benchmark } from '../api'
import Loader from './Loader'
import MetricBars from './MetricBars'
import MetricsTable from './MetricsTable'

export default function Benchmark({ params, defaults }) {
  const [cfg, setCfg] = useState({ runs: defaults.runs, n: defaults.n, max_arrival: defaults.max_arrival, max_burst: defaults.max_burst })
  const [out, setOut] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setCfg({ ...cfg, [k]: e.target.value })

  const run = async () => {
    setBusy(true)
    setError('')
    const t0 = Date.now()
    try {
      setOut(await benchmark({ ...cfg, params }))
    } catch (e) {
      setError(e.message)
    } finally {
      await new Promise((r) => setTimeout(r, Math.max(0, 1200 - (Date.now() - t0))))
      setBusy(false)
    }
  }

  return (
    <div className="stack">
      <p className="muted">
        Runs all three algorithms on many seeded random workloads and averages the metrics (same idea as the “random average” in compare.py).
      </p>
      <div className="fields">
        <label>
          Runs
          <input type="number" min="1" max="200" value={cfg.runs} onChange={set('runs')} />
        </label>
        <label>
          Processes / run
          <input type="number" min="1" max="30" value={cfg.n} onChange={set('n')} />
        </label>
        <label>
          Max arrival
          <input type="number" min="0" value={cfg.max_arrival} onChange={set('max_arrival')} />
        </label>
        <label>
          Max burst
          <input type="number" min="1" max="50" value={cfg.max_burst} onChange={set('max_burst')} />
        </label>
      </div>
      <div>
        <button onClick={run} disabled={busy}>
          {busy ? 'Running…' : 'Run benchmark'}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {busy && <Loader overlay={false} text="Running benchmark" />}
      {!busy && out && (
        <>
          <h3>
            Average over {out.runs} random workloads ({out.n} processes each)
          </h3>
          <MetricsTable data={out.metrics} />
          <MetricBars data={out.metrics} />
        </>
      )}
    </div>
  )
}
