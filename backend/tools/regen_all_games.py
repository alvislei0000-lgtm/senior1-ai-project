#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.benchmark_scraper import BenchmarkScraper
from app.db import benchmark_store_v2, benchmark_store


async def main():
    s = BenchmarkScraper()
    # load GPUs from overrides
    with open("data/hw_performance_override.json", "r", encoding="utf-8") as f:
        overrides = json.load(f)
    gpus = list((overrides.get("gpus") or {}).keys())

    # games: use popular list
    from app.data.game_requirements import GAME_REQUIREMENTS_25
    games = list(GAME_REQUIREMENTS_25.keys())

    cpus_to_write = ["Intel Core i9-14900K", "Intel Core i9-13900K", "Ryzen 9 9950X"]

    total = 0
    for game in games:
        resolution = "3840x2160"
        settings = "Ultra"
        for gpu in gpus:
            total += 1
    print(f"Will refresh approx {total} combos (this may take a while).")

    count = 0
    for game in games:
        for gpu in gpus:
            try:
                refreshed = s._generate_mock_data(
                    game=game,
                    resolution="3840x2160",
                    gpu={"category": "gpu", "model": gpu},
                    cpu={"category": "cpu", "model": s.CPU_REF_MODEL},
                    settings="Ultra",
                )
                await benchmark_store_v2.upsert(game=game, resolution="3840x2160", settings="Ultra", gpu=gpu, value={
                    "avg_fps": refreshed.get("avg_fps"),
                    "p1_low": refreshed.get("p1_low"),
                    "p0_1_low": refreshed.get("p0_1_low"),
                    "notes": refreshed.get("notes"),
                    "raw_snippet": refreshed.get("raw_snippet"),
                    "source": "Predicted Model",
                    "cpu_ref": s.CPU_REF_MODEL,
                    "model_version": s.MODEL_VERSION,
                })
                for cpu in cpus_to_write:
                    adjusted = s._apply_cpu_adjustment(
                        fps_data={**refreshed, "game": game, "resolution": "3840x2160", "settings": "Ultra", "gpu": gpu},
                        game=game,
                        cpu_model=cpu,
                    )
                    await benchmark_store.upsert(game=game, resolution="3840x2160", settings="Ultra", gpu=gpu, cpu=cpu, value={
                        "avg_fps": adjusted.get("avg_fps"),
                        "p1_low": adjusted.get("p1_low"),
                        "p0_1_low": adjusted.get("p0_1_low"),
                        "notes": adjusted.get("notes"),
                        "raw_snippet": adjusted.get("raw_snippet"),
                        "source": "Predicted Model",
                        "model_version": s.MODEL_VERSION,
                    })
                count += 1
                if count % 50 == 0:
                    print(f"Refreshed {count} combos...")
            except Exception as e:
                print("Error refreshing", game, gpu, e)
    print("Done. Refreshed:", count)


if __name__ == "__main__":
    asyncio.run(main())

