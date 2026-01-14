#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search for common HDD and SATA SSD models online and add them to hardware_seed files
"""

import json
from google_programmable_search import google_search

KNOWN_STORAGE = {
    "Samsung 870 EVO": {"brand": "Samsung", "generation": "SATA", "capacity_gb": 1000, "release_year": 2020},
    "Crucial MX500": {"brand": "Crucial", "generation": "SATA", "capacity_gb": 1000, "release_year": 2018},
    "Kingston A400": {"brand": "Kingston", "generation": "SATA", "capacity_gb": 480, "release_year": 2016},
    "WD Blue": {"brand": "Western Digital", "generation": "HDD", "capacity_gb": 1000, "release_year": 2020},
    "Seagate Barracuda": {"brand": "Seagate", "generation": "HDD", "capacity_gb": 4000, "release_year": 2019},
    "Seagate IronWolf": {"brand": "Seagate", "generation": "HDD", "capacity_gb": 4000, "release_year": 2020},
    "Toshiba X300": {"brand": "Toshiba", "generation": "HDD", "capacity_gb": 4000, "release_year": 2017},
    "Samsung 860 EVO": {"brand": "Samsung", "generation": "SATA", "capacity_gb": 1000, "release_year": 2018},
    "Crucial BX500": {"brand": "Crucial", "generation": "SATA", "capacity_gb": 480, "release_year": 2017}
}

API_KEY = "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
CX = "034784ab1b1404dc2"

def search_and_collect():
    found = []
    for model in KNOWN_STORAGE.keys():
        print(f"Searching for: {model}")
        try:
            results = google_search(model + " review 2024", API_KEY, CX, num=5)
        except Exception as e:
            print(f"Search failed for {model}: {e}")
            results = []

        if results:
            # If any result found, consider the model available
            print(f"  Found {len(results)} results for {model}")
            info = KNOWN_STORAGE[model].copy()
            info.update({"category": "storage", "model": model})
            found.append(info)
        else:
            print(f"  No results for {model}")

    return found

def add_to_file(path, new_items):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('items', [])
    existing_models = set(i.get('model') for i in items)
    added = 0
    for ni in new_items:
        if ni['model'] not in existing_models:
            items.append(ni)
            added += 1
            print(f"Added {ni['model']} to {path}")
        else:
            print(f"Skipped (exists) {ni['model']}")

    data['items'] = items
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Finished {path}: added {added} items")

def main():
    print("Searching known storage models online...")
    found = search_and_collect()
    if not found:
        print("No storage models found. Exiting.")
        return

    add_to_file("backend/data/hardware_seed.json", found)
    add_to_file("frontend/src/data/hardware_seed_frontend.json", found)
    print("Done adding storage items.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search latest storage devices (HDD, SATA SSD) and add to hardware seed files
"""

import json
import re
from google_programmable_search import google_search

def extract_storage_from_results(results):
    storage = []
    seen = set()
    # common brands to look for
    brands = ['samsung', 'wd', 'seagate', 'crucial', 'kingston', 'toshiba', 'adata', 'sk hynix', 'intel']

    for r in results:
        title = (r.get('title') or '').lower()
        snippet = (r.get('snippet') or '').lower()
        text = title + ' ' + snippet

        # look for SATA SSD or HDD keywords
        if any(k in text for k in ['ssd', 'hdd', 'sata', 'nvme', 'pro', 'evo', 'barracuda']):
            # try to extract brand + model
            for b in brands:
                if b in text:
                    # simple pattern: Brand Model (e.g., Samsung 870 EVO, Seagate Barracuda 4TB)
                    m = re.search(rf'({b})[\\s:-]+([a-z0-9\\-\\s]+?(?:evo|pro|barracuda|mx|mx500|sn\d+|990|980|870|860|7200|barracuda\\s+pro)?)(?:\\s|,|\\.|/|$)', text, re.IGNORECASE)
                    if m:
                        brand = m.group(1).strip().title()
                        model = m.group(2).strip().upper()
                        # normalize model spacing and casing
                        model = ' '.join(model.split())
                        key = f'{brand} {model}'
                        if key.lower() not in seen:
                            seen.add(key.lower())
                            # decide category and generation
                            cat = 'storage'
                            generation = 'SATA' if 'sata' in text or '870' in model or 'mx' in model or 'evo' in model or 'mx500' in model else ('NVMe' if 'nvme' in text or 'sn' in model or '980' in model or '990' in model else 'HDD' if 'hdd' in text or 'barracuda' in model or '7200' in text else 'Unknown')
                            release_year = 2023
                            vram_gb = 0
                            ram_gb = 0
                            # capacity from snippet
                            cap_match = re.search(r'(\d+)\s?(tb|gb)', text)
                            capacity_gb = None
                            if cap_match:
                                num = int(cap_match.group(1))
                                unit = cap_match.group(2)
                                capacity_gb = num * 1024 if unit == 'tb' else num

                            storage.append({
                                "category": cat,
                                "model": f"{brand} {model}",
                                "generation": generation,
                                "release_year": release_year,
                                "brand": brand,
                                "capacity_gb": capacity_gb,
                                "notes": r.get('link') or '',
                            })
    return storage

def search_and_add():
    queries = [
        "latest SATA SSD releases 2024",
        "best HDD 2024 Seagate Barracuda",
        "Samsung 870 EVO latest release",
        "best SATA SSD 2023 2024",
        "WD Blue HDD and SSD models 2024"
    ]

    all_items = []
    API_KEY = "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
    CX = "034784ab1b1404dc2"
    for q in queries:
        try:
            results = google_search(q, API_KEY, CX, num=8)
            if results:
                items = extract_storage_from_results(results)
                all_items.extend(items)
        except Exception as e:
            print("Search failed:", e)

    # dedupe by model
    unique = []
    seen = set()
    for it in all_items:
        key = it['model'].lower()
        if key not in seen:
            seen.add(key)
            unique.append(it)

    if not unique:
        print("No storage items found from search.")
        return

    # add to backend and frontend seed files
    for path in ["backend/data/hardware_seed.json", "frontend/src/data/hardware_seed_frontend.json"]:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = data.get('items', [])
        added = 0
        for it in unique:
            if not any(existing.get('model','').lower() == it['model'].lower() for existing in items):
                # adapt fields for frontend seed format (no capacity_gb standardized)
                entry = {
                    "category": it["category"],
                    "model": it["model"],
                    "generation": it.get("generation"),
                    "release_year": it.get("release_year"),
                    "brand": it.get("brand"),
                    "capacity_gb": it.get("capacity_gb")
                }
                items.append(entry)
                added += 1
        data['items'] = items
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Added {added} storage items to {path}")

if __name__ == "__main__":
    search_and_add()


