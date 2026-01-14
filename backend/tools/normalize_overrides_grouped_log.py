#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict

BASE = Path(__file__).resolve().parents[1]
CAND = BASE / "data" / "hw_userbenchmark_candidates.json"
OVR = BASE / "data" / "hw_performance_override.json"
BACKUP = BASE / "data" / "hw_performance_override.backup.json"
OUT = BASE / "data" / "hw_performance_normalized_grouped_log.json"


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
    backup = load(BACKUP) or {"gpus": {}, "cpus": {}}

    groups = {}
    for g, mean in gpu_means.items():
        grp = detect_group(g)
        groups.setdefault(grp, {})[g] = float(mean)

    # per-group target ranges (conservative)
    group_ranges = {
        "nvidia": (1.3, 2.6),
        "amd": (1.2, 2.45),
        "intel_arc": (1.0, 1.9),
        "integrated": (0.8, 1.05),
        "other": (1.0, 1.6),
    }

    new_gpus = dict(overrides.get("gpus", {}))

    for grp, items in groups.items():
        vals = list(items.values())
        if not vals:
            continue
        # operate in log-space
        logs = [math.log10(v) if v > 0 else 0.0 for v in vals]
        log_min, log_max = min(logs), max(logs)
        out_min, out_max = group_ranges.get(grp, group_ranges["other"])
        for model, mean in items.items():
            log_mean = math.log10(mean) if mean > 0 else log_min
            mapped = linear_map(log_mean, log_min, log_max, out_min, out_max) if log_max > log_min else (out_min + out_max) / 2.0
            # round to 3 decimals
            new_gpus[model] = round(float(mapped), 3)

    # Manual micro-adjust for key models: use backup values where available to ensure expected ranking
    manual_gpu_models = [
        "RTX 5090", "RTX 5080", "RTX 4090", "RTX 4080", "RX 7900 XTX", "RX 7900 XT", "RTX 5070", "RTX 5060"
    ]
    for m in manual_gpu_models:
        if m in backup.get("gpus", {}):
            new_gpus[m] = backup["gpus"][m]

    # keep CPU overrides but micro-adjust key CPUs
    new_cpus = dict(overrides.get("cpus", {}))
    manual_cpu_models = ["i9-14900K", "i9-13900K", "Ryzen 9 9950X", "Ryzen 9 7950X"]
    for c in manual_cpu_models:
        if c in backup.get("cpus", {}):
            new_cpus[c] = backup["cpus"][c]

    new = {"gpus": new_gpus, "cpus": new_cpus}

    # backup current overrides
    try:
        if OVR.exists():
            (OVR.with_suffix(".grouped_log.normalized.backup.json")).write_text(OVR.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

    OVR.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT.write_text(json.dumps({"grouped_log": True, "groups": list(groups.keys())}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Grouped+log normalized overrides written to", OVR)
    print("Summary written to", OUT)


if __name__ == "__main__":
    main()

