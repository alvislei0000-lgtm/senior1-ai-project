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
    cpu_model = 'Ryzen 9 9950X'
    for gpu_model, ram in [('RTX 5090',32),('RTX 5080',16),('RTX 4090',24)]:
        baseline = s._get_game_baseline_fps_1080p_high(game)
        tgt = s._get_gpu_performance_score(gpu_model)
        ref = s._get_gpu_performance_score('RTX 3060')
        perf_ratio = (tgt/ref) if ref else tgt
        game_demand = s._get_game_performance_demand(game)
        res_mul = s._get_resolution_multiplier_for_game(game, res)
        qual_mul = s._get_quality_multiplier_for_game(game, settings)
        rt_mul, rt_note = s._get_rt_multiplier_for_game(game, settings)
        cpu_score = s._get_cpu_performance_score(cpu_model)
        ref_cpu = s._get_cpu_performance_score('i5-12600K')
        cpu_ratio = (cpu_score/ref_cpu) if ref_cpu else 1.0
        cpu_factor = max(0.75, min(cpu_ratio, 1.35)) if s._is_cpu_bound_game(game) else max(0.9, min(0.98+0.08*cpu_ratio,1.12))
        ram_mul = s._get_ram_multiplier(game, ram)
        storage_mul = s._get_storage_multiplier('SSD')
        base_fps = baseline * game_demand * res_mul * qual_mul * rt_mul * perf_ratio
        base_fps2 = base_fps * cpu_factor * ram_mul * storage_mul
        print('---', gpu_model, 'RAM', ram)
        print('baseline', baseline)
        print('tgt',tgt,'ref',ref,'perf_ratio',round(perf_ratio,3))
        print('game_demand',game_demand,'res_mul',res_mul,'qual_mul',qual_mul,'rt_mul',rt_mul)
        print('cpu_score',cpu_score,'ref_cpu',ref_cpu,'cpu_ratio',round(cpu_ratio,3),'cpu_factor',round(cpu_factor,3))
        print('ram_mul',ram_mul,'storage_mul',storage_mul)
        print('base_fps(before cpu/ram):',round(base_fps,2))
        print('base_fps(after cpu/ram):',round(base_fps2,2))

if __name__ == '__main__':
    main()

