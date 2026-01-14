#!/usr/bin/env python3
"""
調試RAM懲罰的具體計算
"""
import httpx
import json

def debug_ram_penalty():
    """詳細檢查RAM懲罰的應用"""

    print("=== RAM懲罰調試 ===")

    # Cities: Skylines 需要16GB RAM
    test_cases = [
        {"gb": 8, "expected_penalty": "20-30%懲罰"},
        {"gb": 12, "expected_penalty": "5-15%懲罰"},
        {"gb": 16, "expected_penalty": "無懲罰"},
        {"gb": 32, "expected_penalty": "輕微提升"},
    ]

    for test_case in test_cases:
        payload = {
            "game": "Cities: Skylines",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
                {"category": "ram", "model": "DDR4 RAM", "ram_gb": test_case["gb"], "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16.0},
                {"category": "storage", "model": "NVMe SSD", "storage_type": "NVMe SSD"}
            ]
        }

        try:
            resp = httpx.post("http://127.0.0.1:8000/api/benchmarks/search", json=payload, timeout=30.0)

            if resp.status_code == 200:
                data = resp.json()
                if 'results' in data and data['results']:
                    result = data['results'][0]
                    fps = result.get('avg_fps', 'N/A')
                    ram_usage = result.get('memory_usage', 'N/A')

                    print(f"{test_case['gb']}GB RAM ({test_case['expected_penalty']}):")
                    print(f"  FPS: {fps}")
                    print(f"  RAM使用率: {ram_usage}%")
                    print()
                else:
                    print(f"{test_case['gb']}GB: 無結果")
            else:
                print(f"{test_case['gb']}GB: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{test_case['gb']}GB: 錯誤 - {e}")

def test_extreme_ram_cases():
    """測試極端RAM情況"""

    print("=== 極端RAM測試 (Fortnite - 需要8GB) ===")

    test_cases = [
        {"gb": 4, "desc": "4GB (極端不足)"},
        {"gb": 8, "desc": "8GB (足夠)"},
        {"gb": 16, "desc": "16GB (充裕)"},
    ]

    for test_case in test_cases:
        payload = {
            "game": "Fortnite",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
                {"category": "ram", "model": "DDR4 RAM", "ram_gb": test_case["gb"], "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16.0},
                {"category": "storage", "model": "NVMe SSD", "storage_type": "NVMe SSD"}
            ]
        }

        try:
            resp = httpx.post("http://127.0.0.1:8000/api/benchmarks/search", json=payload, timeout=30.0)

            if resp.status_code == 200:
                data = resp.json()
                if 'results' in data and data['results']:
                    result = data['results'][0]
                    fps = result.get('avg_fps', 'N/A')
                    ram_usage = result.get('memory_usage', 'N/A')

                    print(f"{test_case['desc']}: FPS={fps}, RAM使用率={ram_usage}%")
                else:
                    print(f"{test_case['desc']}: 無結果")
            else:
                print(f"{test_case['desc']}: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{test_case['desc']}: 錯誤 - {e}")

if __name__ == "__main__":
    debug_ram_penalty()
    test_extreme_ram_cases()