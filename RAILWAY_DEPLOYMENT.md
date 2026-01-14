# Railway 部署指南

## 方法3：使用 Railway 部署完整的全端應用

Railway 是一個現代化的雲端平台，讓部署應用變得非常簡單。

### 步驟1：準備工作

1. **安裝 Git**（如果還沒安裝）
   - 下載：[https://git-scm.com/download/win](https://git-scm.com/download/win)

2. **建立 GitHub 倉庫**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

### 步驟2：註冊 Railway 帳號

1. 前往 [Railway.app](https://railway.app)
2. 使用 GitHub 帳號註冊/登入

### 步驟3：部署後端

1. **點擊 "New Project"**
2. **選擇 "Deploy from GitHub repo"**
3. **連接你的 GitHub 倉庫** (`senior1-ai-project`)
4. **Railway 會自動檢測並部署**

### 步驟4：配置環境變數

在 Railway 儀表板中，進入你的專案：

1. 點擊 **"Variables"** 標籤
2. 添加以下環境變數：

```
PYTHONPATH=/app
CACHE_TTL_HOURS=24
REQUEST_DELAY_SECONDS=1
MAX_CONCURRENT_REQUESTS=3
REDIS_HOST=${{ REDIS_HOST }}
REDIS_PORT=${{ REDIS_PORT }}
REDIS_PASSWORD=${{ REDIS_PASSWORD }}
```

### 步驟5：添加資料庫（可選）

如果需要 Redis 快取：

1. 在 Railway 中點擊 **"+ Add"** → **"Database"**
2. 選擇 **"Redis"**
3. Railway 會自動設定環境變數

### 步驟6：部署前端

Railway 支援多個服務在同一個專案中：

1. 在專案中點擊 **"+ Add"** → **"Service"**
2. 選擇 **"Empty Service"**
3. 在 **"Settings"** 中設定：
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Start Command**: `cd frontend && npx serve -s dist -l 3000`
4. 設定環境變數：
   ```
   VITE_API_BASE_URL=${{ BACKEND_URL }}
   ```

### 步驟7：設定域名（可選）

1. 在 Railway 中點擊 **"Settings"**
2. 點擊 **"Domains"**
3. Railway 會提供一個免費的 `.up.railway.app` 域名

## 測試部署

部署完成後，你可以：

1. **檢查後端健康狀態**：
   ```
   curl https://your-project.up.railway.app/health
   ```

2. **檢查前端**：
   訪問 Railway 提供的域名

3. **檢查 API 連線**：
   確保前端能正確連接到後端 API

## 疑難排解

### 常見問題

1. **建置失敗**：
   - 檢查 `railway.toml` 配置
   - 確保所有檔案都已提交到 Git

2. **環境變數問題**：
   - 在 Railway 儀表板中檢查變數設定
   - 確保變數名稱正確

3. **資料庫連線問題**：
   - 檢查 Redis 服務是否正確連接
   - 確認環境變數設定

### 重新部署

每次推送程式碼到 GitHub，Railway 會自動重新部署：

```bash
git add .
git commit -m "Update"
git push origin main
```

## 成本估計

Railway 的免費方案包括：
- 512 MB RAM
- 1 GB 儲存空間
- 每月免費額度

如果超過免費額度，會按使用量收費，通常每月 $5-10 左右。

## 下一步

部署完成後，你可以：

1. 設定自訂域名
2. 添加監控和日誌
3. 設定自動備份
4. 添加更多服務（如資料庫）