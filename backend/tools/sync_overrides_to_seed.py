#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

BASE = Path(__file__).resolve().parents[1]
OVR = BASE / "data" / "hw_performance_override.json"
SEED = BASE / "data" / "hardware_seed.json"


def load(p: Path) -> Dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def infer_brand_from_model(model: str) -> str:
    m = model.lower()
    if "rtx" in m or "gtx" in m or "nvidia" in m:
        return "NVIDIA"
    if "rx" in m or "radeon" in m or "amd" in m:
        return "AMD"
    if "intel" in m or "arc" in m:
        return "Intel"
    return ""


def ensure_entry(seed: Dict, category: str, model: str):
    items = seed.setdefault("items", [])
    for it in items:
        if isinstance(it, dict) and (it.get("model") or "").strip().lower() == model.strip().lower():
            return False
    entry = {
        "category": category,
        "model": model,
        "generation": None,
        "release_year": None,
        "brand": infer_brand_from_model(model),
    }
    items.append(entry)
    return True


def main():
    overrides = load(OVR)
    if not overrides:
        print("No overrides file found.")
        return
    seed = load(SEED) or {"items": []}
    gpus = overrides.get("gpus", {}) or {}
    cpus = overrides.get("cpus", {}) or {}
    added = {"gpu": [], "cpu": []}
    for g in gpus.keys():
        if ensure_entry(seed, "gpu", g):
            added["gpu"].append(g)
    for c in cpus.keys():
        if ensure_entry(seed, "cpu", c):
            added["cpu"].append(c)

    SEED.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Added GPUs:", len(added["gpu"]), "Added CPUs:", len(added["cpu"]))
    if added["gpu"] or added["cpu"]:
        print("Sample added GPU:", added["gpu"][:5])
        print("Sample added CPU:", added["cpu"][:5])


if __name__ == "__main__":
    main()

