#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.scrapers.benchmark_scraper import BenchmarkScraper

async def main():
    s = BenchmarkScraper()
    hardware = [
        {"category": "gpu", "model": "RTX 5080"},
        {"category": "cpu", "model": "Intel Core i9-14900K"},
        {"category": "ram", "ram_gb": 32},
        {"category": "storage", "storage_type": "NVMe"},
    ]
    res = await s.search_benchmarks(game="Minecraft", resolution="3840x2160", settings="Ultra", hardware_list=hardware)
    print("results:", len(res))

if __name__ == "__main__":
    asyncio.run(main())

