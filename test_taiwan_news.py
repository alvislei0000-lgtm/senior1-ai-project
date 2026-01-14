#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試台灣最近大事搜索
"""

import requests
import os

def google_search(query, api_key=None, cx=None, num=5):
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    cx = cx or os.getenv('GOOGLE_CX')

    if not api_key or not cx:
        print(f'缺少認證資訊 - API_KEY: {bool(api_key)}, CX: {bool(cx)}')
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cx,
        "num": num
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        results = response.json()

        search_items = []
        if "items" in results:
            for item in results["items"]:
                search_items.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })

        return search_items

    except requests.exceptions.RequestException as e:
        print(f"搜索請求失敗: {e}")
        return []
    except ValueError as e:
        print(f"JSON 解析失敗: {e}")
        return []

if __name__ == "__main__":
    print("正在搜索台灣最近導致全國哀悼的大事...")

    # 搜索關鍵字
    query = "台灣 李登輝 逝世 全國哀悼 2025"

    results = google_search(query, num=5)

    if results:
        print(f"\n找到 {len(results)} 個搜索結果：\n")

        for idx, result in enumerate(results, start=1):
            print(f"{idx}. {result['title']}")
            print(f"   連結: {result['link']}")
            print(f"   摘要: {result['snippet'][:200]}...")
            print("-" * 50)
    else:
        print("搜索無結果，可能是 API 設定問題")







