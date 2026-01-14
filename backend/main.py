import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()

# 1. 解決 CORS (跨網域)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. API 路由 (必須放在靜態檔案掛載之前) ---

@app.get("/api/hardware")
async def get_hardware(category: Optional[str] = None):
    # 這裡提供預設數據，確保前端能顯示選單
    data = {
        "items": [
            {"category": "cpu", "model": "Intel Core Ultra 9 285K", "brand": "Intel", "selected": False},
            {"category": "cpu", "model": "AMD Ryzen 9 9950X", "brand": "AMD", "selected": False},
            {"category": "gpu", "model": "NVIDIA RTX 4090", "brand": "NVIDIA", "selected": False, "vram_options": [24]},
            {"category": "gpu", "model": "NVIDIA RTX 4080 Super", "brand": "NVIDIA", "selected": False, "vram_options": [16]}
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

# --- 3. 靜態檔案定位與 SPA 處理 ---

# 取得 main.py 的絕對路徑
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 往上跳兩層到根目錄，再進入 frontend/dist
BASE_DIR = os.path.dirname(CURRENT_DIR)
frontend_dist = os.path.join(BASE_DIR, "frontend", "dist")

# 掛載 JS/CSS 資源
assets_path = os.path.join(frontend_dist, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# 全捕捉路由 (確保 /benchmark 重新整理不報錯)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # 排除 API 請求，避免 API 404 卻回傳 HTML
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
        
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {
        "error": "前端編譯檔案 (index.html) 未找到",
        "debug_current_dir": CURRENT_DIR,
        "debug_expected_path": index_path
    }
