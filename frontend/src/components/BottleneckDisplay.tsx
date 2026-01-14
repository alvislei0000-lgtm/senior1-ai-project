import { BottleneckAnalysis } from '../App'
import './BottleneckDisplay.css'

interface BottleneckDisplayProps {
  analysis: BottleneckAnalysis
}

function BottleneckDisplay({ analysis }: BottleneckDisplayProps) {
  const getBottleneckColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'gpu-bound':
        return 'var(--danger-color)' // 紅色（重要警示）
      case 'cpu-bound':
        return 'var(--primary-color)' // 使用主色作為 CPU 強調色
      case 'memory-bound':
        return 'var(--warning-color)' // 警示色
      case 'io-bound':
        return 'var(--info-color)' // 次要資訊色
      case 'balanced':
        return 'var(--success-color)' // 成功/良好
      default:
        return '#95a5a6' // 灰色（fallback）
    }
  }

  const getBottleneckLabel = (type: string) => {
    switch (type.toLowerCase()) {
      case 'gpu-bound':
        return 'GPU 瓶頸'
      case 'cpu-bound':
        return 'CPU 瓶頸'
      case 'memory-bound':
        return '記憶體（RAM）瓶頸'
      case 'io-bound':
        return 'I/O 瓶頸'
      case 'balanced':
        return '系統平衡'
      default:
        return '未知'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'var(--success-color)'
    if (confidence >= 0.6) return 'var(--warning-color)'
    return 'var(--danger-color)'
  }

  const bottleneckColor = getBottleneckColor(analysis.bottleneck_type)
  const confidenceColor = getConfidenceColor(analysis.confidence)

  return (
    <div className="bottleneck-display">
      <div className="bottleneck-header">
        <h4>效能瓶頸分析</h4>
        <div
          className="bottleneck-badge"
          style={{ backgroundColor: bottleneckColor }}
        >
          {getBottleneckLabel(analysis.bottleneck_type)}
        </div>
      </div>

      <div className="bottleneck-confidence">
        <span className="confidence-label">置信度:</span>
        <span
          className="confidence-value"
          style={{ color: confidenceColor }}
        >
          {(analysis.confidence * 100).toFixed(0)}%
        </span>
      </div>

      <div className="bottleneck-reasoning">
        <strong>分析說明:</strong>
        <p>{analysis.reasoning}</p>
      </div>

      {analysis.recommendations.length > 0 && (
        <div className="bottleneck-recommendations">
          <strong>建議:</strong>
          <ul>
            {analysis.recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default BottleneckDisplay


