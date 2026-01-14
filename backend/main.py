import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 允許跨域 (開發時很有用)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API 區域：所有的後端數據接口都要放在這裡
@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Backend is running"}

# 2. 靜態資源區域：處理編譯後的 JS/CSS
frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
assets_path = os.path.join(frontend_dist, "assets")

if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# 3. SPA 路由區域：這是一個「全捕捉」邏輯
@app.get("/{rest_of_path:path}")
async def react_app(rest_of_path: str):
    # 如果請求的是 api，但上面沒定義，直接給 404，不要給 index.html
    if rest_of_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API not found")

    # 否則，檢查 index.html 是否存在並回傳
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    
    # 如果連 index.html 都沒有，這代表前端沒編譯成功
    return {
        "error": "Frontend build not found",
        "hint": "Check if 'npm run build' was executed in Render's Build Command"
    }
