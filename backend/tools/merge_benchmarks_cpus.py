#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

def normalize_cpu(k: str) -> str:
    s = k.lower()
    s = re.sub(r'^(intel\\s+core\\s+|intel\\s+|amd\\s+)', '', s)
    s = re.sub(r'\\s+', ' ', s).strip()
    return s

def choose_canonical(keys):
    # prefer keys containing vendor, then longest
    def score(k):
        s = 0
        if 'intel' in k.lower(): s += 2
        if 'amd' in k.lower(): s += 2
        s += len(k)
        return s
    return sorted(keys, key=score, reverse=True)[0]

def merge_values(vals):
    # vals: list of dicts. prefer non-null avg_fps, prefer Predicted Model with latest model_version
    preferred = None
    for v in vals:
        if not preferred and v.get('avg_fps') is not None:
            preferred = v
    if not preferred and vals:
        preferred = vals[0]
    # merge metadata
    merged = preferred.copy() if preferred else {}
    # keep notes concatenated
    notes = []
    for v in vals:
        n = v.get('notes')
        if n:
            notes.append(str(n))
    if notes:
        merged['notes'] = ' | '.join(notes)
    return merged

def main():
    base = Path(__file__).resolve().parents[1]
    cache_path = base / "data" / "benchmarks_cache.json"
    if not cache_path.exists():
        print("benchmarks_cache.json not found")
        return
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    groups = {}
    for k, v in list(data.items()):
        parts = k.split("|")
        if len(parts) != 5:
            groups.setdefault(k, []).append((k, v))
            continue
        game, res, settings, gpu, cpu = parts
        nk = normalize_cpu(cpu)
        group_key = "|".join([game.strip(), res.strip(), settings.strip(), nk])
        groups.setdefault(group_key, []).append((k, v))

    new_data = {}
    changed = 0
    for gk, items in groups.items():
        if len(items) == 1:
            k, v = items[0]
            new_data[k] = v
        else:
            # merge: pick canonical cpu display name
            old_keys = [it[0] for it in items]
            parts = old_keys[0].split("|")
            game, res, settings, gpu = parts[0], parts[1], parts[2], parts[3]
            cpu_candidates = [k.split("|")[4] for k in old_keys]
            canonical = choose_canonical(cpu_candidates)
            new_key = "|".join([game, res, settings, gpu, canonical])
            vals = [it[1] for it in items]
            merged = merge_values(vals)
            new_data[new_key] = merged
            changed += len(items)

    # write backup and replace
    bak = cache_path.with_suffix(".json.bak")
    cache_path.rename(bak)
    cache_path.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("merged entries, wrote new cache; changed items approx:", changed)

if __name__ == "__main__":
    main()

