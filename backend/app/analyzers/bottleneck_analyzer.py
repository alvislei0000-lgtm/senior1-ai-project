"""
瓶頸分析器
根據 FPS、frametime、CPU/GPU 使用率等資料判定效能瓶頸
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

class BottleneckAnalyzer:
    """瓶頸分析器"""
    
    def __init__(self):
        pass
    
    async def analyze(self, benchmark_id: str) -> Dict[str, Any]:
        """
        分析效能瓶頸
        根據可用的資料判定：GPU-bound / CPU-bound / Memory-bound / IO-bound
        """
        # 從快取或資料庫取得基準資料
        # 這裡簡化處理，實際應從資料庫取得
        benchmark_data = await self._get_benchmark_data(benchmark_id)
        
        if not benchmark_data:
            return {
                "bottleneck_type": "Unknown",
                "confidence": 0.0,
                "reasoning": "無法取得基準資料",
                "recommendations": []
            }
        
        # 分析瓶頸
        analysis = self._determine_bottleneck(benchmark_data)
        
        return analysis
    
    async def _get_benchmark_data(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        """取得基準資料（應從資料庫或快取取得）"""
        # 簡化實作，實際應從資料庫取得
        return None
    
    def _determine_bottleneck(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        判定瓶頸類型
        根據 FPS、frametime、CPU/GPU 使用率等資料
        """
        bottleneck_type = "Unknown"
        confidence = 0.0
        reasoning = ""
        recommendations = []
        
        # 取得可用資料
        avg_fps = data.get("avg_fps")
        p1_low = data.get("p1_low")
        gpu_usage = data.get("gpu_usage")
        cpu_usage = data.get("cpu_usage")
        memory_usage = data.get("memory_usage")
        frametime = data.get("frametime")

        # 建立「缺少哪些資料」的診斷訊息，避免 UI 只看到一句「資料不足」
        missing = []
        if avg_fps is None:
            missing.append("avg_fps")
        if p1_low is None:
            missing.append("p1_low")
        if gpu_usage is None:
            missing.append("gpu_usage")
        if cpu_usage is None:
            missing.append("cpu_usage")
        if memory_usage is None:
            missing.append("memory_usage")
        
        # 如果有 GPU 和 CPU 使用率資料
        if gpu_usage is not None and cpu_usage is not None:
            if gpu_usage > 95 and cpu_usage < 80:
                bottleneck_type = "GPU-bound"
                confidence = 0.9
                reasoning = f"GPU 使用率達 {gpu_usage}%，CPU 使用率僅 {cpu_usage}%，顯示 GPU 為瓶頸"
                recommendations = [
                    "降低解析度或畫質設定",
                    "啟用 DLSS/FSR 等升頻技術",
                    "考慮升級 GPU"
                ]
            elif cpu_usage > 95 and gpu_usage < 80:
                bottleneck_type = "CPU-bound"
                confidence = 0.9
                reasoning = f"CPU 使用率達 {cpu_usage}%，GPU 使用率僅 {gpu_usage}%，顯示 CPU 為瓶頸"
                recommendations = [
                    "降低 CPU 密集的設定（如物理效果、AI 數量）",
                    "關閉背景程式",
                    "考慮升級 CPU"
                ]
            elif gpu_usage > 90 and cpu_usage > 90:
                bottleneck_type = "Balanced"
                confidence = 0.7
                reasoning = "CPU 與 GPU 使用率都很高，系統接近平衡狀態"
                recommendations = [
                    "同時升級 CPU 和 GPU 才能獲得明顯提升",
                    "優化系統設定以釋放更多資源"
                ]
            else:
                # usage 有，但不足以用硬閾值判斷 → 留給後面的 FPS/low fallback
                reasoning = f"GPU 使用率 {gpu_usage}%，CPU 使用率 {cpu_usage}%（未達明確瓶頸閾值，改用 FPS/low 推估）"
        
        # 若尚未靠 usage 判定，才用 FPS/low 做推論（避免覆蓋已判定結果）
        if bottleneck_type == "Unknown":
            # 如果有 FPS 資料，使用推論方式（也作為 usage 不夠明確時的 fallback）
            if avg_fps is not None and p1_low is not None:
                # 計算 FPS 穩定性
                fps_stability = p1_low / avg_fps if avg_fps > 0 else 0

                if fps_stability < 0.7:
                    # 1% low 明顯低於平均，可能是 CPU 或記憶體瓶頸
                    bottleneck_type = "CPU-bound"
                    confidence = 0.6
                    reasoning = f"1% low ({p1_low}) 明顯低於平均 FPS ({avg_fps})，顯示有間歇性瓶頸，通常是 CPU 或記憶體"
                    recommendations = [
                        "檢查 CPU 使用率",
                        "檢查記憶體使用情況",
                        "關閉背景程式",
                        "若 CPU 接近滿載：考慮升級 CPU",
                    ]
                else:
                    # FPS 穩定，可能是 GPU 瓶頸（多數遊戲是正常情況）
                    bottleneck_type = "GPU-bound"
                    confidence = 0.6
                    reasoning = f"FPS 相對穩定，平均 {avg_fps}，1% low {p1_low}，可能是 GPU 瓶頸"
                    recommendations = [
                        "降低解析度或畫質（GPU 瓶頸是最常見/最正常的情況）",
                        "啟用 DLSS/FSR 等升頻技術（若支援）",
                        "若 FPS 仍過低：考慮升級 GPU",
                    ]

            # 只有 avg_fps（沒有 1% low/使用率）：仍提供最低限度的提示（避免誤導）
            elif avg_fps is not None:
                bottleneck_type = "Unknown"
                confidence = 0.35
                reasoning = f"目前只有平均 FPS（{avg_fps}），缺少 1% low 或 GPU/CPU 使用率等關鍵資訊，無法可靠判定瓶頸"
                recommendations = [
                    "建議補齊 1% low 或 GPU/CPU 使用率資料（例如：改用含更完整資訊的來源/seed）",
                    "若想判定瓶頸：觀察 GPU 使用率是否長期接近 95% 或 CPU 是否接近滿載",
                ]

        # 若 FPS 太低：給出更直接的硬體升級建議（不論瓶頸類型）
        try:
            if avg_fps is not None and float(avg_fps) < 45.0:
                recommendations = list(recommendations or [])
                recommendations.append("若目標是更高 FPS：考慮升級硬體（通常先升級 GPU；若 CPU 近滿載則優先升級 CPU）")
        except Exception:
            pass
        
        # 如果有記憶體使用率資料（RAM 瓶頸檢測）
        if memory_usage is not None:
            if memory_usage > 90:
                if bottleneck_type == "Unknown":
                    bottleneck_type = "Memory-bound"
                    confidence = 0.85
                    reasoning = f"記憶體（RAM）使用率達 {memory_usage:.1f}%，顯示記憶體為主要瓶頸。這會導致系統頻繁使用虛擬記憶體，造成效能下降。"
                    recommendations = [
                        "增加系統記憶體（RAM）容量",
                        "關閉其他佔用記憶體的應用程式",
                        "降低遊戲的記憶體需求設定（如材質品質）",
                        "檢查是否有記憶體洩漏問題"
                    ]
                elif memory_usage > 85:
                    # 記憶體也可能是次要瓶頸
                    reasoning += f"；同時記憶體（RAM）使用率達 {memory_usage:.1f}%，可能也是瓶頸之一"
                    recommendations.append("檢查記憶體使用情況，考慮增加 RAM")
            elif memory_usage > 80 and bottleneck_type in ["GPU-bound", "CPU-bound"]:
                # 記憶體使用率較高，可能是次要因素
                reasoning += f"；記憶體使用率 {memory_usage:.1f}% 也偏高，可能影響效能"
                recommendations.append("監控記憶體使用情況")
        
        # 如果有 frametime 資料
        if frametime is not None:
            # 分析 frametime 分佈
            if isinstance(frametime, dict):
                avg_frametime = frametime.get("avg")
                max_frametime = frametime.get("max")
                
                if max_frametime and avg_frametime:
                    frametime_spike = max_frametime / avg_frametime if avg_frametime > 0 else 0
                    
                    if frametime_spike > 2.0:
                        reasoning += f"；frametime 有明顯峰值（{frametime_spike:.2f}x），顯示有間歇性瓶頸"
                        if confidence < 0.7:
                            confidence = min(confidence + 0.2, 0.9)
        
        return {
            "bottleneck_type": bottleneck_type,
            "confidence": confidence,
            "reasoning": reasoning or (f"資料不足，無法準確判定瓶頸（缺少：{', '.join(missing)})" if missing else "資料不足，無法準確判定瓶頸"),
            "recommendations": recommendations or ["收集更多效能資料以進行準確分析"]
        }

