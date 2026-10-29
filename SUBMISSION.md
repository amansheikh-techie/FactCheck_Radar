# Nebius x NVIDIA Global AI Hackathon — Project Submission

## Project Name: FactCheck Radar
**Track**: Best Apps & Agents Track  
**Elevator Pitch**: Autonomous multi-stage fact-checking agent combining fast Nemotron extraction with deep reasoning over live Tavily web evidence, featuring switchable inference providers (NVIDIA Build NIM and Nebius Token Factory).  
**Live Demo (Render)**: [https://factcheck-radar.onrender.com](https://factcheck-radar.onrender.com)  
**Demo Video (YouTube)**: [https://www.youtube.com/watch?v=s2DIYEr02RM](https://www.youtube.com/watch?v=s2DIYEr02RM)  
**GitHub Repository**: [https://github.com/amansheikh-techie/FactCheck_Radar](https://github.com/amansheikh-techie/FactCheck_Radar)  
**Deployment Truthfulness Notice**: The hosted live demo runs on **Render** (containerized via Docker) powered by the hosted **NVIDIA NIM API** (`https://integrate.api.nvidia.com/v1`) from `build.nvidia.com` using the high-speed `nvidia/nemotron-3.5-lightning-30b-a3b` model. **Nebius Token Factory** is an officially supported, fully swappable inference provider (`LLM_PROVIDER=nebius`) in the codebase, but has **not** been used for the hosted demo deployment. We do not claim that the hosted demo runs on Nebius Serverless Endpoints or AMD Genoa.

---

### Inspiration

Every breaking news cycle follows the same depressing pattern: an unverified headline drops on X or Reddit, spreads across group chats within minutes, and embeds itself in public opinion long before traditional news desks can publish a debunking.

When people try using standard LLMs to check claims, they hit two major walls:
1. **Hallucination & Knowledge Cutoffs**: LLMs cite defunct links or guess at current events.
2. **Confirmation Bias**: If you ask an LLM *"Is it true that X happened?"*, it often leans into the premise of the prompt rather than playing devil's advocate.

We wanted to build an agent that behaves the way a skeptical senior investigative journalist actually works: break a claim down into its atomic checkable facts, search both sides of the aisle with strictly neutral queries, verify source domains, evaluate conflicting stances, and only then write an evidence-weighted verdict.

---

### What It Does

Paste a claim, a spicy headline, or an entire article URL. FactCheck Radar takes over autonomously:

1. **URL & Text Ingestion**: If you pass a link, it safely fetches and extracts the core article text (with built-in SSRF protection against internal/cloud metadata probing).
2. **Atomic Claim Extraction**: Isolates up to 3 distinct, checkable factual assertions using Nemotron Fast (`nvidia/nemotron-3.5-lightning-30b-a3b` or `nvidia/Nemotron-3-Nano-30B-A3B`).
3. **Neutral Query Synthesis**: Generates balanced, unbiased search phrases designed to retrieve both supporting and debunking evidence without leading the search engine.
4. **Live Evidence Retrieval**: Uses Tavily AI Search to pull relevant web evidence, automatically deduplicating across domains so one SEO-heavy site doesn't dominate the results.
5. **Stance Analysis**: Classifies each source snippet as `supports`, `contradicts`, or `neutral` with a concrete one-sentence justification.
6. **Deep Reasoning & Verdict**: Synthesizes the full evidence graph to assign an overall verdict (`True`, `Mostly True`, `Mixed`, `Mostly False`, `False`, `Unverifiable`), a calibrated confidence score (0–100%), and direct hyperlinked citations.
7. **Real-Time Streaming**: Everything streams over Server-Sent Events (SSE) into a responsive UI with a live progress timeline, animated confidence gauge, and dark/light mode.
8. **Rate Limiting & Quota Protection**: Enforces 10 requests/minute per IP sliding-window rate limits so the live demo cannot burn quotas.

---

### How We Built It (Engineering Architecture)

#### 1. Dual-Model Specialization with Switchable Providers
The pipeline employs specialized Nemotron models for extraction, stance classification, and evidence synthesis.

The architecture features a unified OpenAI-compatible client factory supporting:
- **NVIDIA Build NIM** (`LLM_PROVIDER=nvidia`, active live demo): `https://integrate.api.nvidia.com/v1`, using `nvidia/nemotron-3.5-lightning-30b-a3b` for sub-30s responsive agentic cycles (with `nvidia/nemotron-3-ultra-550b-a55b` as fallback).
- **Nebius Token Factory** (`LLM_PROVIDER=nebius`, supported provider): `https://api.tokenfactory.nebius.com/v1/`, routing to `nvidia/Nemotron-3-Nano-30B-A3B` and `nvidia/Nemotron-3-Ultra-550b-a55b`.

At startup, the backend automatically validates credentials, calls `/models` for the active provider, logs discovered Nemotron model IDs, and resolves to the closest valid matching endpoints.

#### 2. Switching to Nebius
To switch the deployment to Nebius Token Factory:
1. Set `LLM_PROVIDER=nebius` in `.env` or Render dashboard.
2. Provide your `NEBIUS_API_KEY` (from `tokenfactory.nebius.com`).
3. The server switches its base URL to `https://api.tokenfactory.nebius.com/v1/`, probes models, and runs the entire pipeline on Nebius infrastructure.

#### 3. Full-Stack System
- **Backend**: FastAPI (Python 3.11+) with async streaming endpoints, Pydantic v2 schemas for strict JSON validation, proxy-aware sliding-window IP rate limiting (10 req/min/IP), and an in-memory LRU cache with a 15-minute TTL.
- **Frontend**: React 19 bootstrapped with Vite and styled using Tailwind CSS v4 (with class-based dark mode variants).
- **Packaging**: Containerized multi-stage Docker build deployed on Render free tier.

---

### Engineering Challenges & Battle Scars

- **The Event Loop Trap**: Both the OpenAI and Tavily Python SDKs make blocking network calls under their standard synchronous clients. Under concurrent user traffic, this blocked FastAPI's async event loop. We wrapped all third-party SDK calls in `asyncio.to_thread` to ensure zero worker starvation.
- **LLM Markdown Fencing & JSON Resiliency**: Even when setting `response_format={"type": "json_object"}`, models occasionally sneak in markdown fences (` ```json `) or extraneous text. We built a robust JSON extraction sanitizer (`_clean_json_str`) and a self-healing retry handler that re-prompts the model for an in-band correction.
- **Latency Optimization & Timeouts**: Heavy frontier models like 550B can take over 80 seconds. By deploying `nvidia/nemotron-3.5-lightning-30b-a3b` as the default for the live demo, full fact-check runs complete in 15-25 seconds with 35s per-request timeouts and helpful retry messages.
- **Honesty in AI Results**: We eliminated silent fallbacks to sample data. If a live API call fails, the app explicitly displays an error banner and never masquerades canned data as live. Demonstration data only appears when the user explicitly enables Demo Mode.

---

### Accomplishments That We're Proud Of

- **20/20 Passing Automated Unit Tests**: Complete test suite covering schemas, cache, rate limiting, fail-fast provider validation, and pipeline orchestration.
- **Strict Live Smoke Test**: `scripts/smoke_test.py` validates live claim extraction, Tavily retrieval, source assessment, and verdict synthesis end-to-end against the active provider, failing fast on any 401 or empty result.
- **True Latency Optimization**: Sub-second extraction handoffs with the fast model, keeping the total fact-check cycle snappy despite deep web searches.

---

## 📝 (A) Devpost-Ready Submission Description

### Project Title
FactCheck Radar — Autonomous Real-Time Fact-Checking Agent powered by NVIDIA Nemotron with Switchable Providers

### Elevator Pitch
An autonomous multi-agent verification system that takes any natural language claim, breaking news headline, or article URL, isolates atomic assertions using NVIDIA Nemotron Fast (30B), cross-references live web evidence via Tavily AI Search, and synthesizes an evidence-weighted verdict with calibrated confidence and verifiable citations using NVIDIA Nemotron with switchable support for NVIDIA Build NIM and Nebius Token Factory.

### What it does
- **Multi-Modal Input**: Accepts direct claims, viral rumors, or full news article URLs (with automated extraction and SSRF defense).
- **Atomic Decomposition**: Extracts up to 3 checkable factual claims rather than conflating complex statements.
- **Debiased Search**: Formulates objective, multi-angle search queries executed across independent sources using Tavily AI Search.
- **Stance Classification**: Categorizes each source citation as `SUPPORTS`, `CONTRADICTS`, or `NEUTRAL` with explicit rationales.
- **High-Parameter Reasoning**: Synthesizes conflicting reports, weighs domain credibility, and produces a nuanced verdict (`True`, `Mostly True`, `Mixed`, `Mostly False`, `False`, or `Unverifiable`) with calibrated confidence (0–100%).
- **Interactive Live Streaming**: Server-Sent Events (SSE) provide step-by-step transparency into every agent decision in a modern dark/light web UI.
- **Switchable Providers & Honesty**: Transparently reports provider and model IDs; never masks sample data as live.

### Built with
- **LLM Models**: NVIDIA Nemotron-3.5-Lightning-30b-a3b / Nemotron-3-Ultra-550b
- **Active Live Provider**: NVIDIA Build NIM (`https://integrate.api.nvidia.com/v1`)
- **Supported Provider**: Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1/`)
- **Web Search Retrieval**: Tavily AI Search API
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SSE-Starlette, Trafilatura
- **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide Icons
- **Deployment**: Docker multi-stage container deployed on Render
