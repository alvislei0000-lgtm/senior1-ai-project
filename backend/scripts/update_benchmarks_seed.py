#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新 backend/data/hardware_seed.json 的 benchmarks 區塊（用 Google Programmable Search snippet 解析 FPS）

為什麼需要這個腳本？
- 你目前看到的「資料不足」多半是因為某遊戲/硬體沒有 seed 實測數據，且 Google 沒啟用或抓不到
- 這個腳本會把你最常用的組合（例如：25 款遊戲 × 1080p × High × 指定 GPU/CPU）先補齊到 seed

使用方式（Windows PowerShell 範例）：
  cd backend
  notepad .env   # 填 GOOGLE_API_KEY / GOOGLE_CX
  .\venv\Scripts\python.exe scripts\update_benchmarks_seed.py --dry-run
  .\venv\Scripts\python.exe scripts\update_benchmarks_seed.py --write --max-gpus 30 --resolution 1920x1080 --setting High
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv, find_dotenv

from app.services.google_fps_search import GoogleFpsSearchService
from app.data.game_requirements import GAME_REQUIREMENTS_25


def load_seed(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_seed(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_seed_gpus(seed: Dict[str, Any]) -> List[str]:
    models = []
    for it in seed.get("items", []) or []:
        if isinstance(it, dict) and it.get("category") == "gpu" and it.get("model"):
            models.append(str(it["model"]))
    # 去重保序
    seen = set()
    uniq = []
    for m in models:
        k = m.strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(m.strip())
    return uniq


def ensure_path(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    cur = d
    for k in keys:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    return cur


def derive_lows(avg_fps: float, game: str, rng_key: str) -> Tuple[float, float]:
    """
    當 Google snippet 只給 avg_fps 時，推一個合理的 1% low / 0.1% low（保守且可重複）。
    """
    import hashlib
    import random

    h = hashlib.md5((rng_key + "|" + game).encode("utf-8")).hexdigest()
    r = random.Random(int(h[:8], 16))
    p1 = max(5.0, min(avg_fps * r.uniform(0.78, 0.90), avg_fps))
    p01 = max(3.0, min(p1 * r.uniform(0.86, 0.95), p1))
    return round(p1, 1), round(p01, 1)


async def fetch_one(
    svc: GoogleFpsSearchService,
    game: str,
    gpu: str,
    cpu: str,
    resolution: str,
    setting: str,
    num: int,
) -> Optional[Dict[str, Any]]:
    data = await svc.search_fps(game=game, gpu=gpu, cpu=cpu, resolution=resolution, settings=setting, num=num)
    if not data or data.get("avg_fps") is None:
        return None
    avg = float(data["avg_fps"])
    p1 = data.get("p1_low")
    p01 = data.get("p0_1_low")
    if p1 is None or p01 is None:
        key = f"{game}|{gpu}|{cpu}|{resolution}|{setting}"
        p1d, p01d = derive_lows(avg, game, key)
        p1 = p1 if p1 is not None else p1d
        p01 = p01 if p01 is not None else p01d
    return {
        "avg_fps": round(avg, 1),
        "p1_low": float(p1),
        "p0_1_low": float(p01),
        "source": str(data.get("source") or "GoogleSearchSnippet"),
        "raw_snippet": data.get("raw_snippet"),
        "notes": data.get("notes"),
    }


async def main_async(args: argparse.Namespace) -> int:
    # load .env (prefer backend/.env)
    backend_env = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(backend_env, override=False)
    load_dotenv(find_dotenv(), override=False)

    seed_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", "hardware_seed.json"))
    seed = load_seed(seed_path)

    gpus = list_seed_gpus(seed)
    if args.max_gpus and args.max_gpus > 0:
        gpus = gpus[: args.max_gpus]

    games = list(GAME_REQUIREMENTS_25.keys())
    if args.games:
        games = [g.strip() for g in args.games.split(",") if g.strip()]

    resolution = args.resolution
    setting = args.setting
    cpu = args.cpu

    print(f"Seed path: {seed_path}")
    print(f"Games: {len(games)} | GPUs: {len(gpus)} | CPU: {cpu} | {resolution} {setting}")
    print(f"Mode: {'WRITE' if args.write else 'DRY-RUN'}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        svc = GoogleFpsSearchService(client)

        updated = 0
        skipped = 0
        failed = 0

        for game in games:
            for gpu in gpus:
                # 若已存在且未要求覆蓋，跳過
                table = ensure_path(seed, ["benchmarks", game, resolution, setting])
                if (not args.overwrite) and gpu in table and isinstance(table[gpu], dict) and table[gpu].get("avg_fps") is not None:
                    skipped += 1
                    continue

                got = await fetch_one(svc, game, gpu, cpu, resolution, setting, num=args.num)
                if not got:
                    failed += 1
                    continue

                # 只寫入數值欄位，保持與既有 seed 結構相容
                table[gpu] = {
                    "avg_fps": got["avg_fps"],
                    "p1_low": got["p1_low"],
                    "p0_1_low": got["p0_1_low"],
                }
                updated += 1

                if args.verbose:
                    print(f"[OK] {game} | {gpu} | {resolution} {setting} => {got['avg_fps']} fps")

        print(f"Updated: {updated} | Skipped: {skipped} | Failed: {failed}")

    if args.write:
        save_seed(seed_path, seed)
        print("Saved.")
    else:
        print("Dry-run: not saved.")

    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="實際寫回 hardware_seed.json（預設為 dry-run）")
    p.add_argument("--overwrite", action="store_true", help="覆蓋已存在的數值")
    p.add_argument("--max-gpus", type=int, default=20, help="最多處理多少張 GPU（避免配額爆掉）")
    p.add_argument("--games", type=str, default="", help="逗號分隔的遊戲名（不填則用 25 款預設清單）")
    p.add_argument("--cpu", type=str, default="Intel Core i7-12700K", help="用於 Google query 的 CPU 字串")
    p.add_argument("--resolution", type=str, default="1920x1080")
    p.add_argument("--setting", type=str, default="High", choices=["Low", "Medium", "High", "Ultra"])
    p.add_argument("--num", type=int, default=5, help="Google 回傳結果數（1~10）")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    return __import__("asyncio").run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())


