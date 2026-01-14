# 快速啟動指南

## 系統已準備就緒！

本系統現在可以實際運行，具備以下功能：
- ✅ 選擇不同硬體（GPU/CPU）
- ✅ 顯示所選擇硬體的 FPS 資料（平均 FPS、1% Low、0.1% Low）
- ✅ 自動分析並顯示瓶頸位置（GPU/CPU/RAM/I/O）
- ✅ 提供瓶頸分析建議

## 啟動步驟

### 1. 啟動後端

```bash
cd backend

# 安裝依賴（首次運行）
pip install -r requirements.txt

# 啟動服務
uvicorn app.main:app --reload
```

後端將在 `http://localhost:8000` 運行

### 2. 啟動前端

開啟新的終端視窗：

```bash
cd frontend

# 安裝依賴（首次運行）
npm install

# 啟動開發伺服器
npm run dev
```

前端將在 `http://localhost:3000` 運行

## 使用方式

1. **選擇硬體**
   - 點擊「開啟硬體選擇器」按鈕
   - 在表格中選擇 GPU 和 CPU
   - 可以搜尋特定型號（例如：RTX 4090）
   - 點擊「選取」按鈕加入比較

2. **搜尋基準資料**
   - 輸入遊戲名稱（例如：Cyberpunk 2077）
   - 選擇解析度（1080p、1440p、4K）
   - 可選：輸入畫質設定（例如：Ultra）
   - 點擊「搜尋基準資料」

3. **查看結果**
   - 系統會顯示每個硬體組合的 FPS 資料
   - **瓶頸分析**會自動顯示，告訴您：
     - 瓶頸類型（GPU/CPU/RAM/I/O）
     - 置信度
     - 分析說明
     - 改進建議

4. **比較多組硬體**
   - 選擇多個硬體組合後搜尋
   - 系統會顯示比較圖表
   - 可以切換不同的 FPS 指標

## 功能特色

### 瓶頸分析

系統會自動分析效能瓶頸，包括：

- **GPU-bound（GPU 瓶頸）**：GPU 使用率過高
- **CPU-bound（CPU 瓶頸）**：CPU 使用率過高
- **Memory-bound（RAM 瓶頸）**：記憶體使用率過高 ⭐
- **IO-bound（I/O 瓶頸）**：儲存或網路 I/O 限制
- **Balanced（系統平衡）**：各組件使用率均衡

### 顯示的 FPS 資料

- **平均 FPS**：整體效能指標
- **1% Low**：最低 1% 的 FPS，反映卡頓情況
- **0.1% Low**：最低 0.1% 的 FPS，反映嚴重卡頓

## 注意事項

⚠️ **開發模式**：目前系統使用模擬資料以便測試。實際部署時應：
1. 實作真實的網路爬蟲邏輯
2. 移除模擬資料生成功能
3. 確保遵守各網站的 robots.txt 與使用條款

## 故障排除

### 後端無法啟動
- 檢查 Python 版本（需要 3.8+）
- 確認所有依賴已安裝：`pip install -r requirements.txt`

### 前端無法啟動
- 檢查 Node.js 版本（需要 16+）
- 確認所有依賴已安裝：`npm install`

### 無法取得資料
- 檢查後端是否正常運行（訪問 http://localhost:8000/health）
- 檢查瀏覽器控制台是否有錯誤
- 確認前端代理設定正確（vite.config.ts）

## API 測試

可以使用以下命令測試 API：

```bash
# 測試健康檢查
curl http://localhost:8000/health

# 取得硬體列表
curl http://localhost:8000/api/hardware?category=gpu

# 搜尋基準資料
curl -X POST http://localhost:8000/api/benchmarks/search \
  -H "Content-Type: application/json" \
  -d '{
    "game": "Cyberpunk 2077",
    "resolution": "1920x1080",
    "hardware": [
      {"category": "gpu", "model": "RTX 4090"},
      {"category": "cpu", "model": "Intel Core i9-13900K"}
    ]
  }'
```

## 下一步

系統已準備就緒，您可以：
1. 開始使用系統測試不同硬體組合
2. 根據實際需求調整爬蟲邏輯
3. 整合真實的資料來源 API
4. 優化瓶頸分析演算法

祝使用愉快！🎮


