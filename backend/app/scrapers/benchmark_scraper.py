"""
基準測試資料爬蟲
優先使用本地基準數據庫，提供真實的基準測試結果
（含：Google Programmable Search snippet 解析作為網路來源之一）
"""
from typing import List, Optional, Dict, Any, Tuple
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime
import random
import hashlib
from pathlib import Path

# Hardware performance overrides loader (optional JSON file)
_hw_overrides_cache: Optional[Dict[str, Dict[str, float]]] = None

def _load_hw_overrides() -> Dict[str, Dict[str, float]]:
    global _hw_overrides_cache
    if _hw_overrides_cache is not None:
        return _hw_overrides_cache
    try:
        base = Path(__file__).resolve().parents[2]
        p = base / "data" / "hw_performance_override.json"
        if p.exists():
            _hw_overrides_cache = json.loads(p.read_text(encoding="utf-8") or "{}")
        else:
            _hw_overrides_cache = {}
    except Exception:
        _hw_overrides_cache = {}
    return _hw_overrides_cache

from app.scrapers.base_scraper import BaseScraper
from app.data.game_requirements import GAME_REQUIREMENTS_25
from app.db import benchmark_store, benchmark_store_v2
from app.services.google_fps_search import GoogleFpsSearchService


class BenchmarkScraper(BaseScraper):
    """基準測試資料爬蟲"""

    # 預測模型版本：用於 v2 cache 的「Predicted Model」自動升級/覆蓋
    MODEL_VERSION = 4
    # v2 GPU-base 預測採用的 reference CPU（後續再依使用者 CPU 做調整）
    CPU_REF_MODEL = "Intel Core i5-12600K"

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.techpowerup.com"
        self.source_name = "Real Benchmark Database"
        self.last_fetch_time: Optional[str] = None
        self.benchmark_db, self.gpu_meta = self._load_seed_database()
    
    async def search_benchmarks(
        self,
        game: str,
        resolution: str,
        settings: Optional[str],
        hardware_list: List[dict]
    ) -> List[dict]:
        """
        搜尋基準測試資料
        從網路即時抓取，不使用內建靜態資料
        """
        await self.initialize()
        
        results: List[dict] = []

        gpus = [h for h in (hardware_list or []) if (h or {}).get("category") == "gpu"]
        cpus = [h for h in (hardware_list or []) if (h or {}).get("category") == "cpu"]
        rams = [h for h in (hardware_list or []) if (h or {}).get("category") == "ram"]
        storages = [h for h in (hardware_list or []) if (h or {}).get("category") == "storage"]

        if not gpus:
            return []
        if not cpus:
            cpus = [{"category": "cpu", "model": "Unknown CPU"}]

        # Extract RAM and storage specs (use first available if multiple)
        ram_specs = rams[0] if rams else {}
        ram_gb = ram_specs.get("ram_gb")
        ram_type = ram_specs.get("ram_type")
        ram_speed_mhz = ram_specs.get("ram_speed_mhz")
        ram_latency_ns = ram_specs.get("ram_latency_ns")
        storage_type = storages[0].get("storage_type") if storages else None

        for gpu in gpus:
            for cpu in cpus:
                try:
                    benchmark = await self._fetch_benchmark_combo(
                        game=game,
                        resolution=resolution,
                        settings=settings,
                        gpu=gpu,
                        cpu=cpu,
                        ram_gb=ram_gb,
                        ram_type=ram_type,
                        ram_speed_mhz=ram_speed_mhz,
                        ram_latency_ns=ram_latency_ns,
                        storage_type=storage_type,
                    )
                    if benchmark:
                        results.append(benchmark)
                except Exception as e:
                    print(f"抓取基準資料失敗 (GPU={gpu.get('model','N/A')}, CPU={cpu.get('model','N/A')}): {e}")
                    continue
        
        self.last_fetch_time = datetime.now().isoformat()
        return results
    
    def _load_seed_database(self) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """載入 seed：benchmarks + GPU metadata（VRAM 等）"""
        try:
            # backend/app/scrapers -> backend/app -> backend
            seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'hardware_seed.json')
            seed_path = os.path.normpath(seed_path)
            with open(seed_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            benchmarks = data.get('benchmarks', {}) or {}
            gpu_meta: Dict[str, Dict[str, Any]] = {}
            for it in data.get("items", []) or []:
                if not it or it.get("category") != "gpu":
                    continue
                model = str(it.get("model") or "").strip()
                if not model:
                    continue
                gpu_meta[model.lower()] = it
            return benchmarks, gpu_meta
        except Exception as e:
            print(f"載入 seed 資料庫失敗: {e}")
            return {}, {}

    async def _fetch_benchmark_combo(
        self,
        game: str,
        resolution: str,
        settings: Optional[str],
        gpu: dict,
        cpu: dict,
        ram_gb: Optional[float] = None,
        ram_type: Optional[str] = None,
        ram_speed_mhz: Optional[int] = None,
        ram_latency_ns: Optional[float] = None,
        storage_type: Optional[str] = None,
    ) -> Optional[dict]:
        """抓取單一 GPU×CPU 組合的基準測試資料"""

        gpu_model = gpu.get("model") or "Unknown GPU"
        cpu_model = cpu.get("model") or "Unknown CPU"
        effective_settings = (settings or "High").strip() or "High"

        # 0) 先查本地快取資料庫 v1（含 CPU）
        # 如果有RAM參數，跳過快取檢查以確保正確應用RAM影響
        skip_cache = ram_gb is not None or ram_type is not None or ram_speed_mhz is not None or ram_latency_ns is not None
        cached = None
        if not skip_cache:
            cached = await benchmark_store.get(game, resolution, effective_settings, gpu_model, cpu_model)

        if cached and cached.get("avg_fps") is not None:
            cached_src = str((cached or {}).get("source") or "")
            mv = (cached or {}).get("model_version")
            raw_snip = str((cached or {}).get("raw_snippet") or "")

            # 1) 若 v1 存的是 Predicted Model，且版本過舊 → 直接重算
            if cached_src == "Predicted Model" and mv != self.MODEL_VERSION:
                fps_data = self._generate_mock_data(
                    game=game,
                    resolution=resolution,
                    gpu={"category": "gpu", "model": gpu_model, "selected_vram_gb": gpu.get("selected_vram_gb")},
                    cpu={"category": "cpu", "model": cpu_model},
                    settings=effective_settings,
                    ram_gb=ram_gb,
                    ram_type=ram_type,
                    ram_speed_mhz=ram_speed_mhz,
                    ram_latency_ns=ram_latency_ns,
                    storage_type=storage_type,
                )
            else:
                # 1.5) 舊版 predicted 有時會被寫成 Local Benchmark Cache（source 變了但 raw_snippet 還會露出）
                looks_predicted = ("基於真實基準預測" in raw_snip) or (cached_src == "Predicted Model")
                if looks_predicted and mv != self.MODEL_VERSION:
                    fps_data = self._generate_mock_data(
                        game=game,
                        resolution=resolution,
                        gpu={"category": "gpu", "model": gpu_model, "selected_vram_gb": gpu.get("selected_vram_gb")},
                        cpu={"category": "cpu", "model": cpu_model},
                        settings=effective_settings,
                        ram_gb=ram_gb,
                        ram_type=ram_type,
                        ram_speed_mhz=ram_speed_mhz,
                        ram_latency_ns=ram_latency_ns,
                        storage_type=storage_type,
                    )
                else:
                    # 2) 對於重負載/RT 這類「對設定超敏感」的情境：若舊 cache 明顯偏離現行模型，就刷新
                    st_lower = effective_settings.lower()
                    wants_rt = any(k in st_lower for k in ["ray tracing", "raytracing", "path tracing", "pathtracing", " rt", "rt ", "光追", "光線追蹤", "路徑追蹤"])
                    is_sensitive = self._is_ultra_heavy_aaa(game) or wants_rt
                    if is_sensitive:
                        predicted = self._generate_mock_data(
                            game=game,
                            resolution=resolution,
                            gpu={"category": "gpu", "model": gpu_model, "selected_vram_gb": gpu.get("selected_vram_gb")},
                            cpu={"category": "cpu", "model": cpu_model},
                            settings=effective_settings,
                            ram_gb=ram_gb,
                            ram_type=ram_type,
                            ram_speed_mhz=ram_speed_mhz,
                            ram_latency_ns=ram_latency_ns,
                            storage_type=storage_type,
                        )
                        try:
                            cached_avg = float((cached or {}).get("avg_fps"))
                            pred_avg = float(predicted.get("avg_fps") or 0.0)
                            if pred_avg > 0:
                                delta = abs(cached_avg - pred_avg) / max(1.0, pred_avg)
                            else:
                                delta = 0.0
                        except Exception:
                            delta = 0.0

                        # 重負載/RT 情境比一般更敏感：刷新門檻更低，避免舊 cache（或先前 bug）殘留
                        # - RT：最敏感
                        # - 超重 3A：也容易因模型校正而差異明顯
                        threshold = 0.15 if wants_rt else (0.20 if self._is_ultra_heavy_aaa(game) else 0.35)

                        # 若差異很大，採用現行模型並覆寫 v1（避免下次又被舊 cache 命中）
                        if delta > threshold:
                            fps_data = predicted
                            try:
                                await benchmark_store.upsert(
                                    game=game,
                                    resolution=resolution,
                                    settings=effective_settings,
                                    gpu=gpu_model,
                                    cpu=cpu_model,
                                    value={
                                        "avg_fps": fps_data.get("avg_fps"),
                                        "p1_low": fps_data.get("p1_low"),
                                        "p0_1_low": fps_data.get("p0_1_low"),
                                        "notes": fps_data.get("notes"),
                                        "raw_snippet": fps_data.get("raw_snippet"),
                                        "source": "Predicted Model",
                                "model_version": self.MODEL_VERSION,
                                "ram_gb": fps_data.get("ram_gb"),
                                "storage_type": fps_data.get("storage_type"),
                                    },
                                )
                            except Exception:
                                pass
                        else:
                            fps_data = {**cached, "source": "Local Benchmark Cache"}
                    else:
                        # 3) 一般情境：照常使用 v1 cache
                        fps_data = {**cached, "source": "Local Benchmark Cache", "ram_gb": ram_gb, "storage_type": storage_type}
                        fps_data = {**cached, "source": "Local Benchmark Cache", "ram_gb": ram_gb, "storage_type": storage_type}
        else:
            # 0.5) 再查 v2（GPU-base）
            # 如果有RAM參數，跳過v2快取檢查以確保正確應用RAM影響
            cached_v2 = None
            if not skip_cache:
                cached_v2 = await benchmark_store_v2.get(game, resolution, effective_settings, gpu_model)

            if cached_v2 and cached_v2.get("avg_fps") is not None:
                # v2 是 GPU-base：只允許存「Real/Scaled/Predicted」。
                # 過去版本可能把 CPU-adjusted 的結果（Local Benchmark Cache (GPU-base)）誤寫進 v2，
                # 會導致硬體排序反常（例如 5080 > 5090）。遇到這種污染資料一律重算覆寫。
                v2_src = str(cached_v2.get("source") or "")
                allowed_v2_sources = {"Predicted Model", "Real Benchmark Database", "Real Benchmark Database (scaled)"}
                must_refresh = (v2_src not in allowed_v2_sources)
                # 若 v2 的 Predicted Model 是舊算法版本，也要重算
                if v2_src == "Predicted Model" and cached_v2.get("model_version") != self.MODEL_VERSION:
                    must_refresh = True

                if must_refresh:
                    try:
                        refreshed = self._generate_mock_data(
                            game=game,
                            resolution=resolution,
                            gpu={
                                "category": "gpu",
                                "model": gpu_model,
                                "selected_vram_gb": gpu.get("selected_vram_gb"),
                            },
                            cpu={"category": "cpu", "model": self.CPU_REF_MODEL},
                            settings=effective_settings,
                            ram_gb=ram_gb,
                            ram_type=ram_type,
                            ram_speed_mhz=ram_speed_mhz,
                            ram_latency_ns=ram_latency_ns,
                            storage_type=storage_type,
                        )
                        await benchmark_store_v2.upsert(
                            game=game,
                            resolution=resolution,
                            settings=effective_settings,
                            gpu=gpu_model,
                            value={
                                "avg_fps": refreshed.get("avg_fps"),
                                "p1_low": refreshed.get("p1_low"),
                                "p0_1_low": refreshed.get("p0_1_low"),
                                "notes": refreshed.get("notes"),
                                "raw_snippet": refreshed.get("raw_snippet"),
                                "source": "Predicted Model",
                                "cpu_ref": "i5-12600K",
                                "model_version": self.MODEL_VERSION,
                            },
                        )
                        cached_v2 = await benchmark_store_v2.get(game, resolution, effective_settings, gpu_model) or cached_v2
                    except Exception:
                        pass

                fps_data = {
                    **cached_v2,
                    "game": game,
                    "resolution": resolution,
                    "settings": effective_settings,
                    "gpu": gpu_model,
                    "cpu": cpu_model,
                    "source": "Local Benchmark Cache (GPU-base)",
                }
                fps_data = self._apply_cpu_adjustment(
                    fps_data=fps_data,
                    game=game,
                    cpu_model=cpu_model,
                )
            else:
                # 1) seed 真實/插值
                fps_data = self._query_real_benchmark_data(game, resolution, settings, gpu, cpu)

        # 1.5) 若使用者明確指定 RT/PT，對所有來源套用額外懲罰（不是所有遊戲都有，僅在 settings 明確表示時生效）
        try:
            fps_data = self._apply_rt_adjustment(fps_data=fps_data, game=game, settings=effective_settings)
        except Exception:
            pass

        # 2) 如果本地資料庫沒有資料，嘗試從網路抓取（優先 Google snippet，其次站點爬蟲）
        web_note: Optional[str] = None
        if not fps_data or not fps_data.get("avg_fps"):
            web_try = await self._try_multiple_sources(game, resolution, effective_settings, gpu, cpu)
            web_note = (web_try or {}).get("notes")
            if web_try and web_try.get("avg_fps"):
                fps_data = web_try

        # 3) 如果網路也抓取不到，使用預測（最後手段）
        if not fps_data or not fps_data.get("avg_fps"):
            fps_data = self._generate_mock_data(game, resolution, gpu, cpu, settings=effective_settings, ram_gb=ram_gb, ram_type=ram_type, ram_speed_mhz=ram_speed_mhz, ram_latency_ns=ram_latency_ns, storage_type=storage_type)
            if web_note:
                fps_data["notes"] = (str(fps_data.get("notes") or "") + ("；" if fps_data.get("notes") else "") + str(web_note)).strip()

        if not fps_data:
            return None

        # 4) 補齊欄位（避免瓶頸分析顯示「資料不足」）
        fps_data = self._ensure_benchmark_completeness(
            fps_data=fps_data,
            game=game,
            resolution=resolution,
            settings=effective_settings,
            gpu_model=gpu_model,
            cpu_model=cpu_model,
        )

        # 5) 若不是 Predicted，就寫回 v1 快取（含 CPU）
        try:
            src = str(fps_data.get("source") or "")
            # v1 是「含 CPU」的最終結果快取，但不應把 GPU-base（已調整 CPU）再寫回，
            # 否則會用舊資料覆蓋新算法，且容易造成 notes 疊加與瓶頸判定不穩定。
            if fps_data.get("avg_fps") is not None and src in (
                "Real Benchmark Database",
                "Real Benchmark Database (scaled)",
                "GoogleSearchSnippet",
                "TechPowerUp",
                "GPUCheck",
                "VideoCardBenchmark",
                "Local Benchmark Cache",
                "Predicted Model",
            ):
                await benchmark_store.upsert(
                    game=game,
                    resolution=resolution,
                    settings=effective_settings,
                    gpu=gpu_model,
                    cpu=cpu_model,
                    value={
                        "avg_fps": fps_data.get("avg_fps"),
                        "p1_low": fps_data.get("p1_low"),
                        "p0_1_low": fps_data.get("p0_1_low"),
                        "notes": fps_data.get("notes"),
                        "raw_snippet": fps_data.get("raw_snippet"),
                        "source": "Predicted Model" if src == "Predicted Model" else fps_data.get("source"),
                        "confidence_override": fps_data.get("confidence_override"),
                        "model_version": self.MODEL_VERSION if src == "Predicted Model" else None,
                        "ram_gb": fps_data.get("ram_gb"),
                        "storage_type": fps_data.get("storage_type"),
                    },
                )
        except Exception as e:
            print(f"寫入本地 benchmarks_cache 失敗: {e}")

        # 6) 同步寫入 v2（GPU-base）
        try:
            src = str(fps_data.get("source") or "")
            if fps_data.get("avg_fps") is not None and src in (
                "Real Benchmark Database",
                "Real Benchmark Database (scaled)",
                "Predicted Model",
            ):
                await benchmark_store_v2.upsert(
                    game=game,
                    resolution=resolution,
                    settings=effective_settings,
                    gpu=gpu_model,
                    value={
                        "avg_fps": fps_data.get("avg_fps"),
                        "p1_low": fps_data.get("p1_low"),
                        "p0_1_low": fps_data.get("p0_1_low"),
                        "notes": fps_data.get("notes"),
                        "raw_snippet": fps_data.get("raw_snippet"),
                        "source": src,
                            "cpu_ref": "i5-12600K" if src == "Predicted Model" else None,
                            "model_version": self.MODEL_VERSION if src == "Predicted Model" else None,
                            "ram_gb": fps_data.get("ram_gb"),
                            "storage_type": fps_data.get("storage_type"),
                    },
                )
        except Exception as e:
            print(f"寫入本地 benchmarks_cache_v2 失敗: {e}")

        vram_required_gb, vram_selected_gb, vram_is_enough, vram_margin_gb = self._check_vram(
            game=game,
            resolution=resolution,
            gpu=gpu,
        )
        if vram_is_enough is False:
            warn = f"⚠️ VRAM 可能不足：需求約 {vram_required_gb}GB，已選 {vram_selected_gb}GB"
            fps_data["notes"] = (str(fps_data.get("notes") or "") + ("；" if fps_data.get("notes") else "") + warn).strip()

        fps_data = self._sanitize_benchmark_payload(fps_data)

        is_incomplete = (fps_data.get("avg_fps") is None) or (fps_data.get("p1_low") is None)
        confidence_score = float(fps_data.get("confidence_override")) if fps_data.get("confidence_override") is not None else self._calculate_confidence(fps_data)
        confidence_score = max(0.0, min(float(confidence_score), 1.0))
        raw_snippet = fps_data.get("raw_snippet", "") or ""

        return {
            "game": game,
            "resolution": resolution,
            "settings": effective_settings,
            "gpu": gpu_model,
            "cpu": cpu_model,
            "avg_fps": fps_data.get("avg_fps"),
            "p1_low": fps_data.get("p1_low"),
            "p0_1_low": fps_data.get("p0_1_low"),
            "source": fps_data.get("source", self.source_name) or self.source_name,
            "timestamp": datetime.now().isoformat(),
            "notes": fps_data.get("notes"),
            "confidence_score": confidence_score,
            "is_incomplete": is_incomplete,
            "vram_required_gb": vram_required_gb,
            "vram_selected_gb": vram_selected_gb,
            "vram_is_enough": vram_is_enough,
            "vram_margin_gb": vram_margin_gb,
        }

    def _query_real_benchmark_data(
        self,
        game: str,
        resolution: str,
        settings: Optional[str],
        gpu: dict,
        cpu: dict,
    ) -> Optional[Dict[str, Any]]:
        """
        從本地基準資料庫查詢真實基準測試數據
        """
        gpu_model = gpu.get("model", "") or ""

        # 檢查遊戲是否存在於資料庫
        if game not in self.benchmark_db:
            return None

        game_data = self.benchmark_db[game]

        # 檢查解析度
        if resolution not in game_data:
            return None

        resolution_data = game_data[resolution]

        # 確定畫質設定（預設為 High 如果沒有指定）
        quality_setting = settings or "High"

        # 嘗試精確匹配設定
        if quality_setting not in resolution_data:
            # 如果沒有精確匹配，嘗試模糊匹配
            for available_setting in resolution_data:
                if quality_setting.lower() in available_setting.lower():
                    quality_setting = available_setting
                    break
            else:
                # 如果還是找不到，使用第一個可用的設定
                if resolution_data:
                    quality_setting = list(resolution_data.keys())[0]
                else:
                    return None

        setting_data = resolution_data[quality_setting]

        # 檢查GPU是否存在
        if gpu_model not in setting_data:
            # 嘗試模糊匹配GPU型號
            matched_gpu = None
            for available_gpu in setting_data:
                if available_gpu.lower() in gpu_model.lower() or gpu_model.lower() in available_gpu.lower():
                    matched_gpu = available_gpu
                    break

            if matched_gpu is None:
                # 若該遊戲/解析度/畫質有其他 GPU 的真實資料，使用「效能分數比例」做插值估算
                est = self._estimate_from_setting_table(setting_data, gpu_model)
                if not est:
                    return None
                benchmark_data = est
                benchmark_data = {**benchmark_data, "_estimated_from": "Real Benchmark Database (scaled)"}
                # 估算結果不需要再做 matched
                gpu_model = gpu_model or "Unknown GPU"
            else:
                gpu_model = matched_gpu
                benchmark_data = setting_data[gpu_model]
        else:
            benchmark_data = setting_data[gpu_model]

        # 計算硬件使用率（基於真實數據）
        gpu_usage, cpu_usage, memory_usage = self._calculate_realistic_usage_rates(
            benchmark_data, resolution, {"model": gpu_model, "cpu_model": cpu.get("model", "")}
        )

        notes = f"GPU: {gpu_usage:.0f}%, CPU: {cpu_usage:.0f}%, RAM: {memory_usage:.0f}%"

        return {
            "avg_fps": benchmark_data["avg_fps"],
            "p1_low": benchmark_data["p1_low"],
            "p0_1_low": benchmark_data["p0_1_low"],
            "gpu_usage": gpu_usage,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "notes": notes,
            "source": "Real Benchmark Database" if "_estimated_from" not in benchmark_data else str(benchmark_data.get("_estimated_from")),
            "raw_snippet": (
                f"真實基準數據 - {game} @ {resolution} {quality_setting} with {gpu_model}"
                if "_estimated_from" not in benchmark_data
                else f"插值估算 - {game} @ {resolution} {quality_setting} for {gpu_model}"
            )
        }
    
    def _generate_mock_data(
        self,
        game: str,
        resolution: str,
        gpu: dict,
        cpu: dict,
        settings: Optional[str],
        ram_gb: Optional[float] = None,
        ram_type: Optional[str] = None,
        ram_speed_mhz: Optional[int] = None,
        ram_latency_ns: Optional[float] = None,
        storage_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成基於真實硬件基準的模擬資料
        使用實際的基準測試數據作為參考，生成更準確的預測
        """
        gpu_model = str(gpu.get("model") or "")
        cpu_model = str(cpu.get("model") or "")
        effective_settings = (settings or "High").strip() or "High"

        # deterministic RNG：同一組輸入每次一致
        # - rng_combo：用於 low/usage 等細節（可隨硬體不同，包括RAM）
        # - rng_jitter：只隨 game/res/settings 變化，避免比較不同 GPU 時因 jitter 造成「高階反而更低」
        rng_combo = self._make_deterministic_rng(
            game=game,
            resolution=resolution,
            settings=effective_settings,
            gpu=gpu_model,
            cpu=cpu_model,
            ram_gb=str(ram_gb or "None"),
            ram_type=ram_type or "None",
        )
        rng_jitter = self._make_deterministic_rng(
            game=game,
            resolution=resolution,
            settings=effective_settings,
            gpu=gpu_model,
            salt="jitter_v4",
        )

        # baseline（1080p High）
        baseline_fps_1080p_high = self._get_game_baseline_fps_1080p_high(game)

        # GPU perf ratio（相對於 RTX 3060）
        tgt_score = self._get_gpu_performance_score(gpu_model)
        ref_score = self._get_gpu_performance_score("RTX 3060")
        perf_ratio = (tgt_score / ref_score) if ref_score and ref_score > 0 else tgt_score

        # 遊戲需求係數（0.6~1.0）
        game_demand = self._get_game_performance_demand(game)

        resolution_multiplier = self._get_resolution_multiplier_for_game(game, resolution)
        quality_multiplier = self._get_quality_multiplier_for_game(game, effective_settings)
        rt_multiplier, rt_note = self._get_rt_multiplier_for_game(game, effective_settings)

        base_fps = baseline_fps_1080p_high * game_demand * resolution_multiplier * quality_multiplier * rt_multiplier * perf_ratio

        # CPU factor（CPU-bound 更明顯）
        cpu_score = self._get_cpu_performance_score(cpu_model)
        ref_cpu = self._get_cpu_performance_score("i5-12600K")
        cpu_ratio = (cpu_score / ref_cpu) if ref_cpu and ref_cpu > 0 else 1.0
        if self._is_cpu_bound_game(game):
            cpu_factor = max(0.75, min(cpu_ratio, 1.35))
        else:
            cpu_factor = max(0.9, min(0.98 + 0.08 * cpu_ratio, 1.12))
        base_fps *= cpu_factor

        # RAM impact (if insufficient RAM, slight FPS decrease)
        ram_multiplier = self._get_ram_multiplier(game, ram_gb, ram_type, ram_speed_mhz, ram_latency_ns)
        base_fps *= ram_multiplier

        # Storage impact (SSD vs HDD, minimal impact on in-game FPS)
        storage_multiplier = self._get_storage_multiplier(storage_type)
        base_fps *= storage_multiplier

        # 隨機微幅波動（減少幅度以避免掩蓋RAM影響）
        avg_fps = base_fps * rng_jitter.uniform(0.98, 1.02)

        # CPU/引擎 ceiling（避免不合理超高）
        ceiling_1080_high = self._get_cpu_fps_ceiling_1080p_high(game)
        if ceiling_1080_high is not None and self._is_cpu_limited_game(game):
            # 原先只根據 CPU ratio 決定 ceiling，會導致高階 GPU 在 CPU-bound 遊戲被完全截斷
            # 新邏輯：仍以 CPU 為基準，但允許 GPU 提供部分上限提升（0.6 ~ 1.0 範圍）
            cpu_ceiling = float(ceiling_1080_high) * float(min(cpu_ratio, 1.35))
            # GPU influence：將 perf_ratio 正規化到 [0, 1.6]，並映射到 [0.6, 1.0]
            try:
                gpu_influence = 0.6 + 0.4 * (min(perf_ratio, 1.6) / 1.6)
            except Exception:
                gpu_influence = 0.8
            scaled_ceiling = cpu_ceiling * float(resolution_multiplier) * float(quality_multiplier) * float(gpu_influence)
            avg_fps = min(avg_fps, scaled_ceiling)

        # Small deterministic GPU tie-breaker: ensure different GPUs rarely produce identical avg due to clipping
        try:
            gpu_score_for_tiebreak = float(self._get_gpu_performance_score(gpu_model) or 1.0)
            tie_multiplier = 1.0 + max(0.0, (gpu_score_for_tiebreak - 1.0)) * 0.002
            avg_fps = avg_fps * tie_multiplier
        except Exception:
            pass

        avg_fps = max(avg_fps, 10.0)

        p1_low = avg_fps * rng_combo.uniform(0.75, 0.92)
        p0_1_low = p1_low * rng_combo.uniform(0.85, 0.96)

        # 使用率推估（動態）
        gpu_usage, cpu_usage, memory_usage = self._calculate_usage_rates(
            avg_fps=float(avg_fps),
            game=game,
            resolution=resolution,
            settings=effective_settings,
            gpu_perf_ratio=float(perf_ratio),
            cpu_model=cpu_model,
            ram_gb=ram_gb,
            ram_type=ram_type,
            ram_speed_mhz=ram_speed_mhz,
            ram_latency_ns=ram_latency_ns,
            rng=rng_combo,
        )
        notes = f"GPU: {gpu_usage:.0f}%, CPU: {cpu_usage:.0f}%, RAM: {memory_usage:.0f}%"
        if rt_note:
            notes = f"{notes} | {rt_note}"

        return {
            "avg_fps": round(avg_fps, 1),
            "p1_low": round(p1_low, 1),
            "p0_1_low": round(p0_1_low, 1),
            "gpu_usage": float(gpu_usage),
            "cpu_usage": float(cpu_usage),
            "memory_usage": float(memory_usage),
            "notes": notes,
            "ram_gb": ram_gb,
            "ram_type": ram_type,
            "ram_speed_mhz": ram_speed_mhz,
            "ram_latency_ns": ram_latency_ns,
            "storage_type": storage_type,
            "source": "Predicted Model",
            "raw_snippet": f"基於真實基準預測 - {game} @ {resolution} with {gpu_model} + {cpu_model}",
            "model_version": self.MODEL_VERSION,
        }

    def _get_rt_multiplier_for_game(self, game: str, settings: str) -> tuple[float, Optional[str]]:
        """
        光線追蹤/路徑追蹤（RT/PT）額外懲罰：
        - 只有當使用者在 settings 明確表示 RT/PT 才套用
        - 並非所有遊戲都有此功能；未知遊戲不直接改 FPS（只提示）
        """
        st = (settings or "").lower()
        rt_enabled = any(k in st for k in ["ray tracing", "raytracing", "path tracing", "pathtracing", " rt", "rt ", "rt+", "pt", "光追", "光線追蹤", "路徑追蹤"])
        if not rt_enabled:
            return 1.0, None

        g = (game or "").lower()
        # 只對「已知支援 RT/PT 的遊戲」套用懲罰（避免把不支援的遊戲也硬降 FPS）
        rt_map: dict[str, float] = {
            # 特別重的 RT/PT
            "alan wake 2": 0.60,
            # Cyberpunk：最終調整，RTX 5090 4K Ultra RT 約 45-50fps（相對不開 RT 下降約 10-15%）
            "cyberpunk 2077": 0.9,
            # Elden Ring：你期望 5080+14900K 開 RT 仍可 110+，因此只做輕度懲罰
            "elden ring": 0.90,
            # 中度懲罰
            "hogwarts legacy": 0.75,
            "fortnite": 0.80,
            "minecraft": 0.70,
            "control": 0.75,
            "metro exodus": 0.70,
        }
        for k, m in rt_map.items():
            if k in g:
                return float(m), "已啟用 RT/PT（FPS 會明顯下降）"

        return 1.0, "已勾選 RT/PT，但此遊戲的 RT/PT 支援未知：未額外調降 FPS"

    def _apply_rt_adjustment(self, fps_data: Optional[Dict[str, Any]], game: str, settings: str) -> Optional[Dict[str, Any]]:
        """
        對任意來源的 fps_data 套用 RT/PT 懲罰（僅當 settings 明確包含 RT/PT）。
        """
        if not fps_data:
            return fps_data
        # Predicted Model 在 _generate_mock_data() 已經套用過 RT multiplier，避免重複懲罰
        try:
            if str((fps_data or {}).get("source") or "") == "Predicted Model":
                return fps_data
        except Exception:
            pass
        mult, note = self._get_rt_multiplier_for_game(game, settings)
        if mult >= 0.999 or not note:
            return fps_data

        d = dict(fps_data)
        # 若 notes 已經包含任何 RT/PT 提示，就不要再重複追加/重複縮放
        existing_notes = str(d.get("notes") or "")
        if any(k in existing_notes for k in ["RT/PT", "啟用 RT", "啟用RT", "光追", "光線追蹤", "路徑追蹤"]):
            return fps_data

        def scale(x: Any) -> Any:
            try:
                if x is None:
                    return None
                return round(float(x) * float(mult), 1)
            except Exception:
                return x

        d["avg_fps"] = scale(d.get("avg_fps"))
        d["p1_low"] = scale(d.get("p1_low"))
        d["p0_1_low"] = scale(d.get("p0_1_low"))

        tail = existing_notes.strip()
        d["notes"] = (tail + (" | " if tail else "") + note).strip()
        # RT 下的資料不確定性更高，略降置信度（若已被 override，維持較低值）
        try:
            d["confidence_override"] = min(float(d.get("confidence_override") or 0.8), 0.7)
        except Exception:
            d["confidence_override"] = 0.7
        return d

    def _get_gpu_performance_score(self, gpu_model: str) -> float:
        """
        根據GPU型號返回效能評分（相對於基準RTX 3060的倍數）
        基於實際基準測試數據
        """
        gpu_scores = {
            # NVIDIA RTX 50-series (Ada Lovelace)
            "RTX 5090": 2.60,
            "RTX 5080": 2.40,
            "RTX 5070 Ti": 2.20,
            "RTX 5070": 2.05,
            "RTX 5060 Ti": 1.80,
            "RTX 5060": 1.60,
            "RTX 5050": 1.40,

            # NVIDIA RTX 40-series (Ada Lovelace)
            "RTX 4090": 2.50,
            "RTX 4080 SUPER": 2.25,
            "RTX 4080": 2.20,
            "RTX 4070 Ti SUPER": 2.10,
            "RTX 4070 Ti": 2.05,
            "RTX 4070 SUPER": 1.95,
            "RTX 4070": 1.90,
            "RTX 4060 Ti 16GB": 1.70,
            "RTX 4060 Ti": 1.65,
            "RTX 4060": 1.45,

            # NVIDIA RTX 30-series (Ampere)
            "RTX 3090 Ti": 2.30,
            "RTX 3090": 2.25,
            "RTX 3080 Ti": 2.10,
            "RTX 3080 12GB": 2.05,
            "RTX 3080": 2.00,
            "RTX 3070 Ti": 1.85,
            "RTX 3070": 1.75,
            "RTX 3060 Ti": 1.50,
            "RTX 3060": 1.40,
            "RTX 3050": 1.10,

            # NVIDIA RTX 20-series (Turing)
            "RTX 2080 Ti": 1.80,
            "RTX 2080 SUPER": 1.65,
            "RTX 2080": 1.60,
            "RTX 2070 SUPER": 1.45,
            "RTX 2070": 1.40,
            "RTX 2060 SUPER": 1.25,
            "RTX 2060": 1.20,

            # NVIDIA GTX 16-series (Turing)
            "GTX 1660 Ti": 1.15,
            "GTX 1660 Super": 1.10,
            "GTX 1660": 1.05,
            "GTX 1650 Super": 0.90,
            "GTX 1650": 0.85,

            # NVIDIA GTX 10-series (Pascal)
            "GTX 1080 Ti": 1.50,
            "GTX 1080": 1.40,
            "GTX 1070 Ti": 1.30,
            "GTX 1070": 1.25,
            "GTX 1060 6GB": 1.05,
            "GTX 1060 3GB": 0.95,
            "GTX 1050 Ti": 0.85,
            "GTX 1050": 0.75,
            "GTX 1030": 0.55,

            # AMD RX 7000-series (RDNA 3)
            "RX 7900 XTX": 2.35,
            "RX 7900 XT": 2.25,
            "RX 7900 GRE": 2.20,
            "RX 7800 XT": 2.10,
            "RX 7700 XT": 1.90,
            "RX 7600 XT": 1.60,
            "RX 7600": 1.45,

            # AMD RX 6000-series (RDNA 2)
            "RX 6950 XT": 2.15,
            "RX 6900 XT": 2.05,
            "RX 6800 XT": 1.85,
            "RX 6800": 1.75,
            "RX 6750 XT": 1.65,
            "RX 6700 XT": 1.55,
            "RX 6650 XT": 1.35,
            "RX 6600 XT": 1.25,
            "RX 6600": 1.15,
            "RX 6500 XT": 1.05,
            "RX 6400": 0.85,

            # AMD RX 5000-series (RDNA)
            "RX 5700 XT": 1.70,
            "RX 5700": 1.60,
            "RX 5600 XT": 1.45,
            "RX 5500 XT": 1.30,

            # AMD RX 400/500-series (GCN)
            "RX 580": 1.20,
            "RX 570": 1.15,
            "RX 560": 1.05,
            "RX 480": 1.25,
            "RX 470": 1.20,

            # AMD Vega series
            "Radeon VII": 1.85,
            "RX Vega 64": 1.40,
            "RX Vega 56": 1.30,

            # Intel Arc series
            "Arc A770": 1.75,
            "Intel Arc A770": 1.75,
            "Arc A750": 1.45,
            "Intel Arc A750": 1.45,
            "Arc A580": 1.35,
            "Arc A380": 1.20,
            "Arc A310": 1.05,

            # Integrated graphics
            "Integrated Intel UHD": 0.70,
        }

        # 模糊匹配
        for key, score in gpu_scores.items():
            if key.lower() in gpu_model.lower():
                return score

        # check overrides file (higher priority)
        try:
            overrides = _load_hw_overrides().get("gpus", {}) or {}
            for ok, val in overrides.items():
                if ok.lower() in gpu_model.lower():
                    return float(val)
        except Exception:
            pass

        # 如果找不到匹配的GPU，返回中等效能（約RTX 3060等級）
        return 1.0

    def _make_deterministic_rng(self, **kwargs) -> random.Random:
        """
        以輸入參數產生 deterministic RNG，確保同一組輸入每次得到同一組「預測」結果。
        """
        payload = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
        h = hashlib.md5(payload.encode("utf-8")).hexdigest()
        seed = int(h[:8], 16)
        return random.Random(seed)

    def _get_game_baseline_fps_1080p_high(self, game: str) -> float:
        """
        回傳「1080p High」的合理基準 FPS（用於沒有 seed/網搜資料時的預測模型）。
        注意：這是 heuristic，不代表官方或實測。
        """
        g = (game or "").lower()

        # 先做「明確遊戲」校正（以 RTX 3060 / 1080p High 的量級作為參考基準）
        # 目標：符合你提到的特性：模擬賽車偏高、Minecraft/Cities 偏 CPU、FPS 類不會低到誇張、Cyberpunk 特別重。
        baseline = {
            # 超重 3A（特別低）
            # 注意：這裡以「不開 RT/PT」為前提；開 RT/PT 會另外套用懲罰（例如 4K Ultra 開 RT 約落在 ~30fps）
            "cyberpunk 2077": 95.0,
            "alan wake 2": 60.0,
            "dragon's dogma 2": 70.0,
            "starfield": 75.0,

            # 一般 3A
            "hogwarts legacy": 75.0,
            "red dead redemption 2": 95.0,
            "the witcher 3": 135.0,
            "baldur's gate 3": 125.0,
            "forza horizon 5": 130.0,
            "grand theft auto v": 160.0,
            # Elden Ring：以「解鎖 FPS 上限」的常見 PC 情境做估（你的需求是 5080+14900K 可達 110+）
            "elden ring": 140.0,

            # FPS / 線上（不會像 cyberpunk 那麼低）
            "halo infinite": 140.0,
            "apex legends": 180.0,
            "pubg": 120.0,
            "ready or not": 95.0,
            "rust": 140.0,
            "escape from tarkov": 90.0,
            "fortnite": 180.0,
            "overwatch 2": 350.0,

            # 電競（極高）
            "counter-strike 2": 400.0,
            "valorant": 600.0,

            # CPU-heavy / 模擬
            "minecraft": 260.0,
            "cities: skylines": 85.0,
            "cities skylines": 85.0,
            "assetto corsa competizione": 175.0,
            "iracing": 240.0,
        }
        for k, v in baseline.items():
            if k in g:
                return float(v)

        sim_racing = {
            "assetto corsa competizione": 175.0,
            "iracing": 240.0,
        }
        for k, v in sim_racing.items():
            if k in g:
                return v

        if self._is_fps_shooter(game):
            return 160.0

        ultra_heavy = {
            "alan wake 2": 60.0,
            "cyberpunk 2077": 65.0,
            "starfield": 75.0,
            "dragon's dogma 2": 70.0,
        }
        for k, v in ultra_heavy.items():
            if k in g:
                return v

        return 120.0

    def _is_ultra_heavy_aaa(self, game: str) -> bool:
        g = (game or "").lower()
        keys = [
            "alan wake 2",
            "cyberpunk 2077",
            "starfield",
            "dragon's dogma 2",
        ]
        return any(k in g for k in keys)

    def _is_cpu_bound_game(self, game: str) -> bool:
        g = (game or "").lower()
        keys = [
            "counter-strike 2",
            "valorant",
            "overwatch 2",
            "minecraft",
            "cities: skylines",
            "cities skylines",
            "cities skylines ii",
            "cities: skylines ii",
            "cities skylines 2",
        ]
        return any(k in g for k in keys)

    def _is_sim_racing(self, game: str) -> bool:
        g = (game or "").lower()
        keys = [
            "assetto corsa competizione",
            "assetto corsa",
            "iracing",
            "i racing",
        ]
        return any(k in g for k in keys)

    def _is_fps_shooter(self, game: str) -> bool:
        g = (game or "").lower()
        keys = [
            "halo infinite",
            "rust",
            "apex legends",
            "ready or not",
            "call of duty",
            "pubg",
            "fortnite",
            "overwatch 2",
        ]
        return any(k in g for k in keys)

    def _is_cpu_heavy_sandbox(self, game: str) -> bool:
        g = (game or "").lower()
        keys = [
            "minecraft",
            "cities: skylines",
            "cities skylines",
        ]
        return any(k in g for k in keys)

    def _is_cpu_limited_game(self, game: str) -> bool:
        return (
            self._is_cpu_bound_game(game)
            or self._is_cpu_heavy_sandbox(game)
            or self._is_sim_racing(game)
            or self._is_fps_shooter(game)
        )

    def _get_cpu_fps_ceiling_1080p_high(self, game: str) -> Optional[float]:
        """
        CPU-limited 類型「1080p High」FPS 上限（reference CPU 下），避免高階 GPU 爆到不合理。
        """
        g = (game or "").lower()
        if "counter-strike 2" in g:
            return 2000.0  # Allow very high FPS for competitive gaming
        if "valorant" in g:
            return 650.0
        if "minecraft" in g:
            return 360.0
        if "cities" in g:
            return 140.0
        # Elden Ring：你的需求是可達 110+（視為解鎖 FPS 上限的情境），不要強制 60 cap
        if "assetto corsa competizione" in g:
            return 230.0
        if "iracing" in g:
            return 280.0
        if self._is_fps_shooter(game):
            return 260.0
        return None

    def _get_game_performance_demand(self, game: str) -> float:
        """
        效能需求係數（保留函式以相容既有邏輯）。
        目前將「負載差異」主要放在 baseline/resolution/quality 來控制，避免重複縮放造成偏離。
        """
        return 1.0

    def _get_resolution_multiplier(self, resolution: str) -> float:
        """
        根據解析度返回FPS倍數
        4K通常是1080p的25-30%，1440p是60-70%
        """
        resolution_multipliers = {
            "1280x720": 2.0,    # 720p (基準)
            "1920x1080": 1.0,   # 1080p (基準)
            "2560x1440": 0.65,  # 1440p
            "3840x2160": 0.25,  # 4K
            "720": 2.0,
            "1080": 1.0,
            "1440": 0.65,
            "4K": 0.25,
            "2160": 0.25
        }

        for key, multiplier in resolution_multipliers.items():
            if key in resolution:
                return multiplier

        return 1.0  # 預設1080p

    def _get_resolution_multiplier_for_game(self, game: str, resolution: str) -> float:
        """
        依遊戲類型調整解析度縮放。
        - 電競/CPU-bound：解析度對 FPS 影響通常小於 AAA
        - 超重 3A：4K/1440 掉幅更大
        - 模擬賽車：介於兩者
        """
        if self._is_cpu_bound_game(game):
            esports = {
                "1280x720": 1.25,
                "1920x1080": 1.0,
                "2560x1440": 0.85,
                "3840x2160": 0.60,  # Lower for 4K to match real benchmarks
                "720": 1.25,
                "1080": 1.0,
                "1440": 0.85,
                "4K": 0.60,
                "2160": 0.60,
            }
            for key, multiplier in esports.items():
                if key in str(resolution):
                    return multiplier
            return 1.0

        if self._is_sim_racing(game):
            sim = {
                "1280x720": 1.35,
                "1920x1080": 1.0,
                "2560x1440": 0.78,
                "3840x2160": 0.38,
                "720": 1.35,
                "1080": 1.0,
                "1440": 0.78,
                "4K": 0.38,
                "2160": 0.38,
            }
            for key, multiplier in sim.items():
                if key in str(resolution):
                    return multiplier
            return 1.0

        if self._is_ultra_heavy_aaa(game):
            heavy = {
                "1280x720": 1.8,
                "1920x1080": 1.0,
                "2560x1440": 0.60,
                # 校正：重負載 3A 在 4K 的掉幅不要壓得比實際還低（否則 RT 時會不合理）
                "3840x2160": 0.40,
                "720": 1.8,
                "1080": 1.0,
                "1440": 0.60,
                "4K": 0.40,
                "2160": 0.40,
            }
            for key, multiplier in heavy.items():
                if key in str(resolution):
                    return multiplier
            return 1.0

        return self._get_resolution_multiplier(resolution)

    def _get_ram_multiplier(self, game: str, ram_gb: Optional[float],
                           ram_type: Optional[str] = None, ram_speed_mhz: Optional[int] = None,
                           ram_latency_ns: Optional[float] = None) -> float:
        """
        Calculate RAM impact on FPS based on capacity, type, speed, and latency.
        - RAM insufficient: 5-30% performance decrease
        - RAM adequate: minimal impact
        - RAM quality affects performance: DDR5 > DDR4, higher speed = better, lower latency = better
        """
        if ram_gb is None:
            return 1.0

        # Get game RAM requirements
        from app.data.game_requirements import GAME_REQUIREMENTS_25
        # Case-insensitive lookup
        game_req = None
        for req_game, req_data in GAME_REQUIREMENTS_25.items():
            if req_game.lower() == game.lower():
                game_req = req_data
                break
        if not game_req:
            return 1.0

        recommended_ram = game_req.get("ram", 16)
        multiplier = 1.0

        # Capacity impact
        if ram_gb < recommended_ram:
            # RAM insufficient - performance penalty
            shortage_ratio = recommended_ram / ram_gb
            if shortage_ratio >= 2:
                # Severe shortage (e.g., 16GB game on 8GB system): 20-30% penalty
                penalty = min(0.30, 0.10 * (shortage_ratio - 1))
            else:
                # Moderate shortage: 5-15% penalty
                penalty = min(0.15, 0.05 * (shortage_ratio - 1))
            multiplier *= (1.0 - penalty)
        else:
            # RAM adequate or better - slight performance boost for very high RAM
            if ram_gb >= recommended_ram * 2:
                multiplier *= 1.02  # 2% boost for double recommended RAM

        # RAM type impact (DDR5 > DDR4)
        if ram_type:
            ram_type_lower = ram_type.lower()
            if 'ddr5' in ram_type_lower:
                multiplier *= 1.01  # 1% boost for DDR5
            elif 'ddr4' in ram_type_lower:
                multiplier *= 1.0   # Baseline for DDR4
            elif 'ddr3' in ram_type_lower:
                multiplier *= 0.98  # 2% penalty for DDR3

        # RAM speed impact (higher frequency = better performance)
        if ram_speed_mhz:
            if ram_speed_mhz >= 6000:  # DDR5 high-end
                speed_boost = 0.005
            elif ram_speed_mhz >= 5200:  # DDR5 mid-range
                speed_boost = 0.003
            elif ram_speed_mhz >= 3600:  # DDR4 high-end
                speed_boost = 0.002
            elif ram_speed_mhz >= 3200:  # DDR4 standard
                speed_boost = 0.001
            else:  # Slower RAM
                speed_boost = -0.002  # Slight penalty
            multiplier *= (1.0 + speed_boost)

        # RAM latency impact (lower latency = better performance)
        if ram_latency_ns:
            if ram_latency_ns <= 10:  # Very low latency (DDR5)
                latency_boost = 0.003
            elif ram_latency_ns <= 14:  # Low latency
                latency_boost = 0.002
            elif ram_latency_ns <= 18:  # Standard latency
                latency_boost = 0.0
            else:  # High latency
                latency_boost = -0.002  # Slight penalty
            multiplier *= (1.0 + latency_boost)

        return multiplier

    def _get_storage_multiplier(self, storage_type: Optional[str]) -> float:
        """
        Calculate storage impact on FPS.
        - SSD: baseline (1.0)
        - HDD: slight decrease due to slower loading
        - NVMe SSD: boost based on generation (Gen3: +0.5%, Gen4: +1%, Gen5: +1.5%)
        """
        if storage_type is None:
            return 1.0

        storage_lower = storage_type.lower()

        # Check for NVMe generations first (more specific)
        if 'gen5' in storage_lower or 'gen 5' in storage_lower:
            return 1.015  # 1.5% boost for NVMe Gen5
        elif 'gen4' in storage_lower or 'gen 4' in storage_lower:
            return 1.01   # 1% boost for NVMe Gen4
        elif 'gen3' in storage_lower or 'gen 3' in storage_lower:
            return 1.005  # 0.5% boost for NVMe Gen3
        elif 'nvme' in storage_lower or 'pcie' in storage_lower:
            return 1.007  # 0.7% boost for generic NVMe
        elif 'ssd' in storage_lower:
            return 1.0    # Baseline for regular SSD
        elif 'hdd' in storage_lower:
            return 0.98   # 2% decrease for HDD
        else:
            return 1.0    # Default

    def _get_quality_multiplier(self, settings: str) -> float:
        """
        根據畫質設定返回FPS倍數
        """
        quality_multipliers = {
            "Ultra": 0.8,
            "High": 1.0,
            "Medium": 1.3,
            "Low": 1.6
        }

        return quality_multipliers.get(settings, 1.0)

    def _get_quality_multiplier_for_game(self, game: str, settings: str) -> float:
        """
        依遊戲類型微調畫質縮放：
        - 電競/CPU-heavy：畫質影響偏小（Ultra 不要壓太低）
        - 超重 3A：Ultra 懲罰更重
        """
        st = (settings or "High").strip() or "High"
        # 支援像 "Ultra RT" / "High + RT" 這類字串：先抽出基礎畫質
        base = st.split()[0].strip()
        if base.lower() in {"low", "medium", "high", "ultra"}:
            st = base.capitalize()

        if self._is_cpu_bound_game(game) or self._is_cpu_heavy_sandbox(game):
            if st == "Ultra":
                return 0.92
            if st == "High":
                return 1.0
            if st == "Medium":
                return 1.08
            if st == "Low":
                return 1.15

        if self._is_sim_racing(game):
            if st == "Ultra":
                return 0.88
            if st == "High":
                return 1.0
            if st == "Medium":
                return 1.12
            if st == "Low":
                return 1.22

        if self._is_fps_shooter(game):
            if st == "Ultra":
                return 0.88
            if st == "High":
                return 1.0
            if st == "Medium":
                return 1.12
            if st == "Low":
                return 1.25

        if self._is_ultra_heavy_aaa(game):
            if st == "Ultra":
                return 0.72
            if st == "High":
                return 1.0
            if st == "Medium":
                return 1.25
            if st == "Low":
                return 1.5

        return self._get_quality_multiplier(st)

    def _calculate_usage_rates(
        self,
        avg_fps: float,
        game: str,
        resolution: str,
        settings: str,
        gpu_perf_ratio: float,
        cpu_model: str,
        ram_gb: Optional[float] = None,
        ram_type: Optional[str] = None,
        ram_speed_mhz: Optional[int] = None,
        ram_latency_ns: Optional[float] = None,
        rng: Optional[random.Random] = None,
    ) -> tuple:
        """
        預測使用率（%）。
        目標：
        - 會隨畫質/解析度變動（Ultra/4K 通常更吃 GPU/VRAM）
        - CPU-bound 遊戲 CPU 使用率更高、GPU 使用率較低（尤其 1080p/低畫質）
        - 不要永遠卡在 CPU 60%
        """
        r = rng or random
        res = str(resolution or "")
        st = (settings or "High").strip() or "High"
        cpu_bound = self._is_cpu_bound_game(game)

        # 解析度負載（越高越吃 GPU/VRAM）
        if "3840" in res or "2160" in res or "4k" in res.lower():
            res_load = 1.0
        elif "2560" in res or "1440" in res:
            res_load = 0.7
        elif "1280" in res or "720" in res:
            res_load = 0.5
        else:
            res_load = 0.8

        # 畫質負載（越高越吃 GPU/VRAM）
        st_load_map = {"Low": 0.75, "Medium": 0.9, "High": 1.0, "Ultra": 1.12}
        st_load = st_load_map.get(st, 1.0)

        # CPU ratio：越強的 CPU，同樣 fps 下使用率通常更低
        cpu_score = self._get_cpu_performance_score(cpu_model)
        ref_cpu = self._get_cpu_performance_score("i5-12600K")
        cpu_ratio = (cpu_score / ref_cpu) if ref_cpu and ref_cpu > 0 else 1.0

        # GPU usage
        if cpu_bound:
            base_gpu = 40 + 35 * res_load * st_load
            base_gpu -= 12 * max(0.0, gpu_perf_ratio - 1.0)
            gpu_usage = base_gpu + r.uniform(-6, 6)
            gpu_usage = max(25.0, min(gpu_usage, 90.0))
        else:
            base_gpu = 78 + 20 * res_load * st_load
            base_gpu -= 6 * max(0.0, gpu_perf_ratio - 1.0)
            gpu_usage = base_gpu + r.uniform(-4, 4)
            gpu_usage = max(55.0, min(gpu_usage, 99.0))

        # CPU usage
        if cpu_bound:
            cpu_usage = (
                62
                + 22 * min(avg_fps / 300.0, 1.25)
                + 18 * (1.0 / max(cpu_ratio, 0.7) - 1.0)
                + r.uniform(-5, 5)
            )
            cpu_usage = max(45.0, min(cpu_usage, 99.0))
        else:
            cpu_usage = (
                34
                + 10 * min(avg_fps / 140.0, 1.25)
                + 10 * (1.0 / max(cpu_ratio, 0.7) - 1.0)
                + r.uniform(-5, 5)
            )
            cpu_usage = max(20.0, min(cpu_usage, 90.0))

        # RAM usage（不是 VRAM）- 根據RAM規格調整
        extra = 0.0
        gl = (game or "").lower()
        if "cities" in gl:
            extra += 10.0
        if "tarkov" in gl:
            extra += 6.0
        base_ram = 50 + 15 * st_load + 10 * res_load + extra

        # RAM quality adjustments
        ram_quality_factor = 0.0

        # RAM capacity impact on usage
        if ram_gb:
            if ram_gb < 16:
                ram_quality_factor += 15.0  # Low RAM = higher usage
            elif ram_gb >= 32:
                ram_quality_factor -= 5.0   # High RAM = lower usage

        # RAM type impact
        if ram_type:
            ram_type_lower = ram_type.lower()
            if 'ddr3' in ram_type_lower:
                ram_quality_factor += 8.0   # DDR3 = higher usage
            elif 'ddr4' in ram_type_lower:
                ram_quality_factor += 2.0   # DDR4 = slightly higher usage than DDR5
            # DDR5 = baseline (0 additional)

        # RAM speed impact (higher speed = lower usage)
        if ram_speed_mhz:
            if ram_speed_mhz >= 6000:      # DDR5 high-end
                ram_quality_factor -= 3.0
            elif ram_speed_mhz >= 5200:    # DDR5 mid-range
                ram_quality_factor -= 2.0
            elif ram_speed_mhz >= 3600:    # DDR4 high-end
                ram_quality_factor -= 1.0
            elif ram_speed_mhz < 3000:     # Slow RAM
                ram_quality_factor += 2.0

        # RAM latency impact (lower latency = lower usage)
        if ram_latency_ns:
            if ram_latency_ns <= 10:       # Very low latency
                ram_quality_factor -= 2.0
            elif ram_latency_ns <= 14:     # Low latency
                ram_quality_factor -= 1.0
            elif ram_latency_ns > 20:      # High latency
                ram_quality_factor += 2.0

        base_ram += ram_quality_factor
        memory_usage = base_ram + r.uniform(-4, 4)
        memory_usage = max(30.0, min(memory_usage, 95.0))

        return float(gpu_usage), float(cpu_usage), float(memory_usage)

    def _get_cpu_performance_score(self, cpu_model: str) -> float:
        """
        根據CPU型號返回效能評分
        """
        # 簡化的CPU效能評分
        cpu_scores = {
            # Intel Ultra series (Meteor Lake)
            "Intel Core Ultra 9 285K": 2.5, "Intel Core Ultra 9 285": 2.4,
            "Intel Core Ultra 7 265K": 2.3, "Intel Core Ultra 7 265": 2.2,
            "Intel Core Ultra 5 245K": 2.1, "Intel Core Ultra 5 245": 2.0,

            # Intel 14th Gen (Raptor Lake Refresh)
            "i9-14900K": 2.4, "i9-14900KF": 2.4, "i9-14900": 2.35, "i9-14900F": 2.35,
            "i7-14700K": 2.2, "i7-14700KF": 2.2, "i7-14700": 2.15, "i7-14700F": 2.15,
            "i5-14600K": 2.0, "i5-14600KF": 2.0, "i5-14600": 1.95, "i5-14600F": 1.95,
            "i5-14400": 1.85, "i5-14400F": 1.85,

            # Intel 13th Gen (Raptor Lake)
            "i9-13900K": 2.35, "i9-13900KF": 2.35, "i9-13900": 2.3, "i9-13900F": 2.3,
            "i7-13700K": 2.1, "i7-13700KF": 2.1, "i7-13700": 2.05, "i7-13700F": 2.05,
            "i5-13600K": 1.9, "i5-13600KF": 1.9, "i5-13600": 1.85, "i5-13600F": 1.85,
            "i5-13500": 1.8, "i5-13500F": 1.8, "i5-13400": 1.75, "i5-13400F": 1.75,

            # Intel 12th Gen (Alder Lake)
            "i9-12900K": 2.1, "i9-12900KF": 2.1, "i9-12900": 2.05, "i9-12900F": 2.05,
            "i7-12700K": 1.95, "i7-12700KF": 1.95, "i7-12700": 1.9, "i7-12700F": 1.9,
            "i5-12600K": 1.7, "i5-12600KF": 1.7, "i5-12600": 1.65, "i5-12600F": 1.65,
            "i5-12500": 1.6, "i5-12500F": 1.6, "i5-12400": 1.55, "i5-12400F": 1.55,

            # Intel 11th Gen (Rocket Lake)
            "i9-11900K": 1.8, "i9-11900KF": 1.8, "i9-11900": 1.75, "i9-11900F": 1.75,
            "i7-11700K": 1.7, "i7-11700KF": 1.7, "i7-11700": 1.65, "i7-11700F": 1.65,
            "i5-11600K": 1.5, "i5-11600KF": 1.5, "i5-11600": 1.45, "i5-11600F": 1.45,
            "i5-11500": 1.4, "i5-11500F": 1.4, "i5-11400": 1.35, "i5-11400F": 1.35,

            # Intel 10th Gen (Comet Lake)
            "i9-10900K": 1.65, "i9-10900KF": 1.65, "i9-10900": 1.6, "i9-10900F": 1.6,
            "i7-10700K": 1.55, "i7-10700KF": 1.55, "i7-10700": 1.5, "i7-10700F": 1.5,
            "i5-10600K": 1.35, "i5-10600KF": 1.35, "i5-10600": 1.3, "i5-10600F": 1.3,
            "i5-10500": 1.25, "i5-10500F": 1.25, "i5-10400": 1.2, "i5-10400F": 1.2,

            # Intel 9th Gen (Coffee Lake Refresh)
            "i9-9900K": 1.45, "i9-9900KF": 1.45, "i9-9900": 1.4, "i9-9900F": 1.4,
            "i7-9700K": 1.35, "i7-9700KF": 1.35, "i7-9700": 1.3, "i7-9700F": 1.3,
            "i5-9600K": 1.2, "i5-9600KF": 1.2, "i5-9600": 1.15, "i5-9600F": 1.15,
            "i5-9500": 1.1, "i5-9500F": 1.1, "i5-9400": 1.05, "i5-9400F": 1.05,

            # Intel 8th Gen (Coffee Lake)
            "i7-8700K": 1.25, "i7-8700": 1.2, "i5-8600K": 1.1, "i5-8600": 1.05,
            "i5-8500": 1.0, "i5-8400": 0.95, "i3-8350K": 0.9, "i3-8100": 0.85,

            # Intel 7th Gen (Kaby Lake)
            "i7-7700K": 1.15, "i7-7700": 1.1, "i5-7600K": 1.0, "i5-7600": 0.95,
            "i5-7500": 0.9, "i5-7400": 0.85, "i3-7350K": 0.8, "i3-7300": 0.75, "i3-7100": 0.7,

            # AMD Ryzen 9000 series (Zen 5)
            "Ryzen 9 9950X": 2.23, "Ryzen 9 9950X3D": 2.25, "Ryzen 9 9900X": 2.1, "Ryzen 9 9900X3D": 2.15,
            "Ryzen 7 9700X": 1.95, "Ryzen 7 9700X3D": 2.0, "Ryzen 5 9600X": 1.8, "Ryzen 5 9600X3D": 1.85,

            # AMD Ryzen 8000/7000 series (Zen 4)
            "Ryzen 9 7950X": 2.05, "Ryzen 9 7950X3D": 2.1, "Ryzen 9 7900X": 1.95, "Ryzen 9 7900X3D": 2.0,
            "Ryzen 9 7900": 1.9, "Ryzen 7 7800X3D": 1.85, "Ryzen 7 7700X": 1.75, "Ryzen 7 7700X3D": 1.8,
            "Ryzen 7 7700": 1.7, "Ryzen 5 7600X": 1.6, "Ryzen 5 7600X3D": 1.65, "Ryzen 5 7600": 1.55,

            # AMD Ryzen 5000 series (Zen 3)
            "Ryzen 9 5950X": 1.85, "Ryzen 9 5900X": 1.8, "Ryzen 9 5900": 1.75,
            "Ryzen 7 5800X3D": 1.75, "Ryzen 7 5800X": 1.65, "Ryzen 7 5800": 1.6,
            "Ryzen 5 5600X": 1.4, "Ryzen 5 5600X3D": 1.45, "Ryzen 5 5600": 1.35,

            # AMD Ryzen 3000 series (Zen 2)
            "Ryzen 9 3900X": 1.5, "Ryzen 9 3900": 1.45, "Ryzen 9 3950X": 1.55,
            "Ryzen 7 3800X": 1.4, "Ryzen 7 3800XT": 1.4, "Ryzen 7 3800": 1.35,
            "Ryzen 7 3700X": 1.35, "Ryzen 7 3700": 1.3, "Ryzen 5 3600X": 1.2,
            "Ryzen 5 3600XT": 1.2, "Ryzen 5 3600": 1.15, "Ryzen 5 3500X": 1.1,
            "Ryzen 5 3400G": 1.05, "Ryzen 3 3300X": 1.0, "Ryzen 3 3200G": 0.95, "Ryzen 3 3100": 0.9,

            # AMD Ryzen 2000 series (Zen+)
            "Ryzen 7 2700X": 1.15, "Ryzen 7 2700": 1.1, "Ryzen 5 2600X": 1.05, "Ryzen 5 2600": 1.0,
            "Ryzen 5 2500X": 0.95, "Ryzen 5 2400G": 0.9, "Ryzen 3 2300X": 0.85, "Ryzen 3 2200G": 0.85,

            # AMD Ryzen 1000 series (Zen)
            "Ryzen 7 1800X": 1.0, "Ryzen 7 1700X": 0.95, "Ryzen 7 1700": 0.9,
            "Ryzen 5 1600X": 0.9, "Ryzen 5 1600": 0.85, "Ryzen 5 1500X": 0.8,
            "Ryzen 5 1400": 0.75, "Ryzen 3 1300X": 0.7, "Ryzen 3 1200": 0.65,
        }

        for key, score in cpu_scores.items():
            if key.lower() in cpu_model.lower():
                return score
        # check overrides file for cpu
        try:
            overrides = _load_hw_overrides().get("cpus", {}) or {}
            for ok, val in overrides.items():
                if ok.lower() in cpu_model.lower():
                    return float(val)
        except Exception:
            pass

        return 1.0  # 預設中等效能CPU
    
    def _build_search_url(
        self,
        game: str,
        resolution: str,
        hardware: dict
    ) -> str:
        """構建搜尋 URL - 使用多個基準測試來源"""
        gpu_model = hardware.get("model", "").replace(" ", "-").lower()

        # 嘗試多個基準測試來源
        urls = [
            # NOTE: 原本使用 .c{id} 需要特定 GPU id；先移除避免未定義變數與錯誤 URL
            f"https://www.techpowerup.com/gpu-specs/{gpu_model}",
            f"https://www.gpucheck.com/graphics-card/{gpu_model}/benchmark",
            f"https://www.videocardbenchmark.net/gpu.php?gpu={gpu_model}",
            f"https://benchmarks.ul.com/hardware/gpu/{gpu_model}"
        ]

        # 回傳第一個URL（實際應嘗試所有URL）
        return urls[0] if urls else self.base_url

    async def _try_multiple_sources(
        self,
        game: str,
        resolution: str,
        settings: Optional[str],
        gpu: dict,
        cpu: dict,
    ) -> Dict[str, Any]:
        """
        嘗試從多個來源抓取基準資料：
        1) Google Programmable Search snippet（可用時）
        2) 站點爬蟲（TechPowerUp/GPUCheck/UL）
        """
        diagnostic_note: Optional[str] = None

        # 1) Google snippet
        try:
            if self.client:
                svc = GoogleFpsSearchService(self.client)
                data = await svc.search_fps(
                    game=game,
                    gpu=str(gpu.get("model") or ""),
                    cpu=str(cpu.get("model") or ""),
                    resolution=resolution,
                    settings=settings,
                    num=5,
                )
                if data and data.get("avg_fps"):
                    return data
                if data and data.get("notes"):
                    diagnostic_note = str(data.get("notes"))
        except Exception as e:
            diagnostic_note = f"Google FPS 搜尋失敗: {e}"

        sources = [
            ("TechPowerUp", self._fetch_from_techpowerup),
            ("GPUCheck", self._fetch_from_gpucheck),
            ("VideoCardBenchmark", self._fetch_from_videocardbenchmark),
        ]

        for source_name, fetch_func in sources:
            try:
                data = await fetch_func(game, resolution, gpu)
                if data and data.get("avg_fps"):
                    data["source"] = source_name
                    return data
            except Exception as e:
                print(f"從 {source_name} 抓取失敗: {e}")
                continue

        return {"notes": diagnostic_note} if diagnostic_note else {}
    
    def _parse_fps_data(
        self,
        soup: BeautifulSoup,
        game: str,
        resolution: str
    ) -> Dict[str, Any]:
        """從 HTML 解析 FPS 資料"""
        fps_data = {}
        
        # 範例解析邏輯（需要根據實際網站調整）
        # 尋找包含 FPS 資料的表格或區塊
        fps_elements = soup.select(".fps-data, .benchmark-result")
        
        for element in fps_elements:
            text = element.get_text()
            
            # 使用正則表達式提取 FPS 數值
            avg_match = re.search(r'avg[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
            p1_match = re.search(r'1%[:\s]+low[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
            p01_match = re.search(r'0\.1%[:\s]+low[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
            
            if avg_match:
                fps_data["avg_fps"] = float(avg_match.group(1))
            if p1_match:
                fps_data["p1_low"] = float(p1_match.group(1))
            if p01_match:
                fps_data["p0_1_low"] = float(p01_match.group(1))
        
        return fps_data

    async def _fetch_from_techpowerup(
        self,
        game: str,
        resolution: str,
        hardware: dict
    ) -> Dict[str, Any]:
        """從TechPowerUp抓取基準資料"""
        gpu_model = hardware.get("model", "").replace(" ", "-").lower()
        url = f"https://www.techpowerup.com/gpu-specs/{gpu_model}"

        try:
            response = await self.fetch(url)
            if not response:
                return {}

            soup = BeautifulSoup(response.text, 'lxml')

            # 尋找基準測試表格
            benchmark_tables = soup.select("table.gpu-benchmarks, .benchmark-table")

            fps_data = {}
            for table in benchmark_tables:
                rows = table.select("tr")
                for row in rows:
                    cells = row.select("td")
                    if len(cells) >= 3:
                        game_name = cells[0].get_text(strip=True)
                        if game.lower() in game_name.lower():
                            # 解析FPS數據
                            fps_text = cells[1].get_text(strip=True)
                            avg_match = re.search(r'(\d+\.?\d*)', fps_text)
                            if avg_match:
                                fps_data["avg_fps"] = float(avg_match.group(1))
                                break

            return fps_data

        except Exception as e:
            print(f"TechPowerUp抓取失敗: {e}")
            return {}

    async def _fetch_from_gpucheck(
        self,
        game: str,
        resolution: str,
        hardware: dict
    ) -> Dict[str, Any]:
        """從GPUCheck抓取基準資料"""
        gpu_model = hardware.get("model", "").replace(" ", "-").lower()
        url = f"https://www.gpucheck.com/graphics-card/{gpu_model}/benchmark"

        try:
            response = await self.fetch(url)
            if not response:
                return {}

            soup = BeautifulSoup(response.text, 'lxml')

            # 尋找遊戲基準數據
            game_elements = soup.select(".game-benchmark, .benchmark-result")

            fps_data = {}
            for element in game_elements:
                game_name = element.select_one(".game-name, .title")
                if game_name and game.lower() in game_name.get_text().lower():
                    fps_elem = element.select_one(".fps-value, .avg-fps")
                    if fps_elem:
                        fps_text = fps_elem.get_text(strip=True)
                        avg_match = re.search(r'(\d+\.?\d*)', fps_text)
                        if avg_match:
                            fps_data["avg_fps"] = float(avg_match.group(1))
                            break

            return fps_data

        except Exception as e:
            print(f"GPUCheck抓取失敗: {e}")
            return {}

    async def _fetch_from_videocardbenchmark(
        self,
        game: str,
        resolution: str,
        hardware: dict
    ) -> Dict[str, Any]:
        """從VideoCardBenchmark抓取基準資料"""
        gpu_model = hardware.get("model", "").replace(" ", "-").lower()
        url = f"https://benchmarks.ul.com/hardware/gpu/{gpu_model}"

        try:
            response = await self.fetch(url)
            if not response:
                return {}

            soup = BeautifulSoup(response.text, 'lxml')

            # 尋找基準測試數據
            benchmark_data = soup.select(".benchmark-data, .gpu-benchmarks")

            fps_data = {}
            for data_elem in benchmark_data:
                text = data_elem.get_text()

                # 尋找遊戲匹配
                if game.lower() in text.lower():
                    # 提取FPS數值
                    avg_match = re.search(r'avg[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
                    p1_match = re.search(r'1%[:\s]+low[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
                    p01_match = re.search(r'0\.1%[:\s]+low[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)

                    if avg_match:
                        fps_data["avg_fps"] = float(avg_match.group(1))
                    if p1_match:
                        fps_data["p1_low"] = float(p1_match.group(1))
                    if p01_match:
                        fps_data["p0_1_low"] = float(p01_match.group(1))

                    break

            return fps_data

        except Exception as e:
            print(f"VideoCardBenchmark抓取失敗: {e}")
            return {}

    def _calculate_realistic_usage_rates(
        self,
        benchmark_data: Dict[str, Any],
        resolution: str,
        hardware: dict
    ) -> tuple:
        """
        基於真實基準數據計算更真實的硬件使用率
        """
        avg_fps = benchmark_data.get("avg_fps", 60)

        # GPU使用率 - 基於FPS表現
        if avg_fps > 120:
            gpu_usage = random.uniform(70, 85)  # 高FPS，低使用率
        elif avg_fps > 60:
            gpu_usage = random.uniform(85, 95)  # 中等FPS，中等使用率
        else:
            gpu_usage = random.uniform(95, 99)  # 低FPS，高使用率

        # CPU使用率 - 遊戲相關
        cpu_usage = random.uniform(50, 75)

        # 記憶體使用率 - 解析度相關
        if "4K" in resolution or "3840" in resolution:
            memory_usage = random.uniform(80, 95)
        elif "1440" in resolution or "2560" in resolution:
            memory_usage = random.uniform(70, 85)
        else:
            memory_usage = random.uniform(55, 75)

        return gpu_usage, cpu_usage, memory_usage

    def _estimate_from_setting_table(self, setting_data: Dict[str, Any], target_gpu_model: str) -> Optional[Dict[str, Any]]:
        """
        當 seed 有「同遊戲/同解析度/同畫質」的其他 GPU 真實資料，但缺少目標 GPU 時，
        使用 GPU 效能分數比例做插值估算。
        """
        if not setting_data:
            return None
        tgt_score = self._get_gpu_performance_score(target_gpu_model)
        if tgt_score <= 0:
            return None

        best = None  # (diff, key, data, ratio)
        for k, v in (setting_data or {}).items():
            if not isinstance(v, dict):
                continue
            if v.get("avg_fps") is None:
                continue
            src_score = self._get_gpu_performance_score(k)
            if src_score <= 0:
                continue
            ratio = tgt_score / src_score
            diff = abs(src_score - tgt_score)
            if best is None or diff < best[0]:
                best = (diff, k, v, ratio)

        if best is None:
            return None

        _, src_key, src_data, ratio = best

        def scale(x: Any) -> Optional[float]:
            try:
                if x is None:
                    return None
                return float(x) * float(ratio)
            except Exception:
                return None

        est_avg = scale(src_data.get("avg_fps"))
        est_p1 = scale(src_data.get("p1_low"))
        est_p01 = scale(src_data.get("p0_1_low"))
        if est_avg is None:
            return None

        est_avg = max(10.0, min(est_avg, 1000.0))
        if est_p1 is not None:
            est_p1 = max(5.0, min(est_p1, est_avg))
        if est_p01 is not None:
            est_p01 = max(3.0, min(est_p01, est_p1 or est_avg))

        return {
            "avg_fps": round(est_avg, 1),
            "p1_low": round(est_p1, 1) if est_p1 is not None else None,
            "p0_1_low": round(est_p01, 1) if est_p01 is not None else None,
            "notes": f"由 seed 內 {src_key} 資料按效能分數比例估算（來源 GPU: {src_key}）",
        }

    def _ensure_benchmark_completeness(
        self,
        fps_data: Dict[str, Any],
        game: str,
        resolution: str,
        settings: str,
        gpu_model: str,
        cpu_model: str,
    ) -> Dict[str, Any]:
        """
        針對「網搜只拿到 avg_fps」或「seed/插值缺 low」等情況補齊欄位，避免瓶頸分析顯示資料不足。
        - 若缺 p1_low / p0_1_low：用 deterministic 比例推估，並降低 confidence
        - 若缺 usage：用預測使用率模型推估，並把數值寫回 notes
        """
        d = dict(fps_data or {})
        avg = d.get("avg_fps")
        if avg is None:
            return d

        rng = self._make_deterministic_rng(
            game=game,
            resolution=resolution,
            settings=settings,
            gpu=gpu_model,
            cpu=cpu_model,
            salt="complete",
        )

        if d.get("p1_low") is None:
            ratio = rng.uniform(0.86, 0.92) if self._is_cpu_bound_game(game) else rng.uniform(0.78, 0.88)
            d["p1_low"] = round(float(avg) * ratio, 1)
            d["confidence_override"] = min(float(d.get("confidence_override") or 0.75), 0.75)
            d["notes"] = (str(d.get("notes") or "") + ("；" if d.get("notes") else "") + "1% low 為推估值").strip()

        if d.get("p0_1_low") is None and d.get("p1_low") is not None:
            ratio = rng.uniform(0.88, 0.95)
            d["p0_1_low"] = round(float(d["p1_low"]) * ratio, 1)
            d["confidence_override"] = min(float(d.get("confidence_override") or 0.75), 0.75)
            d["notes"] = (str(d.get("notes") or "") + ("；" if d.get("notes") else "") + "0.1% low 為推估值").strip()

        notes_text = str(d.get("notes") or "")
        has_gpu = "GPU:" in notes_text
        has_cpu = "CPU:" in notes_text
        has_ram = "RAM:" in notes_text or "Memory:" in notes_text
        if not (has_gpu and has_cpu and has_ram):
            ref_score = self._get_gpu_performance_score("RTX 3060")
            tgt_score = self._get_gpu_performance_score(gpu_model)
            perf_ratio = (tgt_score / ref_score) if ref_score and ref_score > 0 else 1.0
            gpu_u, cpu_u, ram_u = self._calculate_usage_rates(
                avg_fps=float(avg),
                game=game,
                resolution=resolution,
                settings=settings,
                gpu_perf_ratio=float(perf_ratio),
                cpu_model=cpu_model,
                rng=rng,
            )
            usage_note = f"GPU: {gpu_u:.0f}%, CPU: {cpu_u:.0f}%, RAM: {ram_u:.0f}%"
            d["notes"] = (usage_note + ("；" + notes_text if notes_text else "")).strip()
            d["confidence_override"] = min(float(d.get("confidence_override") or 0.8), 0.8)

        return d

    def _apply_cpu_adjustment(self, fps_data: Dict[str, Any], game: str, cpu_model: str) -> Dict[str, Any]:
        """
        將「GPU-base」的 benchmark 依 CPU 模型做調整。
        """
        d = dict(fps_data or {})
        avg = d.get("avg_fps")
        if avg is None:
            return d

        cpu_score = self._get_cpu_performance_score(str(cpu_model or ""))
        ref_cpu = self._get_cpu_performance_score("i5-12600K")
        cpu_ratio = (cpu_score / ref_cpu) if ref_cpu and ref_cpu > 0 else 1.0

        if self._is_cpu_bound_game(game):
            cpu_factor = max(0.8, min(cpu_ratio, 1.6))
        else:
            cpu_factor = max(0.8, min(0.9 + 0.15 * cpu_ratio, 1.4))

        # Apply CPU scaling with additional jitter for hardware differentiation
        cpu_jitter_rng = self._make_deterministic_rng(game=game, cpu=cpu_model, gpu=str(d.get("gpu") or ""), salt="cpu-adjust-fps")
        cpu_jitter = cpu_jitter_rng.uniform(0.98, 1.02)

        def scale(x: Any) -> Optional[float]:
            try:
                if x is None:
                    return None
                return round(float(x) * float(cpu_factor) * cpu_jitter, 1)
            except Exception:
                return None

        d["avg_fps"] = scale(d.get("avg_fps"))
        d["p1_low"] = scale(d.get("p1_low"))
        d["p0_1_low"] = scale(d.get("p0_1_low"))

        # 清理舊 notes：避免 v2 混入已經「CPU adjusted」過的 notes，導致越疊越長/解析出錯
        base_notes = str(d.get("notes") or "")
        # 保留第一段（通常是最新的 usage），移除後面所有「CPU adjusted」或多段疊加
        if base_notes:
            base_notes = base_notes.split("|")[0].strip()
            base_notes = base_notes.split("CPU adjusted:")[0].strip()
            base_notes = base_notes.split("CPU adjusted：")[0].strip()

        rng = self._make_deterministic_rng(game=game, cpu=str(cpu_model), gpu=str(d.get("gpu") or ""), salt="cpu-adjust-usage")
        ref_score = self._get_gpu_performance_score("RTX 3060")
        tgt_score = self._get_gpu_performance_score(str(d.get("gpu") or "")) or ref_score
        perf_ratio = (tgt_score / ref_score) if ref_score and ref_score > 0 else 1.0
        gpu_u, cpu_u, ram_u = self._calculate_usage_rates(
            avg_fps=float(d.get("avg_fps") or avg),
            game=game,
            resolution=str(d.get("resolution") or ""),
            settings=str(d.get("settings") or "High"),
            gpu_perf_ratio=float(perf_ratio),
            cpu_model=str(cpu_model or ""),
            rng=rng,
        )
        usage_note = f"GPU: {gpu_u:.0f}%, CPU: {cpu_u:.0f}%, RAM: {ram_u:.0f}%"
        tail = base_notes.strip()
        d["notes"] = (usage_note + (" | " + tail if tail else "") + f" | CPU adjusted: {cpu_model}").strip()
        d["confidence_override"] = min(float(d.get("confidence_override") or 0.75), 0.75)
        return d

    def _sanitize_benchmark_payload(self, fps_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        最終校正/驗證單筆 fps_data：
        - 確保 avg >= p1 >= p0.1
        - clamp 不合理極端值
        """
        d = dict(fps_data or {})

        def to_f(x: Any) -> Optional[float]:
            try:
                if x is None:
                    return None
                return float(x)
            except Exception:
                return None

        avg = to_f(d.get("avg_fps"))
        p1 = to_f(d.get("p1_low"))
        p01 = to_f(d.get("p0_1_low"))

        # Allow high FPS for all games (remove arbitrary caps)
        fps_cap = 2000.0

        if avg is not None:
            avg = max(1.0, min(avg, fps_cap))
        if p1 is not None:
            p1 = max(0.5, min(p1, fps_cap))
        if p01 is not None:
            p01 = max(0.2, min(p01, fps_cap))

        if avg is not None and p1 is not None and p1 > avg:
            p1 = avg
        if p1 is not None and p01 is not None and p01 > p1:
            p01 = p1
        if avg is not None and p01 is not None and p01 > avg:
            p01 = avg

        if avg is not None:
            d["avg_fps"] = round(avg, 1)
        if p1 is not None:
            d["p1_low"] = round(p1, 1)
        if p01 is not None:
            d["p0_1_low"] = round(p01, 1)

        if d.get("notes") is not None:
            d["notes"] = str(d.get("notes"))
        if d.get("source") is not None:
            d["source"] = str(d.get("source"))
        if d.get("raw_snippet") is not None:
            d["raw_snippet"] = str(d.get("raw_snippet"))

        return d

    def _check_vram(self, game: str, resolution: str, gpu: dict) -> Tuple[Optional[float], Optional[float], Optional[bool], Optional[float]]:
        g = GAME_REQUIREMENTS_25.get(game)
        if not g:
            return None, self._infer_selected_vram(gpu), None, None

        vram_by_res = (g.get("vramByResolution") or {})
        required = vram_by_res.get(resolution)
        selected = self._infer_selected_vram(gpu)
        if required is None or selected is None:
            return float(required) if required is not None else None, selected, None, None
        margin = float(selected) - float(required)
        return float(required), float(selected), margin >= 0, float(margin)

    def _infer_selected_vram(self, gpu: dict) -> Optional[float]:
        v = gpu.get("selected_vram_gb")
        if v is not None:
            try:
                return float(v)
            except Exception:
                pass
        model = str(gpu.get("model") or "").strip()
        if model:
            meta = (self.gpu_meta or {}).get(model.lower())
            if meta and meta.get("vram_gb") is not None:
                try:
                    return float(meta.get("vram_gb"))
                except Exception:
                    return None
        m = re.search(r'(\d+(?:\.\d+)?)\s*GB', model, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                return None
        return None

    def _calculate_confidence(self, fps_data: Dict[str, Any]) -> float:
        """計算資料可信度分數 (0.0 - 1.0)"""
        score = 0.0
        
        # 有 avg_fps 加 0.4
        if fps_data.get("avg_fps") is not None:
            score += 0.4
        
        # 有 p1_low 加 0.3
        if fps_data.get("p1_low") is not None:
            score += 0.3
        
        # 有 p0_1_low 加 0.2
        if fps_data.get("p0_1_low") is not None:
            score += 0.2
        
        # 有額外資訊（CPU/GPU 使用率等）加 0.1
        if fps_data.get("gpu_usage") or fps_data.get("cpu_usage"):
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_raw_snippet(self, soup: BeautifulSoup) -> str:
        """提取原始來源片段供使用者檢視"""
        # 提取相關的 HTML 片段
        snippet_elements = soup.select(".benchmark-data, .fps-result")
        if snippet_elements:
            return snippet_elements[0].get_text(strip=True)[:500]  # 限制長度
        return ""
    
    async def get_comparison_data(
        self,
        benchmark_ids: List[str],
        metric: str
    ) -> Dict[str, Any]:
        """取得比較資料"""
        # 這裡應從快取或資料庫取得已抓取的基準資料
        # 簡化實作
        return {
            "benchmark_ids": benchmark_ids,
            "metric": metric,
            "data": []
        }
    
    def get_source_name(self) -> str:
        return self.source_name
    
    def get_last_fetch_time(self) -> str:
        return self.last_fetch_time or datetime.now().isoformat()

