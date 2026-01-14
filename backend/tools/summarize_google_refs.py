#!/usr/bin/env python3
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "google_fps_refs.json"
OUT = ROOT / "data" / "google_fps_summary.json"

def main():
    if not P.exists():
        print("no refs file", P)
        return 2
    d = json.loads(P.read_text(encoding="utf-8"))
    rows = d.get("results", [])
    by_gpu = {}
    by_cpu = {}
    by_game_gpu_res = {}
    for r in rows:
        res = r.get("result") or {}
        v = res.get("avg_fps")
        if v is None:
            continue
        gpu = r.get("gpu")
        cpu = r.get("cpu")
        game = r.get("game")
        resn = r.get("resolution")
        by_gpu.setdefault(gpu, []).append(v)
        by_cpu.setdefault(cpu, []).append(v)
        by_game_gpu_res.setdefault((game, gpu, resn), []).append(v)

    out = {
        "by_gpu": {k: {"n": len(v), "median": median(v) if v else None} for k, v in by_gpu.items()},
        "by_cpu": {k: {"n": len(v), "median": median(v) if v else None} for k, v in by_cpu.items()},
        "by_game_gpu_res_samples": {f"{g}||{gpu}||{resn}": {"n": len(v), "median": median(v)} for (g, gpu, resn), v in by_game_gpu_res.items()},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

