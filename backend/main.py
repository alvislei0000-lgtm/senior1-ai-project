import os
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()

# 1. 徹底解決 CORS 問題
# 允許所有來源 (*)，這樣不論前端網址多一個 '1' 還是少一個 '1' 都能通
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. API 路由定義 (必須放在靜態檔案掛載之前) ---

# 硬體選擇器需要的 API
@app.get("/api/hardware")
async def get_hardware(category: Optional[str] = None):
    # 這是基礎種子資料，確保前端 HardwareSelector 不會空空如也
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

# 核心搜尋 API：處理前端 BenchmarkSystem 的 handleSearch 請求
@app.post("/api/benchmarks/search")
async def search_benchmarks(request: Request):
    try:
        params = await request.json()
        print(f"收到搜尋參數: {params}")
        
        # 這裡回傳模擬結果，確保前端能接收到 JSON 並渲染圖表
        return {
            "results": [
                {
                    "game": params.get("game", "未知遊戲"),
                    "resolution": params.get("resolution", "1080p"),
                    "settings": "Ultra",
                    "gpu": "RTX 4090",
                    "cpu": "Ultra 9 285K",
                    "avg_fps": 120,
                    "confidence_score": 0.9,
                    "source": "系統預測數據",
                    "timestamp": "2024-10-24",
                    "is_incomplete": False
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失敗: {str(e)}")

# --- 3. 靜態檔案與 SPA 路由處理 ---

frontend_dist = os.path.join(os.getcwd(), "frontend/dist")

# 掛載 Vite 編譯後的 assets (js, css)
assets_path = os.path.join(frontend_dist, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# 全捕捉路由：處理前端路由 (如 /benchmark) 並回傳 index.html
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # 如果路徑是 api 開頭但沒被上面的路由捕捉，給 404 JSON
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
        
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"error": "index.html not found", "path": index_path}
