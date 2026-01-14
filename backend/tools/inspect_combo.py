#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.benchmark_scraper import BenchmarkScraper


async def main():
    s = BenchmarkScraper()
    combos = [
        ("Counter-Strike 2", "3840x2160", "Ultra", {"category": "gpu", "model": "RTX 5080"}, {"category": "cpu", "model": "Intel Core i9-14900K"}),
        ("Counter-Strike 2", "3840x2160", "Ultra", {"category": "gpu", "model": "RTX 5090"}, {"category": "cpu", "model": "Intel Core i9-14900K"}),
    ]
    for game, res, settings, gpu, cpu in combos:
        d = await s._fetch_benchmark_combo(game, res, settings, gpu, cpu)
        print("----", game, gpu["model"], cpu["model"], "----")
        print(json.dumps(d, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

