#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict


BASE = Path(__file__).resolve().parents[1]
SEED_PATH = BASE / "data" / "hardware_seed.json"
OVR_PATH = BASE / "data" / "hw_performance_override.json"
OUT_NEW = BASE / "data" / "hw_overrides_expanded.json"


def load_json(p: Path) -> Dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def find_best_match(model: str, existing: Dict[str, float]) -> float | None:
    m = model.lower()
    # exact substring match
    for k, v in existing.items():
        if k.lower() in m or m in k.lower():
            return float(v)
    # numeric model match (e.g., 5090, 4080)
    nums = re.findall(r"\d{3,4}", model)
    if nums:
        for num in nums:
            for k, v in existing.items():
                if num in k:
                    return float(v)
    return None


def main():
    seed = load_json(SEED_PATH)
    overrides = load_json(OVR_PATH) or {"gpus": {}, "cpus": {}}
    items = seed.get("items") or []

    added = {"gpus": {}, "cpus": {}}
    for it in items:
        if not isinstance(it, dict):
            continue
        cat = (it.get("category") or "").lower()
        model = str(it.get("model") or "").strip()
        if not model:
            continue
        if cat == "gpu":
            if model in overrides.get("gpus", {}):
                continue
            match = find_best_match(model, overrides.get("gpus", {}))
            val = float(match) if match is not None else 1.0
            overrides.setdefault("gpus", {})[model] = round(val, 3)
            added["gpus"][model] = overrides["gpus"][model]
        elif cat == "cpu":
            if model in overrides.get("cpus", {}):
                continue
            match = find_best_match(model, overrides.get("cpus", {}))
            val = float(match) if match is not None else 1.0
            overrides.setdefault("cpus", {})[model] = round(val, 3)
            added["cpus"][model] = overrides["cpus"][model]

    # backup and write
    backup = OVR_PATH.with_suffix(".seed_expanded.backup.json")
    try:
        if OVR_PATH.exists():
            backup.write_text(json.dumps(load_json(OVR_PATH), ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    OVR_PATH.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_NEW.write_text(json.dumps({"added": added}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("expanded overrides written to", OVR_PATH)
    print("added count gpus:", len(added["gpus"]), "cpus:", len(added["cpus"]))


if __name__ == "__main__":
    main()

