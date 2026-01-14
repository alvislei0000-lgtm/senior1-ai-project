#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Dict, List

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.scrapers.benchmark_scraper import BenchmarkScraper

BASE = Path(__file__).resolve().parents[1]
OVR_PATH = BASE / "data" / "hw_performance_override.json"

GAMES = [
    "Apex Legends", "Fortnite", "Cyberpunk 2077", "Elden Ring", "Minecraft",
    "Forza Horizon 5", "Control", "Metro Exodus", "Rust", "Counter-Strike 2"
]
RES = ["1920x1080", "2560x1440"]
SETTINGS = ["High", "Ultra"]


def load_overrides() -> Dict[str, Dict[str, float]]:
    if not OVR_PATH.exists():
        return {"gpus": {}, "cpus": {}}
    return json.loads(OVR_PATH.read_text(encoding="utf-8"))


def save_overrides(d: Dict[str, Dict[str, float]]):
    OVR_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


async def measure_gpu_mean(s: BenchmarkScraper, gpu: str, ref_cpu: str) -> float:
    vals = []
    for game in GAMES:
        for res in RES:
            for st in SETTINGS:
                md = s._generate_mock_data(game=game, resolution=res, gpu={"category": "gpu", "model": gpu}, cpu={"category": "cpu", "model": ref_cpu}, settings=st)
                v = md.get("avg_fps")
                if v is not None:
                    vals.append(float(v))
    return mean(vals) if vals else 0.0


async def measure_cpu_mean(s: BenchmarkScraper, cpu: str, ref_gpu: str) -> float:
    vals = []
    for game in GAMES:
        for res in RES:
            for st in SETTINGS:
                md = s._generate_mock_data(game=game, resolution=res, gpu={"category": "gpu", "model": ref_gpu}, cpu={"category": "cpu", "model": cpu}, settings=st)
                v = md.get("avg_fps")
                if v is not None:
                    vals.append(float(v))
    return mean(vals) if vals else 0.0


async def main():
    s = BenchmarkScraper()
    overrides = load_overrides()
    gpus = list(overrides.get("gpus", {}).keys())
    cpus = list(overrides.get("cpus", {}).keys())

    # measure means
    gpu_means = {}
    for g in gpus:
        gpu_means[g] = await measure_gpu_mean(s, g, "Intel Core i9-14900K")

    cpu_means = {}
    for c in cpus:
        cpu_means[c] = await measure_cpu_mean(s, c, "RTX 5090")

    # detect anomalies: if override order doesn't match measured mean, adjust
    changed = False
    # GPUs
    sorted_by_mean = sorted(gpus, key=lambda x: gpu_means.get(x, 0), reverse=True)
    for rank, name in enumerate(sorted_by_mean):
        measured = gpu_means.get(name, 0)
        current = overrides["gpus"].get(name, None)
        if current is None:
            continue
        # expected relative scale approx measured / baseline_measured_of_3060 (skip baseline derivation)
        # Simple rule: if measured ordering contradicts numeric value ordering, bump numeric to reflect order
    # enforce monotonic: sort overrides by value, then ensure ordering matches measured
    sorted_by_override = sorted(overrides["gpus"].items(), key=lambda x: x[1], reverse=True)
    override_names_order = [k for k, v in sorted_by_override]
    # if orders differ, adjust overrides to match measured ratios
    if override_names_order != sorted_by_mean:
        # build new values proportional to measured means (normalize to RTX 3060 ~1.3 if present else keep scale)
        ref_val = overrides["gpus"].get("RTX 3060", 1.3)
        ref_mean = gpu_means.get("RTX 3060", None) or 100.0
        new_vals = {}
        for name in gpus:
            mm = gpu_means.get(name, 0.0)
            if ref_mean and ref_mean > 0:
                new_vals[name] = max(0.5, round((mm / ref_mean) * ref_val, 3))
            else:
                new_vals[name] = overrides["gpus"][name]
        overrides["gpus"].update(new_vals)
        changed = True

    # CPUs similar
    sorted_by_mean_cpu = sorted(cpus, key=lambda x: cpu_means.get(x, 0), reverse=True)
    sorted_by_override_cpu = sorted(overrides["cpus"].items(), key=lambda x: x[1], reverse=True)
    if [k for k, v in sorted_by_override_cpu] != sorted_by_mean_cpu:
        ref_val = overrides["cpus"].get("i5-12600K", 1.7)
        ref_mean = cpu_means.get("i5-12600K", None) or 100.0
        new_vals = {}
        for name in cpus:
            mm = cpu_means.get(name, 0.0)
            if ref_mean and ref_mean > 0:
                new_vals[name] = max(0.5, round((mm / ref_mean) * ref_val, 3))
            else:
                new_vals[name] = overrides["cpus"][name]
        overrides["cpus"].update(new_vals)
        changed = True

    if changed:
        save_path = BASE / "data" / "hw_userbenchmark_candidates.json"
        save_path.write_text(json.dumps({"overrides": overrides, "gpu_means": gpu_means, "cpu_means": cpu_means}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("wrote candidates to", save_path)
    else:
        print("no changes required")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

