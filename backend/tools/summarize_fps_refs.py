#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_refs(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return json.loads(p.read_text(encoding="utf-8"))


def summarize(refs: Dict[str, Any]) -> Dict[str, Any]:
    items = refs.get("items", {})
    gpu_stats: Dict[str, list[float]] = {}
    cpu_stats: Dict[str, list[float]] = {}
    combo_stats: Dict[str, list[float]] = {}
    per_game: Dict[str, list[Dict[str, Any]]] = {}

    for k, v in items.items():
        try:
            avg = v.get("avg_fps")
            if avg is None:
                continue
            avg = float(avg)
        except Exception:
            continue
        g = v.get("gpu") or "unknown"
        c = v.get("cpu") or "unknown"
        game = v.get("game") or "unknown"
        gpu_stats.setdefault(g, []).append(avg)
        cpu_stats.setdefault(c, []).append(avg)
        combo_stats.setdefault(f"{g}||{c}", []).append(avg)
        per_game.setdefault(game, []).append({"gpu": g, "cpu": c, "resolution": v.get("resolution"), "settings": v.get("settings"), "avg_fps": avg, "source": v.get("source")})

    def stats(d: Dict[str, list[float]]):
        out = {}
        for k, vals in d.items():
            vals_sorted = sorted(vals)
            n = len(vals)
            out[k] = {
                "count": n,
                "mean": round(sum(vals) / n, 1) if n else None,
                "min": round(min(vals), 1) if n else None,
                "max": round(max(vals), 1) if n else None,
                "median": round(vals_sorted[n // 2], 1) if n else None,
            }
        return out

    summary = {
        "gpu_stats": stats(gpu_stats),
        "cpu_stats": stats(cpu_stats),
        "combo_count": len(combo_stats),
        "per_game_samples": {k: sorted(v, key=lambda x: x["avg_fps"], reverse=True)[:5] for k, v in per_game.items()},
    }
    return summary


def main():
    base = Path(__file__).resolve().parents[1] / "data"
    refs_path = base / "google_fps_refs.json"
    out_path = base / "google_fps_summary.json"
    refs = load_refs(str(refs_path))
    summary = summarize(refs)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out_path)


if __name__ == "__main__":
    main()

