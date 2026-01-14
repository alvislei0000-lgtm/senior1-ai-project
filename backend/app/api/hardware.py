from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from app.scrapers.hardware_scraper import HardwareScraper
import os
import json
from datetime import datetime
import re

def infer_brand_from_model_backend(model: Optional[str]) -> str:
    m = (model or '').lower()
    if not m:
        return ''
    # Intel tokens
    if any(tok in m for tok in ['intel', 'core ', ' i3', ' i5', ' i7', ' i9', 'xeon', 'ultra']):
        return 'Intel'
    # AMD tokens
    if any(tok in m for tok in ['ryzen', 'threadripper', 'amd', 'epyc', 'ryzen']):
        return 'AMD'
    # NVIDIA tokens
    if any(tok in m for tok in ['rtx', 'gtx', 'geforce', 'nvidia', 'quadro']):
        return 'NVIDIA'
    # AMD Radeon/ RX
    if any(tok in m for tok in ['radeon', ' rx', 'rx']):
        return 'AMD'
    # Intel Arc
    if 'arc' in m and 'intel' in m:
        return 'Intel'
    # Storage brands
    if 'samsung' in m:
        return 'Samsung'
    if any(tok in m for tok in ['western', 'wd', 'seagate']):
        if 'seagate' in m:
            return 'Seagate'
        return 'Western Digital'
    if 'crucial' in m:
        return 'Crucial'
    if 'kingston' in m:
        return 'Kingston'
    if 'sandisk' in m:
        return 'SanDisk'
    if 'toshiba' in m:
        return 'Toshiba'
    if 'corsair' in m:
        return 'Corsair'
    if 'solidigm' in m:
        return 'Solidigm'
    return ''


def infer_category_from_model_backend(model: Optional[str], generation: Optional[str], brand: Optional[str]) -> str:
    m = (model or '').lower()
    g = (generation or '').lower()
    b = (brand or '').lower()
    # Heuristics: look for obvious tokens
    # GPUs
    if any(tok in m for tok in ['rtx', 'gtx', 'geforce', 'radeon', 'rx', 'ti']) or 'vram' in m:
        return 'gpu'
    if 'graphics' in m or 'gpu' in m or 'rx' in m and not 'ryzen' in m:
        return 'gpu'
    # CPUs
    if any(tok in m for tok in ['i3', 'i5', 'i7', 'i9', 'core', 'ryzen', 'threadripper', 'epyc']) or any(tok in g for tok in ['gen', 'ultra', 'zen']):
        return 'cpu'
    if any(tok in b for tok in ['intel', 'amd', 'ryzen']) and ('ssd' not in m and 'nvme' not in m):
        # brand suggests CPU/GPU but not storage keywords
        return 'cpu'
    # Storage
    if any(tok in m for tok in ['nvme', 'sata', 'ssd', 'hdd', 'pro', 'evo', 'blue', 'black', 'ssd']) or any(tok in g for tok in ['nvme', 'sata', 'ssd']):
        return 'storage'
    # Fallback: empty => unknown (but we'll return empty to let caller decide)
    return ''

router = APIRouter()

class HardwareItem(BaseModel):
    category: str  # gpu, cpu, storage
    model: str
    generation: Optional[str] = None
    release_year: Optional[int] = None
    brand: str
    capacity_gb: Optional[int] = None  # storage only
    selected: bool = False

class HardwareListResponse(BaseModel):
    items: List[HardwareItem]
    total: int
    source: str
    timestamp: str

@router.get("/hardware", response_model=HardwareListResponse)
async def get_hardware_list(
    category: Optional[str] = Query(None, description="硬體類別: gpu / cpu / storage"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    brand: Optional[str] = Query(None, description="廠牌過濾"),
    series: Optional[str] = Query(None, description="系列/世代過濾"),
    min_vram_gb: Optional[int] = Query(None, description="最低 VRAM (GB)"),
    min_ram_gb: Optional[int] = Query(None, description="最低 RAM (GB)")
):
    """
    取得硬體列表
    從網路即時抓取硬體資訊，不使用內建靜態資料
    """
    try:
        scraper = HardwareScraper()
        scraped_list = await scraper.fetch_hardware_list(
            category=category,
            search=search
        )

        # Always load seed and MERGE with scraped results.
        # Rationale: scraper can intermittently return a small partial list; if we replace the list,
        # users see options "disappear" on refresh. Merging keeps the curated coverage stable.
        seed_items: List[dict] = []
        seed_source_name = None
        try:
            seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'hardware_seed.json')
            seed_path = os.path.normpath(seed_path)
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed = json.load(f)
            for item in seed.get('items', []):
                if not item:
                    continue
                seed_items.append({
                    "category": item.get("category"),
                    "model": item.get("model"),
                    "generation": item.get("generation"),
                    "release_year": item.get("release_year"),
                    "brand": item.get("brand"),
                    "capacity_gb": item.get("capacity_gb"),
                    "selected": False,
                })
            seed_source_name = f"seed:{os.path.basename(seed_path)}"
        except Exception:
            seed_items = []
            seed_source_name = None

        def normalize_item(it) -> Optional[dict]:
            if it is None:
                return None
            if isinstance(it, HardwareItem):
                it = it.model_dump()
            if not isinstance(it, dict):
                return None
            cat = it.get("category")
            model = it.get("model")
            # If category missing, attempt to infer from model/generation/brand
            if not cat and model:
                inferred = infer_category_from_model_backend(model, it.get("generation"), it.get("brand"))
                if inferred:
                    cat = inferred
            if not cat or not model:
                return None
            brand = it.get("brand") or infer_brand_from_model_backend(model)
            return {
                "category": cat,
                "model": model,
                "generation": it.get("generation"),
                "release_year": it.get("release_year") or it.get("year"),
                "brand": brand,
                "capacity_gb": it.get("capacity_gb"),
                "selected": False,
            }

        merged_map = {}
        merged_order = []

        # Stronger normalization for model keys to merge variants like:
        # "Ryzen 7 7800X3D", "7800X3D", "Ryzen 7\n7800X3D", etc.
        def normalize_model_key(s: Optional[str]) -> str:
            if not s:
                return ''
            m = str(s)
            # remove parenthetical notes e.g. "Model (OEM)"
            m = re.sub(r'\(.*?\)', ' ', m)
            # replace common separators with spaces
            m = m.replace('-', ' ').replace('_', ' ').replace('/', ' ')
            # remove trademark or extra punctuation, keep letters/numbers/CJK/space
            m = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', m)
            # remove brand prefixes like "Intel", "AMD", "NVIDIA", "Samsung", "WD"
            m = re.sub(r'^(intel|amd|nvidia|nvidia geforce|geforce|samsung|western digital|wd|kingston|crucial)\\b', ' ', m, flags=re.IGNORECASE)
            # collapse whitespace and lowercase
            m = re.sub(r'\\s+', ' ', m).strip().lower()
            return m

        def upsert(d: dict, prefer_new: bool) -> None:
            # Use case-insensitive keys to avoid duplicates like "i9-13900K" vs "i9-13900k"
            cat_key = str(d.get('category') or '').strip().lower()
            model_key = normalize_model_key(d.get('model'))
            key = f"{cat_key}||{model_key}"
            if key not in merged_map:
                merged_map[key] = d
                merged_order.append(key)
                return
            cur = merged_map[key]
            if prefer_new:
                # prefer scraped fields when present; keep seed-only metadata (e.g. capacity_gb) if missing
                cur["brand"] = d.get("brand") or cur.get("brand")
                cur["generation"] = d.get("generation") or cur.get("generation")
                cur["release_year"] = d.get("release_year") or cur.get("release_year")
                cur["capacity_gb"] = d.get("capacity_gb") or cur.get("capacity_gb")
            else:
                # prefer existing; only fill gaps
                cur["brand"] = cur.get("brand") or d.get("brand")
                cur["generation"] = cur.get("generation") or d.get("generation")
                cur["release_year"] = cur.get("release_year") or d.get("release_year")
                cur["capacity_gb"] = cur.get("capacity_gb") or d.get("capacity_gb")
            merged_map[key] = cur

        for it in seed_items:
            n = normalize_item(it)
            if n:
                upsert(n, prefer_new=False)

        for it in (scraped_list or []):
            n = normalize_item(it)
            if n:
                upsert(n, prefer_new=True)

        hardware_list = [merged_map[k] for k in merged_order]

        # Final dedupe pass: collapse items that share the same normalized model key
        final_map = {}
        final_order = []
        for item in hardware_list:
            nm = normalize_model_key(item.get('model'))
            if not nm:
                # keep items without normalized key as-is (rare)
                key = f"{item.get('category') or ''}||{item.get('model') or ''}"
                if key not in final_map:
                    final_map[key] = item
                    final_order.append(key)
                continue
            if nm not in final_map:
                # clone to avoid mutating original
                final_map[nm] = dict(item)
                final_order.append(nm)
            else:
                # merge metadata: prefer existing fields, but fill gaps
                cur = final_map[nm]
                # prefer brand from existing, otherwise use new
                cur['brand'] = cur.get('brand') or item.get('brand')
                cur['generation'] = cur.get('generation') or item.get('generation')
                cur['release_year'] = cur.get('release_year') or item.get('release_year')
                cur['capacity_gb'] = cur.get('capacity_gb') or item.get('capacity_gb')
                # if categories differ, prefer the one that's not empty, or keep existing
                if not cur.get('category') and item.get('category'):
                    cur['category'] = item.get('category')
                final_map[nm] = cur

        hardware_list = [final_map[k] for k in final_order]

        source_parts = []
        if scraped_list:
            source_parts.append(scraper.get_source_name())
        if seed_source_name:
            source_parts.append(seed_source_name)
        if source_parts and len(source_parts) > 1:
            source_name = "merged:" + "+".join(source_parts)
        elif source_parts:
            source_name = source_parts[0]
        else:
            source_name = scraper.get_source_name()

        timestamp = scraper.get_last_fetch_time() if scraped_list else datetime.now().isoformat()
        # 嘗試讀取 seed map（model -> metadata）供過濾使用
        # 建立 seed_map 時使用標準化 key（小寫、trim），以便與 merged_map 的鍵一致
        seed_map = {}
        try:
            seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'hardware_seed.json')
            seed_path = os.path.normpath(seed_path)
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed = json.load(f)
            for it in seed.get('items', []):
                k = normalize_model_key(it.get('model'))
                if k:
                    seed_map[k] = it
        except Exception:
            seed_map = {}

        def get_storage_type_key(model: str, generation: str) -> str:
            gen = (generation or "").lower()
            m = (model or "").lower()
            if "nvme" in gen or "nvme" in m or "m.2" in m or "m2" in m:
                return "nvme"
            if "sata" in gen or "sata" in m:
                return "sata"
            if "hdd" in gen or "hdd" in m or "hard drive" in m:
                return "hdd"
            return "other"

        def matches_filters(it) -> bool:
            # support both dict and object-like items
            def get_field(obj, name):
                if isinstance(obj, dict):
                    return obj.get(name)
                return getattr(obj, name, None)

            it_brand = get_field(it, 'brand') or ''
            it_model = get_field(it, 'model') or ''
            it_generation = get_field(it, 'generation') or ''
            it_category = get_field(it, 'category') or ''

            if brand and it_brand and brand.lower() not in it_brand.lower():
                return False
            if series:
                sf = series.lower()
                # storage: allow series=nvme/sata/hdd to work even if generation is SATA/HDD etc.
                if it_category == "storage" and sf in ("nvme", "sata", "hdd"):
                    if get_storage_type_key(it_model, it_generation) != sf:
                        return False
                else:
                    if not ((it_generation and sf in it_generation.lower()) or (it_model and sf in it_model.lower())):
                        return False
            # 使用更強的 model key 標準化去查 seed_map（避免大小寫/空白/前綴差異導致找不到 metadata）
            meta = seed_map.get(normalize_model_key(it_model), {})
            vram = meta.get('vram_gb', 0) or 0
            ram = meta.get('ram_gb', 0) or 0
            if min_vram_gb and vram < min_vram_gb:
                return False
            if min_ram_gb and ram < min_ram_gb:
                return False
            if category and it_category != category:
                return False
            if search:
                term = search.lower()
                if term not in it_model.lower() and term not in it_brand.lower() and not (it_generation and term in it_generation.lower()):
                    return False
            return True

        filtered = [it for it in hardware_list if matches_filters(it)]

        return HardwareListResponse(
            items=filtered,
            total=len(filtered),
            source=source_name,
            timestamp=timestamp
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"無法取得硬體列表: {str(e)}"
        )


@router.get("/hardware/brands")
async def get_hardware_brands():
    """
    取得可用品牌與系列選項（來源：seed + 爬蟲結果若可得）
    回傳範例:
    {
      "brands": [
         { "name": "NVIDIA", "series": ["RTX","GTX"] },
         { "name": "AMD", "series": ["RX","RDNA"] }
      ]
    }
    """
    try:
        # 先嘗試從爬蟲取得較新的清單
        scraper = HardwareScraper()
        await scraper.initialize()
        try:
            items = await scraper.fetch_hardware_list()
        except Exception:
            items = []

        # 載入 seed 作為補充
        try:
            seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'hardware_seed.json')
            seed_path = os.path.normpath(seed_path)
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed = json.load(f)
            seed_items = seed.get('items', [])
        except Exception:
            seed_items = []

        combined = []
        if items:
            # items may be list of HardwareItem models or dicts; normalize to dicts
            for it in items:
                if isinstance(it, dict):
                    combined.append(it)
                else:
                    combined.append({
                        "category": getattr(it, "category", None),
                        "model": getattr(it, "model", None),
                        "generation": getattr(it, "generation", None),
                        "brand": getattr(it, "brand", None)
                    })
        combined.extend(seed_items)

        # Aggregate brands and series
        brands_map = {}
        import re
        series_tokens = re.compile(r'(RTX|GTX|RX|RDNA|Core|Arc|Radeon|Threadripper|Ryzen)', re.IGNORECASE)
        for it in combined:
            brand = (it.get('brand') or '').strip()
            if not brand:
                continue
            if brand not in brands_map:
                brands_map[brand] = set()
            gen = it.get('generation') or ''
            if gen:
                brands_map[brand].add(gen)
            model = it.get('model') or ''
            m = series_tokens.findall(model)
            for token in m:
                brands_map[brand].add(token.upper())

        result = {"brands": []}
        for b, sset in brands_map.items():
            result["brands"].append({
                "name": b,
                "series": sorted(list(sset))
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法取得品牌/系列: {e}")

