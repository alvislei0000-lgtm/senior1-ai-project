#!/usr/bin/env python3
"""
全面測試：解析度和RAM影響
"""
import httpx
import json

def test_resolution_impact():
    """測試不同解析度的FPS影響"""

    print("=== 解析度影響測試 (Cyberpunk 2077 - 重負載AAA) ===")

    resolutions = [
        {"res": "1920x1080", "desc": "1080p"},
        {"res": "2560x1440", "desc": "1440p"},
        {"res": "3840x2160", "desc": "4K"},
    ]

    for res in resolutions:
        payload = {
            "game": "Cyberpunk 2077",
            "resolution": res["res"],
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
                {"category": "ram", "model": "DDR4 RAM", "ram_gb": 16, "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16.0},
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

                    print(f"{res['desc']}: FPS={fps}")
                else:
                    print(f"{res['desc']}: 無結果")
            else:
                print(f"{res['desc']}: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{res['desc']}: 錯誤 - {e}")

def test_ram_impact_clear():
    """測試RAM容量對FPS的明顯影響"""

    print("\n=== RAM容量影響測試 (Cities: Skylines - 需要16GB) ===")

    ram_configs = [
        {"gb": 8, "desc": "8GB RAM (嚴重不足)"},
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
                else:
                    print(f"{ram_config['desc']}: 無結果")
            else:
                print(f"{ram_config['desc']}: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{ram_config['desc']}: 錯誤 - {e}")

def test_cpu_bound_resolution():
    """測試CPU-bound遊戲的解析度影響"""

    print("\n=== CPU-bound遊戲解析度測試 (Counter-Strike 2) ===")

    resolutions = [
        {"res": "1920x1080", "desc": "1080p"},
        {"res": "2560x1440", "desc": "1440p"},
    ]

    for res in resolutions:
        payload = {
            "game": "Counter-Strike 2",
            "resolution": res["res"],
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 2060", "selected_vram_gb": 6},
                {"category": "cpu", "model": "Intel Core i3-12100F"},
                {"category": "ram", "model": "DDR4 RAM", "ram_gb": 16, "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16.0},
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

                    print(f"{res['desc']}: FPS={fps}")
                else:
                    print(f"{res['desc']}: 無結果")
            else:
                print(f"{res['desc']}: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{res['desc']}: 錯誤 - {e}")

if __name__ == "__main__":
    test_resolution_impact()
    test_ram_impact_clear()
    test_cpu_bound_resolution()