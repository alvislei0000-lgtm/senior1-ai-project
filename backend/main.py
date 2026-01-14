import os
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()

# 允許跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 定義 API 路由 (必須放在靜態檔案掛載之前) ---

@app.get("/api/hardware")
async def get_hardware(
    category: Optional[str] = None,
    search: Optional[str] = None
):
    # 這裡模擬你 add_intel_ultra_cpus.py 裡的數據結構
    hardware_data = {
        "items": [
            {"category": "cpu", "model": "Intel Core Ultra 9 285K", "brand": "Intel", "release_year": 2024},
            {"category": "cpu", "model": "Intel Core Ultra 7 265K", "brand": "Intel", "release_year": 2024},
            {"category": "gpu", "model": "NVIDIA RTX 4090", "brand": "NVIDIA", "vram_gb": 24},
            {"category": "gpu", "model": "NVIDIA RTX 4080 Super", "brand": "NVIDIA", "vram_gb": 16}
        ]
    }
    
    # 簡單的過濾邏輯
    results = hardware_data["items"]
    if category:
        results = [item for item in results if item["category"] == category]
    if search:
        results = [item for item in results if search.lower() in item["model"].lower()]
        
    return {"items": results}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# --- 2. 處理靜態檔案與 SPA 路由 (保持在最後) ---

frontend_dist = os.path.join(os.getcwd(), "frontend/dist")

# 掛載 assets
assets_path = os.path.join(frontend_dist, "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# 捕捉所有路由導向 index.html
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # 如果是找 API 但沒定義，給 404 JSON
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
        
    # 其他通通給 index.html
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend dist not found. Did you run npm run build?"}
