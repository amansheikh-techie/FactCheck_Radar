# Nebius x NVIDIA Global AI Hackathon — Project Submission

## Project Name: FactCheck Radar
**Track**: Best Apps & Agents Track  
**Elevator Pitch**: Autonomous multi-stage fact-checking agent combining fast Nemotron Nano 30B extraction with deep Nemotron Ultra 550B reasoning over live Tavily web evidence.  
**Demo Video (YouTube)**: [https://www.youtube.com/watch?v=s2DIYEr02RM](https://www.youtube.com/watch?v=s2DIYEr02RM)  
**GitHub Repository**: [https://github.com/amansheikh-techie/FactCheck_Radar](https://github.com/amansheikh-techie/FactCheck_Radar)

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
2. **Atomic Claim Extraction**: Isolates up to 3 distinct, checkable factual assertions.
3. **Neutral Query Synthesis**: Generates balanced, unbiased search phrases designed to retrieve both supporting and debunking evidence without leading the search engine.
4. **Live Evidence Retrieval**: Uses Tavily AI Search to pull relevant web evidence, automatically deduplicating across domains so one SEO-heavy site doesn't dominate the results.
5. **Stance Analysis**: Classifies each source snippet as `supports`, `contradicts`, or `neutral` with a concrete one-sentence justification.
6. **Deep Reasoning & Verdict**: Synthesizes the full evidence graph to assign an overall verdict (`True`, `Mostly True`, `Mixed`, `Mostly False`, `False`, `Unverifiable`), a calibrated confidence score (0–100%), and direct hyperlinked citations.
7. **Real-Time Streaming**: Everything streams over Server-Sent Events (SSE) into a responsive UI with a live progress timeline, animated confidence gauge, and dark/light mode.

---

### How We Built It (Engineering Architecture)

#### 1. Dual-Model Specialization on Nebius Token Factory
Running a 550B model for every lightweight parsing step is expensive and introduces unnecessary latency. We decoupled the pipeline into specialized roles:
- **Fast Agent (`nvidia/Nemotron-3-Nano-30B-A3B`)**: Handles the high-speed work — atomic claim decomposition, search query crafting, and per-snippet stance classification.
- **Reasoning Agent (`nvidia/Nemotron-3-Ultra-550b-a55b`)**: Reserved strictly for the final synthesis step, weighing contradictory sources and calibrating uncertainty.

We connect to the **Nebius Token Factory** using the OpenAI-compatible SDK with a configurable base URL (`https://api.tokenfactory.nebius.com/v1`). At startup, the backend automatically probes `/v1/models` to verify cluster availability and activate fallback chains if needed.

#### 2. Full-Stack System
- **Backend**: FastAPI (Python 3.11+) with async streaming endpoints, Pydantic v2 schemas for strict JSON validation, and an in-memory LRU cache with a 15-minute TTL.
- **Frontend**: React 19 bootstrapped with Vite and styled using Tailwind CSS v4 (with class-based dark mode variants).
- **Packaging**: Self-contained multi-stage Docker container (`node:20-alpine` frontend build stage + `python:3.11-slim` backend runtime) exposing port 8000.

---

### Engineering Challenges & Battle Scars

Building multi-agent pipelines that run reliably in production always uncovers edge cases:

- **The Event Loop Trap**: Both the OpenAI and Tavily Python SDKs make blocking network calls under their standard synchronous clients. Under concurrent user traffic, this blocked FastAPI's async event loop. We wrapped all third-party SDK calls in `asyncio.to_thread` to ensure zero worker starvation.
- **LLM Markdown Fencing & JSON Resiliency**: Even when setting `response_format={"type": "json_object"}`, models occasionally sneak in triple-backtick markdown fences (` ```json `) or hallucinate schema variations. We built a markdown cleaner (`_clean_json_str`) and a self-healing retry handler that feeds the exact Pydantic `ValidationError` back to the model for an in-band correction.
- **SSRF Hardening**: Accepting arbitrary URLs for article extraction is an open invitation for Server-Side Request Forgery. We wrote an `is_safe_url` validator that blocks loopback (`127.0.0.1`, `localhost`), link-local AWS/GCP metadata endpoints (`169.254.169.254`), and private RFC1918 subnets.
- **Tailwind v4 Migration**: Tailwind v4 shifted away from `tailwind.config.js` to CSS-first `@custom-variant` directives. We configured custom CSS variants to keep class-based dark mode switching rock solid.

---

### Accomplishments That We're Proud Of

- **13/13 Passing Automated Tests**: Full test suite covering Pydantic schemas, cache TTL/LRU eviction, SSRF guards, pipeline orchestration, and non-factual input fallback handling.
- **True Latency Optimization**: Sub-second extraction handoffs with the Nano model, keeping the total fact-check cycle snappy despite deep web searches and 550B reasoning.
- **Graceful Degradation**: If an input contains no verifiable claims (like greetings or opinions), the agent doesn't burn Tavily search credits — it immediately explains why the input is unverifiable.

---

### What We Learned

- How to architect real-world agentic handoffs with NVIDIA Nemotron on Nebius Token Factory.
- Designing prompts specifically for *debiased search*: how subtle wording changes in query generation prevent the search engine from returning one-sided echo-chamber results.
- Balancing real-time streaming feedback with structured validation guarantees.

---

### What's Next

- **Multimodal Evidence**: Extending the pipeline to analyze viral screenshots, infographics, and deepfake audio using Nemotron Vision endpoints.
- **Browser Extension**: A lightweight Chrome extension to highlight any sentence on the web and trigger FactCheck Radar in a sidebar.
