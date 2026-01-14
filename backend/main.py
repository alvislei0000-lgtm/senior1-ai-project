from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# 關鍵修復：導入 StaticFiles 以支援前端檔案託管 [cite: 5]
from fastapi.staticfiles import StaticFiles 
import os
from typing import List, Dict

app = FastAPI()

# 允許跨域請求 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康檢查接口
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 硬體與基準測試 API (此處應包含你 Cursor 中的 API 路由邏輯)
@app.get("/api/hardware")
async def get_hardware(category: str = None):
    # 這裡請貼入你原本 Cursor 中獲取硬體列表的邏輯
    return {"items": []}

# 關鍵設定：將前端編譯後的靜態檔案掛載到根路徑 [cite: 5, 9]
# 確保 Render 構建後 frontend/dist 目錄存在
frontend_path = os.path.join(os.getcwd(), "frontend/dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
else:
    print(f"警告: 找不到前端目錄 {frontend_path}，請確認 npm run build 已執行")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

# backend/main.py

# ... 其他代碼 ...

# 修改掛載邏輯，增加判斷
frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    print(f"警告：找不到靜態資料夾 {frontend_dist}，請確認前端已編譯。")
    @app.get("/")
    async def fallback():
        return {"message": "前端尚未編譯，請檢查 Render 建置流程。"}
