import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { INK } from '../../theme/palette'

// Single-series line chart. Never combine two differently-scaled metrics on one
// axis — instantiate this once per metric instead of adding a second Y axis.
function AgentMetricChart({ title, data, dataKey, color, valueFormatter }) {
  const hasData = data && data.length > 0

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">{title}</h3>
      {hasData ? (
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={INK.gridline} vertical={false} />
            <XAxis
              dataKey="tick"
              tick={{ fontSize: 14, fill: INK.muted }}
              stroke={INK.baseline}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 14, fill: INK.muted }}
              stroke={INK.baseline}
              tickLine={false}
              width={64}
              tickFormatter={valueFormatter}
            />
            <Tooltip
              formatter={(value) => (valueFormatter ? valueFormatter(value) : value)}
              contentStyle={{ fontSize: 14, borderRadius: 8 }}
            />
            <Line
              isAnimationActive={false}
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-[180px] flex items-center justify-center text-sm text-gray-400">
          No data yet — start a simulation to see this metric evolve.
        </div>
      )}
    </div>
  )
}

export default AgentMetricChart
