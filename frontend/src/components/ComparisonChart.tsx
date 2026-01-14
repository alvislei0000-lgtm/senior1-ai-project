import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { BenchmarkResult } from '../App'
import './ComparisonChart.css'

interface ComparisonChartProps {
  results: BenchmarkResult[]
}

function ComparisonChart({ results }: ComparisonChartProps) {
  const [metric, setMetric] = useState<'avg_fps' | 'p1_low' | 'p0_1_low'>('avg_fps')

  const getMetricLabel = (m: string) => {
    switch (m) {
      case 'avg_fps':
        return '平均 FPS'
      case 'p1_low':
        return '1% Low'
      case 'p0_1_low':
        return '0.1% Low'
      default:
        return m
    }
  }

  const chartData = results.map((result) => {
    const hardwareLabel = `${result.gpu} / ${result.cpu}`
    const value = result[metric] ?? 0

    return {
      name: hardwareLabel.length > 30 ? hardwareLabel.substring(0, 30) + '...' : hardwareLabel,
      fullName: hardwareLabel,
      value: value,
      game: result.game,
      resolution: result.resolution,
      settings: result.settings,
    }
  }).filter(item => item.value > 0)

  if (chartData.length === 0) {
    return (
      <div className="comparison-chart">
        <h2>比較圖表</h2>
        <div className="no-data">沒有可用的資料進行比較</div>
      </div>
    )
  }

  return (
    <div className="comparison-chart">
      <div className="chart-header">
        <h2>硬體效能比較</h2>
        <div className="metric-selector">
          <label>比較指標:</label>
          <select value={metric} onChange={(e) => setMetric(e.target.value as any)}>
            <option value="avg_fps">平均 FPS</option>
            <option value="p1_low">1% Low</option>
            <option value="p0_1_low">0.1% Low</option>
          </select>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={100}
              interval={0}
            />
            <YAxis label={{ value: getMetricLabel(metric), angle: -90, position: 'insideLeft' }} />
            <Tooltip
              formatter={(value: number) => [value.toFixed(1), getMetricLabel(metric)]}
              labelFormatter={(label, payload) => {
                if (payload && payload[0]) {
                  const data = payload[0].payload
                  return (
                    <div>
                      <div><strong>{data.fullName}</strong></div>
                      <div>{data.game}</div>
                      <div>{data.resolution} - {data.settings}</div>
                    </div>
                  )
                }
                return label
              }}
            />
            <Legend />
            <Bar
              dataKey="value"
              fill="#76b900"
              name={getMetricLabel(metric)}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default ComparisonChart


