from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from app.api import hardware, benchmarks
from app.cache.global_cache import cache_manager

# 確保不論從哪個工作目錄啟動，都能讀到 backend/.env
_BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_DOTENV_PATH = os.path.join(_BACKEND_DIR, ".env")
load_dotenv(dotenv_path=_DOTENV_PATH, override=True)

app = FastAPI(
    title="硬體 FPS 基準分析系統",
    description="即時從網路抓取硬體效能基準資料並進行瓶頸分析",
    version="1.0.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化"""
    await cache_manager.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時清理"""
    await cache_manager.close()

# 註冊路由
app.include_router(hardware.router, prefix="/api", tags=["硬體"])
app.include_router(benchmarks.router, prefix="/api", tags=["基準測試"])

@app.get("/")
async def root():
    return {
        "message": "硬體 FPS 基準分析系統 API",
        "version": "1.0.0",
        "note": "所有資料均即時從網路抓取，不使用內建靜態資料"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "內部伺服器錯誤",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )


