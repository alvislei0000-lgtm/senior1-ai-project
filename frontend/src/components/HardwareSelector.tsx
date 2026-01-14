import { useState, useEffect } from 'react'
import { FixedSizeList as List } from 'react-window'
import { HardwareItem } from '../App'
import './HardwareSelector.css'
import { API_BASE_URL } from '../config/api'

interface HardwareSelectorProps {
  selectedHardware: HardwareItem[]
  onSelect: (hardware: HardwareItem[]) => void
  hardwareType: 'gpu' | 'cpu' | 'storage'
  selectedRam?: number
  onRamSelect?: (ram: number) => void
  expanded?: boolean
}

function HardwareSelector({ selectedHardware, onSelect, hardwareType, selectedRam, onRamSelect, expanded }: HardwareSelectorProps) {
  const [isOpen, setIsOpen] = useState<boolean>(expanded ?? false)
  useEffect(() => {
    setIsOpen(expanded ?? false)
  }, [expanded])
  const [hardwareList, setHardwareList] = useState<HardwareItem[]>([])
  const [filteredList, setFilteredList] = useState<HardwareItem[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>(hardwareType)
  const [brandFilter, setBrandFilter] = useState<string>('all')
  const [seriesFilter, setSeriesFilter] = useState<string>('all')
  const [storageCapacityFilter, setStorageCapacityFilter] = useState<string>('all')
  const [loading, setLoading] = useState(false)
  const [brandOptions, setBrandOptions] = useState<string[]>([])
  const [modelOptions, setModelOptions] = useState<HardwareItem[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [lastFetchInfo, setLastFetchInfo] = useState<{ url?: string; count?: number; raw?: string }>({})
  const [sortBy, setSortBy] = useState<string>('default')
  const [customModel, setCustomModel] = useState<string>('')
  const [customBrand, setCustomBrand] = useState<string>('')
  const [customGeneration, setCustomGeneration] = useState<string>('')
  const [customYear, setCustomYear] = useState<string>('')
  const [customVram, setCustomVram] = useState<string>('')

  const isStorage = hardwareType === 'storage'

  useEffect(() => {
    if (isOpen) {
      // 每次開啟都嘗試刷新清單（若已有資料可快速回填）
      fetchHardwareList()
    }
  }, [isOpen])

  useEffect(() => {
    // 當使用者輸入 searchTerm 時立即使用本地或後端資料做即時過濾與顯示
    filterHardware()
  }, [searchTerm, categoryFilter, hardwareList])
  useEffect(() => {
    filterHardware()
  }, [brandFilter, seriesFilter, storageCapacityFilter, sortBy])

  const fetchHardwareList = async () => {
    setLoading(true)
    // 把 url 移到外層，讓 catch 可以正確顯示最後 fetch URL
    const category = categoryFilter !== 'all' ? categoryFilter : undefined
    const b = brandFilter !== 'all' ? `brand=${encodeURIComponent(brandFilter)}&` : ''
    const s = seriesFilter !== 'all' ? `series=${encodeURIComponent(seriesFilter)}&` : ''
    const url = `${API_BASE_URL}/api/hardware?${category ? `category=${category}&` : ''}${b}${s}${searchTerm ? `search=${encodeURIComponent(searchTerm)}&` : ''}`
    try {
      const response = await fetch(url)
      if (!response.ok) throw new Error('取得硬體列表失敗')

      const data = await response.json()
      const items = data.items || []
      setHardwareList(items)
      // 更新品牌選項
      const brands = Array.from(new Set(items.map((b: any) => b.brand).filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b)))
      setBrandOptions(brands)
      
      setLastFetchInfo({ url, count: items.length, raw: JSON.stringify(data).slice(0, 2000) })
    } catch (error) {
      console.warn('取得硬體列表錯誤，嘗試使用本機 seed 作為回退:', error)
      setLastFetchInfo({ url, raw: String(error) })
      try {
        const seed = await import('../data/hardware_seed_frontend.json')
        const data = seed.items || []
        setHardwareList(data)
        // 重置過濾條件但保持類別過濾
        setBrandFilter('all')
        setSeriesFilter('all')
        setStorageCapacityFilter('all')
        setCategoryFilter(hardwareType) // 保持專用選擇器的類別
        setSearchTerm('')
        // 重新過濾會在 useEffect 中自動觸發
        setFilteredList(data)
        setModelOptions(data)
        setBrandOptions(Array.from(new Set(data.map((b:any)=>b.brand).filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b))))
        
        setLastFetchInfo({ url: 'local seed fallback', count: data.length, raw: JSON.stringify(data).slice(0,2000) })
      } catch (err) {
        console.error('本機 seed 載入失敗', err)
        // 若 seed 也失敗，清空列表並記錄錯誤
        setHardwareList([])
        setFilteredList([])
        setModelOptions([])
        setBrandOptions([])
        setLastFetchInfo({ url, raw: String(error) + ' | SEED ERROR: ' + String(err) })
      }
    } finally {
      setLoading(false)
    }
  }

  // 自動清除篩選並刷新
  const clearFiltersAndRefresh = () => {
    setBrandFilter('all')
    setSeriesFilter('all')
    setStorageCapacityFilter('all')
    setCategoryFilter(hardwareType) // keep selector scoped to its category
    setSearchTerm('')
    setSortBy('default')
    // 立即刷新
    setTimeout(() => fetchHardwareList(), 50)
  }

  const getSelectorTitle = () => {
    if (hardwareType === 'gpu') return 'GPU'
    if (hardwareType === 'cpu') return 'CPU'
    return '儲存體'
  }

  const extractCapacityFromModel = (model?: string) => {
    const m = String(model || '')
    // Examples: "1TB", "2 TB", "500GB"
    const tb = m.match(/(\d+(?:\.\d+)?)\s*TB/i)
    if (tb?.[1]) return Math.round(Number(tb[1]) * 1000)
    const gb = m.match(/(\d+(?:\.\d+)?)\s*GB/i)
    if (gb?.[1]) return Math.round(Number(gb[1]))
    return undefined
  }

  const formatCapacity = (capacityGb?: number) => {
    if (!capacityGb) return ''

    // Prefer "human" TB rounding for common consumer sizes (seed uses 1000-based, some data may be 1024-based)
    const commonTb = [
      { tb: 16, gbMin: 14000, gbMax: 18000 },
      { tb: 8, gbMin: 7000, gbMax: 9200 },
      { tb: 4, gbMin: 3600, gbMax: 4600 },
      { tb: 2, gbMin: 1800, gbMax: 2300 },
      { tb: 1, gbMin: 900, gbMax: 1150 },
    ]
    for (const t of commonTb) {
      if (capacityGb >= t.gbMin && capacityGb <= t.gbMax) return `${t.tb}TB`
    }

    if (capacityGb >= 1000) {
      const tb = capacityGb / 1000
      const tbStr = Number.isInteger(tb) ? String(tb) : tb.toFixed(1)
      return `${tbStr}TB`
    }
    return `${capacityGb}GB`
  }

  const getCategoryTag = (category: string) => {
    if (category === 'gpu') return 'GPU'
    if (category === 'cpu') return 'CPU'
    if (category === 'storage') return '儲存體'
    return category.toUpperCase()
  }

  const inferBrandFromModel = (modelRaw: string) => {
    const m = String(modelRaw || '').toLowerCase()
    if (m.includes('intel') || m.includes('core i') || m.includes('i3-') || m.includes('i5-') || m.includes('i7-') || m.includes('i9-')) return 'Intel'
    if (m.includes('ryzen') || m.includes('threadripper') || m.includes('amd')) return 'AMD'
    if (m.includes('rtx') || m.includes('gtx') || m.includes('geforce')) return 'NVIDIA'
    if (m.includes('radeon') || m.includes('rx ') || m.includes('rx-')) return 'AMD'
    if (m.includes('arc')) return 'Intel'
    if (m.includes('samsung')) return 'Samsung'
    if (m.includes('western digital') || m.includes('wd ')) return 'Western Digital'
    if (m.includes('crucial')) return 'Crucial'
    if (m.includes('seagate')) return 'Seagate'
    if (m.includes('kingston')) return 'Kingston'
    if (m.includes('toshiba')) return 'Toshiba'
    if (m.includes('sandisk')) return 'SanDisk'
    if (m.includes('corsair')) return 'Corsair'
    if (m.includes('solidigm')) return 'Solidigm'
    return ''
  }

  const handleAddCustom = () => {
    const model = customModel.trim()
    if (!model) return alert('請輸入型號')

    const inferredBrand = inferBrandFromModel(model)
    const brand = (customBrand || inferredBrand || 'Unknown').trim()
    const generation = customGeneration.trim() || undefined
    const releaseYear = customYear.trim() ? Number(customYear.trim()) : undefined
    const vramGb = customVram.trim() ? Number(customVram.trim()) : undefined

    const item: HardwareItem = {
      category: hardwareType,
      model,
      generation,
      release_year: releaseYear && Number.isFinite(releaseYear) ? releaseYear : undefined,
      brand,
      selected: true,
      ...(hardwareType === 'gpu' && vramGb && Number.isFinite(vramGb) ? { vram_gb: vramGb, selected_vram_gb: vramGb } : {}),
      ...(hardwareType === 'storage' ? { capacity_gb: getStorageCapacityGb({ category: 'storage', model, generation, brand, selected: true } as any) } : {}),
    }

    // Avoid duplicates by (category, model)
    if (selectedHardware.some(h => h.category === item.category && h.model === item.model)) {
      alert('此型號已在已選清單中')
      return
    }

    onSelect([...selectedHardware, item])
    setCustomModel('')
    setCustomBrand('')
    setCustomGeneration('')
    setCustomYear('')
    setCustomVram('')
  }

  const getStorageTypeKey = (h: HardwareItem) => {
    const gen = String(h.generation || '').toLowerCase()
    const model = String(h.model || '').toLowerCase()
    if (gen.includes('nvme') || model.includes('nvme') || model.includes('m.2') || model.includes('m2') || model.includes('pcie')) return 'nvme'
    if (gen.includes('sata') || model.includes('sata') || gen.includes('ssd') || model.includes('ssd')) return 'sata'
    if (gen.includes('hdd') || model.includes('hdd') || model.includes('hard drive') || gen.includes('hard drive')) return 'hdd'
    return 'other'
  }

  const getStorageCapacityGb = (h: HardwareItem) => {
    const v = Number((h as any).capacity_gb || 0)
    if (v) return v
    return extractCapacityFromModel(h.model)
  }

  const getStorageDisplayModel = (h: HardwareItem) => {
    // Keep underlying model as-is for identity/search; only clean up UI display.
    const m = String(h.model || '').trim()
    return m
      .replace(/\s*\b\d+(?:\.\d+)?\s*TB\b/ig, '')
      .replace(/\s*\b\d+(?:\.\d+)?\s*GB\b/ig, '')
      .trim()
  }

  const getStorageTypeLabel = (h: HardwareItem) => {
    const k = getStorageTypeKey(h)
    if (k === 'nvme') return 'NVMe'
    if (k === 'sata') return 'SATA'
    if (k === 'hdd') return 'HDD'
    return h.generation || '其他'
  }

  const getBrandOrderIndex = (brand: string, type: HardwareSelectorProps['hardwareType']) => {
    // Normalize brand and handle common synonyms / model-derived brands (e.g. 'Ryzen', 'GeForce', 'RX')
    let b = String(brand || '').toLowerCase().trim()

    // Map common tokens to canonical brand names to improve matching
    const synonymMap: Record<string, string[]> = {
      intel: ['intel', 'core', 'ultra', 'xeon'],
      amd: ['amd', 'ryzen', 'radeon', 'threadripper'],
      nvidia: ['nvidia', 'geforce', 'gtx', 'rtx', 'quadro'],
      samsung: ['samsung'],
      'western digital': ['western digital', 'wd', 'wd-black', 'western'],
      crucial: ['crucial'],
      seagate: ['seagate'],
      kingston: ['kingston'],
      corsair: ['corsair'],
      sandisk: ['sandisk'],
      toshiba: ['toshiba'],
      solidigm: ['solidigm'],
    }

    // If brand string doesn't directly match an order list, try to map via synonyms
    for (const [canonical, tokens] of Object.entries(synonymMap)) {
      for (const t of tokens) {
        if (b.includes(t)) {
          b = canonical
          break
        }
      }
      if (b === canonical) break
    }

    const orders: Record<string, string[]> = {
      cpu: ['intel', 'amd'],
      gpu: ['nvidia', 'amd', 'intel'],
      storage: ['samsung', 'western digital', 'wd', 'crucial', 'seagate', 'kingston', 'corsair', 'sandisk', 'toshiba', 'solidigm'],
    }
    const list = orders[type] || []
    const idx = list.findIndex(k => b === k || b.includes(k))
    return idx === -1 ? 99 : idx
  }

  const normalizeModel = (m: string) => String(m || '').trim().replace(/\s+/g, ' ')

  const parseIntelGenNumber = (gen?: string) => {
    const g = String(gen || '').toLowerCase()
    const m = g.match(/(\d+)(st|nd|rd|th)\s*gen/)
    if (m?.[1]) return Number(m[1])
    return undefined
  }

  const cpuTierOrder = (model: string) => {
    const m = model.toLowerCase()
    if (m.includes('i9')) return 0
    if (m.includes('i7')) return 1
    if (m.includes('i5')) return 2
    if (m.includes('i3')) return 3
    if (m.includes('ryzen 9')) return 0
    if (m.includes('ryzen 7')) return 1
    if (m.includes('ryzen 5')) return 2
    if (m.includes('ryzen 3')) return 3
    return 9
  }

  const cpuSuffixOrder = (model: string) => {
    // smaller = higher priority
    const m = model.toUpperCase()
    // Intel: KS > K > KF > F > (none)
    if (m.includes('KS')) return 0
    if (m.includes('KF')) return 2
    if (m.includes('K')) return 1
    if (/\bF\b/.test(m)) return 3
    // AMD: X3D > X > XT > G > (none)
    if (m.includes('X3D')) return 0
    if (m.includes('XT')) return 2
    if (/\bX\b/.test(m)) return 1
    if (/\bG\b/.test(m)) return 3
    return 5
  }

  const extractFirstNumber = (model: string) => {
    // e.g. i5-12400F -> 12400, Ryzen 7 7700X -> 7700
    const m = model.replace(/,/g, '')
    const mm = m.match(/(\d{3,5})/)
    return mm?.[1] ? Number(mm[1]) : undefined
  }

  const gpuFamilyOrder = (model: string) => {
    const m = model.toUpperCase()
    // NVIDIA: RTX first, then GTX
    if (m.includes('RTX')) return 0
    if (m.includes('GTX')) return 1
    // AMD: RX first, then Radeon
    if (m.includes('RX')) return 0
    if (m.includes('RADEON')) return 1
    // Intel: Arc
    if (m.includes('ARC')) return 0
    return 9
  }

  const gpuSuffixOrder = (model: string) => {
    const m = model.toUpperCase()
    // NVIDIA suffixes: Ti > Super > (none)
    if (m.includes('TI') && !m.includes('TITAN')) return 0
    if (m.includes('SUPER')) return 1
    // AMD suffixes: XT > (none)
    if (m.includes('XTX')) return 0
    if (m.includes('XT') && !m.includes('XTX')) return 1
    return 9
  }

  const sortCpu = (a: HardwareItem, b: HardwareItem) => {
    const ba = getBrandOrderIndex(a.brand, 'cpu')
    const bb = getBrandOrderIndex(b.brand, 'cpu')
    if (ba !== bb) return ba - bb

    // Put Ultra Desktop on top of Intel group
    const au = String(a.generation || '').toLowerCase().includes('ultra') ||
                String(a.model || '').toLowerCase().includes('ultra')
    const bu = String(b.generation || '').toLowerCase().includes('ultra') ||
                String(b.model || '').toLowerCase().includes('ultra')
    if (au !== bu) return au ? -1 : 1

    const ga = parseIntelGenNumber(a.generation) ?? 0
    const gb = parseIntelGenNumber(b.generation) ?? 0
    if (ga !== gb) return gb - ga

    const ta = cpuTierOrder(a.model)
    const tb = cpuTierOrder(b.model)
    if (ta !== tb) return ta - tb

    const na = extractFirstNumber(a.model) ?? 0
    const nb = extractFirstNumber(b.model) ?? 0
    if (na !== nb) return nb - na

    const sa = cpuSuffixOrder(a.model)
    const sb = cpuSuffixOrder(b.model)
    if (sa !== sb) return sa - sb

    return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
  }

  const sortGpu = (a: HardwareItem, b: HardwareItem) => {
    const ba = getBrandOrderIndex(a.brand, 'gpu')
    const bb = getBrandOrderIndex(b.brand, 'gpu')
    if (ba !== bb) return ba - bb

    const fa = gpuFamilyOrder(a.model)
    const fb = gpuFamilyOrder(b.model)
    if (fa !== fb) return fa - fb

    const na = extractFirstNumber(a.model) ?? 0
    const nb = extractFirstNumber(b.model) ?? 0
    if (na !== nb) return nb - na

    const sa = gpuSuffixOrder(a.model)
    const sb = gpuSuffixOrder(b.model)
    if (sa !== sb) return sa - sb

    // fallback to year/generation then model
    const ya = Number(a.release_year || 0)
    const yb = Number(b.release_year || 0)
    if (ya !== yb) return yb - ya
    const ga = String(a.generation || '')
    const gb = String(b.generation || '')
    const gc = ga.localeCompare(gb)
    if (gc !== 0) return gc
    return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
  }

  const sortNonStorage = (a: HardwareItem, b: HardwareItem) => {
    if (hardwareType === 'cpu') return sortCpu(a, b)
    if (hardwareType === 'gpu') return sortGpu(a, b)
    // fallback: brand group -> year(desc) -> generation -> model
    const bo = getBrandOrderIndex(a.brand, hardwareType) - getBrandOrderIndex(b.brand, hardwareType)
    if (bo !== 0) return bo
    const ya = Number(a.release_year || 0)
    const yb = Number(b.release_year || 0)
    if (ya !== yb) return yb - ya
    const ga = String(a.generation || '')
    const gb = String(b.generation || '')
    const gc = ga.localeCompare(gb)
    if (gc !== 0) return gc
    const ba = String(a.brand || '')
    const bb = String(b.brand || '')
    const bc = ba.localeCompare(bb)
    if (bc !== 0) return bc
    return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
  }

  const customSortHardware = (hardwareList: HardwareItem[]) => {
    return [...hardwareList].sort((a, b) => {
      switch (sortBy) {
        case 'model-asc':
          return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'model-desc':
          return normalizeModel(b.model).localeCompare(normalizeModel(a.model))
        case 'brand-asc':
          const ba = String(a.brand || '').localeCompare(String(b.brand || ''))
          return ba !== 0 ? ba : normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'brand-desc':
          const bb = String(b.brand || '').localeCompare(String(a.brand || ''))
          return bb !== 0 ? bb : normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'year-desc':
          const ya = Number(a.release_year || 0)
          const yb = Number(b.release_year || 0)
          if (ya !== yb) return yb - ya
          return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'year-asc':
          const yaa = Number(a.release_year || 0)
          const ybb = Number(b.release_year || 0)
          if (yaa !== ybb) return yaa - ybb
          return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'vram-desc':
          if (hardwareType === 'gpu') {
            const va = Number((a as any).vram_gb || 0)
            const vb = Number((b as any).vram_gb || 0)
            if (va !== vb) return vb - va
          }
          return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'vram-asc':
          if (hardwareType === 'gpu') {
            const vaa = Number((a as any).vram_gb || 0)
            const vbb = Number((b as any).vram_gb || 0)
            if (vaa !== vbb) return vaa - vbb
          }
          return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'capacity-desc':
          if (isStorage) {
            const ca = Number(getStorageCapacityGb(a) || 0)
            const cb = Number(getStorageCapacityGb(b) || 0)
            if (ca !== cb) return cb - ca
          }
          return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'capacity-asc':
          if (isStorage) {
            const caa = Number(getStorageCapacityGb(a) || 0)
            const cbb = Number(getStorageCapacityGb(b) || 0)
            if (caa !== cbb) return caa - cbb
          }
          return normalizeModel(a.model).localeCompare(normalizeModel(b.model))
        case 'default':
        default:
          // Use existing sorting logic
          if (isStorage) {
            const typeOrder: Record<string, number> = { nvme: 0, sata: 1, hdd: 2, other: 3 }
            const ta = typeOrder[getStorageTypeKey(a)]
            const tb = typeOrder[getStorageTypeKey(b)]
            if (ta !== tb) return ta - tb
            const ca = Number(getStorageCapacityGb(a) || 0)
            const cb = Number(getStorageCapacityGb(b) || 0)
            if (ca !== cb) return cb - ca
            const bra = String(a.brand || '')
            const brb = String(b.brand || '')
            const brc = bra.localeCompare(brb)
            if (brc !== 0) return brc
            return String(a.model || '').localeCompare(String(b.model || ''))
          } else {
            return sortNonStorage(a, b)
          }
      }
    })
  }

  const filterHardware = () => {
    let filtered = hardwareList
    // brand filter
    if (brandFilter !== 'all') {
      if (brandFilter === 'intel-ultra') {
        // Special case for Intel Ultra: Intel brand + Ultra generation or model
        filtered = filtered.filter(h =>
          h.brand && h.brand.toLowerCase() === 'intel' &&
          ((h.generation && h.generation.toLowerCase().includes('ultra')) ||
           (h.model && h.model.toLowerCase().includes('ultra')))
        )
      } else {
        filtered = filtered.filter(h => h.brand && h.brand.toLowerCase().includes(brandFilter.toLowerCase()))
      }
    }
    // series filter (match generation or model tokens)
    if (seriesFilter !== 'all') {
      const sf = seriesFilter.toLowerCase()
      if (isStorage) {
        // storage: treat series as storage type (NVMe/SATA/HDD)
        if (sf === 'nvme') {
          filtered = filtered.filter(h => getStorageTypeKey(h) === 'nvme')
        } else if (sf === 'sata') {
          filtered = filtered.filter(h => getStorageTypeKey(h) === 'sata')
        } else if (sf === 'hdd') {
          filtered = filtered.filter(h => getStorageTypeKey(h) === 'hdd')
        } else {
          filtered = filtered.filter(h =>
            (h.generation && h.generation.toLowerCase().includes(sf)) ||
            (h.model && h.model.toLowerCase().includes(sf))
          )
        }
      } else {
        // CPU/GPU series filtering
        if (sf === 'core') {
          // Core = non-Ultra Intel (exclude Ultra generation/models), for other brands match existing logic
          filtered = filtered.filter(h => {
            const brand = (h.brand || '').toLowerCase()
            const gen = (h.generation || '').toLowerCase()
            const model = (h.model || '').toLowerCase()
            if (brand === 'intel') {
              return !gen.includes('ultra') && !model.includes('ultra')
            }
            return (gen && gen.includes(sf)) || (model && model.includes(sf))
          })
        } else if (sf === 'ultra') {
          // Ultra = only items explicitly marked Ultra in generation or model
          filtered = filtered.filter(h => {
            const gen = (h.generation || '').toLowerCase()
            const model = (h.model || '').toLowerCase()
            return gen.includes('ultra') || model.includes('ultra')
          })
        } else if (sf === 'rtx') {
          // RTX: for NVIDIA only include models/generations explicitly RTX; exclude GTX
          filtered = filtered.filter(h => {
            const brand = (h.brand || '').toLowerCase()
            const gen = (h.generation || '').toLowerCase()
            const model = (h.model || '').toLowerCase()
            if (brand === 'nvidia') {
              return (gen.includes('rtx') || model.includes('rtx')) && !model.includes('gtx')
            }
            return (gen && gen.includes(sf)) || (model && model.includes(sf))
          })
        } else if (sf === 'gtx') {
          // GTX: only models/generations explicitly GTX
          filtered = filtered.filter(h => {
            const gen = (h.generation || '').toLowerCase()
            const model = (h.model || '').toLowerCase()
            return gen.includes('gtx') || model.includes('gtx')
          })
        } else {
          // General series filtering
          filtered = filtered.filter(h =>
            (h.generation && h.generation.toLowerCase().includes(sf)) ||
            (h.model && h.model.toLowerCase().includes(sf))
          )
        }
      }
    }
    
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(h => h.category === categoryFilter)
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(h =>
        h.model.toLowerCase().includes(term) ||
        h.brand.toLowerCase().includes(term) ||
        (h.generation && h.generation.toLowerCase().includes(term))
      )
    }

    // storage capacity filter
    if (isStorage && storageCapacityFilter !== 'all') {
      filtered = filtered.filter(h => {
        const v = Number(getStorageCapacityGb(h) || 0)
        if (!v) return false
        switch (storageCapacityFilter) {
          case '0-512':
            return v <= 512
          case '513-1024':
            return v >= 513 && v <= 1024
          case '1025-2048':
            return v >= 1025 && v <= 2048
          case '2049-4096':
            return v >= 2049 && v <= 4096
          case '4097+':
            return v >= 4097
          default:
            return true
        }
      })
    }

    // Apply custom sorting
    filtered = customSortHardware(filtered)

    setFilteredList(filtered)
    // 更新 model options 根據目前過濾結果
    setModelOptions(filtered)
    // 若當前 selectedModel 不在列表內，回退到第一個，避免「進階：快速新增」卡住
    if (filtered.length > 0) {
      if (!filtered.some(m => m.model === selectedModel)) {
        setSelectedModel(filtered[0].model)
      }
    } else {
      if (selectedModel) setSelectedModel('')
    }
  }

  const handleToggleSelect = (hardware: HardwareItem) => {
    const isSelected = selectedHardware.some(
      h => h.category === hardware.category && h.model === hardware.model
    )

    if (isSelected) {
      onSelect(selectedHardware.filter(
        h => !(h.category === hardware.category && h.model === hardware.model)
      ))
    } else {
      // determine default vram value (support single vram_gb or vram_options array)
      const defaultVram = Array.isArray((hardware as any).vram_options) && (hardware as any).vram_options.length > 0
        ? (hardware as any).vram_options[0]
        : (hardware as any).vram_gb || undefined
      onSelect([...selectedHardware, { ...hardware, selected: true, selected_vram_gb: defaultVram } as any])
      // 同步更新右側已選型號下拉的值，方便使用者辨識
      setSelectedModel(hardware.model)
    }
  }

  const handleSelectedVramChange = (idx: number, vramValue: number) => {
    const updated = selectedHardware.map((h, i) => {
      if (i !== idx) return h
      return { ...h, selected_vram_gb: vramValue } as any
    })
    onSelect(updated)
  }

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const item = filteredList[index]
    const isSelected = selectedHardware.some(
      h => h.category === item.category && h.model === item.model
    )

    return (
      <div style={style} className={`hardware-row ${isStorage ? 'storage' : ''}`}>
        <div className="cell-icon" aria-hidden="true" />

        <div className="cell-model">
          <span className="hardware-model" title={String(isStorage ? getStorageDisplayModel(item) : item.model)}>
            {isStorage ? getStorageDisplayModel(item) : item.model}
          </span>
          <span className="hardware-brand-inline">{item.brand}</span>
          {isStorage ? (
            <span className="storage-type-badge" style={{ marginLeft: 8 }}>
              {getStorageTypeLabel(item)}
            </span>
          ) : null}
        </div>

        <div className="cell-gen">
          {!isStorage && item.generation ? item.generation : ''}
        </div>

        <div className="cell-year">
          {!isStorage && item.release_year ? item.release_year : (isStorage && getStorageCapacityGb(item) ? formatCapacity(getStorageCapacityGb(item)) : '')}
        </div>

        <div className="cell-action">
          <button
            className={`select-button ${isSelected ? 'selected' : ''}`}
            onClick={() => handleToggleSelect(item)}
          >
            {isSelected ? '已選取' : '選取'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="hardware-selector">
      <div className="selector-header">
        <h2>選擇{getSelectorTitle()}</h2>
      </div>

      {selectedHardware.length > 0 && (
        <div className="selected-hardware">
          <h3>已選取的硬體 ({selectedHardware.length})</h3>
          <div className="selected-list">
            {selectedHardware.map((h, idx) => {
              const vramOptions = (h as any).vram_options || ((h as any).vram_gb ? [(h as any).vram_gb] : [])
              const selectedVram = (h as any).selected_vram_gb ?? vramOptions[0]
              const cap = h.category === 'storage' ? formatCapacity(getStorageCapacityGb(h)) : ''
              return (
                <div key={idx} className="selected-item">
                  <div className="selected-item-content">
                    <span className="selected-category">{getCategoryTag(h.category)}</span>
                    <span className="selected-model">{h.category === 'storage' ? getStorageDisplayModel(h) : h.model}</span>
                    {h.category === 'storage' && cap && (
                      <span className="selected-vram">{getStorageTypeLabel(h)} • {cap}</span>
                    )}
                    {h.category === 'gpu' && vramOptions.length > 0 && (
                      vramOptions.length === 1 ? (
                        <span className="selected-vram">{vramOptions[0]}GB VRAM</span>
                      ) : (
                        <select
                          className="selected-vram-select"
                          value={String(selectedVram)}
                          onChange={(e) => handleSelectedVramChange(idx, Number(e.target.value))}
                        >
                          {vramOptions.map((v: number) => (
                            <option key={v} value={v}>{v} GB VRAM</option>
                          ))}
                        </select>
                      )
                    )}
                  </div>
                  <button
                    className="remove-button"
                    onClick={() => onSelect(selectedHardware.filter((_, i) => i !== idx))}
                  >
                    ×
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}


      {isOpen && (
        <div className="hardware-table-container">
          <div className="table-filters">
            {isStorage ? (
              <div className="storage-filters">
                <div className="storage-type-tabs" role="tablist" aria-label="儲存體介面">
                  <button className={`tab-btn ${seriesFilter === 'all' ? 'active' : ''}`} onClick={() => setSeriesFilter('all')}>全部</button>
                  <button className={`tab-btn ${seriesFilter === 'nvme' ? 'active' : ''}`} onClick={() => setSeriesFilter('nvme')}>NVMe</button>
                  <button className={`tab-btn ${seriesFilter === 'sata' ? 'active' : ''}`} onClick={() => setSeriesFilter('sata')}>SATA</button>
                  <button className={`tab-btn ${seriesFilter === 'hdd' ? 'active' : ''}`} onClick={() => setSeriesFilter('hdd')}>HDD</button>
                </div>

                <select value={brandFilter} onChange={(e) => setBrandFilter(e.target.value)} className="filter-select">
                  <option value="all">所有品牌</option>
                  {brandOptions.map((b) => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>

                <select value={storageCapacityFilter} onChange={(e) => setStorageCapacityFilter(e.target.value)} className="filter-select">
                  <option value="all">所有容量</option>
                  <option value="0-512">≤ 512GB</option>
                  <option value="513-1024">513GB–1TB</option>
                  <option value="1025-2048">1TB–2TB</option>
                  <option value="2049-4096">2TB–4TB</option>
                  <option value="4097+">≥ 4TB</option>
                </select>

                <input
                  type="text"
                  placeholder="搜尋型號或品牌..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="filter-input"
                />
              </div>
            ) : (
              <div className="brand-filter">
                <button className={`brand-btn ${brandFilter==='all'?'active':''}`} onClick={()=>{setBrandFilter('all'); setSeriesFilter('all')}}>All</button>
                {hardwareType === 'gpu' ? (
                  <>
                    <button className={`brand-btn ${brandFilter==='nvidia'?'active':''}`} onClick={()=>{setBrandFilter('nvidia'); setSeriesFilter('all')}}>NVIDIA</button>
                    <button className={`brand-btn ${brandFilter==='amd'?'active':''}`} onClick={()=>{setBrandFilter('amd'); setSeriesFilter('all')}}>AMD</button>
                    <button className={`brand-btn ${brandFilter==='intel'?'active':''}`} onClick={()=>{setBrandFilter('intel'); setSeriesFilter('all')}}>Intel</button>
                  </>
                ) : (
                  <>
                    <button className={`brand-btn ${brandFilter==='intel'?'active':''}`} onClick={()=>{setBrandFilter('intel'); setSeriesFilter('all')}}>Intel</button>
                    <button className={`brand-btn ${brandFilter==='amd'?'active':''}`} onClick={()=>{setBrandFilter('amd'); setSeriesFilter('all')}}>AMD</button>
                  </>
                )}
              </div>
            )}
          <div style={{marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center'}}>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="filter-select"
              style={{ minWidth: '140px' }}
            >
              <option value="default">預設排序</option>
              <option value="model-asc">型號 A-Z</option>
              <option value="model-desc">型號 Z-A</option>
              <option value="brand-asc">品牌 A-Z</option>
              <option value="brand-desc">品牌 Z-A</option>
              <option value="year-desc">年份 (新→舊)</option>
              <option value="year-asc">年份 (舊→新)</option>
              {hardwareType === 'gpu' && (
                <>
                  <option value="vram-desc">VRAM (高→低)</option>
                  <option value="vram-asc">VRAM (低→高)</option>
                </>
              )}
              {isStorage && (
                <>
                  <option value="capacity-desc">容量 (大→小)</option>
                  <option value="capacity-asc">容量 (小→大)</option>
                </>
              )}
            </select>
            <button className="refresh-button" onClick={() => fetchHardwareList()}>刷新</button>
            <button className="refresh-button" onClick={() => clearFiltersAndRefresh()}>清除篩選並刷新</button>
          </div>
          {/* 移除手動載入按鈕，改由輸入時自動過濾與顯示 */}

            {!isStorage && (
              <>
                <select
                  value={seriesFilter}
                  onChange={(e) => setSeriesFilter(e.target.value)}
                  className="filter-select"
                >
                  <option value="all">所有系列</option>
                  {hardwareType === 'gpu' ? (
                    <>
                      {brandFilter==='nvidia' && <>
                        <option value="rtx">RTX</option>
                        <option value="gtx">GTX</option>
                      </>}
                      {brandFilter==='amd' && <>
                        <option value="rx">RX</option>
                        <option value="rdna">RDNA</option>
                      </>}
                      {brandFilter==='intel' && <>
                        <option value="arc">Arc</option>
                      </>}
                    </>
                  ) : (
                    <>
                      {brandFilter==='intel' && <>
                        <option value="core">Core</option>
                        <option value="ultra">Ultra</option>
                      </>}
                      {brandFilter==='amd' && <>
                        <option value="ryzen">Ryzen</option>
                      </>}
                    </>
                  )}
                </select>

                <input
                  type="text"
                  placeholder="搜尋硬體型號、廠牌..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="filter-input"
                />
              </>
            )}

            {!isStorage && (
              <>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="filter-select"
                >
                  <option value={hardwareType}>{hardwareType.toUpperCase()}</option>
                </select>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="filter-select"
                >
                  <option value="">選取型號</option>
                  {modelOptions.map((m, idx) => (
                    <option key={idx} value={m.model}>
                      {m.model} ({m.brand})
                    </option>
                  ))}
                </select>

                <button
                  onClick={() => {
                    if (!selectedModel) return alert('請先選擇型號')
                    const hw = hardwareList.find(h => h.model === selectedModel)
                    if (hw) handleToggleSelect(hw)
                  }}
                  className="refresh-button"
                >
                  新增型號
                </button>
              </>
            )}

            {isStorage && (
              <details className="storage-advanced">
                <summary>進階：快速新增 / 自訂新增</summary>
                <div className="storage-advanced-body">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="filter-select"
                  >
                    <option value="">選取型號</option>
                    {modelOptions.map((m, idx) => (
                      <option key={idx} value={m.model}>
                        {m.brand} — {getStorageDisplayModel(m)}{getStorageCapacityGb(m) ? ` — ${formatCapacity(getStorageCapacityGb(m))}` : ''}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={() => {
                      if (!selectedModel) return alert('請先選擇型號')
                      const hw = hardwareList.find(h => h.model === selectedModel)
                      if (hw) handleToggleSelect(hw)
                    }}
                    className="refresh-button"
                  >
                    新增
                  </button>
                </div>
                <div className="storage-advanced-body" style={{ marginTop: 10 }}>
                  <input
                    type="text"
                    placeholder="自訂型號（例如：Samsung 990 PRO 2TB）"
                    value={customModel}
                    onChange={(e) => setCustomModel(e.target.value)}
                    className="filter-input"
                    style={{ minWidth: 260 }}
                  />
                  <input
                    type="text"
                    placeholder="品牌（可留空自動推測）"
                    value={customBrand}
                    onChange={(e) => setCustomBrand(e.target.value)}
                    className="filter-input"
                    style={{ minWidth: 200 }}
                  />
                  <input
                    type="text"
                    placeholder="介面/類型（NVMe/SATA/HDD，可留空）"
                    value={customGeneration}
                    onChange={(e) => setCustomGeneration(e.target.value)}
                    className="filter-input"
                    style={{ minWidth: 220 }}
                  />
                  <button onClick={handleAddCustom} className="refresh-button">加入</button>
                </div>
              </details>
            )}
          </div>

          {!isStorage && (
            <details className="storage-advanced" style={{ marginLeft: 0, marginTop: 8 }}>
              <summary>進階：自訂新增（支援任何 2016–現在型號）</summary>
              <div className="storage-advanced-body">
                <input
                  type="text"
                  placeholder={hardwareType === 'gpu' ? '自訂 GPU 型號（例：RTX 3090 Ti）' : '自訂 CPU 型號（例：Intel Core i3-12100F）'}
                  value={customModel}
                  onChange={(e) => setCustomModel(e.target.value)}
                  className="filter-input"
                  style={{ minWidth: 320 }}
                />
                <input
                  type="text"
                  placeholder="品牌（可留空自動推測）"
                  value={customBrand}
                  onChange={(e) => setCustomBrand(e.target.value)}
                  className="filter-input"
                  style={{ minWidth: 200 }}
                />
                <input
                  type="text"
                  placeholder="世代/系列（可留空）"
                  value={customGeneration}
                  onChange={(e) => setCustomGeneration(e.target.value)}
                  className="filter-input"
                  style={{ minWidth: 200 }}
                />
                <input
                  type="number"
                  placeholder="年份（可留空）"
                  value={customYear}
                  onChange={(e) => setCustomYear(e.target.value)}
                  className="filter-input"
                  style={{ width: 140 }}
                />
                {hardwareType === 'gpu' && (
                  <input
                    type="number"
                    placeholder="VRAM(GB，可留空)"
                    value={customVram}
                    onChange={(e) => setCustomVram(e.target.value)}
                    className="filter-input"
                    style={{ width: 160 }}
                  />
                )}
                <button onClick={handleAddCustom} className="refresh-button">加入</button>
              </div>
            </details>
          )}

          {loading ? (
            <div className="loading">
              <div className="loading-spinner"></div>
              <p>正在載入硬體列表...</p>
            </div>
          ) : null}

          {!loading && (
            <div className={`table-header ${isStorage ? 'storage' : ''}`}>
              {isStorage ? (
                <>
                  <div className="header-cell">型號</div>
                  <div className="header-cell">廠牌</div>
                  <div className="header-cell">容量</div>
                  <div className="header-cell">操作</div>
                </>
              ) : (
                <>
                  <div className="header-cell">型號</div>
                  <div className="header-cell">廠牌</div>
                  <div className="header-cell">世代</div>
                  <div className="header-cell">釋出年</div>
                  <div className="header-cell">操作</div>
                </>
              )}
            </div>
          )}

          {!loading && filteredList.length > 0 && (
            <List
              height={480}
              itemCount={filteredList.length}
              itemSize={80}
              width="100%"
            >
              {Row}
            </List>
          )}

          {!loading && filteredList.length === 0 && (
            <div className="empty-state">
              沒有找到符合條件的硬體
              <div className="debug-info">
                <div>最後 fetch URL: <code>{lastFetchInfo.url}</code></div>
                <div>回傳數量: {lastFetchInfo.count ?? 0}</div>
                {lastFetchInfo.raw && <details><summary>response (preview)</summary><pre style={{maxHeight:200,overflow:'auto'}}>{lastFetchInfo.raw}</pre></details>}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default HardwareSelector

