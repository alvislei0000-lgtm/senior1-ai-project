#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Search API 測試腳本
演示如何安全地使用 Google Custom Search API
"""

import os
from google_search import google_search

def test_google_search():
    """測試 Google 搜索功能"""

    # 範例：設定環境變數 (在實際使用時設定真實的 API 資訊)
    # os.environ['GOOGLE_API_KEY'] = '你的真實API金鑰'
    # os.environ['GOOGLE_CX'] = '你的真實Search Engine ID'

    # 測試參數驗證
    print("=== 測試參數驗證 ===")

    # 測試無 API 資訊的情況
    try:
        results = google_search("Python")
        print("FAIL: 應該拋出 ValueError")
    except ValueError as e:
        print(f"PASS: 正確捕獲錯誤: {e}")

    # 測試 num 參數驗證
    try:
        # 先設定假的環境變數來測試
        os.environ['GOOGLE_API_KEY'] = 'fake_key'
        os.environ['GOOGLE_CX'] = 'fake_cx'
        results = google_search("Python", num=15)  # num > 10
        print("FAIL: 應該拋出 ValueError")
    except ValueError as e:
        print(f"PASS: 正確捕獲錯誤: {e}")

    # 測試正常調用 (會因為假的 API 資訊而失敗，但會測試錯誤處理)
    print("\n=== 測試 API 調用 (使用假的 API 資訊) ===")
    try:
        results = google_search("Python 教學", num=3)
        print(f"搜索完成，返回 {len(results)} 個結果")
        if results:
            for idx, result in enumerate(results, start=1):
                print(f"{idx}. {result['title']}")
        else:
            print("沒有找到結果 (可能是因為 API 錯誤)")
    except Exception as e:
        print(f"API 調用失敗: {e}")

    # 清理環境變數
    if 'GOOGLE_API_KEY' in os.environ:
        del os.environ['GOOGLE_API_KEY']
    if 'GOOGLE_CX' in os.environ:
        del os.environ['GOOGLE_CX']

def show_usage_example():
    """顯示使用範例"""
    print("\n=== 使用說明 ===")
    print("""
# 1. 設定環境變數 (推薦方式):
export GOOGLE_API_KEY="你的API金鑰"
export GOOGLE_CX="你的Search Engine ID"

# 2. 或者在程式碼中直接傳入:
results = google_search("Python 教學", api_key="你的金鑰", cx="你的ID")

# 3. 使用範例:
from google_search import google_search

results = google_search("人工智能", num=5)
for result in results:
    print(f"標題: {result['title']}")
    print(f"連結: {result['link']}")
    print(f"摘要: {result['snippet']}")
    print("---")
""")

if __name__ == "__main__":
    test_google_search()
    show_usage_example()
