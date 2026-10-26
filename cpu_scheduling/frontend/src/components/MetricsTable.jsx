import { COLORS, METRICS, fmt } from '../constants'

export default function MetricsTable({ data }) {
  const names = Object.keys(data)
  return (
    <div className="scroll">
      <table className="grid metrics">
        <thead>
          <tr>
            <th>Algorithm</th>
            {METRICS.map((m) => (
              <th key={m.key}>{m.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {names.map((n) => (
            <tr key={n}>
              <th>
                <span className="dot" style={{ background: COLORS[n] }} /> {n}
              </th>
              {METRICS.map((m) => {
                const vals = names.map((x) => data[x][m.key])
                const best = m.better === 'low' ? Math.min(...vals) : Math.max(...vals)
                const isBest = data[n][m.key] === best && new Set(vals).size > 1
                return (
                  <td key={m.key} className={isBest ? 'best' : ''}>
                    {fmt(data[n][m.key])}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="hint">Green cell = best value in that column (lower is better, except CPU utilization).</p>
    </div>
  )
}
