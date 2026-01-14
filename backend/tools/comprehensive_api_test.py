#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import httpx
from typing import List, Dict

def test_scenario(name: str, payload: Dict) -> bool:
    print(f"\n=== 測試: {name} ===")
    try:
        resp = httpx.post("http://127.0.0.1:8000/api/benchmarks/search",
                         json=payload, timeout=30.0)
        print(f"狀態: {resp.status_code}")

        if resp.status_code != 200:
            print(f"錯誤: {resp.text}")
            return False

        data = resp.json()
        if 'results' not in data or not data['results']:
            print("錯誤: 沒有結果")
            return False

        result = data['results'][0]
        print(f"遊戲: {result.get('game')}")
        print(f"解析度: {result.get('resolution')}")
        print(f"設定: {result.get('settings')}")
        print(f"GPU: {result.get('gpu')}")
        print(f"CPU: {result.get('cpu')}")
        print(f"平均 FPS: {result.get('avg_fps', 'N/A')}")
        print(f"來源: {result.get('source', 'N/A')}")
        print(f"信心分數: {result.get('confidence_score', 'N/A')}")

        # 檢查關鍵欄位是否存在
        required_fields = ['avg_fps', 'p1_low', 'p0_1_low', 'source', 'bottleneck_analysis']
        missing_fields = [f for f in required_fields if f not in result]
        if missing_fields:
            print(f"警告: 缺少欄位: {missing_fields}")

        # 檢查瓶頸分析
        if 'bottleneck_analysis' in result:
            bottleneck = result['bottleneck_analysis']
            print(f"瓶頸類型: {bottleneck.get('bottleneck_type', 'N/A')}")
            print(f"瓶頸信心: {bottleneck.get('confidence', 'N/A')}")

        # 檢查 VRAM
        if 'vram_required_gb' in result:
            print(f"VRAM 需求: {result.get('vram_required_gb')}GB")
            print(f"VRAM 選擇: {result.get('vram_selected_gb')}GB")
            print(f"VRAM 足夠: {result.get('vram_is_enough', 'N/A')}")

        return True

    except Exception as e:
        print(f"請求錯誤: {e}")
        return False

def main():
    test_cases = [
        {
            "name": "高階遊戲 - RTX 4090 + i9-13900K",
            "payload": {
                "game": "Cyberpunk 2077",
                "resolution": "3840x2160",
                "settings": "Ultra",
                "hardware": [
                    {"category": "gpu", "model": "RTX 4090", "selected_vram_gb": 24},
                    {"category": "cpu", "model": "Intel Core i9-13900K"},
                ],
            }
        },
        {
            "name": "中階遊戲 - RTX 3070 + Ryzen 5 5600X",
            "payload": {
                "game": "Forza Horizon 5",
                "resolution": "2560x1440",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                    {"category": "cpu", "model": "AMD Ryzen 5 5600X"},
                ],
            }
        },
        {
            "name": "Minecraft - 低階硬件",
            "payload": {
                "game": "Minecraft",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "GTX 1650", "selected_vram_gb": 4},
                    {"category": "cpu", "model": "Intel Core i5-10400F"},
                ],
            }
        },
        {
            "name": "Apex Legends - eSports 設定",
            "payload": {
                "game": "Apex Legends",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                    {"category": "cpu", "model": "AMD Ryzen 5 3600"},
                ],
            }
        },
        {
            "name": "Counter-Strike 2 - 競技設定",
            "payload": {
                "game": "Counter-Strike 2",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 2060", "selected_vram_gb": 6},
                    {"category": "cpu", "model": "Intel Core i3-12100F"},
                ],
            }
        }
    ]

    success_count = 0
    total_count = len(test_cases)

    for test_case in test_cases:
        if test_scenario(test_case["name"], test_case["payload"]):
            success_count += 1

    print("\n=== 測試總結 ===")
    print(f"成功: {success_count}/{total_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")

    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    raise SystemExit(main())