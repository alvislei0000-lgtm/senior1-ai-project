#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.benchmark_scraper import BenchmarkScraper


async def main():
    import sys
    s = BenchmarkScraper()
    game = sys.argv[1] if len(sys.argv) > 1 else "Counter-Strike 2"
    resolution = "3840x2160"
    settings = "Ultra"
    gpus = ["RTX 5090", "RTX 5080", "RTX 4090", "RX 7900 XTX"]
    # regenerate v2 (GPU-base) using model reference CPU
    for gpu in gpus:
        print("Refreshing v2 for", gpu)
        refreshed = s._generate_mock_data(
            game=game,
            resolution=resolution,
            gpu={"category": "gpu", "model": gpu},
            cpu={"category": "cpu", "model": s.CPU_REF_MODEL},
            settings=settings,
        )
        # write to v2
        from app.db import benchmark_store_v2, benchmark_store
        await benchmark_store_v2.upsert(game=game, resolution=resolution, settings=settings, gpu=gpu, value={
            "avg_fps": refreshed.get("avg_fps"),
            "p1_low": refreshed.get("p1_low"),
            "p0_1_low": refreshed.get("p0_1_low"),
            "notes": refreshed.get("notes"),
            "raw_snippet": refreshed.get("raw_snippet"),
            "source": "Predicted Model",
            "cpu_ref": s.CPU_REF_MODEL,
            "model_version": s.MODEL_VERSION,
        })
        # also write v1 CPU-adjusted for common CPUs to avoid mismatch
        for cpu in ["Intel Core i9-14900K", "Intel Core i9-13900K", "Ryzen 9 9950X", "Ryzen 9 7950X", "Intel Core i7-14700K"]:
            adjusted = s._apply_cpu_adjustment(
                fps_data={**refreshed, "game": game, "resolution": resolution, "settings": settings, "gpu": gpu},
                game=game,
                cpu_model=cpu,
            )
            await benchmark_store.upsert(game=game, resolution=resolution, settings=settings, gpu=gpu, cpu=cpu, value={
                "avg_fps": adjusted.get("avg_fps"),
                "p1_low": adjusted.get("p1_low"),
                "p0_1_low": adjusted.get("p0_1_low"),
                "notes": adjusted.get("notes"),
                "raw_snippet": adjusted.get("raw_snippet"),
                "source": "Predicted Model",
                "model_version": s.MODEL_VERSION,
            })
    print("Refreshed v2 and v1 for game", game)


if __name__ == "__main__":
    asyncio.run(main())

