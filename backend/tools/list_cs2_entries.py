#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "data" / "benchmarks_cache.json"

def main():
    data = {}
    if not P.exists():
        print("No file", P)
        return
    data = json.loads(P.read_text(encoding="utf-8") or "{}")
    matches = []
    for k, v in data.items():
        if isinstance(k, str) and "counter-strike 2" in k.lower() and isinstance(v, dict):
            matches.append((k, v.get("avg_fps"), v.get("raw_snippet"), v.get("source")))
    matches.sort()
    for k, avg, raw, src in matches:
        print(k, "| avg_fps=", avg, "| source=", src, "| raw_snippet=", raw)
    print("Found", len(matches), "entries")

if __name__ == "__main__":
    main()

