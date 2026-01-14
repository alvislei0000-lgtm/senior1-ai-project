#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.benchmark_scraper import BenchmarkScraper


async def main():
    s = BenchmarkScraper()
    tests = [
        ("Apex Legends", "1920x1080", "High", "RTX 5080", "Intel Core i9-14900K"),
        ("Apex Legends", "1920x1080", "High", "RTX 5090", "Intel Core i9-14900K"),
        ("Minecraft", "1920x1080", "High", "RTX 5090", "Ryzen 9 9950X"),
        ("Minecraft", "1920x1080", "High", "RTX 5090", "Intel Core i9-13900K"),
    ]
    for game, res, st, gpu, cpu in tests:
        d = await s._fetch_benchmark_combo(game, res, st, {"category": "gpu", "model": gpu}, {"category": "cpu", "model": cpu})
        print(f"{game} | {gpu} | {cpu} | avg_fps={d.get('avg_fps')} | source={d.get('source')}")


if __name__ == "__main__":
    asyncio.run(main())

