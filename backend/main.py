import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse # 這是關鍵：用來回傳 HTML 檔案

app = FastAPI()

# 1. 你的 API 路由 (範例)
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# 2. 處理靜態資源 (JS/CSS)
frontend_dist = os.path.join(os.getcwd(), "frontend/dist")
if os.path.exists(os.path.join(frontend_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

# 3. 核心：捕捉所有前端路由路徑 (例如 /benchmark)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # 如果路徑不是以 api 開頭，通通丟回 index.html
    if not full_path.startswith("api/"):
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    
    # 如果是 API 卻沒定義，才給 404
    raise HTTPException(status_code=404, detail="Not Found")
