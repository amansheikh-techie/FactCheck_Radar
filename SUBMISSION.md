# Nebius x NVIDIA Global AI Hackathon — Project Submission

## Project Name: FactCheck Radar
**Track**: Best Apps & Agents Track  
**GitHub Repository**: [https://github.com/amansheikh-techie/FactCheck_Radar](https://github.com/amansheikh-techie/FactCheck_Radar)  
**Demo URL**: Integrated self-hosted web app (Local / Docker / Nebius Serverless Container)

---

## 💡 Elevator Pitch
**FactCheck Radar** is an autonomous multi-stage AI agent that counters misinformation by analyzing claims, breaking headlines, or news URLs in real time. Powered by **NVIDIA Nemotron models via Nebius Token Factory** and **Tavily AI Search**, it extracts atomic assertions, retrieves authoritative cross-web evidence, weighs conflicting sources, and delivers nuanced verdicts with calibrated confidence scores and verifiable citations over a live streaming timeline.

---

## 🎯 Inspiration
In an era dominated by hyper-speed digital news and AI-generated content, misinformation travels faster than traditional fact-checking desks can publish. When people encounter sensationalist claims on social media or in group chats, they rarely have the time to perform rigorous source cross-examination.

Existing AI chatbots often hallucinate, cite outdated knowledge cutoff data, or provide vague opinions. We wanted to build an autonomous fact-checking engine that mirrors the investigative rigor of professional journalism:
1. Deconstructs complex inputs into verifiable atomic statements.
2. Formulates neutral, objective search queries to avoid confirmation bias.
3. Retrieves authoritative evidence across multiple independent web domains.
4. Critically evaluates source credibility and stance (supports, contradicts, neutral).
5. Synthesizes conflicting evidence to deliver a clear verdict with cited proofs.

---

## ⚙️ What It Does
1. **Multi-Format Input**: Accepts single claims, viral headlines, or direct URLs to news articles (extracting full text automatically via `trafilatura` with built-in SSRF protection).
2. **Autonomous Multi-Stage Pipeline**:
   - **Stage 1 (Claim Extraction)**: Isolates up to 3 distinct checkable claims using fast **NVIDIA Nemotron Nano 30B**.
   - **Stage 2 (Query Generation)**: Generates 1–2 neutral, unbiased search queries per claim to prevent search bias.
   - **Stage 3 (Evidence Retrieval)**: Executes parallel targeted web searches via **Tavily AI Search**, with domain deduplication to ensure diverse source representation.
   - **Stage 4 (Source Assessment)**: Nemotron Nano reads each snippet and categorizes the source stance (`supports`, `contradicts`, or `neutral`) with a 1-sentence rationale.
   - **Stage 5 (Reasoning & Verdict)**: **NVIDIA Nemotron Ultra 550B** synthesizes the entire evidentiary body, detects nuances, calibrates a confidence score (0–100%), and produces an articulated verdict with linked citations.
3. **Live Streaming UX**: Built with Server-Sent Events (SSE) so users observe each agent step in real-time.
4. **Rich Verdict Dashboard**: Displays verdict badges (`True`, `Mostly True`, `Mixed`, `Mostly False`, `False`, `Unverifiable`), visual confidence gauge, copy/share actions, and expandable source citation drawers.

---

## 🛠️ How We Built It

### The Stack
- **Inference & LLMs**: **NVIDIA Nemotron** models (`nvidia/Nemotron-3-Nano-30B-A3B`, `nvidia/Nemotron-3-Ultra-550b-a55b`) hosted on **Nebius Token Factory** (`https://api.tokenfactory.nebius.com/v1`).
- **Web Search**: **Tavily AI Search API** (`tavily-python`) with advanced search depth and multi-domain deduplication.
- **Backend**: **FastAPI** (Python 3.11+) with async streaming SSE, Pydantic v2 strict schemas, in-memory LRU TTL caching, and SSRF validation.
- **Frontend**: **React 19 + Vite + Tailwind CSS v4**, featuring class-based dark/light mode toggle, dynamic step timeline, and responsive mobile-first layout.
- **DevOps & Packaging**: Multi-stage Docker container (`node:20-alpine` + `python:3.11-slim`), `docker-compose.yml`, and comprehensive Pytest suite.

---

## 📋 Hackathon Requirements Verification

| Requirement | Implementation Details | Status |
|---|---|:---:|
| **1. NVIDIA Nemotron via Nebius Token Factory** | Configured via OpenAI-compatible SDK pointing to `https://api.tokenfactory.nebius.com/v1`. Probes `GET /v1/models` on startup to verify presence of `nvidia/Nemotron-3-Nano-30B-A3B` and `nvidia/Nemotron-3-Ultra-550b-a55b`. Implements fallback chains for high availability. | ✅ Passed |
| **2. Tavily Search API** | Integrated using `TavilyClient` with `search_depth="advanced"`. Generates 1–2 unbiased search queries per claim and deduplicates results by domain. | ✅ Passed |
| **3. Multi-Stage Agent Pipeline** | 5 discrete steps: Extraction (Nano) → Query Generation (Nano) → Search (Tavily) → Stance Assessment (Nano) → Synthesis & Verdict (Ultra). | ✅ Passed |
| **4. Real-Time Streaming UI** | Server-Sent Events (SSE) stream step transitions, intermediate extracted claims, and the final structured verdict with confidence meters and source citations. | ✅ Passed |
| **5. Robust Error Handling & Resilience** | Retries with exponential backoff on API errors, in-band JSON validation auto-repair, SSRF filtering, path traversal defense, and fallback handling for non-factual inputs. | ✅ Passed |
| **6. Production Ready** | Multi-stage Dockerfile, automated test suite (13/13 passing tests), live smoke test script, and complete architecture documentation. | ✅ Passed |

---

## 🚧 Challenges We Ran Into & Solutions

1. **Async Event Loop Blocking with Synchronous SDKs**:
   - *Challenge*: Both the official OpenAI Python SDK and Tavily SDK perform synchronous blocking HTTP calls under their standard clients, which could freeze FastAPI's async event loop.
   - *Solution*: We encapsulated all third-party SDK calls inside `asyncio.to_thread()`, ensuring high concurrency without thread starvation.

2. **Strict JSON Schema Enforcement across Varied Outputs**:
   - *Challenge*: LLMs occasionally wrap JSON in markdown code blocks (` ```json ... ``` `) or return edge-case structures that cause Pydantic validation failures.
   - *Solution*: Built `_clean_json_str()` to automatically normalize raw model output, coupled with an automatic in-band retry loop that feeds the exact Pydantic `ValidationError` back into the model to self-heal.

3. **Tailwind CSS v4 Dark Mode Compatibility**:
   - *Challenge*: Tailwind CSS v4 transitioned from JavaScript configuration to pure CSS-first configuration, ignoring traditional `tailwind.config.js` dark mode settings.
   - *Solution*: Configured `@custom-variant dark (&:where(.dark, .dark *));` in `index.css`, restoring class-based dark mode toggling.

4. **Security: SSRF Prevention for URL Ingestion**:
   - *Challenge*: Allowing arbitrary user-submitted URLs for article extraction exposes the server to Server-Side Request Forgery against internal cloud metadata endpoints.
   - *Solution*: Engineered a comprehensive `is_safe_url()` filter that blocks `localhost`, `127.0.0.1`, AWS/GCP metadata (`169.254.169.254`), and private RFC1918 subnets.

---

## 🏆 Accomplishments That We're Proud Of
- **Model Specialization Harmony**: Successfully balanced latency and reasoning depth by letting Nemotron Nano handle rapid tasks while reserving Nemotron Ultra for complex synthesis.
- **Zero-Flicker Streaming UI**: Users receive instant feedback the millisecond they submit a claim, seeing the agent extract claims, generate search terms, and pull live sources.
- **Production-Grade Packaging**: Built a single, self-contained multi-stage Docker container that serves both the compiled React frontend and the FastAPI backend on port 8000.

---

## 🔬 What We Learned
- How to harness NVIDIA Nemotron models through Nebius Token Factory for production agentic pipelines.
- Best practices in structuring multi-agent handoffs with Server-Sent Events.
- Techniques for prompt-level debiasing to ensure search queries remain neutral rather than confirmatory.

---

## 🔮 What's Next for FactCheck Radar
- **Multimodal Fact-Checking**: Ingesting misleading screenshots, memes, and deepfake audio using Nemotron Vision models.
- **Browser Extension**: A Chrome/Firefox extension that automatically checks highlighted text or tweets with one click.
- **Community Consensus Staking**: Allowing community fact-checkers to annotate and vote on edge cases.
