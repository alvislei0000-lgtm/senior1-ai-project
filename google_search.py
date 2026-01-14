import requests
import os
from typing import List, Dict, Optional

def google_search(query: str, api_key: Optional[str] = None, cx: Optional[str] = None, num: int = 5) -> List[Dict[str, str]]:
    """
    使用 Google Custom Search API 進行網頁搜索

    :param query: 搜索關鍵字
    :param api_key: Google API 金鑰 (可從環境變數 GOOGLE_API_KEY 取得)
    :param cx: Custom Search Engine ID (可從環境變數 GOOGLE_CX 取得)
    :param num: 返回結果數量 (最多10)
    :return: 搜索結果列表
    """
    # 從環境變數取得 API 資訊，如果沒有提供參數的話
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    cx = cx or os.getenv('GOOGLE_CX')

    if not api_key or not cx:
        raise ValueError("需要提供 API_KEY 和 CX，或者設定環境變數 GOOGLE_API_KEY 和 GOOGLE_CX")

    if num < 1 or num > 10:
        raise ValueError("num 參數必須在 1-10 之間")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cx,
        "num": num
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # 檢查 HTTP 錯誤

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


# 在 Cursor 裡測試
if __name__ == "__main__":
    # 建議使用環境變數設定 API 資訊
    API_KEY = os.getenv('GOOGLE_API_KEY') or "你的API金鑰"  # 從環境變數或手動設定
    CX = os.getenv('GOOGLE_CX') or "你的Search Engine ID"    # 從環境變數或手動設定

    query = "Python 教學"

    results = google_search(query, API_KEY, CX)
    if results:
        for idx, result in enumerate(results, start=1):
            print(f"{idx}. {result['title']}")
            print(f"   {result['link']}")
            print(f"   {result['snippet']}\n")
    else:
        print("沒有找到搜索結果")







