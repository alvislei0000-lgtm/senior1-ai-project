from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.cache.global_cache import cache_manager


@dataclass
class FpsCandidate:
    avg_fps: float
    raw: str
    confidence: float


class GoogleFpsSearchService:
    """
    Google Programmable Search API：
    - 以多組 query 嘗試找到「遊戲 + 硬體 + 解析度/畫質」對應的 FPS
    - 只用 snippet/標題做數字解析（避免網站反爬/動態渲染）
    """

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    def _is_configured(self) -> bool:
        # Support both SerpApi and Google Custom Search API
        serpapi_key = os.getenv("SERPAPI_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        google_cx = os.getenv("GOOGLE_CX")
        return bool(serpapi_key) or (bool(google_key) and bool(google_cx))

    def _use_serpapi(self) -> bool:
        return bool(os.getenv("SERPAPI_KEY"))

    def _cache_key(self, q: str, num: int) -> str:
        return f"google_cse:{num}:{q}"

    def _build_query_candidates(
        self,
        game: str,
        gpu: str,
        cpu: str,
        resolution: str,
        settings: Optional[str],
    ) -> List[str]:
        g = (game or "").strip()
        gpu_s = (gpu or "").strip()
        cpu_s = (cpu or "").strip()
        res = (resolution or "").strip()
        st = ((settings or "") or "").strip()

        base = f"\"{g}\" {gpu_s} {res}"
        strict = f"{base} {st} FPS" if st else f"{base} FPS"
        with_cpu = f"{strict} {cpu_s}" if cpu_s and cpu_s.lower() != "unknown cpu" else strict

        # 由嚴到寬：盡量命中實測文章/表格
        cands = [
            with_cpu,
            strict,
            f"\"{g}\" {gpu_s} {res} benchmark FPS",
            f"\"{g}\" {gpu_s} FPS",
            f"{g} {gpu_s} FPS {res}",
        ]
        # 去重
        out: List[str] = []
        seen = set()
        for q in cands:
            qn = " ".join(q.split())
            if qn and qn not in seen:
                seen.add(qn)
                out.append(qn)
        return out

    def _extract_fps_candidates(self, text: str) -> List[FpsCandidate]:
        """
        從 snippet/標題抓數字：
        - 支援 "120 FPS", "avg 144 fps", "平均 165 fps" 等
        - 只取合理範圍 (5~1000)
        """
        if not text:
            return []

        t = " ".join(str(text).split())
        cands: List[FpsCandidate] = []

        patterns = [
            r"(?:avg|average|平均|around|about)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:-|to|~)?\s*(\d+(?:\.\d+)?)?\s*fps",
            r"(\d+(?:\.\d+)?)\s*(?:-|to|~)?\s*(\d+(?:\.\d+)?)?\s*fps",
        ]
        for p in patterns:
            for m in re.finditer(p, t, re.IGNORECASE):
                try:
                    v1 = float(m.group(1))
                    v2 = m.group(2)
                    if v2:
                        v2 = float(v2)
                        v = (v1 + v2) / 2.0  # 取範圍的平均值
                    else:
                        v = v1
                except Exception:
                    continue
                if 5.0 <= v <= 1000.0:
                    # 基礎置信度：有 avg/average 等字眼更高
                    conf = 0.8 if any(word in m.group(0).lower() for word in ["avg", "average", "平均", "around", "about"]) else 0.6
                    cands.append(FpsCandidate(avg_fps=v, raw=m.group(0), confidence=conf))
        return cands

    def _pick_best_fps(self, candidates: List[FpsCandidate]) -> Optional[Tuple[float, float]]:
        if not candidates:
            return None
        # 以「群聚一致性」拉高 confidence，但對於基準數據更寬容
        values = sorted([c.avg_fps for c in candidates])
        # 用中位數當代表
        mid = values[len(values) // 2]

        # 放寬一致性檢查：允許更大的差異，因為基準數據本來就有變化
        # 對於高 FPS（>100），允許 20% 差異；對於低 FPS，允許固定 15 FPS 差異
        tolerance = max(15.0, 0.2 * mid)  # 至少 15 FPS 或 20% 的差異
        near = [v for v in values if abs(v - mid) <= tolerance]
        agreement = len(near) / max(1, len(values))

        # 如果至少有 2 個候選項且協議度 > 0.3，就接受
        if len(candidates) >= 2 and agreement > 0.3:
            base = max(c.confidence for c in candidates)
            confidence = min(0.9, base * (0.6 + 0.4 * agreement))
            return float(mid), float(confidence)
        elif len(candidates) == 1:
            # 單一候選項也接受，但降低信心
            return float(mid), 0.4

        return None

    async def _call_cse(self, q: str, num: int) -> Dict[str, Any]:
        if self._use_serpapi():
            # Use SerpApi
            api_key = os.getenv("SERPAPI_KEY", "")
            url = "https://serpapi.com/search"
            params = {"api_key": api_key, "q": q, "engine": "google", "num": str(num)}
        else:
            # Use Google Custom Search API
            api_key = os.getenv("GOOGLE_API_KEY", "")
            cx = os.getenv("GOOGLE_CX", "")
            url = "https://www.googleapis.com/customsearch/v1"
            params = {"key": api_key, "cx": cx, "q": q, "num": str(num)}

        r = await self.client.get(url, params=params, timeout=15.0)
        r.raise_for_status()
        return r.json()

    async def search_fps(
        self,
        game: str,
        gpu: str,
        cpu: str,
        resolution: str,
        settings: Optional[str],
        num: int = 5,
    ) -> Dict[str, Any]:
        if not self._is_configured():
            return {
                "avg_fps": None,
                "confidence_override": 0.0,
                "notes": "未設定 API（需要 SERPAPI_KEY 或 GOOGLE_API_KEY+GOOGLE_CX）",
                "source": "GoogleSearchSnippet",
            }

        queries = self._build_query_candidates(game, gpu, cpu, resolution, settings)
        all_candidates: List[FpsCandidate] = []
        picked_snippet = ""

        for q in queries:
            cache_key = self._cache_key(q, num)
            cached = await cache_manager.get(cache_key)
            if cached is None:
                try:
                    data = await self._call_cse(q, num=num)
                    await cache_manager.set(cache_key, data, ttl_seconds=3600)
                except Exception as e:
                    # 不中斷，繼續下一個 query
                    continue
            else:
                data = cached

            # Handle different response formats
            if self._use_serpapi():
                # SerpApi format
                items = (data or {}).get("organic_results") or []
                for it in items:
                    snip = (it or {}).get("snippet") or ""
                    title = (it or {}).get("title") or ""
                    cands = self._extract_fps_candidates(f"{title} {snip}")
                    if cands:
                        picked_snippet = snip or title
                        all_candidates.extend(cands)
            else:
                # Google Custom Search API format
                items = (data or {}).get("items") or []
                for it in items:
                    snip = (it or {}).get("snippet") or ""
                    title = (it or {}).get("title") or ""
                    cands = self._extract_fps_candidates(f"{title} {snip}")
                    if cands:
                        picked_snippet = snip or title
                        all_candidates.extend(cands)

            best = self._pick_best_fps(all_candidates)
            if best:
                avg, conf = best
                return {
                    "avg_fps": round(avg, 1),
                    "p1_low": None,
                    "p0_1_low": None,
                    "raw_snippet": picked_snippet[:500],
                    "notes": f"Google snippet 解析（query={q})",
                    "source": "GoogleSearchSnippet",
                    "confidence_override": conf,
                }
        # 若 snippet 無法解析到數字，嘗試抓取每個 search result 的實際頁面（fallback）
        # 這會提高抓取成功率，但也會增加延遲與流量
        for q in queries:
            try:
                data = await self._call_cse(q, num=num)
            except Exception:
                continue
            # Handle different response formats for page scraping
            if self._use_serpapi():
                items = (data or {}).get("organic_results") or []
            else:
                items = (data or {}).get("items") or []
            for it in items:
                link = (it or {}).get("link") or ""
                if not link:
                    continue
                try:
                    resp = await self.client.get(link, timeout=15.0)
                    text = resp.text or ""
                except Exception:
                    # 無法抓取頁面則跳過
                    continue
                # domain-specific extraction first (site-specific heuristics)
                page_cands = []
                try:
                    from urllib.parse import urlparse

                    domain = urlparse(link).netloc.lower()
                    # Site-specific heuristics (TechPowerUp / GPUCheck / Guru3D / UserBenchmark)
                    if any(x in domain for x in ("techpowerup.com", "gpucheck.com", "guru3d.com", "userbenchmark.com")):
                        import re

                        # UserBenchmark often uses 'Average' or table labels; try a tighter pattern first
                        m = re.search(r"(?:average|avg|mean|average fps|avg fps)[:\\s\\-]{0,8}(\\d+(?:\\.\\d+)?)\\s*fps", text, re.IGNORECASE)
                        if m:
                            page_cands.append(FpsCandidate(avg_fps=float(m.group(1)), raw=m.group(0), confidence=0.9 if 'userbenchmark' in domain else 0.85))
                        else:
                            # fallback: search for 'FPS' nearby numbers within 100 chars and weight by context keywords
                            for m in re.finditer(r"(\\d+(?:\\.\\d+)?)\\s*fps", text, re.IGNORECASE):
                                ctx_start = max(0, m.start() - 120)
                                ctx = text[ctx_start : m.end() + 120].lower()
                                # prefer contexts with these keywords
                                if any(k in ctx for k in ("average", "avg", "benchmark", "median", "mean", "avg fps", "average fps")):
                                    conf = 0.8
                                elif "userbenchmark.com" in domain:
                                    # accept more liberally from userbenchmark but with lower confidence
                                    conf = 0.6
                                else:
                                    conf = 0.65
                                try:
                                    page_cands.append(FpsCandidate(avg_fps=float(m.group(1)), raw=m.group(0), confidence=conf))
                                except Exception:
                                    continue
                except Exception:
                    page_cands = []

                # 如果 site-specific 沒抓到，再做一般擷取
                if not page_cands:
                    page_cands = self._extract_fps_candidates(text)
                if page_cands:
                    all_candidates.extend(page_cands)
            best = self._pick_best_fps(all_candidates)
            if best:
                avg, conf = best
                return {
                    "avg_fps": round(avg, 1),
                    "p1_low": None,
                    "p0_1_low": None,
                    "raw_snippet": f"page_parse_from_query={q}"[:500].replace('\\n',' '),
                    "notes": f"Google result page 解析（query={q})",
                    "source": "GoogleResultPage",
                    "confidence_override": conf,
                }

        return {
            "avg_fps": None,
            "confidence_override": 0.0,
            "notes": "Google snippet/linked pages 未找到可解析的 FPS 數字",
            "source": "GoogleSearchSnippet",
        }










