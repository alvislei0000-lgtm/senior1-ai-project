#!/usr/bin/env python3
"""
極端RAM測試 - 顯示明顯差異
"""
import httpx
import json

def test_extreme_ram():
    """測試極端RAM情況"""

    print("=== 極端RAM測試 (Fortnite - 需要8GB) ===")

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
                    gpu_usage = result.get('gpu_usage', 'N/A')
                    cpu_usage = result.get('cpu_usage', 'N/A')

                    print(f"{ram_config['desc']}:")
                    print(f"  FPS: {fps}")
                    print(f"  RAM使用率: {ram_usage}%")
                    print(f"  GPU使用率: {gpu_usage}%")
                    print(f"  CPU使用率: {cpu_usage}%")
                    print()

                    results.append({
                        'config': ram_config['desc'],
                        'fps': fps,
                        'ram_usage': ram_usage,
                        'gpu_usage': gpu_usage,
                        'cpu_usage': cpu_usage
                    })
                else:
                    print(f"{ram_config['desc']}: 無結果")
            else:
                print(f"{ram_config['desc']}: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{ram_config['desc']}: 錯誤 - {e}")

    # 比較結果
    if len(results) >= 2:
        print("=== 結果比較 ===")
        for i in range(1, len(results)):
            fps_diff = results[i]['fps'] - results[0]['fps']
            ram_diff = results[i]['ram_usage'] - results[0]['ram_usage']

            print(f"{results[i]['config']} vs {results[0]['config']}:")
            print(f"  FPS差異: {fps_diff:+.1f}")
            print(f"  RAM使用率差異: {ram_diff:+.1f}%")
            print()

def test_ram_types_extreme():
    """測試RAM類型的極端差異"""

    print("\n=== RAM類型極端測試 (Minecraft - CPU-bound) ===")

    ram_configs = [
        {"gb": 16, "type": "DDR3", "speed": 1333, "latency": 25.0, "desc": "16GB DDR3-1333 (舊款)"},
        {"gb": 16, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "16GB DDR4-3200 (標準)"},
        {"gb": 16, "type": "DDR5", "speed": 6000, "latency": 10.0, "desc": "16GB DDR5-6000 (旗艦)"},
    ]

    for ram_config in ram_configs:
        payload = {
            "game": "Minecraft",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                {"category": "cpu", "model": "Intel Core i3-12100F"},
                {"category": "ram", "model": "RAM", "ram_gb": ram_config["gb"], "ram_type": ram_config["type"], "ram_speed_mhz": ram_config["speed"], "ram_latency_ns": ram_config["latency"]},
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
                else:
                    print(f"{ram_config['desc']}: 無結果")
            else:
                print(f"{ram_config['desc']}: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{ram_config['desc']}: 錯誤 - {e}")

if __name__ == "__main__":
    test_extreme_ram()
    test_ram_types_extreme()