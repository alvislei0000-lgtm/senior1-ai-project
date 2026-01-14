#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

# ensure backend/ is on sys.path so `app` package imports work when invoked from tools/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.google_fps_search import GoogleFpsSearchService
import httpx

async def test_api():
    os.environ["SERPAPI_KEY"] = "50ea289dd22e73b350b964c4ee33cf68b4b0529a2d68d48c8057fa96ac8903cf"

    async with httpx.AsyncClient(timeout=15.0) as client:
        svc = GoogleFpsSearchService(client)

        # Test a simple query
        try:
            result = await svc._call_cse("RTX 4090 Cyberpunk 2077 FPS 4K Ultra", 5)
            print("API call successful")
            print(f"Response keys: {list(result.keys())}")

            # Check different possible result formats
            organic_results = result.get('organic_results', [])
            items = result.get('items', [])

            print(f"Organic results found: {len(organic_results)}")
            print(f"Items found: {len(items)}")

            if organic_results:
                print("Using organic_results format:")
                for i, item in enumerate(organic_results[:3]):
                    print(f"Item {i+1}:")
                    print(f"  Title: {item.get('title', '')}")
                    print(f"  Link: {item.get('link', '')}")
                    print(f"  Snippet: {item.get('snippet', '')[:200]}...")
                    print()
            elif items:
                print("Using items format:")
                for i, item in enumerate(items[:3]):
                    print(f"Item {i+1}:")
                    print(f"  Title: {item.get('title', '')}")
                    print(f"  Link: {item.get('link', '')}")
                    print(f"  Snippet: {item.get('snippet', '')[:200]}...")
                    print()

        except Exception as e:
            print(f"API call failed: {e}")

        # Test search_fps method
        try:
            # First, let's see what queries are generated
            queries = svc._build_query_candidates(
                game="Cyberpunk 2077",
                gpu="RTX 4090",
                cpu="Intel Core i9-13900K",
                resolution="3840x2160",
                settings="Ultra"
            )
            print("Generated queries:")
            for i, q in enumerate(queries):
                print(f"  {i+1}: {q}")

            # Test one query manually to see if it works
            test_query = '"Cyberpunk 2077" RTX 4090 3840x2160 Ultra FPS'
            print(f"\nTesting single query: {test_query}")
            try:
                manual_result = await svc._call_cse(test_query, 5)
                if svc._use_serpapi():
                    manual_items = manual_result.get('organic_results', [])
                else:
                    manual_items = manual_result.get('items', [])
                print(f"Manual query returned {len(manual_items)} items")

                if manual_items:
                    item = manual_items[0]
                    snippet = item.get('snippet', '')
                    title = item.get('title', '')
                    combined = f"{title} {snippet}"
                    manual_cands = svc._extract_fps_candidates(combined)
                    print(f"Manual extraction: {len(manual_cands)} candidates")
                    if manual_cands:
                        for cand in manual_cands:
                            print(f"  FPS: {cand.avg_fps}, Raw: '{cand.raw}'")

            except Exception as e:
                print(f"Manual query failed: {e}")

            # Debug: manually test each query
            print("\nDebugging each query:")
            all_found_candidates = []
            for i, q in enumerate(queries[:2]):  # Test first 2 queries
                print(f"Testing query {i+1}: {q}")
                try:
                    data = await svc._call_cse(q, 5)
                    if svc._use_serpapi():
                        items = data.get('organic_results', [])
                    else:
                        items = data.get('items', [])

                    query_candidates = []
                    for item in items:
                        snip = item.get('snippet', '')
                        title = item.get('title', '')
                        combined = f"{title} {snip}"
                        cands = svc._extract_fps_candidates(combined)
                        if cands:
                            query_candidates.extend(cands)
                            print(f"  Found {len(cands)} candidates in item")

                    if query_candidates:
                        best = svc._pick_best_fps(query_candidates)
                        if best:
                            avg, conf = best
                            print(f"  Query {i+1} result: {avg} FPS (confidence: {conf})")
                            all_found_candidates.extend(query_candidates)
                        else:
                            print(f"  Query {i+1}: candidates found but no best pick")
                    else:
                        print(f"  Query {i+1}: no candidates found")

                except Exception as e:
                    print(f"  Query {i+1} failed: {e}")

            if all_found_candidates:
                print(f"\nTotal candidates across all queries: {len(all_found_candidates)}")
                overall_best = svc._pick_best_fps(all_found_candidates)
                if overall_best:
                    print(f"Overall best: {overall_best[0]} FPS (confidence: {overall_best[1]})")

            fps_result = await svc.search_fps(
                game="Cyberpunk 2077",
                gpu="RTX 4090",
                cpu="Intel Core i9-13900K",
                resolution="3840x2160",
                settings="Ultra"
            )
            print("FPS search result:")
            print(f"  avg_fps: {fps_result.get('avg_fps')}")
            print(f"  confidence: {fps_result.get('confidence_override')}")
            print(f"  notes: {fps_result.get('notes', '').encode('utf-8').decode('utf-8', errors='ignore')}")
            print(f"  source: {fps_result.get('source')}")

        except Exception as e:
            print(f"FPS search failed: {e}")

        # Test FPS extraction directly
        test_text = "Currently I get about 50-60 fps at 4K all ultra with RT off."
        cands = svc._extract_fps_candidates(test_text)
        print(f"Direct FPS extraction test: {len(cands)} candidates found")
        for cand in cands:
            print(f"  FPS: {cand.avg_fps}, Confidence: {cand.confidence}")

        # Test extraction from actual snippets
        print("\nTesting extraction from actual snippets:")
        for i, item in enumerate(organic_results[:3]):
            snippet = item.get('snippet', '')
            title = item.get('title', '')
            combined = f"{title} {snippet}"
            cands = svc._extract_fps_candidates(combined)
            print(f"Snippet {i+1}: {len(cands)} candidates found")
            if cands:
                for cand in cands:
                    print(f"  FPS: {cand.avg_fps}, Raw: '{cand.raw}', Confidence: {cand.confidence}")

if __name__ == "__main__":
    asyncio.run(test_api())