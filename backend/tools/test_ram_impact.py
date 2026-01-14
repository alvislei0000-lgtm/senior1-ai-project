#!/usr/bin/env python3
"""
測試 RAM 容量和類型對 FPS 和使用率的影響
"""
import httpx
import json

def test_ram_impact():
    """測試不同 RAM 配置對遊戲性能的影響"""

    print("=== RAM 容量和類型影響測試 ===")
    print("=" * 50)

    # 測試配置：使用對RAM敏感的遊戲
    test_configs = [
        {
            "game": "Cities: Skylines",  # 16GB RAM需求
            "resolution": "1920x1080",
            "settings": "High",
            "ram_configs": [
                {"gb": 8, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "8GB DDR4-3200 (不足)"},
                {"gb": 16, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "16GB DDR4-3200 (足夠)"},
                {"gb": 32, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "32GB DDR4-3200 (充裕)"},
            ]
        },
        {
            "game": "Cyberpunk 2077",  # 16GB RAM需求
            "resolution": "1920x1080",
            "settings": "High",
            "ram_configs": [
                {"gb": 8, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "8GB DDR4-3200 (嚴重不足)"},
                {"gb": 16, "type": "DDR4", "speed": 3200, "latency": 16.0, "desc": "16GB DDR4-3200 (基準)"},
                {"gb": 16, "type": "DDR5", "speed": 5200, "latency": 12.0, "desc": "16GB DDR5-5200 (高速)"},
                {"gb": 16, "type": "DDR3", "speed": 1600, "latency": 20.0, "desc": "16GB DDR3-1600 (舊款)"},
            ]
        }
    ]

    base_hardware = [
        {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
        {"category": "cpu", "model": "Intel Core i5-12600K"},
        {"category": "storage", "model": "NVMe SSD", "storage_type": "NVMe SSD"}
    ]

    for game_config in test_configs:
        print(f"\n[遊戲] {game_config['game']} ({game_config['resolution']} {game_config['settings']})")
        print("-" * 70)

        for ram_config in game_config["ram_configs"]:
            hardware = base_hardware + [{
                "category": "ram",
                "model": f"{ram_config['type']} RAM",
                "ram_gb": ram_config["gb"],
                "ram_type": ram_config["type"],
                "ram_speed_mhz": ram_config["speed"],
                "ram_latency_ns": ram_config["latency"]
            }]

            payload = {
                "game": game_config["game"],
                "resolution": game_config["resolution"],
                "settings": game_config["settings"],
                "hardware": hardware
            }

            try:
                resp = httpx.post("http://127.0.0.1:8000/api/benchmarks/search", json=payload, timeout=30.0)

                if resp.status_code == 200:
                    data = resp.json()
                    if 'results' in data and data['results']:
                        result = data['results'][0]
                        fps = result.get('avg_fps', 'N/A')
                        gpu_usage = result.get('gpu_usage', 'N/A')
                        cpu_usage = result.get('cpu_usage', 'N/A')
                        ram_usage = result.get('memory_usage', 'N/A')

                        print("<25"
                              "<8"
                              "<8"
                              "<8"
                              "<8")
                    else:
                        print(f"{ram_config['desc']}: 無結果")
                else:
                    print(f"{ram_config['desc']}: API錯誤 {resp.status_code}")

            except Exception as e:
                print(f"{ram_config['desc']}: 請求錯誤 - {e}")

if __name__ == "__main__":
    test_ram_impact()