export default function ProcessEditor({ rows, setRows, limits }) {
  const update = (id, field, value) =>
    setRows(rows.map((r) => (r.id === id ? { ...r, [field]: value } : r)))

  const remove = (id) => setRows(rows.filter((r) => r.id !== id))

  const add = () => {
    const maxPid = rows.reduce((m, r) => Math.max(m, Number(r.pid) || 0), 0)
    setRows([...rows, { id: crypto.randomUUID(), pid: String(maxPid + 1), arrival: '0', burst: '1' }])
  }

  const atLimit = rows.length >= limits.processes

  return (
    <div>
      <table className="grid editor">
        <thead>
          <tr>
            <th>PID</th>
            <th>Arrival</th>
            <th>Burst</th>
            <th aria-label="Remove" />
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              {['pid', 'arrival', 'burst'].map((f) => (
                <td key={f}>
                  <input
                    type="number"
                    min={f === 'burst' || f === 'pid' ? 1 : 0}
                    value={r[f]}
                    onChange={(e) => update(r.id, f, e.target.value)}
                    aria-label={`${f} for row`}
                  />
                </td>
              ))}
              <td>
                <button className="icon" onClick={() => remove(r.id)} title="Remove process" disabled={rows.length === 1}>
                  ×
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button className="ghost" onClick={add} disabled={atLimit}>
        + Add process
      </button>
      {atLimit && <span className="hint"> Max {limits.processes} processes</span>}
    </div>
  )
}
