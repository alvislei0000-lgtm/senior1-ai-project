from __future__ import annotations

import asyncio

from app.db.benchmark_store_v2 import benchmark_store_v2
from app.scrapers.benchmark_scraper import BenchmarkScraper


async def main() -> None:
    """
    冒煙測試：
    - v2 cache 可讀
    - _fetch_benchmark_combo 可跑通
    - 回傳 notes 內含 GPU/CPU/RAM
    - v2 的 Predicted Model 可補上/升級 model_version（若原本缺失或舊版）
    """
    game = "Minecraft"
    res = "1280x720"
    st = "Low"
    gpu = "RTX 5090"

    v0 = await benchmark_store_v2.get(game, res, st, gpu)
    print("before_mv:", (v0 or {}).get("model_version"))

    s = BenchmarkScraper()
    out = await s._fetch_benchmark_combo(
        game=game,
        resolution=res,
        settings=st,
        gpu={"category": "gpu", "model": gpu},
        cpu={"category": "cpu", "model": "Intel i9-13900K"},
    )
    print("out_avg:", (out or {}).get("avg_fps"), "out_p1:", (out or {}).get("p1_low"))
    print("usage_in_notes:", ("GPU:" in ((out or {}).get("notes") or "")))

    v1 = await benchmark_store_v2.get(game, res, st, gpu)
    print("after_mv:", (v1 or {}).get("model_version"), "v2_avg:", (v1 or {}).get("avg_fps"))


if __name__ == "__main__":
    asyncio.run(main())


