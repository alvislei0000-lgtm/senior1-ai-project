from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# --- 就是下面這一行，一定要加上去 ---
from fastapi.staticfiles import StaticFiles 
import os

app = FastAPI()

# 允許跨域 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... 你的其他 API 路由 (例如 @app.get("/benchmark")) ...

# --- 結尾部分也要確保路徑正確 ---
# 這行代碼告訴 FastAPI 去哪裡找前端編譯好的網頁
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")