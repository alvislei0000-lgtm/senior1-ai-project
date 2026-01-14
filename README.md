# Google Custom Search API 工具

這個工具使用 Google Custom Search API 來進行網頁搜索，提供安全且易用的介面。

## 功能特色

- ✅ 安全的 API 金鑰管理（使用環境變數）
- ✅ 完整的錯誤處理
- ✅ 參數驗證
- ✅ 類型提示
- ✅ 支援請求超時

## 安裝依賴

```bash
pip install requests
```

## 設定 API 認證

### 方法 1：環境變數（推薦）

```bash
# Linux/Mac
export GOOGLE_API_KEY="你的API金鑰"
export GOOGLE_CX="你的Search Engine ID"

# Windows PowerShell
$env:GOOGLE_API_KEY="你的API金鑰"
$env:GOOGLE_CX="你的Search Engine ID"

# Windows CMD
set GOOGLE_API_KEY=你的API金鑰
set GOOGLE_CX=你的Search Engine ID
```

### 方法 2：程式碼中直接設定

```python
from google_search import google_search

results = google_search(
    "Python 教學",
    api_key="你的API金鑰",
    cx="你的Search Engine ID",
    num=5
)
```

## 使用範例

```python
from google_search import google_search

# 基本搜索
results = google_search("人工智能")

# 自訂參數
results = google_search("機器學習", num=10)

# 顯示結果
for result in results:
    print(f"標題: {result['title']}")
    print(f"連結: {result['link']}")
    print(f"摘要: {result['snippet']}")
    print("---")
```

## API 設定步驟

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 啟用 "Custom Search API"
4. 建立 API 金鑰
5. 前往 [Custom Search Engine](https://cse.google.com/)
6. 建立新的搜索引擎
7. 取得 Search Engine ID

## 測試

運行測試腳本：

```bash
python test_google_search.py
```

## 安全性注意事項

- 不要將 API 金鑰硬編碼在程式碼中
- 使用環境變數或安全的金鑰管理系統
- 定期輪換 API 金鑰
- 監控 API 使用量以避免超出配額