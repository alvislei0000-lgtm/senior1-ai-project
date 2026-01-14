@echo off
REM 前端啟動腳本 (Windows)

echo 啟動硬體 FPS 基準分析系統前端...
cd /d "%~dp0"

REM 檢查 node_modules
if not exist "node_modules" (
    echo 安裝依賴...
    call npm install
)

REM 啟動開發伺服器
echo 啟動 Vite 開發伺服器...
call npm run dev

pause


