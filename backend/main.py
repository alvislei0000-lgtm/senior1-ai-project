import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()

# 1. 徹底開放 CORS (解決跨網域問題)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. API 路由 (必須放在 StaticFiles 之前) ---

@app.get("/api/hardware")
async def get_hardware(category: Optional[str] = None):
    data = {
        "items": [
            {"category": "cpu", "model": "Intel Core Ultra 9 285K", "brand": "Intel"},
            {"category": "cpu", "model": "AMD Ryzen 9 9950X", "brand": "AMD"},
            {"category": "gpu", "model": "NVIDIA RTX 4090", "brand": "NVIDIA", "vram_options": [24]},
            {"category": "gpu", "model": "NVIDIA RTX 4080 Super", "brand": "NVIDIA", "vram_options": [16]}
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
            "source": "AI 預測數據",
            "timestamp": "2024-10-25",
            "is_incomplete": False
        }]
    }

# --- 3. 靜態檔案與路徑定位 ---

# 自動獲取 frontend/dist 的絕對路徑
# __file__ 是 backend/main.py，dirname 兩次回到根目錄
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dist = os.path.join(BASE_DIR, "frontend", "dist")

# 掛載 assets (js/css)
assets_path = os.path.join(frontend_dist, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# 全捕捉路由：處理前端所有頁面 (如 /benchmark)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API Not Found")
    
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"error": "前端編譯檔案 (dist/index.html) 不存在", "debug_path": index_path}
