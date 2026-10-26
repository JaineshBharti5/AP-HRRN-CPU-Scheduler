import { COLORS } from '../constants'

export default function WaitingChart({ results }) {
  const names = Object.keys(results)
  const pids = results[names[0]].processes.map((p) => p.pid)
  const byAlgo = Object.fromEntries(names.map((n) => [n, Object.fromEntries(results[n].processes.map((p) => [p.pid, p.waiting]))]))
  const maxV = Math.max(1, ...names.flatMap((n) => pids.map((p) => byAlgo[n][p]))) * 1.1
  const W = Math.max(640, pids.length * 62)
  const H = 260
  const base = H - 28
  const group = (W - 50) / pids.length
  const bw = Math.min(16, (group - 8) / names.length)
  const yTicks = 4

  return (
    <div className="scroll">
      <svg viewBox={`0 0 ${W} ${H}`} style={{ minWidth: W > 700 ? W : undefined }} role="img" aria-label="Waiting time per process">
        {Array.from({ length: yTicks + 1 }, (_, i) => {
          const v = (maxV / yTicks) * i
          const y = base - (v / maxV) * (base - 14)
          return (
            <g key={i}>
              <line x1="40" x2={W} y1={y} y2={y} className="gridline" />
              <text x="34" y={y + 4} textAnchor="end" className="tick">
                {Math.round(v)}
              </text>
            </g>
          )
        })}
        {pids.map((pid, gi) => (
          <g key={pid}>
            {names.map((n, ni) => {
              const v = byAlgo[n][pid]
              const h = (v / maxV) * (base - 14)
              const bx = 46 + gi * group + (group - bw * names.length) / 2 + ni * bw
              return (
                <rect key={n} x={bx} y={base - h} width={bw - 1} height={h} fill={COLORS[n]} rx="2">
                  <title>{`P${pid} · ${n}: waited ${v}`}</title>
                </rect>
              )
            })}
            <text x={46 + gi * group + group / 2} y={H - 10} textAnchor="middle" className="tick">
              P{pid}
            </text>
          </g>
        ))}
      </svg>
      <div className="legend">
        {names.map((n) => (
          <span key={n}>
            <span className="dot" style={{ background: COLORS[n] }} /> {n}
          </span>
        ))}
      </div>
    </div>
  )
}
