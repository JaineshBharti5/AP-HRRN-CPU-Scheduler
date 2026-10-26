async function request(path, options) {
  let res
  try {
    res = await fetch(path, options)
  } catch {
    throw new Error('Cannot reach the backend. Start it with: python api.py')
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`)
  return data
}

const post = (path, body) =>
  request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

export const getMeta = () => request('/api/meta')
export const getPresets = () => request('/api/presets')
export const randomWorkload = (body) => post('/api/random', body)
export const simulate = (body) => post('/api/simulate', body)
export const benchmark = (body) => post('/api/benchmark', body)
