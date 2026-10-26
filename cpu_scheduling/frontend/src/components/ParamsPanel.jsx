const FIELDS = [
  { key: 'k', label: 'k (preemption threshold)', step: 0.25, min: 1 },
  { key: 'wait_limit', label: 'Wait limit L', step: 1, min: 1 },
  { key: 'boost', label: 'Aging boost', step: 1, min: 0 },
  { key: 'alpha', label: 'alpha (smoothing)', step: 0.1, min: 0, max: 1 },
  { key: 'tau0', label: 'tau0 (initial estimate)', step: 1, min: 1 },
]

export default function ParamsPanel({ params, setParams, defaults }) {
  const set = (k, v) => setParams({ ...params, [k]: v })
  return (
    <div>
      <div className="fields">
        {FIELDS.map((f) => (
          <label key={f.key} className={f.key === 'alpha' || f.key === 'tau0' ? (params.estimator === 'exp' ? '' : 'dim') : ''}>
            {f.label}
            <input
              type="number"
              step={f.step}
              min={f.min}
              max={f.max}
              value={params[f.key]}
              onChange={(e) => set(f.key, e.target.value)}
            />
          </label>
        ))}
        <label>
          Burst estimator
          <select value={params.estimator} onChange={(e) => set('estimator', e.target.value)}>
            <option value="exact">exact (burst known)</option>
            <option value="exp">exponential average</option>
          </select>
        </label>
      </div>
      <p className="hint">
        These only affect AP-HRRN. alpha and tau0 are used only with the exponential estimator.
      </p>
      <button className="ghost" onClick={() => setParams({ ...defaults })}>
        Reset to defaults
      </button>
    </div>
  )
}
