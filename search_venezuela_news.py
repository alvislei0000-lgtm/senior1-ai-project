#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜尋委內瑞拉最近的新聞
"""
import os
import sys
from google_programmable_search import google_search

# 設定輸出編碼為 UTF-8（Windows 環境）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# API 設定
API_KEY = os.getenv('GOOGLE_API_KEY') or "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
CX = os.getenv('GOOGLE_CX') or "034784ab1b1404dc2"

def search_venezuela_news():
    """搜尋委內瑞拉最近的新聞"""
    queries = [
        "委內瑞拉 最新新聞 2024",
        "Venezuela news 2024",
        "委內瑞拉 最近發生",
    ]
    
    all_results = []
    
    for query in queries:
        try:
            print(f"\n正在搜尋: {query}...")
            results = google_search(query, API_KEY, CX, num=10)
            
            if results:
                print(f"找到 {len(results)} 個結果\n")
                for idx, result in enumerate(results, start=1):
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    link = result.get('link', '')
                    
                    # 避免重複結果
                    if link not in [r.get('link', '') for r in all_results]:
                        all_results.append(result)
                        print(f"{len(all_results)}. {title}")
                        print(f"   連結: {link}")
                        print(f"   摘要: {snippet}\n")
                        print("-" * 80)
            
        except Exception as e:
            print(f"搜尋失敗: {e}\n")
            continue
    
    return all_results

if __name__ == "__main__":
    print("=" * 80)
    print("搜尋委內瑞拉最近的新聞")
    print("=" * 80)
    
    results = search_venezuela_news()
    
    if results:
        print(f"\n總共找到 {len(results)} 個相關結果")
    else:
        print("\n沒有找到相關結果")
