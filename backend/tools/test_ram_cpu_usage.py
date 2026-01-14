#!/usr/bin/env python3
"""
測試 RAM 和 CPU 使用率的影響
檢查不同硬件配置下使用率變化及 FPS 影響
"""
import json
import sys
from pathlib import Path
import httpx

def test_ram_cpu_usage():
    """測試 RAM 和 CPU 使用率對 FPS 的影響"""

    print("=== 測試 RAM 和 CPU 使用率影響 ===")
    print("=" * 50)

    test_cases = [
        {
            "name": "基準配置 - RTX 3070 + i7-13700K",
            "payload": {
                "game": "Cyberpunk 2077",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                    {"category": "cpu", "model": "Intel Core i7-13700K"},
                ],
            }
        },
        {
            "name": "相同硬件 - 測試一致性",
            "payload": {
                "game": "Cyberpunk 2077",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                    {"category": "cpu", "model": "Intel Core i7-13700K"},
                ],
            }
        },
        {
            "name": "Minecraft - 弱 CPU (i3-12100F)",
            "payload": {
                "game": "Minecraft",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                    {"category": "cpu", "model": "Intel Core i3-12100F"},
                ],
            }
        },
        {
            "name": "Minecraft - 強 CPU (Ryzen 9 7950X)",
            "payload": {
                "game": "Minecraft",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                    {"category": "cpu", "model": "AMD Ryzen 9 7950X"},
                ],
            }
        },
        {
            "name": "CS2 - 弱 CPU (i3-12100F)",
            "payload": {
                "game": "Counter-Strike 2",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 2060", "selected_vram_gb": 6},
                    {"category": "cpu", "model": "Intel Core i3-12100F"},
                ],
            }
        },
        {
            "name": "CS2 - 強 CPU (Ryzen 9 7950X)",
            "payload": {
                "game": "Counter-Strike 2",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 2060", "selected_vram_gb": 6},
                    {"category": "cpu", "model": "AMD Ryzen 9 7950X"},
                ],
            }
        },
        {
            "name": "GTA V - 測試基準",
            "payload": {
                "game": "Grand Theft Auto V",
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                    {"category": "cpu", "model": "Intel Core i5-12600K"},
                ],
            }
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)

        try:
            resp = httpx.post(
                "http://127.0.0.1:8000/api/benchmarks/search",
                json=test_case['payload'],
                timeout=30.0
            )

            if resp.status_code == 200:
                data = resp.json()
                if 'results' in data and data['results']:
                    result = data['results'][0]
                    fps = result.get('avg_fps', 'N/A')
                    gpu_usage = result.get('gpu_usage', 'N/A')
                    cpu_usage = result.get('cpu_usage', 'N/A')
                    ram_usage = result.get('memory_usage', 'N/A')
                    notes = result.get('notes', '')

                    print(f"  FPS: {fps}")
                    print(f"  GPU 使用率: {gpu_usage}%")
                    print(f"  CPU 使用率: {cpu_usage}%")
                    print(f"  RAM 使用率: {ram_usage}%")
                    print(f"  備註: {notes}")

                    results.append({
                        'test_name': test_case['name'],
                        'fps': fps,
                        'gpu_usage': gpu_usage,
                        'cpu_usage': cpu_usage,
                        'ram_usage': ram_usage,
                        'notes': notes
                    })
                else:
                    print("  [ERROR] 無結果")
            else:
                print(f"  [ERROR] API 錯誤: {resp.status_code}")

        except Exception as e:
            print(f"  [ERROR] 請求錯誤: {e}")

    # 分析結果
    print("\n=== 分析總結 ===")
    print("=" * 50)

    if results:
        # RAM 影響分析
        ram_tests = [r for r in results if 'RAM' in r['test_name']]
        if len(ram_tests) >= 2:
            print("--- RAM 影響分析 ---")
            for test in ram_tests:
                print(f"  {test['test_name']}: FPS={test['fps']}, RAM使用率={test['ram_usage']}%")

        # CPU 影響分析
        cpu_tests = [r for r in results if 'CPU' in r['test_name']]
        if len(cpu_tests) >= 2:
            print("\n--- CPU 影響分析 ---")
            for test in cpu_tests:
                print(f"  {test['test_name']}: FPS={test['fps']}, CPU使用率={test['cpu_usage']}%")

        # 存儲影響分析
        storage_tests = [r for r in results if 'HDD' in r['test_name']]
        if storage_tests:
            print("\n--- 存儲影響分析 ---")
            for test in storage_tests:
                print(f"  {test['test_name']}: FPS={test['fps']}")

    return len(results) > 0

if __name__ == "__main__":
    success = test_ram_cpu_usage()
    sys.exit(0 if success else 1)