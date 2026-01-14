import { useState } from 'react'
import './SearchBar.css'
import { POPULAR_GAMES } from '../data/games'

interface SearchBarProps {
  onSearch: (params: {
    game: string
    games?: string[]
    resolution: string
    settings?: string
    mode?: 'single' | 'batch'
  }) => void
  isSearching: boolean
}

function SearchBar({ onSearch, isSearching }: SearchBarProps) {
  const [selectedGameIndex, setSelectedGameIndex] = useState<number | null>(0)
  const [resolution, setResolution] = useState('1920x1080')
  const [settings, setSettings] = useState('High')
  const [rayTracing, setRayTracing] = useState(false)

  const handleGameSelect = (index: number) => {
    setSelectedGameIndex(index)
  }

  const handleResolutionChange = (newResolution: string) => {
    setResolution(newResolution)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedGameIndex === null) {
      alert('請選擇遊戲')
      return
    }
    const game = POPULAR_GAMES[selectedGameIndex].name
    onSearch({
      game,
      resolution,
      settings: (settings ? `${settings}${rayTracing ? ' RT' : ''}` : rayTracing ? 'RT' : '') || undefined,
      mode: 'single'
    })
  }

  const handleBatchSearch = () => {
    const games = POPULAR_GAMES.map(g => g.name)
    onSearch({
      game: games[0] || '',
      games,
      resolution,
      settings: (settings ? `${settings}${rayTracing ? ' RT' : ''}` : rayTracing ? 'RT' : '') || undefined,
      mode: 'batch'
    })
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-field game-selector">
        <label>選擇遊戲（熱門 25 款）</label>
        <div className="game-grid">
          {POPULAR_GAMES.map((g, idx) => {
            return (
              <button
                type="button"
                key={g.name}
                className={`game-chip ${selectedGameIndex === idx ? 'selected' : ''}`}
                onClick={() => handleGameSelect(idx)}
              >
                <div className="game-name">{g.name}</div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="search-field">
        <label>解析度</label>
        <select
          value={resolution}
          onChange={(e) => handleResolutionChange(e.target.value)}
        >
          <option value="1280x720">1280x720 (720p)</option>
          <option value="1920x1080">1920x1080 (1080p)</option>
          <option value="2560x1440">2560x1440 (1440p)</option>
          <option value="3840x2160">3840x2160 (4K)</option>
        </select>
      </div>

      <div className="search-field">
        <label>畫質設定（選填）</label>
        <select value={settings} onChange={(e) => setSettings(e.target.value)}>
          <option value="">自動 / 未指定</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
          <option value="Ultra">Ultra</option>
        </select>
      </div>

      <div className="search-field">
        <label>光線追蹤（RT/PT）</label>
        <label className="rt-toggle">
          <input
            type="checkbox"
            checked={rayTracing}
            onChange={(e) => setRayTracing(e.target.checked)}
          />
          <span>啟用（僅當遊戲支援時才會大幅降低 FPS）</span>
        </label>
      </div>

      <button type="submit" disabled={isSearching} className="search-button">
        {isSearching ? '搜尋中...' : '搜尋基準資料'}
      </button>

      <button
        type="button"
        disabled={isSearching}
        className="search-button"
        onClick={handleBatchSearch}
        title="一次查 25 款（若要抓取網路實測，需設定 GOOGLE_API_KEY / GOOGLE_CX；否則會用本地快取/預測模型）"
      >
        {isSearching ? '搜尋中...' : '搜尋 25 款遊戲'}
      </button>
    </form>
  )
}

export default SearchBar


