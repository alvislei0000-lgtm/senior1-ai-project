#!/bin/bash
# 後端啟動腳本

echo "啟動硬體 FPS 基準分析系統後端..."
cd "$(dirname "$0")"

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "建立虛擬環境..."
    python -m venv venv
fi

# 啟動虛擬環境
source venv/bin/activate 2>/dev/null || . venv/bin/activate

# 安裝依賴
echo "安裝依賴..."
pip install -r requirements.txt

# 啟動服務
echo "啟動 FastAPI 服務..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


