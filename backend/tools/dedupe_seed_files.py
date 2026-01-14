#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

def normalize_model_key(s: str) -> str:
    if not s:
        return ''
    m = str(s)
    m = re.sub(r'\(.*?\)', ' ', m)
    m = m.replace('-', ' ').replace('_', ' ').replace('/', ' ')
    m = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', m)
    m = re.sub(r'^(intel|amd|nvidia|nvidia geforce|geforce|samsung|western digital|wd|kingston|crucial)\b', ' ', m, flags=re.IGNORECASE)
    m = re.sub(r'\s+', ' ', m).strip().lower()
    return m

def choose_canonical(entries):
    # prefer entry with non-empty brand, then longer model string
    entries_sorted = sorted(entries, key=lambda e: (bool(e.get('brand')), len(e.get('model') or '')), reverse=True)
    return entries_sorted[0]

def dedupe_file(path: Path):
    data = json.loads(path.read_text(encoding='utf-8'))
    items = data.get('items', [])
    groups = {}
    for it in items:
        key = normalize_model_key(it.get('model') or '')
        if not key:
            # keep as-is under unique key
            groups.setdefault(f"__raw__{len(groups)}", []).append(it)
        else:
            groups.setdefault(key, []).append(it)

    new_items = []
    changed = 0
    for k, group in groups.items():
        if len(group) == 1:
            new_items.append(group[0])
        else:
            canonical = choose_canonical(group)
            # merge metadata: prefer canonical values but fill gaps
            merged = dict(canonical)
            for other in group:
                for f in ('generation','release_year','brand','capacity_gb','vram_gb','ram_gb'):
                    if not merged.get(f) and other.get(f) is not None:
                        merged[f] = other.get(f)
            new_items.append(merged)
            changed += len(group) - 1

    data['items'] = new_items
    bak = path.with_suffix(path.suffix + '.bak')
    path.rename(bak)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return changed, bak

def main():
    repo_root = Path(__file__).resolve().parents[1]
    backend_seed = repo_root / 'data' / 'hardware_seed.json'
    frontend_seed = repo_root.parent / 'frontend' / 'src' / 'data' / 'hardware_seed_frontend.json'
    results = []
    if backend_seed.exists():
        ch, bak = dedupe_file(backend_seed)
        results.append(f"backend seed deduped, removed {ch} items, backup at {bak}")
    if frontend_seed.exists():
        ch, bak = dedupe_file(frontend_seed)
        results.append(f"frontend seed deduped, removed {ch} items, backup at {bak}")
    for r in results:
        print(r)

if __name__ == '__main__':
    main()

