@echo off
REM 後端啟動腳本 (Windows)

echo 啟動硬體 FPS 基準分析系統後端...
cd /d "%~dp0"

REM 檢查虛擬環境
if not exist "venv" (
    echo 建立虛擬環境...
    python -m venv venv
)

REM 啟動虛擬環境
call venv\Scripts\activate.bat

REM 安裝依賴
echo 安裝依賴...
pip install -r requirements.txt

REM 啟動服務
echo 啟動 FastAPI 服務...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause


