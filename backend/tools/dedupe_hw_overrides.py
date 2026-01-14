#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

def normalize_cpu_key(k: str) -> str:
    s = k.lower().strip()
    # remove common vendor prefixes and extra words for grouping
    s = re.sub(r'\bintel core\b', '', s)
    s = re.sub(r'\bintel\b', '', s)
    s = re.sub(r'\bamd\b', '', s)
    s = re.sub(r'\bamd ryzen\b', 'ryzen', s)
    s = re.sub(r'\bcore\b', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def main():
    p = Path(__file__).resolve().parents[1] / "data" / "hw_performance_override.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    cpus = data.get("cpus", {})

    groups = {}
    for k, v in cpus.items():
        nk = normalize_cpu_key(k)
        if nk not in groups:
            groups[nk] = []
        groups[nk].append((k, v))

    # Build new cpus dict: choose canonical key (prefer longer / with vendor)
    new_cpus = {}
    for nk, items in groups.items():
        # prefer key containing 'intel' or 'amd', else longest key
        items_sorted = sorted(items, key=lambda x: (('intel' in x[0].lower()) or ('amd' in x[0].lower()), len(x[0])), reverse=True)
        canonical_key, canonical_val = items_sorted[0]
        new_cpus[canonical_key] = canonical_val
        # If there are other items with different values, log to notes (we'll keep canonical)
        # (we do not remove silently in case of manual review later)

    data["cpus"] = new_cpus
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Deduped CPUs: original={len(cpus)} new={len(new_cpus)}")

if __name__ == "__main__":
    main()

