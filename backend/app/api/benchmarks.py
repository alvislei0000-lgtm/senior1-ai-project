from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.scrapers.benchmark_scraper import BenchmarkScraper
from app.analyzers.bottleneck_analyzer import BottleneckAnalyzer

router = APIRouter()

def _extract_usage_from_notes(notes: str) -> dict:
    """
    從 notes 解析 GPU/CPU/RAM 使用率。
    相容格式：
    - GPU: 63%, CPU: 99%, RAM: 80%
    - GPU：63％ CPU：99％ RAM：80％
    - 多段 notes（以 | / ； 等分隔）→ 取第一組（BenchmarkScraper 會把當前結果放在最前面）
    """
    import re

    if not notes:
        return {"gpu_usage": None, "cpu_usage": None, "memory_usage": None}

    text = str(notes)
    # 取最前段，避免 v2 汙染或多 CPU 疊加造成解析到錯段
    head = re.split(r"[|；;\n\r]+", text, maxsplit=1)[0]

    def first_num(pattern: str) -> Optional[float]:
        m = re.search(pattern, head, re.IGNORECASE)
        if not m:
            return None
        try:
            return float(m.group(1))
        except Exception:
            return None

    # 同時支援半形/全形冒號與百分比
    gpu = first_num(r"GPU[:：\s]+(\d+(?:\.\d+)?)\s*(?:%|％)?")
    cpu = first_num(r"CPU[:：\s]+(\d+(?:\.\d+)?)\s*(?:%|％)?")
    mem = first_num(r"(?:RAM|Memory|記憶體)[:：\s]+(\d+(?:\.\d+)?)\s*(?:%|％)?")

    return {"gpu_usage": gpu, "cpu_usage": cpu, "memory_usage": mem}

class HardwareSpec(BaseModel):
    category: str  # gpu, cpu, ram, storage
    model: Optional[str] = None  # Optional for ram/storage, required for gpu/cpu
    selected_vram_gb: Optional[float] = None
    ram_gb: Optional[float] = None  # for RAM specs
    ram_type: Optional[str] = None  # DDR4, DDR5, etc.
    ram_speed_mhz: Optional[int] = None  # RAM frequency in MHz
    ram_latency_ns: Optional[float] = None  # CAS latency in nanoseconds
    storage_type: Optional[str] = None  # SSD, HDD, NVMe, etc.

class BenchmarkSearchRequest(BaseModel):
    game: Optional[str] = None
    games: Optional[List[str]] = None
    resolution: str
    settings: Optional[str] = None
    hardware: List[HardwareSpec]

class BenchmarkResult(BaseModel):
    game: str
    resolution: str
    settings: str
    gpu: str
    cpu: str
    avg_fps: Optional[float] = None
    p1_low: Optional[float] = None
    p0_1_low: Optional[float] = None
    source: str
    timestamp: str
    notes: Optional[str] = None
    confidence_score: float
    is_incomplete: bool = False
    bottleneck_analysis: Optional[dict] = None  # 瓶頸分析結果
    vram_required_gb: Optional[float] = None
    vram_selected_gb: Optional[float] = None
    vram_is_enough: Optional[bool] = None
    vram_margin_gb: Optional[float] = None
    # RAM specs
    ram_gb: Optional[float] = None
    ram_type: Optional[str] = None
    ram_speed_mhz: Optional[int] = None
    ram_latency_ns: Optional[float] = None
    # Storage specs
    storage_type: Optional[str] = None
    # Usage rates
    gpu_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None

class BottleneckAnalysis(BaseModel):
    bottleneck_type: str  # GPU-bound, CPU-bound, Memory-bound, IO-bound, Unknown
    confidence: float  # 0.0 - 1.0
    reasoning: str
    recommendations: List[str]

class BenchmarkSearchResponse(BaseModel):
    results: List[BenchmarkResult]
    total: int

@router.post("/benchmarks/search", response_model=BenchmarkSearchResponse)
async def search_benchmarks(request: BenchmarkSearchRequest):
    """
    搜尋基準測試資料
    從網路即時抓取，不使用內建靜態資料
    """
    try:
        # 強制要求至少一顆 CPU：否則瓶頸分析（CPU/GPU）不可靠
        if not any((h.category or "").lower() == "cpu" for h in (request.hardware or [])):
            raise HTTPException(status_code=400, detail="請至少選擇一顆 CPU")

        scraper = BenchmarkScraper()
        games: List[str] = []
        if request.games:
            games = list(request.games)
        elif request.game:
            games = [request.game]
        else:
            raise HTTPException(status_code=400, detail="請提供 game 或 games")

        results = []
        for g in games:
            batch = await scraper.search_benchmarks(
                game=g,
                resolution=request.resolution,
                settings=request.settings,
                hardware_list=[h.model_dump() for h in request.hardware],
            )
            results.extend(batch)
        
        # 為每個結果進行瓶頸分析
        analyzer = BottleneckAnalyzer()
        for result in results:
            analysis_data = {
                "avg_fps": result.get("avg_fps") if isinstance(result, dict) else result.avg_fps,
                "p1_low": result.get("p1_low") if isinstance(result, dict) else result.p1_low,
                "p0_1_low": result.get("p0_1_low") if isinstance(result, dict) else result.p0_1_low,
                "gpu_usage": None,
                "cpu_usage": None,
                "memory_usage": None,
                "frametime": None,
            }

            # 嘗試從 notes 中提取使用率資訊
            notes = result.get("notes") if isinstance(result, dict) else result.notes
            if notes:
                usage = _extract_usage_from_notes(str(notes))
                analysis_data["gpu_usage"] = usage["gpu_usage"]
                analysis_data["cpu_usage"] = usage["cpu_usage"]
                analysis_data["memory_usage"] = usage["memory_usage"]

            # 進行瓶頸分析
            analysis = analyzer._determine_bottleneck(analysis_data)
            if isinstance(result, dict):
                result["bottleneck_analysis"] = analysis
                # 設置使用率信息到結果中
                result["gpu_usage"] = analysis_data["gpu_usage"]
                result["cpu_usage"] = analysis_data["cpu_usage"]
                result["memory_usage"] = analysis_data["memory_usage"]
            else:
                result.bottleneck_analysis = analysis
                result.gpu_usage = analysis_data["gpu_usage"]
                result.cpu_usage = analysis_data["cpu_usage"]
                result.memory_usage = analysis_data["memory_usage"]

            # 確保RAM和存儲規格被正確設置
            if isinstance(result, dict):
                # 從hardware_list中提取RAM和存儲信息
                for hw in request.hardware:
                    if hw.category.lower() == "ram":
                        result["ram_gb"] = hw.ram_gb
                        result["ram_type"] = hw.ram_type
                        result["ram_speed_mhz"] = hw.ram_speed_mhz
                        result["ram_latency_ns"] = hw.ram_latency_ns
                    elif hw.category.lower() == "storage":
                        result["storage_type"] = hw.storage_type
        
        return BenchmarkSearchResponse(
            results=results,  # list[dict] 也可被 response_model 解析
            total=len(results)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜尋基準測試失敗: {str(e)}"
        )

@router.post("/benchmarks/analyze", response_model=BottleneckAnalysis)
async def analyze_bottleneck_from_result(result: BenchmarkResult):
    """
    從基準測試結果直接分析效能瓶頸
    """
    try:
        analyzer = BottleneckAnalyzer()
        
        # 將 BenchmarkResult 轉換為分析所需的資料格式
        analysis_data = {
            "avg_fps": result.avg_fps,
            "p1_low": result.p1_low,
            "p0_1_low": result.p0_1_low,
            "gpu_usage": None,  # 從原始資料中提取（如果有的話）
            "cpu_usage": None,
            "memory_usage": None,
            "frametime": None,
        }
        
        # 嘗試從 notes 或 raw_source_snippet 中提取使用率資訊
        if result.notes:
            usage = _extract_usage_from_notes(str(result.notes))
            analysis_data["gpu_usage"] = usage["gpu_usage"]
            analysis_data["cpu_usage"] = usage["cpu_usage"]
            analysis_data["memory_usage"] = usage["memory_usage"]
        
        analysis = analyzer._determine_bottleneck(analysis_data)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"瓶頸分析失敗: {str(e)}"
        )

@router.get("/benchmarks/{benchmark_id}/bottleneck", response_model=BottleneckAnalysis)
async def analyze_bottleneck(benchmark_id: str):
    """
    分析效能瓶頸（保留舊 API 以向後兼容）
    """
    try:
        analyzer = BottleneckAnalyzer()
        analysis = await analyzer.analyze(benchmark_id)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"瓶頸分析失敗: {str(e)}"
        )

@router.post("/benchmarks/compare")
async def compare_benchmarks(
    benchmark_ids: List[str],
    metric: str = Query("avg_fps", description="比較指標: avg_fps, p1_low, p0_1_low")
):
    """
    比較多組基準測試結果
    """
    try:
        scraper = BenchmarkScraper()
        comparison_data = await scraper.get_comparison_data(
            benchmark_ids=benchmark_ids,
            metric=metric
        )
        return comparison_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"比較失敗: {str(e)}"
        )

