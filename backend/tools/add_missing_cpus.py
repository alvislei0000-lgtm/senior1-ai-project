#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

BASE = Path(__file__).resolve().parents[1]
SEED = BASE / "data" / "hardware_seed.json"

NEW_CPUS: List[Dict] = [
    {"category": "cpu", "model": "Ryzen 9 9800X", "generation": "Zen 5", "release_year": 2024, "brand": "AMD", "vram_gb": 0, "ram_gb": 32},
    {"category": "cpu", "model": "Ryzen 9 9800", "generation": "Zen 5", "release_year": 2024, "brand": "AMD", "vram_gb": 0, "ram_gb": 32},
    {"category": "cpu", "model": "Ryzen 9 9800X3D", "generation": "Zen 5 X3D", "release_year": 2024, "brand": "AMD", "vram_gb": 0, "ram_gb": 32},
    {"category": "cpu", "model": "Ryzen 7 9800X", "generation": "Zen 5", "release_year": 2024, "brand": "AMD", "vram_gb": 0, "ram_gb": 32},
    {"category": "cpu", "model": "Ryzen 7 9800X3D", "generation": "Zen 5 X3D", "release_year": 2024, "brand": "AMD", "vram_gb": 0, "ram_gb": 32},
    {"category": "cpu", "model": "Ryzen 5 9600X", "generation": "Zen 5", "release_year": 2024, "brand": "AMD", "vram_gb": 0, "ram_gb": 16}
]


def load_seed() -> Dict:
    if not SEED.exists():
        return {"items": []}
    return json.loads(SEED.read_text(encoding="utf-8"))


def save_seed(data: Dict):
    SEED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    data = load_seed()
    items = data.get("items", [])
    existing = set((it.get("model") or "").strip() for it in items if isinstance(it, dict))
    added = []
    for cpu in NEW_CPUS:
        if cpu["model"] not in existing:
            items.append(cpu)
            added.append(cpu["model"])
    data["items"] = items
    save_seed(data)
    print("Added CPUs:", added)


if __name__ == "__main__":
    main()

