#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

BASE = Path(__file__).resolve().parents[1]
CAND = BASE / "data" / "hw_userbenchmark_candidates.json"
OVR = BASE / "data" / "hw_performance_override.json"
OUT = BASE / "data" / "hw_performance_normalized.json"


def load(p: Path):
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


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
    cpu_means: Dict[str, float] = cand.get("cpu_means", {})
    overrides = load(OVR) or {"gpus": {}, "cpus": {}}

    # determine ranges
    g_vals = list(gpu_means.values()) or [1.0]
    c_vals = list(cpu_means.values()) or [1.0]
    g_min, g_max = min(g_vals), max(g_vals)
    c_min, c_max = min(c_vals), max(c_vals)

    # target multiplier ranges (narrowed to reduce inversions/noise)
    # Adjusted per user request to shrink GPU range and avoid extreme multipliers
    GPU_MIN, GPU_MAX = 1.0, 2.6
    CPU_MIN, CPU_MAX = 0.8, 2.6

    new = {"gpus": dict(overrides.get("gpus", {})), "cpus": dict(overrides.get("cpus", {}))}

    for g, mean in gpu_means.items():
        try:
            m = float(mean)
        except Exception:
            continue
        val = round(linear_map(m, g_min, g_max, GPU_MIN, GPU_MAX), 3)
        new["gpus"][g] = val

    for c, mean in cpu_means.items():
        try:
            m = float(mean)
        except Exception:
            continue
        val = round(linear_map(m, c_min, c_max, CPU_MIN, CPU_MAX), 3)
        new["cpus"][c] = val

    # write normalized overrides (backup existing)
    try:
        if OVR.exists():
            (OVR.with_suffix(".normalized.backup.json")).write_text(OVR.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

    OVR.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT.write_text(json.dumps({"normalized": True, "gpu_min": g_min, "gpu_max": g_max, "cpu_min": c_min, "cpu_max": c_max}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Normalized overrides written to", OVR)
    print("Summary written to", OUT)


if __name__ == "__main__":
    main()

