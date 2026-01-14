# API 文件

## 基礎資訊

- **Base URL**: `http://localhost:8000`
- **API 版本**: v1.0.0
- **資料格式**: JSON

## 重要聲明

⚠️ **所有硬體與基準資料必須即時從網路抓取，不可使用任何內建靜態資料。**

## 端點列表

### 1. 健康檢查

**GET** `/health`

檢查 API 服務狀態。

**回應:**
```json
{
  "status": "healthy"
}
```

---

### 2. 取得硬體列表

**GET** `/api/hardware`

從網路即時抓取硬體列表。

**查詢參數:**
- `category` (選填): 硬體類別，`gpu` / `cpu` / `storage`
- `search` (選填): 搜尋關鍵字（型號/廠牌/世代）
- `brand` (選填): 廠牌過濾（模糊比對）
- `series` (選填): 系列/世代過濾（模糊比對）
  - `storage` 類別時也支援：`nvme` / `sata` / `hdd`
- `min_vram_gb` (選填): 最低 VRAM (GB)（主要用於 GPU）
- `min_ram_gb` (選填): 最低 RAM (GB)（主要用於 CPU）

**範例請求:**
```
GET /api/hardware?category=gpu&search=RTX
```

**回應:**
```json
{
  "items": [
    {
      "category": "gpu",
      "model": "RTX 4090",
      "generation": "Ada",
      "release_year": 2022,
      "brand": "NVIDIA",
      "selected": false
    },
    {
      "category": "gpu",
      "model": "RTX 4080",
      "generation": "Ada",
      "release_year": 2022,
      "brand": "NVIDIA",
      "selected": false
    }
  ],
  "total": 2,
  "source": "TechPowerUp GPU Database",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**錯誤回應:**
```json
{
  "detail": "無法取得硬體列表: <錯誤訊息>"
}
```

---

### 3. 搜尋基準測試資料

**POST** `/api/benchmarks/search`

從網路即時搜尋遊戲效能基準資料。

**請求體:**
```json
{
  "game": "Cyberpunk 2077",
  "resolution": "1920x1080",
  "settings": "Ultra",
  "hardware": [
    {
      "category": "gpu",
      "model": "RTX 4090"
    },
    {
      "category": "cpu",
      "model": "Intel i9-13900K"
    }
  ]
}
```

**回應:**
```json
{
  "results": [
    {
      "game": "Cyberpunk 2077",
      "resolution": "1920x1080",
      "settings": "Ultra",
      "gpu": "RTX 4090",
      "cpu": "Intel i9-13900K",
      "avg_fps": 120.5,
      "p1_low": 95.2,
      "p0_1_low": 88.1,
      "source": "TechPowerUp GPU Database",
      "timestamp": "2024-01-01T12:00:00.000000",
      "notes": null,
      "confidence_score": 0.9,
      "raw_source_snippet": "原始來源片段...",
      "is_incomplete": false
    }
  ],
  "total": 1
}
```

**欄位說明:**
- `avg_fps`: 平均 FPS（可能為 null）
- `p1_low`: 1% low FPS（可能為 null）
- `p0_1_low`: 0.1% low FPS（可能為 null）
- `confidence_score`: 可信度分數 (0.0 - 1.0)
- `is_incomplete`: 是否為不完整資料
- `raw_source_snippet`: 原始來源片段（供使用者檢視）

**錯誤回應:**
```json
{
  "detail": "搜尋基準測試失敗: <錯誤訊息>"
}
```

---

### 4. 取得瓶頸分析

**GET** `/api/benchmarks/{benchmark_id}/bottleneck`

分析指定基準測試的效能瓶頸。

**路徑參數:**
- `benchmark_id`: 基準測試 ID

**回應:**
```json
{
  "bottleneck_type": "GPU-bound",
  "confidence": 0.9,
  "reasoning": "GPU 使用率達 98%，CPU 使用率僅 65%，顯示 GPU 為瓶頸",
  "recommendations": [
    "降低解析度或畫質設定",
    "啟用 DLSS/FSR 等升頻技術",
    "考慮升級 GPU"
  ]
}
```

**瓶頸類型:**
- `GPU-bound`: GPU 瓶頸
- `CPU-bound`: CPU 瓶頸
- `Memory-bound`: 記憶體瓶頸
- `IO-bound`: I/O 瓶頸
- `Balanced`: 系統平衡
- `Unknown`: 無法判定

**錯誤回應:**
```json
{
  "detail": "瓶頸分析失敗: <錯誤訊息>"
}
```

---

### 5. 比較基準測試

**POST** `/api/benchmarks/compare`

比較多組基準測試結果。

**查詢參數:**
- `metric` (選填): 比較指標，預設為 `avg_fps`
  - `avg_fps`: 平均 FPS
  - `p1_low`: 1% low
  - `p0_1_low`: 0.1% low

**請求體:**
```json
["benchmark_id_1", "benchmark_id_2", "benchmark_id_3"]
```

**回應:**
```json
{
  "benchmark_ids": ["benchmark_id_1", "benchmark_id_2"],
  "metric": "avg_fps",
  "data": [
    {
      "benchmark_id": "benchmark_id_1",
      "value": 120.5,
      "hardware": "RTX 4090 / Intel i9-13900K"
    },
    {
      "benchmark_id": "benchmark_id_2",
      "value": 95.3,
      "hardware": "RTX 4080 / Intel i9-13900K"
    }
  ]
}
```

---

## 錯誤處理

所有錯誤回應都遵循以下格式:

```json
{
  "detail": "錯誤訊息"
}
```

**HTTP 狀態碼:**
- `200`: 成功
- `400`: 請求錯誤
- `404`: 資源不存在
- `500`: 伺服器錯誤

---

## 快取策略

- **預設快取時間**: 24 小時
- **熱門項目快取時間**: 1 小時
- **手動刷新**: 可透過 API 或前端介面手動刷新快取

---

## Rate Limiting

系統遵守來源網站的 robots.txt 與使用條款，並實作以下限制:

- **請求延遲**: 預設 1 秒（可透過環境變數調整）
- **並發請求**: 最多 3 個同時請求

---

## 資料來源

系統會從以下來源抓取資料（遵守各網站 robots.txt 與使用條款）:

- TechPowerUp GPU Database
- 其他公開的基準測試資料庫

**注意**: 實際可用的資料來源需要根據網站結構與 API 可用性進行調整。


