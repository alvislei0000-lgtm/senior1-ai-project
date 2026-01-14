#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.benchmark_scraper import BenchmarkScraper


async def main():
    s = BenchmarkScraper()
    games = [
        ("Counter-Strike 2", "3840x2160", "Ultra"),
        ("Halo Infinite", "3840x2160", "Ultra"),
        ("Apex Legends", "3840x2160", "Ultra"),
        ("Rust", "3840x2160", "Ultra"),
    ]

    hw_sets = [
        ("RTX 5090", "Intel Core i9-14900K"),
        ("RTX 5080", "Intel Core i9-14900K"),
        ("RTX 4090", "Intel Core i9-14900K"),
        ("RX 7900 XTX", "Intel Core i9-14900K"),
        ("RTX 5080", "Ryzen 9 9950X"),
    ]

    out_csv = Path(__file__).resolve().parents[1] / "data" / "fps_games_comparison.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for game, res, settings in games:
        for gpu, cpu in hw_sets:
            d = await s._fetch_benchmark_combo(game, res, settings, {"category": "gpu", "model": gpu}, {"category": "cpu", "model": cpu})
            if not d:
                rows.append({"game": game, "resolution": res, "settings": settings, "gpu": gpu, "cpu": cpu, "avg_fps": None, "p1_low": None, "p0_1_low": None, "source": None, "notes": None})
            else:
                rows.append({
                    "game": game,
                    "resolution": res,
                    "settings": settings,
                    "gpu": gpu,
                    "cpu": cpu,
                    "avg_fps": d.get("avg_fps"),
                    "p1_low": d.get("p1_low"),
                    "p0_1_low": d.get("p0_1_low"),
                    "source": d.get("source"),
                    "notes": d.get("notes"),
                })

    # write CSV
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["game"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # print summary
    for r in rows:
        print(f"{r['game']} | {r['gpu']} | {r['cpu']} | avg_fps={r['avg_fps']} | p1_low={r['p1_low']} | source={r['source']}")

    print("CSV written to", out_csv)


if __name__ == "__main__":
    asyncio.run(main())

