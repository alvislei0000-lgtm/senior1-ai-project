#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import httpx


def main():
    url = "http://127.0.0.1:8000/api/benchmarks/search"
    payload = {
        "game": "Cyberpunk 2077",
        "resolution": "3840x2160",
        "settings": "Ultra",
        "hardware": [
            {"category": "gpu", "model": "RTX 4090", "selected_vram_gb": 24},
            {"category": "cpu", "model": "Intel Core i9-13900K"},
        ],
    }
    try:
        resp = httpx.post(url, json=payload, timeout=30.0)
    except Exception as e:
        print("REQUEST_ERROR", str(e))
        return 2

    print("STATUS", resp.status_code)
    try:
        data = resp.json()
        print("RESP_JSON_KEYS:", list(data.keys()) if isinstance(data, dict) else type(data))
        print(json.dumps(data, ensure_ascii=False)[:4000])
    except Exception:
        print("RESP_TEXT:", resp.text[:4000])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

