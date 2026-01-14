#!/usr/bin/env python3
import httpx
import json

def test_ram_details():
    payload = {
        "game": "Cyberpunk 2077",
        "resolution": "1920x1080",
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
        print(f"Status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            if 'results' in data and data['results']:
                result = data['results'][0]
                print(f"FPS: {result.get('avg_fps')}")
                print(f"GPU Usage: {result.get('gpu_usage')}%")
                print(f"CPU Usage: {result.get('cpu_usage')}%")
                print(f"RAM Usage: {result.get('memory_usage')}%")
                print(f"Notes: {result.get('notes')}")
                print(f"RAM GB: {result.get('ram_gb')}")
                print(f"RAM Type: {result.get('ram_type')}")
                print(f"RAM Speed: {result.get('ram_speed_mhz')}")
                print(f"RAM Latency: {result.get('ram_latency_ns')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ram_details()