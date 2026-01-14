#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
import re

BASE = Path(__file__).resolve().parents[1]
CAND = BASE / "data" / "hw_userbenchmark_candidates.json"
OVR = BASE / "data" / "hw_performance_override.json"
OUT = BASE / "data" / "hw_performance_normalized_grouped.json"


def load(p: Path):
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def detect_group(model: str) -> str:
    m = model.lower()
    if "rtx" in m or "gtx" in m or "nvidia" in m:
        return "nvidia"
    if m.startswith("rx") or "radeon" in m or "amd" in m:
        return "amd"
    if "arc" in m:
        return "intel_arc"
    if "integrated" in m or "uhd" in m:
        return "integrated"
    return "other"


def linear_map(x, in_min, in_max, out_min, out_max):
    if in_max <= in_min:
        return (out_min + out_max) / 2.0
    return out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min)


def main():
    cand = load(CAND)
    if not cand:
        print("No candidates file", CAND)
        return
    gpu_means: Dict[str, float] = cand.get("gpu_means", {})
    overrides = load(OVR) or {"gpus": {}, "cpus": {}}

    # group models
    groups: Dict[str, Dict[str, float]] = {}
    for g, mean in gpu_means.items():
        grp = detect_group(g)
        groups.setdefault(grp, {})[g] = float(mean)

    # define per-group target ranges (conservative, tuned)
    group_ranges = {
        "nvidia": (1.4, 2.6),
        "amd": (1.2, 2.4),
        "intel_arc": (1.0, 1.9),
        "integrated": (0.8, 1.1),
        "other": (1.0, 1.6),
    }

    new_gpus = dict(overrides.get("gpus", {}))

    # map each group separately
    for grp, items in groups.items():
        vals = list(items.values())
        vmin, vmax = min(vals), max(vals)
        out_min, out_max = group_ranges.get(grp, group_ranges["other"])
        for model, mean in items.items():
            mapped = round(linear_map(mean, vmin, vmax, out_min, out_max), 3) if vmax > vmin else round((out_min + out_max) / 2.0, 3)
            new_gpus[model] = mapped

    # keep existing CPU overrides unchanged (we're only adjusting GPUs here)
    new = {"gpus": new_gpus, "cpus": dict(overrides.get("cpus", {}))}

    # backup existing and write
    try:
        if OVR.exists():
            (OVR.with_suffix(".grouped.normalized.backup.json")).write_text(OVR.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

    OVR.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT.write_text(json.dumps({"normalized_grouped": True, "groups": list(groups.keys())}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Grouped normalized overrides written to", OVR)
    print("Summary written to", OUT)


if __name__ == "__main__":
    main()

