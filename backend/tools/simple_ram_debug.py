#!/usr/bin/env python3
"""
極其簡單的RAM調試測試
"""
import httpx
import json

def test_ram_step_by_step():
    """一步步測試RAM影響"""

    print("=== 步步測試RAM影響 (Cyberpunk 2077) ===")

    # 測試Cyberpunk 2077 - 需要16GB RAM
    ram_sizes = [8, 16, 32, 64, 128]

    for ram_gb in ram_sizes:
        print(f"\n--- 測試 {ram_gb}GB RAM ---")

        payload = {
            "game": "Cyberpunk 2077",
            "resolution": "1920x1080",
            "settings": "High",
            "hardware": [
                {"category": "gpu", "model": "RTX 3070", "selected_vram_gb": 8},
                {"category": "cpu", "model": "Intel Core i5-12600K"},
                {"category": "ram", "model": "RAM", "ram_gb": ram_gb, "ram_type": "DDR4", "ram_speed_mhz": 3200, "ram_latency_ns": 16.0},
                {"category": "storage", "model": "NVMe SSD", "storage_type": "NVMe SSD"}
            ]
        }

        try:
            resp = httpx.post("http://127.0.0.1:8000/api/benchmarks/search", json=payload, timeout=30.0)
            print(f"狀態碼: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                if 'results' in data and data['results']:
                    result = data['results'][0]
                    fps = result.get('avg_fps', 'N/A')
                    ram_usage = result.get('memory_usage', 'N/A')
                    notes = result.get('notes', '')

                    print(f"FPS: {fps}")
                    print(f"RAM使用率: {ram_usage}%")
                    print(f"RAM GB: {result.get('ram_gb', 'N/A')}")
                    print(f"RAM類型: {result.get('ram_type', 'N/A')}")
                    if "GPU:" in notes:
                        usage_part = notes.split("GPU:")[1].split("|")[0]
                        print(f"詳細使用率: GPU:{usage_part}")
                else:
                    print("無結果")
            else:
                print(f"API錯誤: {resp.status_code}")
                try:
                    error_data = resp.json()
                    print(f"錯誤詳情: {error_data}")
                except:
                    print(f"錯誤內容: {resp.text[:200]}")

        except Exception as e:
            print(f"請求錯誤: {e}")

if __name__ == "__main__":
    test_ram_step_by_step()