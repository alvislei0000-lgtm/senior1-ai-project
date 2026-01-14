#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的 Google Programmable Search API key
"""

import requests
import json
import os

def test_google_api():
    """測試 Google Custom Search API"""

    api_key = os.getenv('GOOGLE_API_KEY') or 'AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU'

    print(f'測試 API Key: {api_key[:15]}...')
    print('=' * 50)

    # 測試 1: 沒有 cx 的請求
    print('測試 1: 沒有 Search Engine ID 的請求')
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': 'coffee',
        'key': api_key,
        'num': 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f'HTTP 狀態碼: {response.status_code}')

        if response.status_code == 400:
            try:
                error_data = response.json()
                print('錯誤訊息:')
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print('原始回應:', response.text[:300])
        elif response.status_code == 200:
            print('✅ API Key 有效！')
            data = response.json()
            print(f'找到 {len(data.get("items", []))} 個結果')
        else:
            print(f'意外狀態碼: {response.status_code}')
            print('回應:', response.text[:200])

    except Exception as e:
        print(f'請求失敗: {e}')

    print()
    print('=' * 50)

    # 測試 2: 檢查 API key 格式
    print('測試 2: API Key 格式檢查')
    if api_key.startswith('AIzaSy'):
        print('PASS: API Key 格式正確 (Google API Key)')
    else:
        print('FAIL: API Key 格式不對')

    print(f'API Key 長度: {len(api_key)} 個字符')
    print(f'預期長度: Google API Keys 通常是 39 個字符')

    # 測試 3: 檢查 API 是否已啟用
    print()
    print('測試 3: 疑難排解建議')
    print('- 確認 Google Cloud Console 中已啟用 Custom Search API')
    print('- 檢查 API key 是否有使用配額')
    print('- 確認 API key 沒有被停用')
    print('- 檢查是否有正確的 Search Engine ID (cx)')

if __name__ == '__main__':
    test_google_api()
