import { COLORS, METRICS, fmt } from '../constants'

function Panel({ metric, data, names }) {
  const vals = names.map((n) => data[n][metric.key])
  const max = metric.key === 'cpu_utilization' ? 110 : Math.max(...vals, 1) * 1.2
  const W = 300
  const H = 150
  const base = H - 24
  const bw = 52
  const gap = (W - bw * names.length) / (names.length + 1)
  return (
    <div className="panel">
      <h4>{metric.label}</h4>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={metric.label}>
        <line x1="0" x2={W} y1={base} y2={base} className="axis" />
        {names.map((n, i) => {
          const h = (vals[i] / max) * (base - 18)
          const bx = gap + i * (bw + gap)
          return (
            <g key={n}>
              <rect x={bx} y={base - h} width={bw} height={Math.max(h, 0)} rx="3" fill={COLORS[n]}>
                <title>{`${n}: ${fmt(vals[i])}`}</title>
              </rect>
              <text x={bx + bw / 2} y={base - h - 5} textAnchor="middle" className="val">
                {fmt(vals[i])}
              </text>
              <text x={bx + bw / 2} y={H - 8} textAnchor="middle" className="tick">
                {n}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

export default function MetricBars({ data }) {
  const names = Object.keys(data)
  return (
    <div className="panels">
      {METRICS.map((m) => (
        <Panel key={m.key} metric={m} data={data} names={names} />
      ))}
    </div>
  )
}
