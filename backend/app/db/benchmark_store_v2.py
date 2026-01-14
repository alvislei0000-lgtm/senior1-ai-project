from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


def _norm(s: str) -> str:
    return " ".join((s or "").strip().split())

def _canon_part(s: str) -> str:
    return _norm(s).lower()


def _canon_key(game: str, resolution: str, settings: str, gpu: str) -> str:
    # v2 canonical: case-insensitive + "||" separator（向後相容舊檔案格式）
    return "||".join([_canon_part(game), _canon_part(resolution), _canon_part(settings), _canon_part(gpu)])


def _try_canonicalize_existing_key(k: str) -> Optional[str]:
    """
    支援舊格式 key：
    - "game|resolution|settings|gpu"
    - "game||resolution||settings||gpu"
    轉成 canonical "game||resolution||settings||gpu"（全小寫）。
    """
    if not k:
        return None
    s = str(k)
    # prefer "||" split
    if "||" in s:
        parts = s.split("||")
        if len(parts) == 4:
            return _canon_key(*parts)
    if "|" in s:
        parts = s.split("|")
        if len(parts) == 4:
            return _canon_key(*parts)
    return None


@dataclass
class BenchmarkStoreV2:
    """
    v2 cache（GPU-base）：
    key = game|resolution|settings|gpu
    value = 任意 JSON dict（avg_fps/p1_low/notes/source/raw_snippet...）

    用途：
    - 大量預熱 25 games × GPUs × resolutions × settings
    - 由後端再套用 CPU 調整/使用率推估，提升覆蓋率與一致性
    """

    file_path: str
    _lock: asyncio.Lock
    _data: Dict[str, Any]

    @classmethod
    def create_default(cls) -> "BenchmarkStoreV2":
        base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        fp = os.path.join(base, "data", "benchmarks_cache_v2.json")
        return cls(file_path=fp, _lock=asyncio.Lock(), _data={})

    async def _load(self) -> None:
        if self._data:
            return
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    raw = json.load(f) or {}

                # 支援 envelope 格式：{"version":2, "updated_at":..., "items": {...}}
                # 也支援混合檔（頂層殘留少量舊 key）
                items: Dict[str, Any] = {}
                if isinstance(raw, dict) and isinstance(raw.get("items"), dict):
                    items = dict(raw.get("items") or {})
                    # merge top-level legacy records into items (don't overwrite existing)
                    for k, v in raw.items():
                        if k in ("version", "updated_at", "items"):
                            continue
                        if isinstance(v, dict):
                            items.setdefault(k, v)
                elif isinstance(raw, dict):
                    items = dict(raw)

                # canonicalize keys to maximize cache hit-rate (case-insensitive + separator tolerant)
                canon: Dict[str, Any] = {}
                for k, v in (items or {}).items():
                    if not isinstance(v, dict):
                        continue
                    ck = _try_canonicalize_existing_key(k) or str(k)
                    # if collision, prefer entry with avg_fps present
                    if ck in canon:
                        prev = canon.get(ck) or {}
                        prev_has = isinstance(prev, dict) and prev.get("avg_fps") is not None
                        new_has = v.get("avg_fps") is not None
                        if (not prev_has) and new_has:
                            canon[ck] = v
                    else:
                        canon[ck] = v

                self._data = canon or {}
        except Exception:
            self._data = {}

    def _key(self, game: str, resolution: str, settings: str, gpu: str) -> str:
        return _canon_key(game, resolution, settings, gpu)

    async def get(self, game: str, resolution: str, settings: str, gpu: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            await self._load()
            # 兼容：曾經存在 "|" 格式或大小寫不同的 key
            k1 = self._key(game, resolution, settings, gpu)
            if k1 in self._data:
                return self._data.get(k1)
            k2 = "|".join([_norm(game), _norm(resolution), _norm(settings), _norm(gpu)])
            return self._data.get(k2)

    async def upsert(self, game: str, resolution: str, settings: str, gpu: str, value: Dict[str, Any]) -> None:
        async with self._lock:
            await self._load()
            self._data[self._key(game, resolution, settings, gpu)] = value
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            tmp = f"{self.file_path}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": 2,
                        "updated_at": datetime.now().isoformat(),
                        "items": self._data,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            os.replace(tmp, self.file_path)

    async def bulk_upsert(self, records: list[dict]) -> None:
        """
        批次寫入，避免 prewarm 時每筆都寫檔造成極慢（Windows 特別明顯）。
        records item: {"game":..., "resolution":..., "settings":..., "gpu":..., "value": {...}}
        """
        async with self._lock:
            await self._load()
            for r in records or []:
                k = self._key(r.get("game", ""), r.get("resolution", ""), r.get("settings", ""), r.get("gpu", ""))
                self._data[k] = r.get("value", {})
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            tmp = f"{self.file_path}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": 2,
                        "updated_at": datetime.now().isoformat(),
                        "items": self._data,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            os.replace(tmp, self.file_path)


benchmark_store_v2 = BenchmarkStoreV2.create_default()


