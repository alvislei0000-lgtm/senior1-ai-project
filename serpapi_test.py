#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SerpApi Python 測試程式
對應於 Ruby 程式碼：
require "serpapi"

client = SerpApi::Client.new(
  engine: "google",
  q: "Coffee",
  api_key: "50ea289dd22e73b350b964c4ee33cf68b4b0529a2d68d48c8057fa96ac8903cf"
)

results = client.search
organic_results = results[:organic_results]
"""

import serpapi

def test_serpapi():
    """測試 SerpApi 搜索功能"""

    # 建立 SerpApi 客戶端 (使用原來的 API key，因為新的似乎是 Google API key)
    client = serpapi.Client(api_key="50ea289dd22e73b350b964c4ee33cf68b4b0529a2d68d48c8057fa96ac8903cf")

    print("正在搜索 'Coffee'...")

    try:
        # 執行搜索
        results = client.search({
            "engine": "google",
            "q": "Coffee",
            "num": 5
        })

        # 獲取有機搜索結果
        organic_results = results.get("organic_results", [])

        print(f"\n找到 {len(organic_results)} 個有機搜索結果：\n")

        for idx, result in enumerate(organic_results, start=1):
            print(f"{idx}. {result.get('title', '無標題')}")
            print(f"   連結: {result.get('link', '無連結')}")
            print(f"   摘要: {result.get('snippet', '無摘要')[:150]}...")
            print("-" * 50)

        # 顯示完整結果結構（用於調試）
        print("\n完整結果鍵值：")
        for key in results.keys():
            print(f"  - {key}")

    except Exception as e:
        print(f"搜索失敗: {e}")
        print("可能的錯誤原因：")
        print("1. API 金鑰無效")
        print("2. 超出 API 配額")
        print("3. 網路連線問題")

def test_taiwan_news():
    """測試台灣新聞搜索"""

    client = serpapi.Client(api_key="AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU")

    print("\n正在搜索台灣最近大事...")

    try:
        results = client.search({
            "engine": "google",
            "q": "台灣 李登輝 逝世 全國哀悼 2025",
            "num": 5
        })

        organic_results = results.get("organic_results", [])

        print(f"\n找到 {len(organic_results)} 個相關結果：\n")

        for idx, result in enumerate(organic_results, start=1):
            print(f"{idx}. {result.get('title', '無標題')}")
            print(f"   連結: {result.get('link', '無連結')}")
            print(f"   摘要: {result.get('snippet', '無摘要')[:200]}...")
            print("-" * 50)

    except Exception as e:
        print(f"搜索失敗: {e}")

if __name__ == "__main__":
    test_serpapi()
    test_taiwan_news()
