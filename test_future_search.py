#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試搜索2026年資訊 - 展示API可以獲取最新公開資訊
"""

import requests
from datetime import datetime

def google_search(query, api_key, cx, num=3):
    """Google Programmable Search Engine 搜索"""
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

def safe_print(text, max_length=80):
    """安全打印，避免編碼問題"""
    try:
        clean_text = ''.join(c for c in text if ord(c) < 128 or ord(c) > 255 or c in '年月日時分秒')
        print(clean_text[:max_length])
    except:
        print("[編碼錯誤]")

if __name__ == "__main__":
    # API 認證
    API_KEY = "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
    CX = "034784ab1b1404dc2"

    print("=== 2026年資訊搜索測試 ===")
    print("當前時間:", datetime.now().strftime('%Y年%m月%d日 %H:%M:%S'))
    print("=" * 50)

    # 測試不同查詢
    queries = [
        "2026 年預測",
        "2026 科技趨勢",
        "2026 重要事件"
    ]

    for query in queries:
        print(f"\n搜索: '{query}'")
        print("-" * 30)

        results = google_search(query, API_KEY, CX, num=3)

        if results:
            print(f"找到 {len(results)} 個公開結果:")
            for idx, result in enumerate(results, start=1):
                print(f"{idx}. ", end="")
                safe_print(result['title'])
                print(f"   來源: {result['link']}")
                print("   摘要: ", end="")
                safe_print(result['snippet'], 120)
                print()
        else:
            print("此查詢無公開結果")

    print("=" * 50)
    print("結論: API 可以搜索網路上公開的資訊")
    print("但無法預測或知道尚未發生的未來事件")







