#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

BASE = Path(__file__).resolve().parents[1]
CAND = BASE / "data" / "hw_userbenchmark_candidates.json"
OVR = BASE / "data" / "hw_performance_override.json"
BACKUP = BASE / "data" / "hw_performance_override.backup.json"
OUT = BASE / "data" / "hw_performance_normalized_grouped_piecewise.json"


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


def piecewise_map(value: float, breaks: List[float], ranges: List[Tuple[float, float]]) -> float:
    """
    Map value into piecewise linear ranges defined by breaks and output ranges.
    breaks: sorted ascending input breakpoints [b0, b1, b2] (min..max)
    ranges: list of (out_min, out_max) for each segment (len == len(breaks)-1)
    """
    if value <= breaks[0]:
        return ranges[0][0]
    for i in range(len(breaks) - 1):
        lo, hi = breaks[i], breaks[i + 1]
        out_lo, out_hi = ranges[i]
        if lo <= value <= hi:
            # linear interpolate
            t = (value - lo) / (hi - lo) if hi > lo else 0.5
            return out_lo + t * (out_hi - out_lo)
    return ranges[-1][1]


def smooth_values(sorted_items: List[Tuple[str, float]], window: int = 3) -> Dict[str, float]:
    """
    Apply simple moving average smoothing to mapped multipliers to reduce discrete ties.
    """
    names = [n for n, v in sorted_items]
    vals = [v for n, v in sorted_items]
    smoothed = []
    n = len(vals)
    for i in range(n):
        lo = max(0, i - window // 2)
        hi = min(n, i + window // 2 + 1)
        smoothed.append(sum(vals[lo:hi]) / max(1, hi - lo))
    return {names[i]: round(smoothed[i], 3) for i in range(n)}


def main():
    cand = load(CAND)
    if not cand:
        print("No candidates file", CAND)
        return
    gpu_means: Dict[str, float] = cand.get("gpu_means", {}) or {}
    overrides = load(OVR) or {"gpus": {}, "cpus": {}}
    backup = load(BACKUP) or {"gpus": {}, "cpus": {}}

    groups: Dict[str, Dict[str, float]] = {}
    for g, mean in gpu_means.items():
        grp = detect_group(g)
        groups.setdefault(grp, {})[g] = float(mean)

    # define per-group piecewise ranges (in log-space input)
    group_output_ranges = {
        "nvidia": (1.3, 1.8, 2.15, 2.6),  # broken into 3 segments
        "amd": (1.2, 1.7, 2.05, 2.45),
        "intel_arc": (1.0, 1.4, 1.65, 1.9),
        "integrated": (0.8, 0.9, 0.98, 1.05),
        "other": (1.0, 1.25, 1.4, 1.6),
    }

    new_gpus = dict(overrides.get("gpus", {}))

    for grp, items in groups.items():
        vals = list(items.values())
        if not vals:
            continue
        # operate in log10 space
        log_vals = {k: math.log10(v) if v > 0 else 0.0 for k, v in items.items()}
        sorted_pairs = sorted(log_vals.items(), key=lambda x: x[1])
        logs = [v for k, v in sorted_pairs]
        # create 4 breakpoints (min, 33pct, 66pct, max)
        n = len(logs)
        b0 = logs[0]
        b1 = logs[max(0, n // 3 - 1)]
        b2 = logs[min(n - 1, 2 * n // 3)]
        b3 = logs[-1]
        breaks = [b0, b1, b2, b3]
        out_vals = group_output_ranges.get(grp, group_output_ranges["other"])
        # define ranges per segment
        ranges = [(out_vals[0], out_vals[1]), (out_vals[1], out_vals[2]), (out_vals[2], out_vals[3])]

        mapped = {}
        for model, logv in sorted_pairs:
            mapped_val = piecewise_map(logv, breaks, ranges)
            mapped[model] = mapped_val

        # smooth mapped values to reduce exact ties
        ordered = sorted(mapped.items(), key=lambda x: x[1])
        smoothed = smooth_values(ordered, window=3)
        for k, v in smoothed.items():
            new_gpus[k] = round(v, 3)

    # manual micro-adjust key models from backup to ensure top ranks correct
    manual_gpu_models = [
        "RTX 5090", "RTX 5080", "RTX 4090", "RTX 4080", "RX 7900 XTX", "RX 7900 XT"
    ]
    for m in manual_gpu_models:
        if m in backup.get("gpus", {}):
            new_gpus[m] = backup["gpus"][m]

    new = {"gpus": new_gpus, "cpus": dict(overrides.get("cpus", {}))}

    # backup current overrides and write
    try:
        if OVR.exists():
            (OVR.with_suffix(".grouped_piecewise.normalized.backup.json")).write_text(OVR.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

    OVR.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT.write_text(json.dumps({"grouped_piecewise": True, "groups": list(groups.keys())}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Grouped+piecewise normalized overrides written to", OVR)
    print("Summary written to", OUT)


if __name__ == "__main__":
    main()

