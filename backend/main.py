import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 關鍵：新增前端需要的搜尋 API ---
@app.post("/api/benchmarks/search")
async def search_benchmarks(data: Request):
    # 接收前端傳來的搜尋參數
    params = await data.json()
    print(f"收到搜尋請求: {params}")
    
    # 這裡目前回傳模擬數據，確保前端不報錯
    # 之後你可以把 Google Search 邏輯接在這裡
    return {
        "results": [
            {
                "game": params.get("game", "未知遊戲"),
                "resolution": params.get("resolution", "1080p"),
                "settings": "Ultra",
                "gpu": "RTX 4090",
                "cpu": "Ultra 9 285K",
                "avg_fps": 144,
                "confidence_score": 0.95,
                "source": "AI 模擬數據",
                "timestamp": "2024-10-24",
                "is_incomplete": False
            }
        ]
    }

# 舊有的硬體清單 API (供 HardwareSelector 使用)
@app.get("/api/hardware")
async def get_hardware():
    return {"items": []}

# --- 靜態檔案掛載 ---
frontend_dist = os.path.join(os.getcwd(), "frontend/dist")

if os.path.exists(os.path.join(frontend_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API Not Found")
    
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found"}
