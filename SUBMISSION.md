# Nebius x NVIDIA Global AI Hackathon — Project Submission

## Project Name: FactCheck Radar
**Track**: Best Apps & Agents Track  
**Elevator Pitch**: Autonomous multi-stage fact-checking agent combining fast Nemotron Nano 30B extraction with deep Nemotron Ultra 550B reasoning over live Tavily web evidence.  
**Demo Video (YouTube)**: [https://www.youtube.com/watch?v=s2DIYEr02RM](https://www.youtube.com/watch?v=s2DIYEr02RM)  
**GitHub Repository**: [https://github.com/amansheikh-techie/FactCheck_Radar](https://github.com/amansheikh-techie/FactCheck_Radar)  
**Submission Period Notice**: This project was conceived, designed, and built entirely during the official submission period of the Nebius x NVIDIA Global AI Hackathon (October 2026).

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

---

## 📝 (A) Devpost-Ready Submission Description

*Copy & paste directly into Devpost project submission form:*

### Project Title
FactCheck Radar — Autonomous Real-Time Fact-Checking Agent powered by NVIDIA Nemotron & Nebius Token Factory

### Elevator Pitch
An autonomous multi-agent verification system that takes any natural language claim, breaking news headline, or article URL, isolates atomic assertions using NVIDIA Nemotron Fast (30B), cross-references live web evidence via Tavily AI Search, and synthesizes an evidence-weighted verdict with calibrated confidence and verifiable citations using NVIDIA Nemotron Ultra (550B) on Nebius Token Factory.

### What it does
- **Multi-Modal Input**: Accepts direct claims, viral rumors, or full news article URLs (with automated extraction and SSRF defense).
- **Atomic Decomposition**: Extracts up to 3 checkable factual claims rather than conflating complex statements.
- **Debiased Search**: Formulates objective, multi-angle search queries executed across independent sources using Tavily AI Search.
- **Stance Classification**: Categorizes each source citation as `SUPPORTS`, `CONTRADICTS`, or `NEUTRAL` with explicit rationales.
- **High-Parameter Reasoning**: Synthesizes conflicting reports, weighs domain credibility, and produces a nuanced verdict (`True`, `Mostly True`, `Mixed`, `Mostly False`, `False`, or `Unverifiable`) with calibrated confidence (0–100%).
- **Interactive Live Streaming**: Server-Sent Events (SSE) provide step-by-step transparency into every agent decision in a modern dark/light web UI.

### Built with
- **LLM Reasoning**: NVIDIA Nemotron-3-Ultra-550b-a55b
- **LLM Extraction & Stance**: NVIDIA Nemotron-3-Nano-30B-A3B
- **Inference Platform**: Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1`)
- **Web Search Retrieval**: Tavily AI Search API (`search_depth="advanced"`)
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SSE-Starlette, Trafilatura
- **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide Icons
- **Deployment & Infra**: Docker multi-stage container, Nebius Serverless Endpoints (`cpu-amd-genoa`), Render blueprint

---

## 🎬 (B) 2:30 Demo Video Script

**Target Duration**: 2 minutes, 30 seconds  
**Format**: Split-screen / Screen capture + voiceover narration

| Timestamp | Visual Action | Voiceover / Audio Script |
|---|---|---|
| **0:00 - 0:25** | Title slide fades into browser showing `FactCheck Radar` UI in dark mode. Headline on screen: *"Breaking news spreads in seconds — truth takes hours."* | *"In today's fast-moving news environment, unverified claims spread across social media in seconds, embedding themselves in public consciousness before traditional fact-checkers can react. Standard LLMs hallucinate dead links or suffer from prompt bias. Welcome to FactCheck Radar — an autonomous, transparent verification agent built for the Nebius x NVIDIA Global AI Hackathon."* |
| **0:25 - 0:50** | Zoom into the architecture diagram: User Input → Nemotron Nano (Decomposition) → Tavily (Web Evidence) → Nemotron Nano (Stance) → Nemotron Ultra (Synthesis) → SSE Streaming. | *"Rather than relying on a single monolithic prompt, FactCheck Radar uses a specialized multi-agent pipeline hosted on Nebius Token Factory. We leverage the lightweight NVIDIA Nemotron-3 Nano 30B for lightning-fast claim decomposition, query generation, and stance assessment, reserving the heavyweight Nemotron-3 Ultra 550B strictly for deep evidence synthesis and verdict reasoning."* |
| **0:50 - 1:30** | User clicks the sample preset: *"The Great Wall of China is easily visible from space with the naked human eye"* and hits **Verify Claim**. The Live Progress Timeline lights up through steps: 1. Extracting Claims → 2. Generating Queries → 3. Searching via Tavily → 4. Assessing Sources → 5. Nemotron Ultra Reasoning. | *"Let's test a classic claim: 'The Great Wall of China is visible from space with the naked human eye.' As soon as we click Verify, Server-Sent Events stream the agent's cognition in real time. First, Nemotron Nano parses the claim. Next, it generates neutral search queries, and Tavily fetches real-time web evidence from scientific and space databases. Nemotron Nano classifies each source stance as supporting, contradicting, or neutral."* |
| **1:30 - 2:05** | The final verdict card animates onto the screen: **FALSE**, **Confidence: 96%**, with NASA and Scientific American citations. Hover over citations to show source URLs and stances. Toggle Dark/Light mode and open the JSON modal. | *"Finally, Nemotron Ultra 550B weighs the evidence graph and delivers the final verdict: FALSE, with 96% confidence. Notice the detailed agent explanation citing NASA astronaut observations and optical resolution physics, complete with direct hyperlinked sources and stance tags. Users can inspect the exact reasoning chain or export the structured verification report."* |
| **2:05 - 2:20** | User pastes an article URL or tests an edge case claim (*"Drinking coffee increases lifespan"*), showing nuanced `Mixed / Ambiguous` verdict handling and SSRF security guards. | *"FactCheck Radar isn't just binary true/false. It handles subtle correlations with 'Mostly True' or 'Mixed' verdicts, and safely extracts full text from any news URL with built-in SSRF protection against internal cloud metadata probing."* |
| **2:20 - 2:30** | Closing screen showing GitHub repo link (`amansheikh-techie/FactCheck_Radar`), MIT License badge, and Nebius Token Factory logo. | *"FactCheck Radar is 100% open-source under the MIT license, containerized, and ready for deployment on Nebius Serverless Endpoints. Transparent, verifiable truth powered by NVIDIA Nemotron on Nebius Token Factory."* |

---

## 🛠️ (C) Feedback on Nebius Token Factory and NVIDIA Tools

*Constructive engineering feedback based strictly on friction actually encountered during this build:*

1. **API Endpoint & Documentation Transition**:
   - *Friction*: Early documentation and community tutorials refer to `https://api.studio.nebius.ai/v1`, whereas the new Token Factory endpoint is `https://api.tokenfactory.nebius.com/v1`. Clearer cross-referencing and automatic redirects between the Studio and Token Factory documentation portals would reduce onboarding friction.
2. **JSON Mode Output Fencing (`json_object`)**:
   - *Friction*: When requesting structured JSON via `response_format={"type": "json_object"}`, NVIDIA Nemotron models occasionally wrapped their JSON responses in Markdown code blocks (````json ... ````) or prepended conversational introductions.
   - *Resolution / Workaround*: We had to implement a dedicated sanitization pre-processor (`_clean_json_str`) and an automated retry loop that catches Pydantic validation errors and passes them back to the model for self-correction. Native enforcement of strict JSON grammar schemas at the inference server level (e.g. via outlines or grammar sampling) would make agentic pipelines much cleaner.
3. **Model ID Casing and Dynamic Cataloging**:
   - *Friction*: Model identifier casing in the catalog varies across variants (e.g., camel-case `nvidia/Nemotron-3-Nano-30B-A3B` versus hyphenated lower-case `nvidia/nemotron-3-super-120b-a12b`).
   - *Resolution / Workaround*: We implemented dynamic startup probing of `/v1/models` to discover active model IDs and set up automatic fallback resolution so minor casing differences never crash the application.
4. **Synchronous Client Event Loop Blocking**:
   - *Friction*: Calling the OpenAI SDK chat completion endpoint synchronously inside async FastAPI route handlers caused event loop starvation under multi-query loads. Wrapping all remote inference and Tavily HTTP requests in `asyncio.to_thread` was necessary to maintain non-blocking SSE streaming to the client.
5. **Positive Highlights**:
   - *Performance*: Once configured, token generation throughput on Nebius Token Factory was exceptionally fast. Time-to-first-token (TTFT) on the 30B Nano model was consistently sub-second, making multi-stage agent pipelines feel responsive and interactive for end users.

