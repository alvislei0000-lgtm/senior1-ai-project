#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索瑞士最近的全國哀悼事件
"""

import requests

def google_search(query, api_key, cx, num=5):
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
        clean_text = ''.join(c for c in text if ord(c) < 128 or ord(c) > 255 or c in '瑞士哀悼國全國人物逝世事件')
        print(clean_text[:max_length])
    except:
        print("[編碼錯誤]")

if __name__ == "__main__":
    # API 認證
    API_KEY = "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
    CX = "034784ab1b1404dc2"

    print("=== 瑞士全國哀悼事件搜索 ===")
    print("=" * 50)

    # 多個查詢來找到相關資訊
    queries = [
        "瑞士 全國哀悼",
        "Switzerland national mourning",
        "瑞士 重要人物逝世 哀悼",
        "瑞士 總統逝世",
        "Switzerland president death"
    ]

    all_results = []

    for query in queries:
        print(f"\n搜索: '{query}'")
        print("-" * 40)

        results = google_search(query, API_KEY, CX, num=3)

        if results:
            print(f"找到 {len(results)} 個結果")
            all_results.extend(results[:2])  # 只保留前2個最相關的

            for idx, result in enumerate(results[:2], start=1):
                print(f"{idx}. ", end="")
                safe_print(result['title'])
                print(f"   來源: {result['link']}")
                print("   摘要: ", end="")
                safe_print(result['snippet'], 120)
                print()
        else:
            print("無相關結果")

    print("=" * 50)
    print("分析總結:")

    if all_results:
        print(f"總共找到 {len(all_results)} 個潛在相關結果")
        print("如果沒有明顯的全國哀悼事件，可能原因:")
        print("1. 瑞士近期沒有重大喪事")
        print("2. 瑞士文化中哀悼形式較為低調")
        print("3. 搜索結果可能不夠具體")
    else:
        print("沒有找到瑞士全國哀悼的相關資訊")
        print("瑞士作為中立和平國家，較少發生導致全國哀悼的重大事件")







