#!/usr/bin/env python3
"""
測試不同NVMe代際對FPS的影響
"""
import httpx
import json

def test_nvme_generations():
    """測試NVMe Gen3/4/5的性能差異"""

    print("=== 測試NVMe不同代際的FPS影響 ===")

    storage_configs = [
        {"type": "NVMe Gen3", "desc": "NVMe Gen3 (+0.5%)"},
        {"type": "NVMe Gen4", "desc": "NVMe Gen4 (+1.0%)"},
        {"type": "NVMe Gen5", "desc": "NVMe Gen5 (+1.5%)"},
        {"type": "SSD", "desc": "SATA SSD (基準)"},
    ]

    test_games = [
        {"name": "Minecraft", "desc": "CPU-bound + 載入密集"},
        {"name": "Cyberpunk 2077", "desc": "重負載AAA"},
        {"name": "Counter-Strike 2", "desc": "電競遊戲"},
    ]

    results = {}

    for game in test_games:
        print(f"\n[Game] {game['name']} ({game['desc']})")
        print("-" * 60)

        game_results = []

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
                        ram_usage = result.get('memory_usage', 'N/A')
                        gpu_usage = result.get('gpu_usage', 'N/A')
                        cpu_usage = result.get('cpu_usage', 'N/A')

                        print(f"  {storage['desc']}: FPS={fps}")
                        game_results.append({
                            'storage': storage['desc'],
                            'fps': fps,
                            'ram_usage': ram_usage,
                            'gpu_usage': gpu_usage,
                            'cpu_usage': cpu_usage
                        })
                    else:
                        print(f"  {storage['desc']}: 無結果")
                else:
                    print(f"  {storage['desc']}: API錯誤 {resp.status_code}")

            except Exception as e:
                print(f"  {storage['desc']}: 錯誤 - {e}")

        results[game['name']] = game_results

        # 比較結果
        if len(game_results) >= 2:
            print("  比較:")
            baseline = next((r for r in game_results if 'SSD (基準)' in r['storage']), game_results[0])

            for result in game_results:
                if result != baseline and isinstance(result['fps'], (int, float)) and isinstance(baseline['fps'], (int, float)):
                    fps_diff = result['fps'] - baseline['fps']
                    fps_percent = (fps_diff / baseline['fps']) * 100
                    print(".1f")

    print("\n=== 總結分析 ===")
    print("NVMe代際性能提升:")
    print("  • Gen3 vs SSD: +0.5%")
    print("  • Gen4 vs SSD: +1.0%")
    print("  • Gen5 vs SSD: +1.5%")

    print("\n影響最大的遊戲:")
    for game_name, game_results in results.items():
        if len(game_results) >= 2:
            baseline = next((r for r in game_results if 'SSD (基準)' in r['storage']), game_results[0])
            max_diff = 0
            best_storage = baseline['storage']

            for result in game_results:
                if isinstance(result['fps'], (int, float)) and isinstance(baseline['fps'], (int, float)):
                    diff = result['fps'] - baseline['fps']
                    if diff > max_diff:
                        max_diff = diff
                        best_storage = result['storage']

            if max_diff > 0.1:  # 至少0.1 FPS差異
                print(".1f")

def test_storage_multiplier_logic():
    """測試儲存乘數邏輯"""

    print("\n=== 儲存乘數邏輯測試 ===")

    def calculate_storage_multiplier(storage_type: str) -> float:
        """模擬_get_storage_multiplier邏輯"""
        if storage_type is None:
            return 1.0

        storage_lower = storage_type.lower()

        # Check for NVMe generations first (more specific)
        if 'gen5' in storage_lower or 'gen 5' in storage_lower:
            return 1.015  # 1.5% boost for NVMe Gen5
        elif 'gen4' in storage_lower or 'gen 4' in storage_lower:
            return 1.01   # 1% boost for NVMe Gen4
        elif 'gen3' in storage_lower or 'gen 3' in storage_lower:
            return 1.005  # 0.5% boost for NVMe Gen3
        elif 'nvme' in storage_lower or 'pcie' in storage_lower:
            return 1.007  # 0.7% boost for generic NVMe
        elif 'ssd' in storage_lower:
            return 1.0    # Baseline for regular SSD
        elif 'hdd' in storage_lower:
            return 0.98   # 2% decrease for HDD
        else:
            return 1.0    # Default

    test_types = [
        "NVMe Gen3", "NVMe Gen4", "NVMe Gen5", "NVMe", "SSD", "HDD"
    ]

    base_fps = 100.0

    print("儲存類型乘數計算:")
    print("類型".ljust(12) + "乘數".ljust(8) + "FPS".ljust(8) + "差異")
    print("-" * 40)

    for storage_type in test_types:
        multiplier = calculate_storage_multiplier(storage_type)
        final_fps = base_fps * multiplier
        fps_diff = (multiplier - 1.0) * 100

        print("12"
              "6.3f"
              "6.1f"
              "5.1f")

if __name__ == "__main__":
    test_nvme_generations()
    test_storage_multiplier_logic()