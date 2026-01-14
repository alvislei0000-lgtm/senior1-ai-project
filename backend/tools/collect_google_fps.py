#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List

import httpx
import sys
from pathlib import Path

# ensure backend/ is on sys.path so `app` package imports work when invoked from tools/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.google_fps_search import GoogleFpsSearchService


GAMES = [
    "Cyberpunk 2077",
    "Elden Ring",
    "Minecraft",
    "Cities: Skylines",
    "Apex Legends",
    "Halo Infinite",
    "Rust",
    "Forza Horizon 5",
    "Fortnite",
    "Counter-Strike 2",
]

GPUS = ["RTX 5090", "RTX 5080", "RTX 4090", "RTX 4080"]
CPUS = ["Intel Core i9-14900K", "Intel Core i9-13900K", "Ryzen 9 9950X", "Ryzen 9 7950X"]
RESOLUTIONS = ["1920x1080", "3840x2160"]
SETTINGS = ["High", "Ultra"]

OUTPUT_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "google_fps_refs.json"))


async def fetch_one(svc: GoogleFpsSearchService, game: str, gpu: str, cpu: str, resolution: str, setting: str) -> Dict[str, Any]:
    try:
        data = await svc.search_fps(game=game, gpu=gpu, cpu=cpu, resolution=resolution, settings=setting, num=5)
        return {
            "game": game,
            "gpu": gpu,
            "cpu": cpu,
            "resolution": resolution,
            "settings": setting,
            "result": data,
        }
    except Exception as e:
        return {
            "game": game,
            "gpu": gpu,
            "cpu": cpu,
            "resolution": resolution,
            "settings": setting,
            "error": str(e),
        }


async def main() -> int:
    # Set environment variables directly in script
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU"
    os.environ["GOOGLE_CX"] = "034784ab1b1404dc2"

    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")
    if not api_key or not cx:
        print("Missing GOOGLE_API_KEY / GOOGLE_CX in environment")
        return 2

    tasks: List[asyncio.Task] = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        svc = GoogleFpsSearchService(client)
        for game in GAMES:
            for gpu in GPUS:
                for cpu in CPUS:
                    for res in RESOLUTIONS:
                        for st in SETTINGS:
                            tasks.append(asyncio.create_task(fetch_one(svc, game, gpu, cpu, res, st)))

        results = []
        for t in asyncio.as_completed(tasks):
            r = await t
            results.append(r)
            print(".", end="", flush=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"meta": {"games": GAMES, "gpus": GPUS, "cpus": CPUS, "resolutions": RESOLUTIONS, "settings": SETTINGS}, "results": results}, f, ensure_ascii=False, indent=2)
    print("\nSaved:", OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

