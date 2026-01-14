import os
import requests
from typing import List, Dict, Optional


def google_search(query: str, api_key: Optional[str] = None, cx: Optional[str] = None, num: int = 5) -> List[Dict[str, str]]:
    """
    使用 Google Programmable Search Engine API 進行網頁搜索
    
    :param query: 搜索關鍵字
    :param api_key: Google API 金鑰 (可從環境變數 GOOGLE_API_KEY 取得)
    :param cx: Programmable Search Engine ID (可從環境變數 GOOGLE_CX 取得)
    :param num: 返回結果數量 (1-10，預設為 5)
    :return: 搜索結果列表，每個結果包含 title, link, snippet
    """
    # 從環境變數取得 API 資訊，如果沒有提供參數的話
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    cx = cx or os.getenv('GOOGLE_CX')
    
    if not api_key or not cx:
        raise ValueError("需要提供 API_KEY 和 CX，或者設定環境變數 GOOGLE_API_KEY 和 GOOGLE_CX")
    
    if not query or not query.strip():
        raise ValueError("查詢關鍵字不能為空")
    
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
        
        # 檢查 API 錯誤
        if "error" in results:
            error_info = results["error"]
            error_msg = error_info.get("message", "未知錯誤")
            raise Exception(f"Google API 錯誤: {error_msg}")
        
        search_items = []
        if "items" in results:
            for item in results["items"]:
                search_items.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
        
        return search_items
    
    except requests.exceptions.Timeout:
        raise Exception("搜索請求超時，請稍後再試")
    except requests.exceptions.RequestException as e:
        raise Exception(f"搜索請求失敗: {str(e)}")
    except ValueError as e:
        raise Exception(f"JSON 解析失敗: {str(e)}")


# 在 Cursor 裡測試
if __name__ == "__main__":
    # 預設 API 金鑰和 Search Engine ID（可在環境變數中設定）
    API_KEY = os.getenv('GOOGLE_API_KEY') or "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
    CX = os.getenv('GOOGLE_CX') or "034784ab1b1404dc2"
    
    query = "Python 教學"
    
    try:
        # 設定輸出編碼為 UTF-8（Windows 環境）
        import sys
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
        results = google_search(query, API_KEY, CX, num=5)
        
        if results:
            print(f"搜索成功！找到 {len(results)} 個結果：\n")
            for idx, result in enumerate(results, start=1):
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                link = result.get('link', '')
                
                print(f"{idx}. {title}")
                print(f"   連結: {link}")
                print(f"   摘要: {snippet}\n")
        else:
            print("沒有找到搜索結果")
    
    except Exception as e:
        print(f"搜索失敗: {e}")
        print("\n提示：")
        print("1. 確認 API_KEY 和 CX 是否正確")
        print("2. 確認 Google Cloud Console 中已啟用 Custom Search API")
        print("3. 確認 API 配額是否足夠")
