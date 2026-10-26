import { COLORS } from '../constants'

export default function ProcessTables({ results }) {
  return (
    <div className="stack">
      {Object.entries(results).map(([name, r]) => (
        <section key={name}>
          <h3>
            <span className="dot" style={{ background: COLORS[name] }} /> {name}
          </h3>
          <div className="scroll">
            <table className="grid">
              <thead>
                <tr>
                  <th>PID</th>
                  <th>Arrival</th>
                  <th>Burst</th>
                  <th>Start</th>
                  <th>Completion</th>
                  <th>Turnaround</th>
                  <th>Waiting</th>
                  <th>Response</th>
                </tr>
              </thead>
              <tbody>
                {r.processes.map((p) => (
                  <tr key={p.pid}>
                    <th>P{p.pid}</th>
                    <td>{p.arrival}</td>
                    <td>{p.burst}</td>
                    <td>{p.start}</td>
                    <td>{p.completion}</td>
                    <td>{p.turnaround}</td>
                    <td>{p.waiting}</td>
                    <td>{p.response}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  )
}
