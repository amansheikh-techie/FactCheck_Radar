"""Smoke-test script running 3 sample claims against real live APIs.

Benchmarks:
1. True claim: 'Water boils at 100 degrees Celsius at sea level'
2. False claim: 'The Great Wall of China is visible from space with the naked eye'
3. Ambiguous claim: 'Drinking coffee every day significantly increases lifespan'

Usage:
    python backend/smoke_test.py
"""

import asyncio
import json
import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from backend.app.config import settings
from backend.app.services.nebius_client import nebius_client
from backend.app.agents.pipeline import run_factcheck_pipeline


BENCHMARK_CLAIMS = [
    {
        "expected": "True",
        "category": "Scientific fact",
        "input": "Water boils at 100 degrees Celsius at standard atmospheric pressure at sea level.",
    },
    {
        "expected": "False",
        "category": "Common myth",
        "input": "The Great Wall of China is easily visible from the Moon with the naked human eye.",
    },
    {
        "expected": "Mixed / Ambiguous",
        "category": "Health correlation",
        "input": "Drinking two cups of coffee every single day directly increases human lifespan.",
    },
]


async def run_single_smoke_test(item: dict, index: int):
    print("\n" + "=" * 70)
    print(f"[{index + 1}/3] TESTING CLAIM ({item['category']})")
    print(f"Input:    \"{item['input']}\"")
    print(f"Expected: {item['expected']}")
    print("-" * 70)

    start_time = time.time()
    final_result = None

    try:
        async for sse_line in run_factcheck_pipeline(item["input"]):
            if sse_line.startswith("event: step"):
                data_part = sse_line.split("data: ", 1)[1].strip()
                step_obj = json.loads(data_part)
                print(f"  -> Step: {step_obj.get('step')} | {step_obj.get('message')}")
            elif sse_line.startswith("event: result"):
                data_part = sse_line.split("data: ", 1)[1].strip()
                final_result = json.loads(data_part)
            elif sse_line.startswith("event: error"):
                data_part = sse_line.split("data: ", 1)[1].strip()
                err_obj = json.loads(data_part)
                print(f"  ❌ ERROR: {err_obj.get('message')}")
                return False

        duration = time.time() - start_time

        if not final_result or "claim_verdicts" not in final_result:
            print("  ❌ Failed: No result object received")
            return False

        print("\n  RESULTS:")
        for v in final_result["claim_verdicts"]:
            print(f"  • Claim:      \"{v['claim']}\"")
            print(f"  • Verdict:    {v['verdict'].upper()} (Confidence: {v['confidence']}%)")
            print(f"  • Reasoning:  {v['explanation']}")
            print(f"  • Citations:  {len(v.get('citations', []))} sources")
            for c in v.get("citations", []):
                print(f"      - [{c['stance'].upper()}] {c['domain']} ({c['title']})")

        print(f"\n  ⏱  Completed in {duration:.2f}s using Fast: {final_result.get('model_fast')}")
        print("=" * 70)
        return True

    except Exception as exc:
        print(f"  ❌ Exception during smoke test: {exc}")
        return False


async def main():
    print("=" * 70)
    print("FACTCHECK RADAR — LIVE SMOKE TEST SUITE")
    print("=" * 70)

    # 1. Verify Credentials
    if not settings.nebius_api_key or settings.nebius_api_key.startswith("your_"):
        print("\n❌ NEBIUS_API_KEY is not configured in .env!")
        print("Please set your Nebius Token Factory API key to run live smoke tests.")
        return 1

    if not settings.tavily_api_key or settings.tavily_api_key.startswith("your_"):
        print("\n❌ TAVILY_API_KEY is not configured in .env!")
        print("Please set your Tavily API key to run live smoke tests.")
        return 1

    # 2. Verify Models endpoint
    print("\n[+] Checking Nebius Token Factory connection & models...")
    await nebius_client.discover_models()
    print(f"  Fast model:      {nebius_client.fast_model}")
    print(f"  Reasoning model: {nebius_client.reasoning_model}")

    # 3. Run Benchmark Claims
    successes = 0
    for idx, item in enumerate(BENCHMARK_CLAIMS):
        ok = await run_single_smoke_test(item, idx)
        if ok:
            successes += 1

    print("\n" + "=" * 70)
    print(f"SMOKE TEST SUMMARY: {successes}/{len(BENCHMARK_CLAIMS)} Passed")
    print("=" * 70)
    return 0 if successes == len(BENCHMARK_CLAIMS) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
