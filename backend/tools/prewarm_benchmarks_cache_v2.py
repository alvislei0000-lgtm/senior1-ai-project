from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

# 讓 tools/ 可以 import backend/app/*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.benchmark_scraper import BenchmarkScraper  # noqa: E402
from app.data.game_requirements import POPULAR_GAMES_25  # noqa: E402
from app.db.benchmark_store_v2 import benchmark_store_v2  # noqa: E402


RESOLUTIONS = ["1280x720", "1920x1080", "2560x1440", "3840x2160"]
SETTINGS = ["Low", "Medium", "High", "Ultra"]


async def main() -> None:
    # 讀 GPU 清單：從 seed items 取 category=gpu
    seed_path = Path(__file__).resolve().parents[1] / "data" / "hardware_seed.json"
    data = {}
    try:
        data = __import__("json").loads(seed_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    gpus = [it.get("model") for it in (data.get("items") or []) if (it or {}).get("category") == "gpu" and it.get("model")]
    gpus = list(dict.fromkeys(gpus))  # unique, keep order

    total = len(gpus) * len(POPULAR_GAMES_25) * len(RESOLUTIONS) * len(SETTINGS)
    print(f"Prewarm v2 cache: gpu={len(gpus)}, games={len(POPULAR_GAMES_25)}, resolutions={len(RESOLUTIONS)}, settings={len(SETTINGS)}, total~{total}")

    async with httpx.AsyncClient() as client:
        scraper = BenchmarkScraper()
        scraper.client = client  # 讓 Google service 可用同一個 client

        done = 0
        for gpu in gpus:
            batch_records = []
            for game in POPULAR_GAMES_25:
                for res in RESOLUTIONS:
                    for st in SETTINGS:
                        # v2 用 GPU-base：CPU 用 reference
                        payload = scraper._generate_mock_data(
                            game=game,
                            resolution=res,
                            gpu={"category": "gpu", "model": gpu, "selected_vram_gb": None},
                            cpu={"category": "cpu", "model": "Intel Core i5-12600K"},
                            settings=st,
                        )
                        batch_records.append(
                            {
                                "game": game,
                                "resolution": res,
                                "settings": st,
                                "gpu": gpu,
                                "value": {
                                    "avg_fps": payload.get("avg_fps"),
                                    "p1_low": payload.get("p1_low"),
                                    "p0_1_low": payload.get("p0_1_low"),
                                    "notes": payload.get("notes"),
                                    "raw_snippet": payload.get("raw_snippet"),
                                    "source": "Predicted Model",
                                    "cpu_ref": "i5-12600K",
                                    "model_version": getattr(BenchmarkScraper, "MODEL_VERSION", None),
                                },
                            }
                        )
                        done += 1

            await benchmark_store_v2.bulk_upsert(batch_records)
            print(f"Done GPU: {gpu} ({done}/{total})")

    out = Path(__file__).resolve().parents[1] / "data" / "benchmarks_cache_v2.json"
    print(f"Completed: wrote {out} (items={done})")


if __name__ == "__main__":
    asyncio.run(main())


