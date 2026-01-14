#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

# ensure backend/ is on sys.path so `app` package imports work when invoked from tools/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.google_fps_search import GoogleFpsSearchService
from app.cache.global_cache import cache_manager

async def clear_cache():
    os.environ["SERPAPI_KEY"] = "50ea289dd22e73b350b964c4ee33cf68b4b0529a2d68d48c8057fa96ac8903cf"
    svc = GoogleFpsSearchService(None)

    # Clear cache for Cyberpunk 2077 + RTX 4090 queries
    queries = svc._build_query_candidates(
        game="Cyberpunk 2077",
        gpu="RTX 4090",
        cpu="Intel Core i9-13900K",
        resolution="3840x2160",
        settings="Ultra"
    )

    for q in queries:
        key = svc._cache_key(q, 5)
        await cache_manager.delete(key)
        print(f"Cleared cache for: {q}")

    print("Cache cleared successfully")

if __name__ == "__main__":
    asyncio.run(clear_cache())