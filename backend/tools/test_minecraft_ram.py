#!/usr/bin/env python3
"""
測試Minecraft RAM影響
"""
import httpx
import json

def test_minecraft_ram():
    """測試Minecraft不同RAM配置的影響"""

    print("=== Minecraft RAM影響測試 (需要16GB RAM) ===")

    ram_configs = [
        {"gb": 8, "desc": "8GB RAM (不足)"},
        {"gb": 16, "desc": "16GB RAM (足夠)"},
        {"gb": 32, "desc": "32GB RAM (充裕)"},
        {"gb": 64, "desc": "64GB RAM (極充裕)"},
    ]

    results = []

    for ram_config in ram_configs:
        print(f"\n測試: {ram_config['desc']}")

        payload = {
            "game": "Minecraft",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                {"category": "cpu", "model": "Intel Core i3-12100F"},  # CPU-bound遊戲使用較弱CPU
                {"category": "ram", "model": f"RAM {ram_config['gb']}GB", "ram_gb": ram_config["gb"], "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16},
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
                        'ram_gb': ram_config['gb'],
                        'fps': fps,
                        'ram_usage': ram_usage,
                        'gpu_usage': gpu_usage,
                        'cpu_usage': cpu_usage
                    })
                else:
                    print("  無結果")
            else:
                print(f"  API錯誤: {resp.status_code}")

        except Exception as e:
            print(f"  錯誤: {e}")

    # 分析結果
    if len(results) >= 2:
        print("\n=== 結果分析 ===")
        print("Minecraft RAM影響:")
        for result in results:
            config_name = result['config'][:10]
            fps_val = result['fps']
            ram_usage_val = result['ram_usage']
            print("<12"
                  "<8"
                  "<8")

        print("\n=== 差異比較 ===")
        baseline = results[0]  # 8GB
        for result in results[1:]:
            fps_diff = result['fps'] - baseline['fps']
            ram_diff = result['ram_usage'] - baseline['ram_usage']

            print(f"{result['config']} vs {baseline['config']}:")
            print(".1f")
            print(".1f")
            print()

def test_different_cpus():
    """測試Minecraft在不同CPU下的RAM影響"""

    print("\n=== Minecraft - 不同CPU下的RAM影響 ===")

    test_configs = [
        {"cpu": "Intel Core i3-12100F", "ram": 8, "desc": "i3 + 8GB RAM"},
        {"cpu": "Intel Core i3-12100F", "ram": 16, "desc": "i3 + 16GB RAM"},
        {"cpu": "AMD Ryzen 9 7950X", "ram": 8, "desc": "Ryzen 9 + 8GB RAM"},
        {"cpu": "AMD Ryzen 9 7950X", "ram": 16, "desc": "Ryzen 9 + 16GB RAM"},
    ]

    for config in test_configs:
        payload = {
            "game": "Minecraft",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3060", "selected_vram_gb": 12},
                {"category": "cpu", "model": config["cpu"]},
                {"category": "ram", "model": f"RAM {config['ram']}GB", "ram_gb": config["ram"], "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16},
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
                    cpu_usage = result.get('cpu_usage', 'N/A')
                    ram_usage = result.get('memory_usage', 'N/A')

                    print(f"{config['desc']}: FPS={fps}, CPU使用率={cpu_usage}%, RAM使用率={ram_usage}%")

        except Exception as e:
            print(f"{config['desc']}: 錯誤 - {e}")

if __name__ == "__main__":
    test_minecraft_ram()
    test_different_cpus()