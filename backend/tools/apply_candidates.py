#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


BASE = Path(__file__).resolve().parents[1]
CAND_PATH = BASE / "data" / "hw_userbenchmark_candidates.json"
OVR_PATH = BASE / "data" / "hw_performance_override.json"


def load_json(p: Path) -> Dict[str, Any]:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    cand = load_json(CAND_PATH)
    if not cand:
        print("No candidates found:", CAND_PATH)
        return

    gpu_means = cand.get("gpu_means", {})
    cpu_means = cand.get("cpu_means", {})
    overrides = load_json(OVR_PATH) or {"gpus": {}, "cpus": {}}

    # pick reference keys
    ref_gpu = "RTX 5090" if "RTX 5090" in overrides.get("gpus", {}) else next(iter(overrides.get("gpus", {})), None)
    ref_cpu = "i9-14900K" if "i9-14900K" in overrides.get("cpus", {}) else next(iter(overrides.get("cpus", {})), None)

    if not ref_gpu or ref_gpu not in overrides.get("gpus", {}):
        print("No GPU reference found in overrides; abort")
        return
    if not ref_cpu or ref_cpu not in overrides.get("cpus", {}):
        print("No CPU reference found in overrides; abort")
        return

    ref_gpu_val = float(overrides["gpus"][ref_gpu])
    ref_gpu_mean = float(gpu_means.get(ref_gpu, 1.0))
    gpu_scale = ref_gpu_val / ref_gpu_mean if ref_gpu_mean else 1.0

    ref_cpu_val = float(overrides["cpus"][ref_cpu])
    ref_cpu_mean = float(cpu_means.get(ref_cpu, 1.0))
    cpu_scale = ref_cpu_val / ref_cpu_mean if ref_cpu_mean else 1.0

    new_overrides = {"gpus": dict(overrides.get("gpus", {})), "cpus": dict(overrides.get("cpus", {}))}

    # update GPUs
    for g, mean in gpu_means.items():
        try:
            meanf = float(mean)
        except Exception:
            continue
        new_val = round(meanf * gpu_scale, 3)
        new_overrides["gpus"][g] = new_val

    # update CPUs
    for c, mean in cpu_means.items():
        try:
            meanf = float(mean)
        except Exception:
            continue
        new_val = round(meanf * cpu_scale, 3)
        new_overrides["cpus"][c] = new_val

    # write candidate file and backup old overrides
    try:
        old = load_json(OVR_PATH)
    except Exception:
        old = {}

    cand_out = BASE / "data" / "hw_userbenchmark_applied.json"
    cand_out.write_text(json.dumps({"old": old, "new": new_overrides, "ref": {"ref_gpu": ref_gpu, "ref_cpu": ref_cpu}}, ensure_ascii=False, indent=2), encoding="utf-8")

    # backup existing overrides
    backup_path = OVR_PATH.with_suffix(".backup.json")
    try:
        if OVR_PATH.exists():
            backup_path.write_text(json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    # overwrite overrides file
    OVR_PATH.write_text(json.dumps(new_overrides, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE new overrides to", OVR_PATH)
    print("Also saved comparison to", cand_out, "and backup to", backup_path)


if __name__ == "__main__":
    main()

