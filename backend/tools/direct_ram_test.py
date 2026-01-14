#!/usr/bin/env python3
"""
直接測試RAM影響 - 強制顯示差異
"""
import httpx
import json
import time

def test_ram_direct():
    """直接測試RAM容量差異"""

    print("=== 直接RAM測試 (Cities: Skylines) ===")

    ram_configs = [
        {"gb": 8, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "8GB DDR4-3200"},
        {"gb": 16, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "16GB DDR4-3200"},
        {"gb": 32, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "32GB DDR4-3200"},
    ]

    results = []

    for i, ram_config in enumerate(ram_configs):
        print(f"\n測試 {i+1}: {ram_config['desc']}")

        payload = {
            "game": "Cities: Skylines",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
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
                    gpu_usage = result.get('gpu_usage', 'N/A')
                    cpu_usage = result.get('cpu_usage', 'N/A')

                    print(f"  FPS: {fps}")
                    print(f"  RAM使用率: {ram_usage}%")
                    print(f"  GPU使用率: {gpu_usage}%")
                    print(f"  CPU使用率: {cpu_usage}%")

                    results.append({
                        'config': ram_config['desc'],
                        'fps': fps,
                        'ram_usage': ram_usage,
                        'gpu_usage': gpu_usage,
                        'cpu_usage': cpu_usage
                    })
                else:
                    print("  [ERROR] 無結果")
            else:
                print(f"  [ERROR] API錯誤 {resp.status_code}")
                try:
                    error_data = resp.json()
                    print(f"  錯誤詳情: {error_data}")
                except:
                    print(f"  錯誤內容: {resp.text[:200]}")

        except Exception as e:
            print(f"  [ERROR] 請求錯誤: {e}")

        # 延遲一下避免快取問題
        time.sleep(1)

    # 比較結果
    if len(results) >= 2:
        print("\n=== 結果比較 ===")
        baseline = results[0]
        for result in results[1:]:
            fps_diff = result['fps'] - baseline['fps']
            ram_diff = result['ram_usage'] - baseline['ram_usage']

            print(f"{result['config']} vs {baseline['config']}:")
            print(f"  FPS差異: {fps_diff:+.1f}")
            print(f"  RAM使用率差異: {ram_diff:+.1f}%")
            print()

def test_ram_types():
    """測試不同RAM類型"""

    print("\n=== RAM類型測試 (Cyberpunk 2077) ===")

    ram_configs = [
        {"gb": 16, "type": "DDR3", "speed": 1600, "latency": 20.0, "desc": "16GB DDR3-1600"},
        {"gb": 16, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "16GB DDR4-3200"},
        {"gb": 16, "type": "DDR5", "speed": 5200, "latency": 12.0, "desc": "16GB DDR5-5200"},
    ]

    for ram_config in ram_configs:
        payload = {
            "game": "Cyberpunk 2077",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
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
    test_ram_direct()
    test_ram_types()