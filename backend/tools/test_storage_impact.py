#!/usr/bin/env python3
"""
測試儲存類型對FPS的影響
"""
import httpx
import json

def test_storage_types():
    """測試不同儲存類型對FPS的影響"""

    print("=== Storage Type FPS Impact Test ===")

    storage_configs = [
        {"type": "NVMe SSD", "desc": "NVMe SSD (+1%)"},
        {"type": "SSD", "desc": "SSD (baseline)"},
        {"type": "HDD", "desc": "HDD (-2%)"},
    ]

    test_games = [
        {"name": "Cyberpunk 2077", "desc": "Heavy AAA game"},
        {"name": "Minecraft", "desc": "CPU-bound game"},
        {"name": "Fortnite", "desc": "Esports game"},
    ]

    for game in test_games:
        print(f"\n[Game] {game['name']} ({game['desc']})")
        print("-" * 50)

        results = []

        for storage in storage_configs:
            payload = {
                "game": game["name"],
                "resolution": "1920x1080",
                "settings": "High",
                "hardware": [
                    {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                    {"category": "cpu", "model": "Intel Core i5-12600K"},
                    {"category": "ram", "model": "DDR4 RAM", "ram_gb": 16, "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16},
                    {"category": "storage", "model": storage["type"], "storage_type": storage["type"]}
                ]
            }

            try:
                resp = httpx.post("http://127.0.0.1:8000/api/benchmarks/search", json=payload, timeout=30.0)

                if resp.status_code == 200:
                    data = resp.json()
                    if 'results' in data and data['results']:
                        result = data['results'][0]
                        fps = result.get('avg_fps', 'N/A')

                        print(f"{storage['desc']}: FPS={fps}")
                        results.append({
                            'storage': storage['desc'],
                            'fps': fps
                        })
                    else:
                        print(f"{storage['desc']}: No results")
                else:
                    print(f"{storage['desc']}: API error {resp.status_code}")

            except Exception as e:
                print(f"{storage['desc']}: Error - {e}")

        # 比較結果
        if len(results) >= 2:
            print("Comparison:")
            baseline = results[1]  # SSD as baseline
            for result in results:
                if result != baseline:
                    fps_diff = result['fps'] - baseline['fps']
                    print(f"{result['storage']} vs {baseline['storage']}: {fps_diff:+.1f} FPS ({fps_diff/baseline['fps']*100:+.2f}%)")

def test_storage_extreme():
    """測試極端儲存差異"""

    print("\n=== Extreme Storage Test (Cities: Skylines) ===")

    storage_configs = [
        {"type": "NVMe SSD", "desc": "NVMe SSD"},
        {"type": "SATA SSD", "desc": "SATA SSD"},
        {"type": "7200RPM HDD", "desc": "7200RPM HDD"},
        {"type": "5400RPM HDD", "desc": "5400RPM HDD"},
    ]

    for storage in storage_configs:
        payload = {
            "game": "Cities: Skylines",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
                {"category": "ram", "model": "DDR4 RAM", "ram_gb": 16, "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16},
                {"category": "storage", "model": storage["type"], "storage_type": storage["type"]}
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

                    print(f"{storage['desc']}: FPS={fps}, RAM使用率={ram_usage}%")
                else:
                    print(f"{storage['desc']}: 無結果")
            else:
                print(f"{storage['desc']}: API錯誤 {resp.status_code}")

        except Exception as e:
            print(f"{storage['desc']}: 錯誤 - {e}")

def test_storage_multiplier_logic():
    """手動測試儲存乘數邏輯"""

    print("\n=== Storage Multiplier Logic Test ===")

    def calculate_storage_multiplier(storage_type: str) -> float:
        """模擬_get_storage_multiplier邏輯"""
        if storage_type is None:
            return 1.0

        storage_lower = storage_type.lower()

        if 'nvme' in storage_lower or 'pcie' in storage_lower:
            return 1.01  # 1% boost for NVMe SSD
        elif 'ssd' in storage_lower:
            return 1.0   # Baseline for regular SSD
        elif 'hdd' in storage_lower:
            return 0.98  # 2% decrease for HDD
        else:
            return 1.0   # Default

    test_types = [
        "NVMe SSD", "PCIe SSD", "SATA SSD", "SSD",
        "7200RPM HDD", "5400RPM HDD", "HDD"
    ]

    base_fps = 100.0

    print("儲存類型乘數計算:")
    for storage_type in test_types:
        multiplier = calculate_storage_multiplier(storage_type)
        final_fps = base_fps * multiplier
        fps_diff = (multiplier - 1.0) * 100

        storage_name = storage_type[:10]
        print("12"
              "6.3f"
              "6.1f")

if __name__ == "__main__":
    test_storage_types()
    test_storage_extreme()
    test_storage_multiplier_logic()