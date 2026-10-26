import { useState } from 'react'

export default function RandomPanel({ onGenerate, busy }) {
  const [cfg, setCfg] = useState({ n: 10, max_arrival: 30, max_burst: 15, seed: '' })
  const set = (k) => (e) => setCfg({ ...cfg, [k]: e.target.value })

  return (
    <div className="random">
      <div className="fields">
        <label>
          Processes
          <input type="number" min="1" value={cfg.n} onChange={set('n')} />
        </label>
        <label>
          Max arrival
          <input type="number" min="0" value={cfg.max_arrival} onChange={set('max_arrival')} />
        </label>
        <label>
          Max burst
          <input type="number" min="1" value={cfg.max_burst} onChange={set('max_burst')} />
        </label>
        <label>
          Seed (optional)
          <input type="number" min="0" placeholder="random" value={cfg.seed} onChange={set('seed')} />
        </label>
      </div>
      <button onClick={() => onGenerate(cfg)} disabled={busy}>
        🎲 Generate random values
      </button>
    </div>
  )
}
