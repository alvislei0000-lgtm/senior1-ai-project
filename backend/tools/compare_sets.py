#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.benchmark_scraper import BenchmarkScraper


async def main():
    s = BenchmarkScraper()
    groups = [
        # Group A: Valorant, RTX trio
        ("Valorant", "3840x2160", "Ultra", [
            ("RTX 5090", "Intel Core i9-14900K"),
            ("RTX 5080", "Intel Core i9-14900K"),
            ("RTX 4090", "Intel Core i9-14900K"),
        ]),
        # Group B: Valorant, RX duo
        ("Valorant", "3840x2160", "Ultra", [
            ("RX 7900 XTX", "Intel Core i9-14900K"),
            ("RX 7900 XT", "Intel Core i9-14900K"),
        ]),
        # Group C: Cyberpunk 4K Ultra RT, RTX 5090 vs 5080
        ("Cyberpunk 2077", "3840x2160", "Ultra RT", [
            ("RTX 5090", "Intel Core i9-14900K"),
            ("RTX 5080", "Intel Core i9-14900K"),
        ]),
        # Group D: Elden Ring RT, same GPU different CPU
        ("Elden Ring", "3840x2160", "Ultra RT", [
            ("RTX 5080", "Intel Core i9-14900K"),
            ("RTX 5080", "Ryzen 9 9950X"),
        ]),
        # Group E: Minecraft high, CPU comparison on same GPU
        ("Minecraft", "3840x2160", "High", [
            ("RTX 5090", "Ryzen 9 9950X"),
            ("RTX 5090", "Intel Core i9-14900K"),
        ]),
    ]

    for game, res, settings, hw_list in groups:
        print("=== Group:", game, res, settings, "===")
        for gpu, cpu in hw_list:
            d = await s._fetch_benchmark_combo(game, res, settings, {"category": "gpu", "model": gpu}, {"category": "cpu", "model": cpu})
            if not d:
                print(f"{gpu} | {cpu} | NO DATA")
            else:
                print(f"{gpu} | {cpu} | avg_fps={d.get('avg_fps')} | p1_low={d.get('p1_low')} | p0_1_low={d.get('p0_1_low')} | source={d.get('source')} | notes={d.get('notes')}")
        print("")


if __name__ == "__main__":
    asyncio.run(main())

