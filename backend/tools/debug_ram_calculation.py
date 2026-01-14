#!/usr/bin/env python3
"""
手動計算RAM multiplier來驗證邏輯
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def debug_ram_multiplier():
    """手動計算RAM multiplier"""

    print("=== 手動計算RAM Multiplier ===")

    # 模擬_get_ram_multiplier的邏輯
    def calculate_ram_multiplier(game: str, ram_gb: float, ram_type: str = "DDR4",
                               ram_speed_mhz: int = 3200, ram_latency_ns: float = 16.0):
        # 模擬遊戲需求查詢
        game_requirements = {
            "cyberpunk 2077": {"ram": 16},
            "cities: skylines": {"ram": 16},
            "fortnite": {"ram": 8},
            "minecraft": {"ram": 16}
        }

        game_req = game_requirements.get(game.lower())
        if not game_req:
            return 1.0

        recommended_ram = game_req.get("ram", 16)
        multiplier = 1.0

        print(f"遊戲: {game}, 需要RAM: {recommended_ram}GB, 提供RAM: {ram_gb}GB")

        # Capacity impact
        if ram_gb < recommended_ram:
            shortage_ratio = recommended_ram / ram_gb
            print(".2f")

            if shortage_ratio >= 2:
                penalty = min(0.30, 0.10 * (shortage_ratio - 1))
            else:
                penalty = min(0.15, 0.05 * (shortage_ratio - 1))
            multiplier *= (1.0 - penalty)
            print(".3f")
        else:
            if ram_gb >= recommended_ram * 2:
                multiplier *= 1.02
                print(f"RAM充足 (2倍需求), 提升2%: multiplier = {multiplier}")

        # RAM type impact
        if ram_type:
            ram_type_lower = ram_type.lower()
            if 'ddr5' in ram_type_lower:
                multiplier *= 1.01
                print(f"DDR5類型, 提升1%: multiplier = {multiplier}")
            elif 'ddr4' in ram_type_lower:
                print(f"DDR4類型, 無影響: multiplier = {multiplier}")
            elif 'ddr3' in ram_type_lower:
                multiplier *= 0.98
                print(f"DDR3類型, 懲罰2%: multiplier = {multiplier}")

        # RAM speed impact
        if ram_speed_mhz:
            if ram_speed_mhz >= 6000:
                speed_boost = 0.005
            elif ram_speed_mhz >= 5200:
                speed_boost = 0.003
            elif ram_speed_mhz >= 3600:
                speed_boost = 0.002
            elif ram_speed_mhz >= 3200:
                speed_boost = 0.001
            else:
                speed_boost = -0.002
            multiplier *= (1.0 + speed_boost)
            print(f"RAM速度 {ram_speed_mhz}MHz, 調整{speed_boost*100:+.1f}%: multiplier = {multiplier}")

        # RAM latency impact
        if ram_latency_ns:
            if ram_latency_ns <= 10:
                latency_boost = 0.003
            elif ram_latency_ns <= 14:
                latency_boost = 0.002
            elif ram_latency_ns <= 18:
                latency_boost = 0.0
            else:
                latency_boost = -0.002
            multiplier *= (1.0 + latency_boost)
            print(f"RAM延遲 {ram_latency_ns}ns, 調整{latency_boost*100:+.1f}%: multiplier = {multiplier}")

        return multiplier

    # 測試Cyberpunk 2077 (需要16GB)
    test_cases = [
        {"game": "Cyberpunk 2077", "ram_gb": 8, "ram_type": "DDR4", "ram_speed": 3200, "ram_latency": 16.0},
        {"game": "Cyberpunk 2077", "ram_gb": 16, "ram_type": "DDR4", "ram_speed": 3200, "ram_latency": 16.0},
        {"game": "Cyberpunk 2077", "ram_gb": 32, "ram_type": "DDR4", "ram_speed": 3200, "ram_latency": 16.0},
        {"game": "Cyberpunk 2077", "ram_gb": 128, "ram_type": "DDR4", "ram_speed": 3200, "ram_latency": 16.0},
    ]

    base_fps = 136.7  # 假設的基礎FPS

    for test_case in test_cases:
        print(f"\n--- {test_case['ram_gb']}GB RAM ---")
        multiplier = calculate_ram_multiplier(
            test_case["game"],
            test_case["ram_gb"],
            test_case["ram_type"],
            test_case["ram_speed"],
            test_case["ram_latency"]
        )

        final_fps = base_fps * multiplier
        print(f"基礎FPS: {base_fps}")
        print(f"RAM multiplier: {multiplier}")
        print(f"最終FPS (無隨機): {final_fps:.1f}")
        print(f"隨機範圍: {(final_fps * 0.95):.1f} - {(final_fps * 1.05):.1f}")

if __name__ == "__main__":
    debug_ram_multiplier()