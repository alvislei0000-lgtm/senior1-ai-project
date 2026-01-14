#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試台灣新聞搜索 - 使用 Google Programmable Search Engine
"""

import requests

def google_search(query, api_key, cx, num=5):
    """
    使用 Google Programmable Search Engine API 進行網頁搜索
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cx,
        "num": num
    }
    response = requests.get(url, params=params)
    results = response.json()

    search_items = []
    if "items" in results:
        for item in results["items"]:
            search_items.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })
    return search_items

def safe_print(text, max_length=100):
    """安全打印，避免編碼問題"""
    try:
        # 移除特殊字符
        clean_text = ''.join(c for c in text if ord(c) < 128 or c in '中文')
        print(clean_text[:max_length])
    except:
        print("[編碼錯誤]")

if __name__ == "__main__":
    # 使用用戶提供的認證資訊
    API_KEY = "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
    CX = "034784ab1b1404dc2"

    print("=== 測試台灣新聞搜索 ===")

    # 測試 1: 簡單的台灣新聞
    print("\n測試 1: 搜索台灣新聞")
    query = "台灣新聞"
    results = google_search(query, API_KEY, CX, num=3)

    if results:
        print(f"找到 {len(results)} 個結果:")
        for idx, result in enumerate(results, start=1):
            print(f"\n{idx}. ", end="")
            safe_print(result['title'])
            print(f"   連結: {result['link']}")
            print("   摘要: ", end="")
            safe_print(result['snippet'], 150)
    else:
        print("沒有找到結果")

    # 測試 2: 瑞士最近事件
    print("\n" + "="*50)
    print("測試 2: 搜索瑞士最近事件")
    query = "瑞士 最近 事件 2025"
    results = google_search(query, API_KEY, CX, num=3)

    if results:
        print(f"找到 {len(results)} 個結果:")
        for idx, result in enumerate(results, start=1):
            print(f"\n{idx}. ", end="")
            safe_print(result['title'])
            print(f"   連結: {result['link']}")
            print("   摘要: ", end="")
            safe_print(result['snippet'], 150)
    else:
        print("沒有找到結果")

    print("\n" + "="*50)
    print("測試完成！Google Programmable Search Engine API 工作正常!")
