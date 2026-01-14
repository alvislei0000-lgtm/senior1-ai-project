#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性清洗/遷移本地快取（v1/v2）裡的 Predicted Model 資料，避免不同模型版本混用造成：
- RTX 5080 > RTX 5090（快取污染/舊版預測）
- 13900K > 9950X（CPU 型號未辨識或舊版預測）

做什麼：
- v2（GPU-base）：若 source 不是 Real/Scaled/Predicted，或 Predicted 的 model_version != CURRENT → 重新生成並覆寫
- v1（含 CPU）：若 raw_snippet 顯示是預測、或 source=Predicted，但 model_version != CURRENT → 重新生成並覆寫

使用方式：
  cd backend
  .\venv\Scripts\python.exe scripts\migrate_predicted_caches.py --dry-run
  .\venv\Scripts\python.exe scripts\migrate_predicted_caches.py --write
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
import sys

# 讓 scripts/ 可以 import backend/app/*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _save_json(p: Path, data: Any) -> None:
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_v2_key(k: str) -> Optional[Tuple[str, str, str, str]]:
    # canonical: game||res||settings||gpu (lower)
    if not k or "||" not in k:
        return None
    parts = k.split("||")
    if len(parts) != 4:
        return None
    game, res, st, gpu = [p.strip() for p in parts]
    if not game or not res or not st or not gpu:
        return None
    # normalize setting to Title-case base token (e.g. "ultra rt" -> "Ultra RT")
    st_tokens = st.split()
    if not st_tokens:
        st_norm = st
    else:
        base = st_tokens[0].capitalize()
        tail = " ".join(st_tokens[1:])
        st_norm = (base + (" " + tail.upper() if tail else "")).strip()
    return game, res, st_norm, gpu


def _parse_v1_key(k: str) -> Optional[Tuple[str, str, str, str, str]]:
    # v1: game|res|settings|gpu|cpu
    if not k or "|" not in k:
        return None
    parts = k.split("|")
    if len(parts) != 5:
        return None
    game, res, st, gpu, cpu = [p.strip() for p in parts]
    if not game or not res or not st or not gpu or not cpu:
        return None
    return game, res, st, gpu, cpu


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="實際寫回快取檔案（預設 dry-run）")
    ap.add_argument("--dry-run", action="store_true", help="只列印統計，不寫檔（預設）")
    args = ap.parse_args()

    do_write = bool(args.write) and not bool(args.dry_run)

    # lazy import（需要在 backend 目錄下）
    from app.scrapers.benchmark_scraper import BenchmarkScraper  # noqa

    scraper = BenchmarkScraper()
    current_mv = scraper.MODEL_VERSION

    base = Path(__file__).resolve().parents[1]
    v1_path = base / "data" / "benchmarks_cache.json"
    v2_path = base / "data" / "benchmarks_cache_v2.json"

    v1_changed = 0
    v1_total = 0
    v2_changed = 0
    v2_total = 0

    # ---- v2 ----
    if v2_path.exists():
        raw = _load_json(v2_path)
        items: Dict[str, Any]
        if isinstance(raw, dict) and isinstance(raw.get("items"), dict):
            items = dict(raw.get("items") or {})
        elif isinstance(raw, dict):
            items = dict(raw)
        else:
            items = {}

        allowed = {"Predicted Model", "Real Benchmark Database", "Real Benchmark Database (scaled)"}
        out_items: Dict[str, Any] = dict(items)
        for k, v in items.items():
            v2_total += 1
            if not isinstance(v, dict):
                continue
            src = str(v.get("source") or "")
            mv = v.get("model_version")
            must = (src not in allowed) or (src == "Predicted Model" and mv != current_mv)
            if not must:
                continue
            parsed = _parse_v2_key(k)
            if not parsed:
                continue
            game, res, st, gpu = parsed
            refreshed = scraper._generate_mock_data(
                game=game,
                resolution=res,
                gpu={"category": "gpu", "model": gpu},
                cpu={"category": "cpu", "model": scraper.CPU_REF_MODEL},
                settings=st,
            )
            out_items[k] = {
                "avg_fps": refreshed.get("avg_fps"),
                "p1_low": refreshed.get("p1_low"),
                "p0_1_low": refreshed.get("p0_1_low"),
                "notes": refreshed.get("notes"),
                "raw_snippet": refreshed.get("raw_snippet"),
                "source": "Predicted Model",
                "cpu_ref": "i5-12600K",
                "model_version": current_mv,
            }
            v2_changed += 1

        if do_write:
            _save_json(
                v2_path,
                {"version": 2, "updated_at": datetime.now().isoformat(), "items": out_items},
            )

    # ---- v1 ----
    if v1_path.exists():
        raw = _load_json(v1_path)
        if isinstance(raw, dict):
            items = dict(raw)
        else:
            items = {}
        out_items: Dict[str, Any] = dict(items)
        for k, v in items.items():
            v1_total += 1
            if not isinstance(v, dict):
                continue
            src = str(v.get("source") or "")
            mv = v.get("model_version")
            raw_snip = str(v.get("raw_snippet") or "")
            looks_pred = ("基於真實基準預測" in raw_snip) or (src == "Predicted Model")
            must = looks_pred and (mv != current_mv)
            if not must:
                continue
            parsed = _parse_v1_key(k)
            if not parsed:
                continue
            game, res, st, gpu, cpu = parsed
            refreshed = scraper._generate_mock_data(
                game=game,
                resolution=res,
                gpu={"category": "gpu", "model": gpu},
                cpu={"category": "cpu", "model": cpu},
                settings=st,
            )
            out_items[k] = {
                "avg_fps": refreshed.get("avg_fps"),
                "p1_low": refreshed.get("p1_low"),
                "p0_1_low": refreshed.get("p0_1_low"),
                "notes": refreshed.get("notes"),
                "raw_snippet": refreshed.get("raw_snippet"),
                "source": "Predicted Model",
                "confidence_override": refreshed.get("confidence_override"),
                "model_version": current_mv,
            }
            v1_changed += 1

        if do_write:
            _save_json(v1_path, out_items)

    print(f"MODEL_VERSION={current_mv}")
    print(f"v2: total={v2_total} changed={v2_changed} path={v2_path}")
    print(f"v1: total={v1_total} changed={v1_changed} path={v1_path}")
    print("mode:", "WRITE" if do_write else "DRY-RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


