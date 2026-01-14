# 環境變數設定

請在 `backend` 目錄下建立 `.env` 檔案，並參考以下設定：

```env
# Redis Cache (可選，未設定則使用記憶體快取)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Cache Settings
CACHE_TTL_HOURS=24
CACHE_HOT_TTL_HOURS=1

# Rate Limiting
REQUEST_DELAY_SECONDS=1
MAX_CONCURRENT_REQUESTS=3

# API Keys (如有需要)
# Google Programmable Search API（可選；未設定時會回退到本地快取/預測模型）
# GOOGLE_API_KEY=
# GOOGLE_CX=
```

## 說明

- **REDIS_HOST/PORT/DB**: Redis 連線設定（選填，未設定則使用記憶體快取）
- **CACHE_TTL_HOURS**: 預設快取時間（小時）
- **CACHE_HOT_TTL_HOURS**: 熱門項目快取時間（小時）
- **REQUEST_DELAY_SECONDS**: 請求之間的延遲時間（秒），遵守 rate limiting
- **MAX_CONCURRENT_REQUESTS**: 最大並發請求數


