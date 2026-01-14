#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.scrapers.benchmark_scraper import BenchmarkScraper

def main():
    s = BenchmarkScraper()
    ref = s._get_gpu_performance_score('RTX 3060')
    for gpu in ['RTX 5090','RTX 5080','RTX 4090']:
        tgt = s._get_gpu_performance_score(gpu)
        ratio = tgt / ref if ref else None
        print(f'{gpu}: tgt={tgt}, ref={ref}, ratio={ratio:.3f}')

if __name__ == '__main__':
    main()

