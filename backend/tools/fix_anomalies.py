#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.benchmark_scraper import BenchmarkScraper
from app.db import benchmark_store, benchmark_store_v2


async def main():
    s = BenchmarkScraper()
    report = json.load(open("data/anomaly_report.json", "r", encoding="utf-8"))
    anomalies = report.get("anomalies", [])
    fixed = 0
    for a in anomalies:
        combo = a.get("combo")
        if not combo:
            continue
        game, res, settings, cpu = combo
        # find GPUs currently present in cache for this combo
        # we'll regenerate for common GPUs list from overrides
        with open("data/hw_performance_override.json", "r", encoding="utf-8") as f:
            overrides = json.load(f)
        gpus = list(overrides.get("gpus", {}).keys())
        for gpu in gpus:
            try:
                refreshed = s._generate_mock_data(
                    game=game,
                    resolution=res,
                    gpu={"category": "gpu", "model": gpu},
                    cpu={"category": "cpu", "model": s.CPU_REF_MODEL},
                    settings=settings,
                )
                await benchmark_store_v2.upsert(game=game, resolution=res, settings=settings, gpu=gpu, value={
                    "avg_fps": refreshed.get("avg_fps"),
                    "p1_low": refreshed.get("p1_low"),
                    "p0_1_low": refreshed.get("p0_1_low"),
                    "notes": refreshed.get("notes"),
                    "raw_snippet": refreshed.get("raw_snippet"),
                    "source": "Predicted Model",
                    "cpu_ref": s.CPU_REF_MODEL,
                    "model_version": s.MODEL_VERSION,
                })
                adjusted = s._apply_cpu_adjustment(
                    fps_data={**refreshed, "game": game, "resolution": res, "settings": settings, "gpu": gpu},
                    game=game,
                    cpu_model=cpu,
                )
                await benchmark_store.upsert(game=game, resolution=res, settings=settings, gpu=gpu, cpu=cpu, value={
                    "avg_fps": adjusted.get("avg_fps"),
                    "p1_low": adjusted.get("p1_low"),
                    "p0_1_low": adjusted.get("p0_1_low"),
                    "notes": adjusted.get("notes"),
                    "raw_snippet": adjusted.get("raw_snippet"),
                    "source": "Predicted Model",
                    "model_version": s.MODEL_VERSION,
                })
                fixed += 1
            except Exception:
                continue
    print("Attempted fixes for anomaly items:", fixed)


if __name__ == "__main__":
    asyncio.run(main())

