#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

BASE = Path(__file__).resolve().parents[1]
OVR = BASE / "data" / "hw_performance_override.json"
BACKUP = BASE / "data" / "hw_performance_override.backup.json"


def load(p: Path) -> Dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def parse_numeric(model: str) -> Tuple[int, int]:
    """
    Try to extract primary numeric series from model (e.g., 'RTX 5090' -> (5090, 0))
    Return (major, minor) where minor captures suffix strength (Ti/XTX etc) heuristically.
    """
    s = model.upper()
    m = re.search(r'(\d{3,4})', s)
    major = int(m.group(1)) if m else 0
    minor = 0
    # heuristics for suffix strength
    if 'XTX' in s or 'TI' in s or 'SUPER' in s or '3D' in s:
        minor += 2
    if 'XT' in s and 'XTX' not in s:
        minor += 1
    if 'MAX' in s or 'ULTRA' in s:
        minor += 3
    return major, minor


def find_inversions(gpu_map: Dict[str, float]) -> List[str]:
    items = list(gpu_map.items())
    anomalies = []
    # compare each pair where numeric parsed exists
    parsed = [(k, v, *parse_numeric(k)) for k, v in items]
    # for each pair with same brand prefix (RTX/RX/GTX/Integrated/Arc), check inversion
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            k1, v1, m1, s1 = parsed[i]
            k2, v2, m2, s2 = parsed[j]
            if m1 == 0 or m2 == 0:
                continue
            # expected: higher major+minor -> higher multiplier
            score1 = m1 * 10 + s1
            score2 = m2 * 10 + s2
            if score1 > score2 and v1 + 0.001 < v2:
                anomalies.append(f"Inversion: {k1} ({v1}) > {k2} ({v2}) but model rank {score1}>{score2}")
            if score2 > score1 and v2 + 0.001 < v1:
                anomalies.append(f"Inversion: {k2} ({v2}) > {k1} ({v1}) but model rank {score2}>{score1}")
    return anomalies


def find_close_values(gpu_map: Dict[str, float], thresh: float = 0.01) -> List[str]:
    items = sorted(gpu_map.items(), key=lambda x: x[1], reverse=True)
    close = []
    for i in range(len(items) - 1):
        a, av = items[i]
        b, bv = items[i + 1]
        if abs(av - bv) <= thresh:
            close.append(f"Very close: {a}={av} vs {b}={bv} (diff {round(abs(av-bv),6)})")
    return close


def top_changes(current: Dict[str, float], backup: Dict[str, float], top_n: int = 20) -> List[str]:
    changes = []
    for k, v in current.items():
        old = backup.get(k)
        if old is None:
            continue
        diff = v - old
        rel = diff / old if old else float('inf')
        changes.append((abs(rel), k, old, v, diff, rel))
    changes.sort(reverse=True)
    lines = []
    for rel_abs, k, old, v, diff, rel in changes[:top_n]:
        lines.append(f"{k}: old={old} new={v} diff={round(diff,3)} rel={round(rel*100,2)}%")
    return lines


def main():
    data = load(OVR)
    if not data:
        print("No override file found at", OVR)
        return
    gpu_map = data.get("gpus", {}) or {}
    cpu_map = data.get("cpus", {}) or {}
    backup = load(BACKUP) or {}
    backup_gpus = backup.get("gpus", {}) if isinstance(backup, dict) else {}

    print("GPU count:", len(gpu_map), "CPU count:", len(cpu_map))
    print("--- GPU inversions (numeric heuristic) ---")
    inv = find_inversions(gpu_map)
    if inv:
        for l in inv[:50]:
            print(l)
    else:
        print("No numeric inversions found.")

    print("--- GPUs with very close multipliers (<=0.01) ---")
    for l in find_close_values(gpu_map, thresh=0.01)[:50]:
        print(l)

    print("--- Top multiplier changes vs backup ---")
    for l in top_changes(gpu_map, backup_gpus, top_n=50):
        print(l)

    # report some top/bottom GPUs
    sorted_g = sorted(gpu_map.items(), key=lambda x: x[1], reverse=True)
    print("--- Top 10 GPUs by multiplier ---")
    for k, v in sorted_g[:10]:
        print(f"{k}: {v}")
    print("--- Bottom 10 GPUs by multiplier ---")
    for k, v in sorted_g[-10:]:
        print(f"{k}: {v}")

    # quick recommendation
    print("\nRecommendation:")
    print(" - If many GPUs are very close or inversions appear, consider reducing normalization range or using log scaling.")
    print(" - For immediate fix: revert to backup and re-run normalization with narrower target ranges (e.g., GPU_MAX=2.6 GPU_MIN=1.0).")


if __name__ == "__main__":
    main()

