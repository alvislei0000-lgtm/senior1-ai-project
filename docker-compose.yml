import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 嘗試導入你上傳的模組，如果不存在則提供 fallback
try:
    from google_programmable_search import google_search
except ImportError:
    print("Warning: google_programmable_search.py not found. Search functionality will be disabled.")
    google_search = None

try:
    from add_intel_ultra_cpus import add_intel_ultra_cpus
except ImportError:
    add_intel_ultra_cpus = None

app = FastAPI(title="Senior1 AI Hardware Benchmark API")

# 設定 CORS (允許前端存取)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境建議改為具體的前端網域
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 資料模型 ---

class HardwareItem(BaseModel):
    category: str
    model: str
    brand: str
    release_year: Optional[int] = None
    vram_gb: Optional[int] = 0
    ram_gb: Optional[int] = 0

class BenchmarkRequest(BaseModel):
    game: str
    resolution: str = "1080p"
    settings: str = "High"
    hardware: List[HardwareItem]

# --- 啟動事件 ---

@app.on_event("startup")
async def startup_event():
    """服務啟動時初始化資料"""
    # 確保資料目錄存在
    os.makedirs("data", exist_ok=True)
    
    # 嘗試初始化硬體資料庫
    if add_intel_ultra_cpus:
        try:
            # 這裡簡單呼叫該函式，實際應用可能需要更複雜的檢查避免重複寫入
            # 注意：需確保 add_intel_ultra_cpus 內部邏輯適配這個調用
            print("Initializing hardware database...")
            # add_intel_ultra_cpus() 
        except Exception as e:
            print(f"Error initializing hardware DB: {e}")

# --- API 端點 ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/hardware")
async def get_hardware(category: Optional[str] = None, search: Optional[str] = None):
    """
    取得硬體列表
    這是一個範例實作，實際應讀取 data/hardware_seed.json
    """
    try:
        file_path = "data/hardware_seed.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = data.get("items", [])
        else:
            # Fallback 預設資料
            items = [
                {"category": "cpu", "model": "Intel Core Ultra 9 285K", "brand": "Intel"},
                {"category": "gpu", "model": "NVIDIA RTX 4090", "brand": "NVIDIA"}
            ]
        
        # 過濾邏輯
        if category:
            items = [i for i in items if i.get("category") == category]
        
        if search:
            items = [i for i in items if search.lower() in i.get("model", "").lower()]
            
        return {"items": items}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load hardware data: {str(e)}")

@app.post("/api/benchmarks/search")
async def search_benchmarks(request: BenchmarkRequest):
    """
    搜尋基準測試結果
    """
    if not google_search:
        return {
            "error": "Search module not loaded",
            "results": []
        }

    # 組合搜尋關鍵字
    query_parts = [f"{hw.brand} {hw.model}" for hw in request.hardware]
    query_parts.append(f"{request.game} {request.resolution} benchmark")
    query = " ".join(query_parts)
    
    print(f"Executing search for: {query}")

    try:
        # 呼叫 Google Search (使用環境變數中的 Key)
        # 注意：這裡假設 google_search 函式會自動讀取環境變數
        results = google_search(query, num=5)
        
        # 這裡未來可以加入 LLM 解析邏輯，目前先回傳原始搜尋結果
        return {
            "query": query,
            "results": results,
            "analysis": "LLM 分析模組尚未連接" 
        }
        
    except Exception as e:
        print(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 本地測試用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
