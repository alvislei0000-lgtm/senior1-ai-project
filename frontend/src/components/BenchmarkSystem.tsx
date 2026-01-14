import { useRef, useState } from 'react'
import SearchBar from './SearchBar'
import HardwareSelector from './HardwareSelector'
import BenchmarkResults from './BenchmarkResults'
import ComparisonChart from './ComparisonChart'
import { API_BASE_URL } from '../config/api'

export interface HardwareItem {
  category: string
  model: string
  generation?: string
  release_year?: number
  brand: string
  selected: boolean
  vram_gb?: number
  vram_options?: number[]
  selected_vram_gb?: number
  capacity_gb?: number
}

export interface BottleneckAnalysis {
  bottleneck_type: string
  confidence: number
  reasoning: string
  recommendations: string[]
}

export interface BenchmarkResult {
  game: string
  resolution: string
  settings: string
  gpu: string
  cpu: string
  avg_fps?: number
  p1_low?: number
  p0_1_low?: number
  source: string
  timestamp: string
  notes?: string
  confidence_score: number
  raw_source_snippet?: string
  is_incomplete: boolean
  bottleneck_analysis?: BottleneckAnalysis
  vram_required_gb?: number
  vram_selected_gb?: number
  vram_is_enough?: boolean
  vram_margin_gb?: number
}

const BenchmarkSystem = () => {
  const [selectedGPU, setSelectedGPU] = useState<HardwareItem[]>([])
  const [selectedCPU, setSelectedCPU] = useState<HardwareItem[]>([])
  const [selectedStorage, setSelectedStorage] = useState<string>('') // 儲存體類型：'nvme-gen3' | 'nvme-gen4' | 'nvme-gen5' | 'sata' | 'hdd' | ''
  const [selectedRam, setSelectedRam] = useState<number>(16) // 預設16GB
  const [selectedRamType, setSelectedRamType] = useState<string>('DDR5') // DDR 類型
  const [selectedRamCL, setSelectedRamCL] = useState<number>(16) // CAS Latency
  const [selectedRamFreq, setSelectedRamFreq] = useState<number>(5200) // 頻率 (MT/s)
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const requestSeqRef = useRef<number>(0)
  const [ramOpen, setRamOpen] = useState<boolean>(true)
  const [gpuOpen, setGpuOpen] = useState<boolean>(true)
  const [cpuOpen, setCpuOpen] = useState<boolean>(true)
  const [storageOpen, setStorageOpen] = useState<boolean>(true)

  // 合併GPU和CPU作為selectedHardware供API使用
  // include storage in selectedHardware (簡化為類型，但支持詳細的 NVMe 世代)
  const selectedHardwareWithStorage = [
    ...selectedGPU,
    ...selectedCPU,
    // RAM硬件对象
    {
      category: 'ram',
      model: `${selectedRamType} ${selectedRam}GB ${selectedRamFreq}MHz CL${selectedRamCL}`,
      brand: selectedRamType,
      selected: true,
    } as HardwareItem,
    ...(selectedStorage ? [{
      category: 'storage',
      model: selectedStorage.includes('gen')
        ? `NVMe ${selectedStorage.split('-')[1].toUpperCase()}`
        : selectedStorage.toUpperCase(),
      brand: '',
      selected: true,
      generation: selectedStorage.includes('gen')
        ? `NVMe ${selectedStorage.split('-')[1].toUpperCase()}`
        : selectedStorage.toUpperCase()
    } as HardwareItem] : [])
  ]

  const handleGPUSelect = (hardware: HardwareItem[]) => {
    setSelectedGPU(hardware)
  }

  const handleCPUSelect = (hardware: HardwareItem[]) => {
    setSelectedCPU(hardware)
  }
  const handleStorageSelect = (storageType: string) => {
    setSelectedStorage(storageType)
  }

  const handleRamSelect = (ram: number) => {
    setSelectedRam(ram)
  }

  const handleRamTypeChange = (type: string) => {
    setSelectedRamType(type)
    // 當切換 RAM 類型時，自動選擇該類型的第一個 CL 值
    const specs: Record<string, { clOptions: number[]; freqRange: { min: number; max: number; step: number } }> = {
      DDR4: { clOptions: Array.from({ length: 13 }, (_, i) => 10 + i), freqRange: { min: 1600, max: 4000, step: 100 } },
      DDR5: { clOptions: Array.from({ length: 13 }, (_, i) => 28 + i), freqRange: { min: 4800, max: 8000, step: 100 } },
      LPDDR5: { clOptions: Array.from({ length: 13 }, (_, i) => 28 + i), freqRange: { min: 3200, max: 6400, step: 100 } },
    }
    const spec = specs[type] || specs.DDR5
    setSelectedRamCL(spec.clOptions[0])
    setSelectedRamFreq(spec.freqRange.min)
  }

  const handleRamCLChange = (cl: number) => {
    setSelectedRamCL(cl)
  }

  const handleRamFreqChange = (freq: number) => {
    setSelectedRamFreq(freq)
  }

  const handleSearch = async (searchParams: {
    game: string
    games?: string[]
    resolution: string
    settings?: string
    mode?: 'single' | 'batch'
  }) => {
    if (selectedHardwareWithStorage.length === 0) {
      alert('請先選擇至少一個硬體')
      return
    }
    if (selectedCPU.length === 0) {
      alert('請先選擇至少一顆 CPU（沒有 CPU 會導致瓶頸分析不可靠）')
      return
    }

    // 取消前一個請求（避免連點造成結果互相覆蓋）
    if (abortRef.current) {
      try { abortRef.current.abort() } catch {}
    }
    const controller = new AbortController()
    abortRef.current = controller
    const reqId = ++requestSeqRef.current

    setIsSearching(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/benchmarks/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
        body: JSON.stringify({
          ...searchParams,
          min_ram_gb: selectedRam,
          ram_type: selectedRamType,
          ram_cl: selectedRamCL,
          ram_freq_mt_s: selectedRamFreq,
        hardware: selectedHardwareWithStorage.map((h: HardwareItem) => {
            const hw: any = {
              category: h.category,
              model: h.model,
            }
            if (h.category === 'gpu') {
              hw.selected_vram_gb = (h as any).selected_vram_gb
            }
            if (h.category === 'ram') {
              hw.ram_gb = selectedRam
              hw.ram_type = selectedRamType
              hw.ram_speed_mhz = selectedRamFreq
              hw.ram_latency_ns = selectedRamCL
            }
            if (h.category === 'storage') {
              hw.storage_type = h.generation || 'SSD'
            }
            return hw
          }),
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || '搜尋失敗')
      }

      const data = await response.json()
      // 只接受最後一次請求的回應
      if (reqId === requestSeqRef.current) {
        setBenchmarkResults(data.results || [])
      }

      // 平滑滾動到結果區域
      setTimeout(() => {
        const resultsSection = document.querySelector('.results-section')
        if (resultsSection) {
          resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 100)
    } catch (error) {
      // 若是被 abort，直接忽略（代表使用者已開始新搜尋）
      if (error && typeof error === 'object' && (error as any).name === 'AbortError') return
      console.error('搜尋錯誤:', error)
      // 使用更友好的錯誤提示
      const errorMessage = error instanceof Error ? error.message : '搜尋失敗，請稍後再試'
      alert(`❌ ${errorMessage}`)
    } finally {
      if (reqId === requestSeqRef.current) {
        setIsSearching(false)
      }
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div style={{display:'flex', alignItems:'center', justifyContent:'center', gap:16}}>
          <div>
            <h1 style={{margin:0}}>硬體 FPS 基準分析系統</h1>
            <p className="subtitle">即時從網路抓取硬體效能基準資料</p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="hardware-section">
          <div className={`cpu-selector-section hw-selection ${cpuOpen ? '' : 'collapsed'}`}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: cpuOpen ? '0.75rem' : 0}}>
              <h3 style={{margin:0}}>選擇CPU</h3>
              <button className="toggle-button" onClick={() => setCpuOpen(!cpuOpen)}>{cpuOpen ? '收起' : '展開'}</button>
            </div>
            {cpuOpen ? (
              <HardwareSelector
                selectedHardware={selectedCPU}
                onSelect={handleCPUSelect}
                hardwareType="cpu"
                expanded={cpuOpen}
              />
            ) : (
              <div className="hw-summary" style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
                <div style={{fontWeight:700}}>{selectedCPU.length} 顆 CPU</div>
                {selectedCPU.slice(0,3).map((c, i) => (
                  <div key={i} style={{color:'#cccccc'}}>{c.model}</div>
                ))}
                {selectedCPU.length > 3 && <div style={{color:'#cccccc'}}>…</div>}
              </div>
            )}
          </div>

          <div className={`gpu-selector-section hw-selection ${gpuOpen ? '' : 'collapsed'}`}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: gpuOpen ? '0.75rem' : 0}}>
              <h3 style={{margin:0}}>選擇GPU</h3>
              <button className="toggle-button" onClick={() => setGpuOpen(!gpuOpen)}>{gpuOpen ? '收起' : '展開'}</button>
            </div>
            {gpuOpen ? (
              <HardwareSelector
                selectedHardware={selectedGPU}
                onSelect={handleGPUSelect}
                hardwareType="gpu"
                expanded={gpuOpen}
              />
            ) : (
              <div className="hw-summary" style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
                <div style={{fontWeight:700}}>{selectedGPU.length} 張 GPU</div>
                {selectedGPU.slice(0,3).map((g, i) => (
                  <div key={i} style={{color:'#cccccc'}}>{g.model}{(g as any).selected_vram_gb ? ` • ${(g as any).selected_vram_gb}GB` : ''}</div>
                ))}
                {selectedGPU.length > 3 && <div style={{color:'#cccccc'}}>…</div>}
              </div>
            )}
          </div>

          <div className={`storage-selector-section hw-selection ${storageOpen ? '' : 'collapsed'}`}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: storageOpen ? '0.75rem' : 0}}>
              <h3 style={{margin:0}}>選擇儲存體類型</h3>
              <button className="toggle-button" onClick={() => setStorageOpen(!storageOpen)}>{storageOpen ? '收起' : '展開'}</button>
            </div>
            {storageOpen ? (
              <div className="storage-options-container">
                <div className="storage-category-group">
                  <div className="storage-category-label">NVMe SSD</div>
                  <div className="storage-buttons-group">
                    {['nvme-gen3', 'nvme-gen4', 'nvme-gen5'].map((type) => (
                      <button
                        key={type}
                        className={`storage-button ${selectedStorage === type ? 'selected' : ''}`}
                        onClick={() => handleStorageSelect(selectedStorage === type ? '' : type)}
                      >
                        {type.replace('nvme-', 'NVMe ').toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="storage-category-group">
                  <div className="storage-category-label">SATA SSD</div>
                  <div className="storage-buttons-group">
                    <button
                      className={`storage-button ${selectedStorage === 'sata' ? 'selected' : ''}`}
                      onClick={() => handleStorageSelect(selectedStorage === 'sata' ? '' : 'sata')}
                    >
                      SATA
                    </button>
                  </div>
                </div>

                <div className="storage-category-group">
                  <div className="storage-category-label">HDD</div>
                  <div className="storage-buttons-group">
                    <button
                      className={`storage-button ${selectedStorage === 'hdd' ? 'selected' : ''}`}
                      onClick={() => handleStorageSelect(selectedStorage === 'hdd' ? '' : 'hdd')}
                    >
                      HDD
                    </button>
                  </div>
                </div>

                {selectedStorage && (
                  <div className="storage-selected-info">
                    <span className="storage-selected-label">已選擇：</span>
                    <span className="storage-selected-value">{selectedStorage.replace('nvme-', 'NVMe ').toUpperCase()}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="hw-summary" style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
                {selectedStorage ? (
                  <>
                    <div style={{fontWeight:700}}>已選擇儲存體</div>
                    <div style={{color:'#cccccc'}}>{selectedStorage.replace('nvme-', 'NVMe ').toUpperCase()}</div>
                  </>
                ) : (
                  <div style={{color:'#999'}}>未選擇儲存體</div>
                )}
              </div>
            )}
          </div>

          <div className="ram-selection-section">
            <div className={`ram-selection ${ramOpen ? '' : 'collapsed'}`}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: ramOpen ? '1rem' : 0}}>
                <h3>系統RAM</h3>
                <button className="toggle-button" onClick={() => setRamOpen(!ramOpen)}>{ramOpen ? '收起' : '展開'}</button>
              </div>

              {ramOpen ? (
                <>
                  <div className="ram-options">
                    {[8, 16, 32, 64, 128].map(ram => (
                      <button
                        key={ram}
                        className={`ram-button ${selectedRam === ram ? 'selected' : ''}`}
                        onClick={() => handleRamSelect(ram)}
                      >
                        {ram} GB
                      </button>
                    ))}
                  </div>

                  <div style={{marginTop: '1rem', display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap'}}>
                    <div style={{display:'flex', flexDirection:'column', gap:6}}>
                      <label style={{fontWeight:600}}>RAM 類型</label>
                      <select value={selectedRamType} onChange={(e) => handleRamTypeChange(e.target.value)} className="filter-select">
                        <option value="DDR4">DDR4</option>
                        <option value="DDR5">DDR5</option>
                        <option value="LPDDR5">LPDDR5</option>
                      </select>
                    </div>

                    <div style={{display:'flex', flexDirection:'column', gap:6}}>
                      <label style={{fontWeight:600}}>CAS Latency (CL)</label>
                      {(() => {
                        const specs: Record<string, { clOptions: number[]; freqRange: { min: number; max: number; step: number } }> = {
                          DDR4: { clOptions: Array.from({ length: 13 }, (_, i) => 10 + i), freqRange: { min: 1600, max: 4000, step: 100 } },
                          DDR5: { clOptions: Array.from({ length: 13 }, (_, i) => 28 + i), freqRange: { min: 4800, max: 8000, step: 100 } },
                          LPDDR5: { clOptions: Array.from({ length: 13 }, (_, i) => 28 + i), freqRange: { min: 3200, max: 6400, step: 100 } },
                        }
                        const clOptions = specs[selectedRamType]?.clOptions || [16]
                        return (
                          <select value={String(selectedRamCL)} onChange={(e) => handleRamCLChange(Number(e.target.value))} className="filter-select">
                            {clOptions.map(cl => (
                              <option key={cl} value={cl}>{`CL${cl}`}</option>
                            ))}
                          </select>
                        )
                      })()}
                    </div>

                    <div style={{display:'flex', flexDirection:'column', gap:6}}>
                      <label style={{fontWeight:600}}>頻率 (MT/s)</label>
                      {(() => {
                        const specs: Record<string, { clOptions: number[]; freqRange: { min: number; max: number; step: number } }> = {
                          DDR4: { clOptions: Array.from({ length: 13 }, (_, i) => 10 + i), freqRange: { min: 1600, max: 4000, step: 100 } },
                          DDR5: { clOptions: Array.from({ length: 13 }, (_, i) => 28 + i), freqRange: { min: 4800, max: 8000, step: 100 } },
                          LPDDR5: { clOptions: Array.from({ length: 13 }, (_, i) => 28 + i), freqRange: { min: 3200, max: 6400, step: 100 } },
                        }
                        const range = specs[selectedRamType]?.freqRange || { min: 4800, max: 5600, step: 100 }
                        const freqOptions: number[] = []
                        for (let v = range.min; v <= range.max; v += range.step) freqOptions.push(v)
                        return (
                          <select value={String(selectedRamFreq)} onChange={(e) => handleRamFreqChange(Number(e.target.value))} className="filter-select">
                            {freqOptions.map(f => (
                              <option key={f} value={f}>{`${f} MT/s`}</option>
                            ))}
                          </select>
                        )
                      })()}
                    </div>
                  </div>
                </>
              ) : (
                <div className="ram-summary" style={{display:'flex', gap:12, alignItems:'center', justifyContent:'flex-start'}}>
                  <div style={{fontWeight:700}}>{selectedRam} GB</div>
                  <div style={{color:'#cccccc'}}>{selectedRamType}</div>
                  <div style={{color:'#cccccc'}}>CL{selectedRamCL}</div>
                  <div style={{color:'#cccccc'}}>{selectedRamFreq} MT/s</div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="search-section">
          <SearchBar onSearch={handleSearch} isSearching={isSearching} />
        </div>

        {benchmarkResults.length > 0 && (
          <>
            <div className="results-section">
              <BenchmarkResults results={benchmarkResults} />
            </div>

            {benchmarkResults.length > 1 && (
              <div className="comparison-section">
                <ComparisonChart results={benchmarkResults} />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default BenchmarkSystem