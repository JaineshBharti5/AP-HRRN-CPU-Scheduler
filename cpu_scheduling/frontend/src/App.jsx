import { useCallback, useEffect, useState } from 'react'
import { getMeta, getPresets, randomWorkload, simulate } from './api'
import Benchmark from './components/Benchmark'
import Gantt from './components/Gantt'
import Loader from './components/Loader'
import MetricBars from './components/MetricBars'
import MetricsTable from './components/MetricsTable'
import ParamsPanel from './components/ParamsPanel'
import ProcessEditor from './components/ProcessEditor'
import ProcessTables from './components/ProcessTables'
import RandomPanel from './components/RandomPanel'
import WaitingChart from './components/WaitingChart'

const TABS = [
  ['overview', 'Comparison'],
  ['gantt', 'Gantt charts'],
  ['tables', 'Process tables'],
  ['benchmark', 'Random benchmark'],
]

// Keep the loader visible long enough to be seen (the API answers in a few ms).
const MIN_LOADER_MS = 1200
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const toRows = (procs) =>
  procs.map((p) => ({ id: crypto.randomUUID(), pid: String(p.pid), arrival: String(p.arrival), burst: String(p.burst) }))

export default function App() {
  const [meta, setMeta] = useState(null)
  const [presets, setPresets] = useState([])
  const [rows, setRows] = useState([])
  const [params, setParams] = useState(null)
  const [label, setLabel] = useState('')
  const [out, setOut] = useState(null)
  const [tab, setTab] = useState('overview')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const run = useCallback(
    async (rowsArg, paramsArg) => {
      setBusy(true)
      setError('')
      const t0 = Date.now()
      try {
        const body = {
          processes: rowsArg.map((r) => ({ pid: r.pid, arrival: r.arrival, burst: r.burst })),
          params: paramsArg,
        }
        setOut(await simulate(body))
      } catch (e) {
        setError(e.message)
      } finally {
        await sleep(Math.max(0, MIN_LOADER_MS - (Date.now() - t0)))
        setBusy(false)
      }
    },
    [],
  )

  useEffect(() => {
    ;(async () => {
      try {
        const [m, p] = await Promise.all([getMeta(), getPresets()])
        setMeta(m)
        setPresets(p)
        const first = p[0]
        const r = toRows(first.processes)
        setRows(r)
        setParams(m.defaults)
        setLabel(first.title)
        run(r, m.defaults)
      } catch (e) {
        setError(e.message)
      }
    })()
  }, [run])

  const loadPreset = (p) => {
    const r = toRows(p.processes)
    setRows(r)
    setLabel(p.title)
    run(r, params)
  }

  const generate = async (cfg) => {
    setBusy(true)
    setError('')
    try {
      const body = { n: cfg.n, max_arrival: cfg.max_arrival, max_burst: cfg.max_burst }
      if (cfg.seed !== '') body.seed = cfg.seed
      const res = await randomWorkload(body)
      const r = toRows(res.processes)
      setRows(r)
      setLabel(`Random workload (seed ${res.seed})`)
      await run(r, params)
    } catch (e) {
      setError(e.message)
      setBusy(false)
    }
  }

  const edited = (next) => {
    setRows(next)
    setLabel('Custom input')
  }

  if (!meta || !params) {
    return (
      <main className="app">
        <h1>CPU Scheduling Simulator</h1>
        {error ? <div className="error">{error}</div> : <p className="muted">Loading…</p>}
      </main>
    )
  }

  const metricsByAlgo = out && Object.fromEntries(Object.entries(out.results).map(([n, r]) => [n, r.metrics]))

  return (
    <main className="app">
      <header>
        <h1>CPU Scheduling Simulator</h1>
        <p className="muted">
          Compare SJF, HRRN and the new AP-HRRN algorithm. Enter your own processes, load an example, or generate random values.
        </p>
      </header>

      <div className="layout">
        <aside className="side">
          <section className="card">
            <h2>Examples</h2>
            <p className="hint">The cases built in the project (process.py).</p>
            <div className="presets">
              {presets.map((p) => (
                <button key={p.key} className="preset" onClick={() => loadPreset(p)} title={p.description} disabled={busy}>
                  {p.title}
                </button>
              ))}
            </div>
          </section>

          <section className="card">
            <h2>Random values</h2>
            <RandomPanel onGenerate={generate} busy={busy} />
          </section>

          <section className="card">
            <h2>Processes</h2>
            <p className="hint">Current: {label}</p>
            <ProcessEditor rows={rows} setRows={edited} limits={meta.limits} />
          </section>

          <section className="card">
            <h2>AP-HRRN parameters</h2>
            <ParamsPanel params={params} setParams={setParams} defaults={meta.defaults} />
          </section>

          <button className="primary" onClick={() => run(rows, params)} disabled={busy}>
            {busy ? 'Running…' : '▶ Run simulation'}
          </button>
        </aside>

        <section className="main">
          {busy && <Loader />}
          {error && <div className="error">{error}</div>}
          <nav className="tabs" role="tablist">
            {TABS.map(([k, t]) => (
              <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>
                {t}
              </button>
            ))}
          </nav>

          {tab === 'benchmark' ? (
            <Benchmark params={params} defaults={meta.benchmark} />
          ) : busy ? null : !out ? (
            <p className="muted">Run a simulation to see results.</p>
          ) : tab === 'overview' ? (
            <div className="stack">
              <h3>Metrics table</h3>
              <MetricsTable data={metricsByAlgo} />
              <h3>Metric comparison</h3>
              <MetricBars data={metricsByAlgo} />
              <h3>Waiting time per process</h3>
              <WaitingChart results={out.results} />
            </div>
          ) : tab === 'gantt' ? (
            <div className="stack">
              {Object.entries(out.results).map(([n, r]) => (
                <Gantt key={n} name={n} timeline={r.timeline} processes={r.processes} contextSwitches={r.metrics.context_switches} />
              ))}
            </div>
          ) : (
            <ProcessTables results={out.results} />
          )}
        </section>
      </div>
    </main>
  )
}
