export const COLORS = { SJF: '#2a78d6', HRRN: '#eb6834', 'AP-HRRN': '#1baf7a' }

export const METRICS = [
  { key: 'avg_waiting', label: 'Average waiting time', better: 'low' },
  { key: 'avg_turnaround', label: 'Average turnaround time', better: 'low' },
  { key: 'avg_response', label: 'Average response time', better: 'low' },
  { key: 'max_waiting', label: 'Maximum waiting time', better: 'low' },
  { key: 'context_switches', label: 'Context switches', better: 'low' },
  { key: 'cpu_utilization', label: 'CPU utilization (%)', better: 'high' },
]

export const fmt = (v) => (Number.isInteger(v) ? String(v) : v.toFixed(2))
