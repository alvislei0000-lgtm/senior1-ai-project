#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Use existing Google Programmable Search to find storage device model names in snippets,
then add matched models (SATA SSD / HDD) into backend + frontend seed files.

Note: This script avoids non-ASCII console output for Windows cp950 compatibility.
"""

import json
import re
from typing import Dict, List

from google_programmable_search import google_search


API_KEY = "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
CX = "034784ab1b1404dc2"


STORAGE_CANDIDATES: Dict[str, Dict] = {
    # SATA SSD
    "WD Blue SA510": {"brand": "Western Digital", "generation": "SATA", "capacity_gb": 1000, "release_year": 2022},
    "Samsung 870 QVO": {"brand": "Samsung", "generation": "SATA", "capacity_gb": 1000, "release_year": 2020},
    "Samsung 870 EVO": {"brand": "Samsung", "generation": "SATA", "capacity_gb": 1000, "release_year": 2020},
    "Crucial MX500": {"brand": "Crucial", "generation": "SATA", "capacity_gb": 1000, "release_year": 2018},
    "Crucial BX500": {"brand": "Crucial", "generation": "SATA", "capacity_gb": 1000, "release_year": 2019},
    "SanDisk Ultra 3D": {"brand": "SanDisk", "generation": "SATA", "capacity_gb": 1000, "release_year": 2017},
    "Kingston A400": {"brand": "Kingston", "generation": "SATA", "capacity_gb": 480, "release_year": 2016},
    # HDD
    "WD Red Plus": {"brand": "Western Digital", "generation": "HDD", "capacity_gb": 4096, "release_year": 2020},
    "Seagate IronWolf": {"brand": "Seagate", "generation": "HDD", "capacity_gb": 4096, "release_year": 2020},
    "Toshiba N300": {"brand": "Toshiba", "generation": "HDD", "capacity_gb": 4096, "release_year": 2021},
    "Seagate Exos": {"brand": "Seagate", "generation": "HDD", "capacity_gb": 16384, "release_year": 2023},
}


SEARCH_QUERIES = [
    "best SATA SSD 2024 2025",
    "best HDD 2024 2025",
    "WD Blue SA510 vs Samsung 870 EVO SATA SSD",
    "Seagate IronWolf WD Red Plus Toshiba N300 HDD",
]


def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def find_candidates_in_results(results: List[Dict[str, str]]) -> List[str]:
    hay = " ".join(
        normalize_text(r.get("title", "")) + " " + normalize_text(r.get("snippet", ""))
        for r in results
    ).lower()

    matched: List[str] = []
    for name in STORAGE_CANDIDATES.keys():
        if name.lower() in hay:
            matched.append(name)
    return matched


def load_seed(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seed(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_storage_items(seed_path: str, models: List[str]) -> int:
    data = load_seed(seed_path)
    items = data.get("items", [])
    existing = set((it.get("category"), it.get("model")) for it in items if isinstance(it, dict))

    added = 0
    for model in models:
        key = ("storage", model)
        if key in existing:
            continue
        meta = STORAGE_CANDIDATES[model]
        items.append({
            "category": "storage",
            "model": model,
            "generation": meta["generation"],
            "release_year": meta["release_year"],
            "brand": meta["brand"],
            "capacity_gb": meta["capacity_gb"],
        })
        added += 1
        existing.add(key)

    data["items"] = items
    save_seed(seed_path, data)
    return added


def main() -> None:
    print("Searching online for storage model mentions...")
    matched_all: List[str] = []
    for q in SEARCH_QUERIES:
        print(f"Query: {q}")
        try:
            results = google_search(q, API_KEY, CX, num=10)
        except Exception as e:
            print(f"  Search failed: {e}")
            continue
        matched = find_candidates_in_results(results)
        print(f"  Matched models: {', '.join(matched) if matched else '(none)'}")
        matched_all.extend(matched)

    # de-dupe preserve order
    seen = set()
    matched_unique = []
    for m in matched_all:
        if m in seen:
            continue
        matched_unique.append(m)
        seen.add(m)

    if not matched_unique:
        print("No models matched from search snippets. No changes applied.")
        return

    backend_added = add_storage_items("backend/data/hardware_seed.json", matched_unique)
    frontend_added = add_storage_items("frontend/src/data/hardware_seed_frontend.json", matched_unique)
    print(f"Added to backend seed: {backend_added}")
    print(f"Added to frontend seed: {frontend_added}")
    print("Done.")


if __name__ == "__main__":
    main()





