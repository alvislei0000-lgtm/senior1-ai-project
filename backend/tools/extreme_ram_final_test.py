#!/usr/bin/env python3
"""
最終極端RAM測試 - 顯示FPS差異
"""
import httpx
import json

def test_extreme_ram_fps():
    """測試極端RAM情況下的FPS差異"""

    print("=== 最終極端RAM FPS測試 (Fortnite - 需要8GB) ===")

    ram_configs = [
        {"gb": 4, "desc": "4GB RAM (極端不足)"},
        {"gb": 8, "desc": "8GB RAM (足夠)"},
        {"gb": 16, "desc": "16GB RAM (充裕)"},
    ]

    results = []

    for ram_config in ram_configs:
        payload = {
            "game": "Fortnite",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
                {"category": "ram", "model": "RAM", "ram_gb": ram_config["gb"], "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16.0},
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

                    print(f"{ram_config['desc']}: FPS={fps}, RAM使用率={ram_usage}%")
                    results.append({
                        'config': ram_config['desc'],
                        'fps': fps,
                        'ram_usage': ram_usage
                    })
                else:
                    print(f"{ram_config['desc']}: 無結果")
            else:
                print(f"{ram_config['desc']}: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{ram_config['desc']}: 錯誤 - {e}")

    # 分析結果
    if len(results) >= 2:
        print("\n=== 結果分析 ===")
        baseline = results[0]
        for result in results[1:]:
            fps_diff = result['fps'] - baseline['fps']
            ram_diff = result['ram_usage'] - baseline['ram_usage']

            print(f"{result['config']} vs {baseline['config']}:")
            print(".1f")
            print(".1f")
            print()

if __name__ == "__main__":
    test_extreme_ram_fps()