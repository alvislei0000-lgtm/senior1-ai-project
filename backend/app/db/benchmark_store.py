from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


def _norm(s: str) -> str:
    return " ".join((s or "").strip().split())


@dataclass
class BenchmarkStore:
    """
    v1 cache（含 CPU）：
    key = game|resolution|settings|gpu|cpu
    value = 任意 JSON dict（avg_fps/p1_low/notes/source/raw_snippet...）
    """

    file_path: str
    _lock: asyncio.Lock
    _data: Dict[str, Any]

    @classmethod
    def create_default(cls) -> "BenchmarkStore":
        # backend/app/db -> backend/app -> backend
        base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        fp = os.path.join(base, "data", "benchmarks_cache.json")
        return cls(file_path=fp, _lock=asyncio.Lock(), _data={})

    async def _load(self) -> None:
        if self._data:
            return
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f) or {}
        except Exception:
            self._data = {}

    def _key(self, game: str, resolution: str, settings: str, gpu: str, cpu: str) -> str:
        return "|".join([_norm(game), _norm(resolution), _norm(settings), _norm(gpu), _norm(cpu)])

    async def get(self, game: str, resolution: str, settings: str, gpu: str, cpu: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            await self._load()
            return self._data.get(self._key(game, resolution, settings, gpu, cpu))

    async def upsert(self, game: str, resolution: str, settings: str, gpu: str, cpu: str, value: Dict[str, Any]) -> None:
        async with self._lock:
            await self._load()
            self._data[self._key(game, resolution, settings, gpu, cpu)] = value
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            tmp = f"{self.file_path}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.file_path)


benchmark_store = BenchmarkStore.create_default()










