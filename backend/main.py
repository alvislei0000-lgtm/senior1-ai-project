import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

app = FastAPI()

# 1. 允許跨域 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. API 路由 (優先權最高) ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/hardware")
async def get_hardware(category: Optional[str] = None):
    # 這裡回傳模擬資料
    data = {
        "items": [
            {"category": "cpu", "model": "Intel Core Ultra 9 285K", "brand": "Intel", "selected": False},
            {"category": "cpu", "model": "AMD Ryzen 9 9950X", "brand": "AMD", "selected": False},
            {"category": "gpu", "model": "NVIDIA RTX 4090", "brand": "NVIDIA", "selected": False},
            {"category": "gpu", "model": "NVIDIA RTX 4080 Super", "brand": "NVIDIA", "selected": False}
        ]
    }
    if category:
        filtered = [item for item in data["items"] if item["category"] == category]
        return {"items": filtered}
    return data

@app.post("/api/benchmarks/search")
async def search_benchmarks(request: Request):
    params = await request.json()
    return {
        "results": [{
            "game": params.get("game", "未知遊戲"),
            "resolution": params.get("resolution", "1080p"),
            "settings": "Ultra",
            "gpu": "RTX 4090",
            "cpu": "Ultra 9 285K",
            "avg_fps": 120,
            "confidence_score": 0.95,
            "source": "AI 模擬數據",
            "timestamp": "2024-10-25",
            "is_incomplete": False
        }]
    }

# --- 3. 靜態檔案處理 (SPA 關鍵部分) ---

# 定位 frontend/dist 資料夾
# 邏輯：當前 main.py 在 backend/，往上兩層找到根目錄，再進 frontend/dist
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dist = os.path.join(BASE_DIR, "frontend", "dist")
assets_path = os.path.join(frontend_dist, "assets")

print(f"前端路徑檢查: {frontend_dist}") # 這會在日誌中顯示，方便除錯

# 掛載 /assets 路徑 (處理 JS/CSS)
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# [關鍵修正] 明確處理根路徑 "/"，確保首頁能被讀取
@app.get("/")
async def serve_index():
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"error": "index.html not found", "path": index_path})

# [關鍵修正] 處理 React Router 的其他路徑 (例如 /benchmark, /about)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # 排除 API 請求 (避免 API 404 時誤傳回 HTML)
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
        
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return JSONResponse(status_code=404, content={"error": "Frontend not built", "path": index_path})
