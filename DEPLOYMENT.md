# 部署指南

## 系統需求

### 後端
- Python 3.8+
- pip
- (選填) Redis (用於分散式快取)

### 前端
- Node.js 16+
- npm 或 yarn

## 安裝步驟

### 1. 後端安裝

```bash
cd backend

# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 檔案設定必要的環境變數

# 啟動服務
uvicorn app.main:app --reload
```

### 2. 前端安裝

```bash
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器
npm run dev
```

## 生產環境部署

### 後端 (使用 Gunicorn)

```bash
# 安裝 Gunicorn
pip install gunicorn

# 啟動服務
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 前端 (建置靜態檔案)

```bash
# 建置生產版本
npm run build

# 使用 Nginx 或其他靜態檔案伺服器提供服務
# 建置後的檔案在 dist/ 目錄
```

### Nginx 設定範例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端靜態檔案
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 後端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 環境變數說明

### 後端 (.env)

```env
# Redis 設定 (選填)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 快取設定
CACHE_TTL_HOURS=24
CACHE_HOT_TTL_HOURS=1

# Rate Limiting
REQUEST_DELAY_SECONDS=1
MAX_CONCURRENT_REQUESTS=3
```

## Docker 部署 (選填)

### Dockerfile (後端)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile (前端)

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
```

## 注意事項

1. **資料來源**: 確保系統能正常連接到資料來源網站
2. **Rate Limiting**: 遵守各網站的 robots.txt 與使用條款
3. **快取**: 生產環境建議使用 Redis 進行快取
4. **安全性**: 設定適當的 CORS 政策與 API 認證（如需要）


