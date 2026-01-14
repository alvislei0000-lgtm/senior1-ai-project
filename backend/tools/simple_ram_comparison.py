#!/usr/bin/env python3
"""
簡單的 RAM 容量比較測試
"""
import httpx
import json

def test_ram_capacity():
    """測試不同 RAM 容量對 Cities: Skylines 的影響"""

    print("=== RAM 容量影響測試 (Cities: Skylines) ===")

    ram_configs = [
        {"gb": 8, "desc": "8GB RAM (不足)"},
        {"gb": 16, "desc": "16GB RAM (足夠)"},
        {"gb": 32, "desc": "32GB RAM (充裕)"},
    ]

    for ram_config in ram_configs:
        payload = {
            "game": "Cities: Skylines",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
                {"category": "ram", "model": "DDR4 RAM", "ram_gb": ram_config["gb"], "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16.0},
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

def test_ram_type():
    """測試不同 RAM 類型對 Cyberpunk 2077 的影響"""

    print("\n=== RAM 類型影響測試 (Cyberpunk 2077) ===")

    ram_configs = [
        {"type": "DDR3", "speed": 1600, "latency": 20.0, "desc": "DDR3-1600 (舊款)"},
        {"type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "DDR4-3200 (標準)"},
        {"type": "DDR5", "speed": 5200, "latency": 12.0, "desc": "DDR5-5200 (新款)"},
    ]

    for ram_config in ram_configs:
        payload = {
            "game": "Cyberpunk 2077",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
                {"category": "ram", "model": "RAM", "ram_gb": 16, "ram_type": ram_config["type"], "ram_speed_mhz": ram_config["speed"], "ram_latency_ns": ram_config["latency"]},
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
    test_ram_capacity()
    test_ram_type()