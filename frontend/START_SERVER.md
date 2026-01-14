# 如何正確啟動網站

## ⚠️ 重要：必須使用 Vite 開發服務器

您目前看到的目錄列表是因為使用了錯誤的服務器。請按照以下步驟操作：

## 正確的啟動方式

### 1. 打開終端/命令提示字元

### 2. 進入 frontend 目錄
```bash
cd frontend
```

### 3. 安裝依賴（如果還沒安裝）
```bash
npm install
```

### 4. 啟動 Vite 開發服務器
```bash
npm run dev
```

### 5. 在瀏覽器中打開
您應該會看到類似這樣的輸出：
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**請打開 `http://localhost:5173/` 而不是 `127.0.0.1:5500`**

## 為什麼不能使用 Live Server？

- Live Server 無法處理 TypeScript/React
- 無法正確載入 Vite 的模組系統
- CSS 和 JS 可能無法正確編譯和載入

## 如果遇到問題

1. **確保 Node.js 已安裝**
   ```bash
   node --version
   ```
   應該顯示 v16 或更高版本

2. **清除快取並重新安裝**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run dev
   ```

3. **檢查端口是否被占用**
   如果 5173 端口被占用，Vite 會自動使用下一個可用端口（如 5174）

## 後端也需要啟動

在另一個終端視窗中：

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

後端應該在 `http://localhost:8000` 運行


