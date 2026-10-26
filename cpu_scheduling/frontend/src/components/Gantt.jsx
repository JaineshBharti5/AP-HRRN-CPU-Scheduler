import { COLORS } from '../constants'

const ROW = 24
const LEFT = 40
const TOP = 8
const AXIS = 24
const W = 1000

function niceStep(max) {
  for (const s of [1, 2, 5, 10, 20, 25, 50, 100, 200, 500]) if (max / s <= 20) return s
  return 1000
}

export default function Gantt({ name, timeline, processes, contextSwitches }) {
  const pids = processes.map((p) => p.pid).sort((a, b) => a - b)
  const row = Object.fromEntries(pids.map((pid, i) => [pid, i]))
  const end = Math.max(...timeline.map((s) => s.end))
  const start = Math.min(...timeline.map((s) => s.start))
  const plotW = W - LEFT - 12
  const x = (t) => LEFT + (t / end) * plotW
  const H = TOP + pids.length * ROW + AXIS
  const step = niceStep(end)
  const ticks = []
  for (let t = 0; t <= end; t += step) ticks.push(t)
  if (ticks[ticks.length - 1] !== end && end - ticks[ticks.length - 1] > step / 2) ticks.push(end)

  return (
    <figure className="chart">
      <figcaption>
        <span className="dot" style={{ background: COLORS[name] }} />
        <strong>{name}</strong>
        <span className="muted"> · {contextSwitches} context switches</span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Gantt chart for ${name}`}>
        {pids.map((pid, i) => (
          <g key={pid}>
            <line x1={LEFT} x2={W - 12} y1={TOP + i * ROW + ROW / 2} y2={TOP + i * ROW + ROW / 2} className="gridline" />
            <text x={LEFT - 8} y={TOP + i * ROW + ROW / 2 + 4} textAnchor="end" className="tick">
              P{pid}
            </text>
          </g>
        ))}
        {ticks.map((t) => (
          <g key={t}>
            <line x1={x(t)} x2={x(t)} y1={TOP} y2={TOP + pids.length * ROW} className="vgrid" />
            <text x={x(t)} y={H - 8} textAnchor="middle" className="tick">
              {t}
            </text>
          </g>
        ))}
        {timeline
          .filter((s) => s.pid !== null)
          .map((s, i) => {
            const w = Math.max(x(s.end) - x(s.start), 1)
            return (
              <g key={i}>
                <rect x={x(s.start)} y={TOP + row[s.pid] * ROW + 3} width={w} height={ROW - 6} rx="2" fill={COLORS[name]} stroke="var(--surface)" strokeWidth="1">
                  <title>{`P${s.pid}: ${s.start} → ${s.end}`}</title>
                </rect>
                {w > 22 && (
                  <text x={x(s.start) + w / 2} y={TOP + row[s.pid] * ROW + ROW / 2 + 4} textAnchor="middle" className="bar-label">
                    {s.end - s.start}
                  </text>
                )}
              </g>
            )
          })}
      </svg>
      {start > 0 && <p className="hint">CPU idle before t={start}.</p>}
    </figure>
  )
}
