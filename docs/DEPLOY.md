# FactCheck Radar — Deployment Guide

This guide provides instructions for deploying FactCheck Radar with switchable LLM providers (**NVIDIA Build NIM** or **Nebius Token Factory**).

> **Deployment Truthfulness Statement**: The live deployed demonstration of FactCheck Radar runs on **Render** (via Docker container) using the hosted **NVIDIA NIM API** (`https://integrate.api.nvidia.com/v1`) from `build.nvidia.com`. **Nebius Token Factory** is an officially supported, fully swappable inference provider (`LLM_PROVIDER=nebius`), not the currently deployed live instance host.

---

## Environment Variables Reference

Configure these variables in your deployment dashboard or `.env`. **Never commit real secret keys to source control.**

| Variable | Required? | Default / Example | Purpose |
|---|---|---|---|
| `LLM_PROVIDER` | No | `nvidia` | Active LLM inference provider: `"nvidia"` (default) or `"nebius"` |
| `NVIDIA_API_KEY` | **Yes** (if `nvidia`) | `nvapi-...` | NVIDIA API Catalog key from `build.nvidia.com` |
| `NVIDIA_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` | OpenAI-compatible endpoint for NVIDIA NIM inference |
| `NVIDIA_MODEL_FAST` | No | `nvidia/nemotron-3.5-lightning-30b-a3b` | Fast model for extraction & query generation on NVIDIA |
| `NVIDIA_MODEL_REASONING` | No | `nvidia/nemotron-3-ultra-550b-a55b` | Frontier reasoning model for final verdict on NVIDIA |
| `NEBIUS_API_KEY` | **Yes** (if `nebius`) | `your_nebius_key` | Nebius Token Factory API key |
| `NEBIUS_BASE_URL` | No | `https://api.tokenfactory.nebius.com/v1/` | OpenAI-compatible Token Factory endpoint |
| `NEBIUS_MODEL_FAST` | No | `nvidia/Nemotron-3-Nano-30B-A3B` | Fast model for extraction & query generation on Nebius |
| `NEBIUS_MODEL_REASONING` | No | `nvidia/Nemotron-3-Ultra-550b-a55b` | Heavyweight reasoning model on Nebius |
| `TAVILY_API_KEY` | **Yes** | `tvly-...` | Tavily AI Web Search access for evidence retrieval |
| `PORT` | No | `8000` | HTTP port bound by the container |
| `ALLOWED_ORIGINS` | No | Same-origin (`http://localhost:8000`) | Permitted CORS origins (comma-separated) |
| `DEMO_MODE` | No | `false` | Explicit sample demo mode (never silently enabled) |

---

## 1. Deploying to Render (Active Live Deployment)

FactCheck Radar includes a `render.yaml` blueprint for 1-click containerized deployment on Render.

### Step-by-Step Instructions:
1. Push your repository to GitHub: `https://github.com/amansheikh-techie/FactCheck_Radar`.
2. Open the [Render Dashboard](https://dashboard.render.com).
3. Click **New +** > **Blueprint**.
4. Connect the repository.
5. Render detects `render.yaml` and sets up the Docker web service:
   - **Environment**: Docker (multi-stage build)
   - **Health Check Path**: `/health`
   - **Plan**: Starter / Free
6. Under **Environment Variables**, provide your secret keys:
   - `LLM_PROVIDER`: `nvidia` (or `nebius`)
   - `NVIDIA_API_KEY`: Your key from `build.nvidia.com`
   - `TAVILY_API_KEY`: Your key from Tavily
   - If switching to Nebius: set `LLM_PROVIDER=nebius` and supply `NEBIUS_API_KEY`.
7. Click **Apply**. Render builds the image and deploys the service.

---

## 2. Running Locally or in Self-Hosted Docker

### Run with Docker:
```bash
# Build multi-stage image
docker build -t factcheck-radar:latest .

# Run container with environment file
docker run -p 8000:8000 --env-file .env factcheck-radar:latest
```

### Run Locally (Python 3.11+ / 3.14):
```bash
# Start backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Open browser
http://localhost:8000
```

---

## 3. Verification After Deployment

Verify that your deployed instance is operational:
```bash
# Check health endpoint
curl -f https://<YOUR_DEPLOYED_URL>/health

# Expected response:
# {
#   "status": "ok",
#   "provider": "nvidia",
#   "base_url": "https://integrate.api.nvidia.com/v1",
#   "model_fast": "nvidia/nemotron-3.5-lightning-30b-a3b",
#   "model_reasoning": "nvidia/nemotron-3-ultra-550b-a55b",
#   "models_used": {
#     "fast": "nvidia/nemotron-3.5-lightning-30b-a3b",
#     "reasoning": "nvidia/nemotron-3-ultra-550b-a55b"
#   },
#   "api_keys": {
#     "configured": true,
#     "provider": "nvidia",
#     "tavily": true
#   }
# }
```
