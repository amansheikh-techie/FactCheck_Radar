#!/usr/bin/env python3
"""Smoke test script for FactCheck Radar.

Sends one real claim through the full live pipeline:
Claim extraction -> Tavily search -> Source assessment -> Reasoning verdict.

Must exit non-zero on any 401, live API error, or empty results.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure UTF-8 stdout encoding on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

from backend.app.config import settings
from backend.app.services.nebius_client import nebius_client
from backend.app.agents.pipeline import run_factcheck_pipeline

TEST_CLAIM = "Water boils at 100 degrees Celsius at standard atmospheric pressure at sea level."


async def run_smoke_test() -> int:
    print("=" * 72)
    print("FACTCHECK RADAR — LIVE PIPELINE SMOKE TEST")
    print("=" * 72)

    # 1. Validate active provider credentials
    print(f"\n[1/4] Validating active provider credentials ({nebius_client.provider.upper()})...")
    try:
        nebius_client.validate_configuration()
        print(f"  ✓ Active provider: {nebius_client.provider.upper()}")
        print(f"  ✓ Base URL:        {nebius_client.base_url}")
        print("  ✓ Credentials configured and valid (non-placeholder)")
    except Exception as exc:
        print(f"\n❌ Credential validation failed: {exc}")
        return 1

    if not settings.tavily_api_key or settings.tavily_api_key.startswith("your_"):
        print("\n❌ TAVILY_API_KEY is not configured or placeholder in .env!")
        return 1
    print("  ✓ Tavily API key configured")

    # 2. Model discovery
    print(f"\n[2/4] Querying {nebius_client.provider.upper()} models endpoint...")
    try:
        await nebius_client.discover_models()
        print(f"  ✓ Fast model:      {nebius_client.fast_model}")
        print(f"  ✓ Reasoning model: {nebius_client.reasoning_model}")
    except Exception as exc:
        print(f"\n❌ Model discovery error: {exc}")
        return 1

    # 3. Execute live pipeline
    print(f"\n[3/4] Sending live claim through full agent pipeline:")
    print(f"  Claim: \"{TEST_CLAIM}\"")
    print("-" * 72)

    start_time = time.time()
    final_result = None
    live_error: str | None = None

    try:
        async for sse_line in run_factcheck_pipeline(TEST_CLAIM):
            if sse_line.startswith("event: step"):
                data_part = sse_line.split("data: ", 1)[1].strip()
                step_obj = json.loads(data_part)
                print(f"  -> Step: {step_obj.get('step')} | {step_obj.get('message')}")
            elif sse_line.startswith("event: claims"):
                data_part = sse_line.split("data: ", 1)[1].strip()
                claims_obj = json.loads(data_part)
                claims = claims_obj.get("claims", [])
                print(f"  -> Claims extracted ({len(claims)}): {[c.get('claim') for c in claims]}")
            elif sse_line.startswith("event: result"):
                data_part = sse_line.split("data: ", 1)[1].strip()
                final_result = json.loads(data_part)
            elif sse_line.startswith("event: error"):
                data_part = sse_line.split("data: ", 1)[1].strip()
                err_obj = json.loads(data_part)
                live_error = err_obj.get("message", "Unknown error")
                print(f"  ❌ Pipeline error: {live_error}")

    except Exception as exc:
        print(f"\n❌ Exception during pipeline execution: {exc}")
        return 1

    elapsed = time.time() - start_time

    # 4. Assertions on results (fail on error, 401, or empty results)
    print("\n" + "-" * 72)
    print("[4/4] Validating verification result...")

    if live_error:
        print(f"❌ SMOKE TEST FAILED: Live API error encountered: {live_error}")
        return 1

    if not final_result:
        print("❌ SMOKE TEST FAILED: No final result payload received from pipeline.")
        return 1

    if not final_result.get("is_live", False):
        print("❌ SMOKE TEST FAILED: Pipeline returned sample/non-live result. Live API required.")
        return 1

    verdicts = final_result.get("claim_verdicts", [])
    if not verdicts:
        print("❌ SMOKE TEST FAILED: Empty results — no claim verdicts were produced.")
        return 1

    provider_used = final_result.get("provider", "unknown")
    models_used = final_result.get("models_used", {})

    print(f"\n  ✓ Verification completed in {elapsed:.2f}s")
    print(f"  ✓ Provider Used: {provider_used.upper()}")
    print(f"  ✓ Fast Model:    {final_result.get('model_fast') or models_used.get('fast')}")
    print(f"  ✓ Reasoning:     {final_result.get('model_reasoning') or models_used.get('reasoning')}")

    total_citations = 0
    for idx, v in enumerate(verdicts):
        print(f"\n  Claim [{idx + 1}]: \"{v.get('claim')}\"")
        print(f"  Verdict:     {v.get('verdict')} (Confidence: {v.get('confidence')}%)")
        print(f"  Explanation: {v.get('explanation')}")
        citations = v.get("citations", [])
        total_citations += len(citations)
        print(f"  Citations ({len(citations)}):")
        for c in citations:
            print(f"    [{c.get('number')}] [{c.get('stance', '').upper()}] {c.get('domain')}: {c.get('title')}")
            print(f"        URL: {c.get('url')}")

    if total_citations == 0:
        print("\n❌ SMOKE TEST FAILED: Expected citations from Tavily web search, but got 0.")
        return 1

    print("\n" + "=" * 72)
    print(f"✅ SMOKE TEST PASSED: Live verification succeeded via {provider_used.upper()}!")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    code = asyncio.run(run_smoke_test())
    sys.exit(code)

