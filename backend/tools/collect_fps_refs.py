#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import httpx

import sys
# allow running from tools/ with relative imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.google_fps_search import GoogleFpsSearchService


GAMES = [
    "Cyberpunk 2077",
    "Elden Ring",
    "Apex Legends",
    "Minecraft",
    "Forza Horizon 5",
    "Assetto Corsa Competizione",
    "Cities: Skylines",
    "Halo Infinite",
    "Rust",
    "Fortnite",
    "Red Dead Redemption 2",
    "The Witcher 3",
    "Battlefield 2042",
    "Escape from Tarkov",
    "Control",
    "Metro Exodus",
    "Hogwarts Legacy",
    "Grand Theft Auto V",
    "Valorant",
    "Counter-Strike 2",
]

# Expanded GPU/CPU lists for broader coverage (will produce many queries)
GPUS = [
    "RTX 5090", "RTX 5080", "RTX 5070", "RTX 5060",
    "RTX 4090", "RTX 4080", "RTX 4070", "RTX 4060",
    "RTX 3090 Ti", "RTX 3090", "RTX 3080 Ti", "RTX 3080",
    "RTX 3070", "RTX 3060", "GTX 1660 Super", "GTX 1660",
    "RX 7900 XTX", "RX 7900 XT", "RX 7800 XT", "RX 7700 XT",
    "RX 6950 XT", "RX 6900 XT", "RX 6800 XT"
]

CPUS = [
    "Intel Core i9-14900K", "Intel Core i9-13900K", "Intel Core i9-12900K",
    "Intel Core i7-14700K", "Intel Core i7-13700K", "Intel Core i7-12700K",
    "Intel Core i5-14600K", "Intel Core i5-13600K",
    "Ryzen 9 9950X", "Ryzen 9 9950X3D", "Ryzen 9 7950X", "Ryzen 7 7800X3D",
    "Ryzen 7 7800X", "Ryzen 5 7600X", "Ryzen 5 9600X", "Ryzen 7 9800X3D"
]

RES = ["1920x1080", "2560x1440", "3840x2160"]
SETTINGS = ["High", "Ultra"]

# games that commonly support RT/PT
RT_SUPPORTED = {
    "cyberpunk 2077",
    "alan wake 2",
    "control",
    "metro exodus",
    "forza horizon 5",
    "elden ring",
    "hogwarts legacy",
}


async def collect(api_key: str, cx: str, out_path: str, max_queries: int = 500) -> None:
    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ["GOOGLE_CX"] = cx

    client = httpx.AsyncClient(timeout=20.0)
    svc = GoogleFpsSearchService(client)

    results: Dict[str, Any] = {"meta": {"engine_cx": cx}, "items": {}}
    count = 0

    try:
        for game in GAMES:
            for gpu in GPUS:
                for cpu in CPUS:
                    for res in RES:
                        for st in SETTINGS:
                            settings = st
                            # optionally add RT if supported
                            combos = [settings]
                            if game.lower() in RT_SUPPORTED:
                                combos.append(f"{settings} RT")

                            for s in combos:
                                if count >= max_queries:
                                    return await client.aclose()

                                key = "|".join([game, res, s, gpu, cpu])
                                try:
                                    data = await svc.search_fps(game=game, gpu=gpu, cpu=cpu, resolution=res, settings=s, num=5)
                                except Exception as e:
                                    data = {"avg_fps": None, "notes": f"error: {e}", "source": "GoogleSearchSnippet"}

                                results["items"][key] = {
                                    "game": game,
                                    "resolution": res,
                                    "settings": s,
                                    "gpu": gpu,
                                    "cpu": cpu,
                                    "avg_fps": data.get("avg_fps"),
                                    "p1_low": data.get("p1_low"),
                                    "p0_1_low": data.get("p0_1_low"),
                                    "confidence_override": data.get("confidence_override"),
                                    "source": data.get("source"),
                                    "raw_snippet": (data.get("raw_snippet") or "")[:1000],
                                    "notes": (data.get("notes") or "")[:2000],
                                }
                                count += 1

    finally:
        await client.aclose()

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--api-key", required=True)
    p.add_argument("--cx", required=True)
    p.add_argument("--out", default=os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "fps_reference.json")))
    p.add_argument("--max-queries", type=int, default=300)
    args = p.parse_args()

    asyncio.run(collect(api_key=args.api_key, cx=args.cx, out_path=args.out, max_queries=args.max_queries))
    print("Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

