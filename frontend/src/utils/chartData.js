// Snapshots arrive newest-first; reverse to chronological order for the x-axis.
export function toChartData(snapshots, metricKey) {
  return [...snapshots].reverse().map((snap, i) => ({
    tick: i + 1,
    [metricKey]: snap.state?.[metricKey],
  }))
}
