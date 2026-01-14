# Google 搜尋工具使用說明

這個工具讓你在編寫代碼時可以透過 Google Programmable Search Engine API 進行網頁搜尋。

## 快速開始

### 方法一：直接使用（已設定 API 金鑰）

```python
from google_programmable_search import google_search

# 直接使用預設的 API 金鑰
results = google_search("Python 教學", num=5)

for idx, result in enumerate(results, start=1):
    print(f"{idx}. {result['title']}")
    print(f"   連結: {result['link']}")
    print(f"   摘要: {result['snippet']}\n")
```

### 方法二：使用環境變數

設定環境變數後，可以更安全地管理 API 金鑰：

**Windows PowerShell:**
```powershell
$env:GOOGLE_API_KEY="你的API金鑰"
$env:GOOGLE_CX="你的Search Engine ID"
```

**Windows CMD:**
```cmd
set GOOGLE_API_KEY=你的API金鑰
set GOOGLE_CX=你的Search Engine ID
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY="你的API金鑰"
export GOOGLE_CX="你的Search Engine ID"
```

然後在代碼中使用：
```python
from google_programmable_search import google_search

# 會自動從環境變數讀取
results = google_search("Python 教學")
```

### 方法三：手動指定 API 金鑰

```python
from google_programmable_search import google_search

API_KEY = "你的API金鑰"
CX = "你的Search Engine ID"

results = google_search("Python 教學", api_key=API_KEY, cx=CX, num=5)
```

## 參數說明

- `query` (必填): 搜尋關鍵字
- `api_key` (選填): Google API 金鑰，如果不提供會從環境變數讀取
- `cx` (選填): Programmable Search Engine ID，如果不提供會從環境變數讀取
- `num` (選填): 返回結果數量，範圍 1-10，預設為 5

## 返回值

返回一個列表，每個元素包含：
- `title`: 網頁標題
- `link`: 網頁連結
- `snippet`: 網頁摘要

## 錯誤處理

程式會自動處理以下錯誤：
- API 金鑰或 CX 未設定
- 查詢關鍵字為空
- 結果數量超出範圍
- 網路請求失敗
- API 錯誤

## 使用範例

### 搜尋技術文件
```python
results = google_search("FastAPI 文件", num=10)
```

### 搜尋錯誤解決方案
```python
results = google_search("Python ImportError 解決方法")
```

### 搜尋最新技術資訊
```python
results = google_search("React 18 新功能", num=8)
```

## 注意事項

1. API 有每日配額限制，請合理使用
2. 確保在 Google Cloud Console 中已啟用 Custom Search API
3. 建議將 API 金鑰存放在環境變數中，不要直接寫在代碼裡

## 測試

執行以下命令測試功能：
```bash
python google_programmable_search.py
```
