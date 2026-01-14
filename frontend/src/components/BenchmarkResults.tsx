import type { BenchmarkResult } from '../App'
import { useState } from 'react'
import BottleneckDisplay from './BottleneckDisplay'
import './BenchmarkResults.css'

interface BenchmarkResultsProps {
  results: BenchmarkResult[]
}

function BenchmarkResults({ results }: BenchmarkResultsProps) {
  // raw source snippet view removed per request

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return '#28a745'
    if (score >= 0.6) return '#ffc107'
    return '#dc3545'
  }

  const getConfidenceText = (score: number) => {
    if (score >= 0.8) return '高'
    if (score >= 0.6) return '中'
    return '低'
  }

  return (
    <div className="benchmark-results">
      <h2>基準測試結果 ({results.length})</h2>

      <div className="results-grid">
        {results.map((result, idx) => (
          <div
            key={idx}
            className={`result-card ${result.is_incomplete ? 'incomplete' : ''}`}
          >
            {result.is_incomplete && (
              <div className="incomplete-badge">不完整資料</div>
            )}

            <div className="result-header">
              <h3>{result.game}</h3>
              <div className="result-meta">
                <span>{result.resolution}</span>
                <span>{result.settings}</span>
              </div>
            </div>

            <div className="result-hardware">
              <div className="hardware-item">
                <span className="label">GPU:</span>
                <span className="value">{result.gpu}</span>
              </div>
              <div className="hardware-item">
                <span className="label">CPU:</span>
                <span className="value">{result.cpu}</span>
              </div>
              {(result.vram_required_gb !== undefined ||
                result.vram_selected_gb !== undefined ||
                result.vram_is_enough !== undefined) && (
                <div className="hardware-item">
                  <span className="label">VRAM:</span>
                  <span className="value">
                    {result.vram_required_gb !== undefined ? `需求 ${result.vram_required_gb}GB` : '需求 ?'}
                    {result.vram_selected_gb !== undefined ? ` / 已選 ${result.vram_selected_gb}GB` : ''}
                    {result.vram_is_enough !== undefined
                      ? `（${result.vram_is_enough ? '足夠' : '可能不足'}）`
                      : ''}
                  </span>
                </div>
              )}
            </div>

            <div className="result-fps">
              {result.avg_fps !== null && result.avg_fps !== undefined && (
                <div className="fps-item gradient-bg">
                  <span className="fps-label">平均 FPS</span>
                  <span className="fps-value gradient">{result.avg_fps.toFixed(1)}</span>
                </div>
              )}
              {result.p1_low !== null && result.p1_low !== undefined && (
                <div className="fps-item gradient-bg">
                  <span className="fps-label">1% Low</span>
                  <span className="fps-value gradient">{result.p1_low.toFixed(1)}</span>
                </div>
              )}
              {result.p0_1_low !== null && result.p0_1_low !== undefined && (
                <div className="fps-item gradient-bg">
                  <span className="fps-label">0.1% Low</span>
                  <span className="fps-value gradient">{result.p0_1_low.toFixed(1)}</span>
                </div>
              )}
            </div>

            <div className="result-source">
              <div className="source-info">
                <span className="source-label">來源:</span>
                <span className="source-name">{result.source}</span>
              </div>
              <div className="source-info">
                <span className="source-label">抓取時間:</span>
                <span className="source-time">
                  {new Date(result.timestamp).toLocaleString('zh-TW')}
                </span>
              </div>
              <div className="source-info">
                <span className="source-label">可信度:</span>
                <span
                  className="confidence-score"
                  style={{ color: getConfidenceColor(result.confidence_score) }}
                >
                  {getConfidenceText(result.confidence_score)} (
                  {(result.confidence_score * 100).toFixed(0)}%)
                </span>
              </div>
            </div>

            {result.notes && (
              <div className="result-notes">
                <strong>備註:</strong> {result.notes}
              </div>
            )}

            {result.bottleneck_analysis && (
              <BottleneckDisplay analysis={result.bottleneck_analysis} />
            )}

            {/* 原始來源片段檢視已移除 */}
          </div>
        ))}
      </div>
    </div>
  )
}

export default BenchmarkResults

