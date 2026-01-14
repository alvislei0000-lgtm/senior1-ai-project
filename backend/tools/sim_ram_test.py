#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.scrapers.benchmark_scraper import BenchmarkScraper

def main():
    s = BenchmarkScraper()
    game = 'Minecraft'
    res = '3840x2160'
    settings = 'Ultra'
    cpu = {'category': 'cpu', 'model': 'Ryzen 9 9950X'}
    configs = [
        ('RTX 5090', 32),
        ('RTX 5080', 16),
        ('RTX 4090', 24),
    ]
    for gpu_model, ram in configs:
        out = s._generate_mock_data(
            game,
            res,
            {'category': 'gpu', 'model': gpu_model, 'selected_vram_gb': 10},
            cpu,
            settings,
            ram_gb=ram,
            storage_type='SSD'
        )
        print(f"{gpu_model} | RAM {ram}GB -> avg_fps={out.get('avg_fps'):.1f}, p1_low={out.get('p1_low'):.1f}, p0_1_low={out.get('p0_1_low'):.1f}")

if __name__ == '__main__':
    main()

