#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

def classify_cpu(name: str) -> str:
    n = name.lower()
    if "ryzen" in n:
        return "AMD Ryzen"
    if "ultra" in n or "core ultra" in n:
        return "Intel Core Ultra"
    if "intel" in n or "core" in n:
        return "Intel Core"
    return "Other CPU"

def classify_gpu(name: str) -> str:
    n = name.lower()
    if "rtx" in n:
        return "NVIDIA RTX"
    if "gtx" in n:
        return "NVIDIA GTX"
    if "rx" in n or "radeon" in n:
        return "AMD RX"
    if "arc" in n:
        return "Intel Arc"
    return "Other GPU"

def normalize_cpu_key(k: str) -> str:
    s = k.strip()
    # unify spacing, remove duplicate vendor tokens
    s = re.sub(r'\s+', ' ', s)
    return s

def main():
    base = Path(__file__).resolve().parents[1]
    p = base / "data" / "hw_performance_override.json"
    out = base / "data" / "hw_classification_report.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    cpus = data.get("cpus", {})
    gpus = data.get("gpus", {})

    cpu_groups = {}
    for k,v in cpus.items():
        cat = classify_cpu(k)
        cpu_groups.setdefault(cat, []).append({"key": normalize_cpu_key(k), "score": v})

    gpu_groups = {}
    for k,v in gpus.items():
        cat = classify_gpu(k)
        gpu_groups.setdefault(cat, []).append({"key": k, "score": v})

    # stats
    report = {
        "cpu_count": len(cpus),
        "gpu_count": len(gpus),
        "cpu_groups": {k: {"count": len(v), "examples": v[:5]} for k,v in cpu_groups.items()},
        "gpu_groups": {k: {"count": len(v), "examples": v[:5]} for k,v in gpu_groups.items()},
    }

    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)

if __name__ == "__main__":
    main()

