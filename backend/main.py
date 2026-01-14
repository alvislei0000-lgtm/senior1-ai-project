from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse # 必須確保有這行
import os

app = FastAPI()

# --- 這裡放你原本的 API 路由 (例如 @app.get("/api/hardware")) ---
@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# --- 以下是關鍵的路由處理邏輯 ---

# 取得前端 dist 目錄的絕對路徑
frontend_dist = os.path.join(os.getcwd(), "frontend/dist")

# 1. 先掛載靜態資源 (JS, CSS, 圖片)，這些檔案通常在 assets 資料夾內
if os.path.exists(os.path.join(frontend_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

# 2. 核心：捕捉所有「非 API」的路徑，並統一回傳 index.html
# 這能解決重新整理 /benchmark 時出現 404 的問題
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # 如果路徑是 api 開頭但上面沒定義到，才給 404
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API 路由不存在")
    
    # 其他所有路徑 (如 /benchmark) 通通回傳 index.html
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"error": "找不到前端編譯檔案 index.html，請檢查 Render 建置流程"}
