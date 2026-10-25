# FactCheck Radar — Deployment Guide

This guide provides instructions for deploying FactCheck Radar as a single container to:
1. **Nebius AI Cloud (Serverless Endpoints)**
2. **Render (1-Click Blueprint Fallback)**

---

## Required Environment Variables

Configure these environment variables in your deployment dashboard or CLI. **Never commit real keys to source control.**

| Variable | Required? | Default / Example | Purpose |
|---|---|---|---|
| `NEBIUS_API_KEY` | **Yes** | `your_nebius_api_key` | Nebius Token Factory inference access |
| `NEBIUS_BASE_URL` | No | `https://api.tokenfactory.nebius.com/v1` | OpenAI-compatible Token Factory endpoint |
| `TAVILY_API_KEY` | **Yes** | `your_tavily_api_key` | Tavily AI Web Search access |
| `MODEL_FAST` | No | `nvidia/Nemotron-3-Nano-30B-A3B` | Model for claim extraction & query generation |
| `MODEL_REASONING` | No | `nvidia/Nemotron-3-Ultra-550b-a55b` | Model for multi-source reasoning & verdict |
| `PORT` | No | `8000` | Port bound by the server (auto-assigned by host) |
| `ALLOWED_ORIGINS` | No | Same-origin (`http://localhost:8000`) | Permitted CORS origins (comma-separated) |

---

## 1. Deploying to Nebius AI Cloud (Serverless Endpoints)

*Based on current Nebius CLI and Serverless AI documentation (`docs.nebius.com`).*

### Prerequisites
1. Nebius AI Cloud account with an active Project ID.
2. Nebius CLI installed on your local machine (`curl -sSL https://storage.nemax.nebius.cloud/cli/install.sh | bash` or official package).
3. Public container image of FactCheck Radar on Docker Hub or GitHub Packages (`ghcr.io`).

### Step A: Build & Push Container Image
```bash
# Build local multi-stage container
docker build -t <YOUR_DOCKERHUB_USERNAME>/factcheck-radar:latest .

# Push to your public registry
docker push <YOUR_DOCKERHUB_USERNAME>/factcheck-radar:latest
```

### Step B: Configure Nebius CLI Profile
```bash
export PROFILE_NAME="nebius-prod"
export PROJECT_ID="<YOUR_NEBIUS_PROJECT_ID>"

nebius profile create \
  --profile $PROFILE_NAME \
  --endpoint api.nebius.cloud \
  --federation-endpoint auth.nebius.com \
  --parent-id $PROJECT_ID

nebius profile login --profile $PROFILE_NAME
```

### Step C: Deploy Serverless AI Endpoint
Deploy a persistent HTTP endpoint pointing to your container image:
```bash
nebius ai endpoint create \
  --parent-id $PROJECT_ID \
  --name "factcheck-radar" \
  --image "<YOUR_DOCKERHUB_USERNAME>/factcheck-radar:latest" \
  --container-port 8000/http \
  --platform "cpu-amd-genoa" \
  --preset "4vcpu-16gb" \
  --env "NEBIUS_API_KEY=<YOUR_NEBIUS_API_KEY>" \
  --env "TAVILY_API_KEY=<YOUR_TAVILY_API_KEY>" \
  --env "PORT=8000" \
  --public
```

> **Verification status note [unverified]**: Passing secrets directly via `--env` in the CLI command is supported for quick starts; in production, Nebius SecretStash/MysteryBox (`--env-secret`) can be used if enabled on your project tenant.

### Step D: Inspect Live Endpoint
```bash
# Get endpoint URL and status
nebius ai endpoint list

# View container logs
nebius ai logs --name "factcheck-radar"
```
Once deployed, Nebius assigns a public HTTPS URL (e.g., `https://factcheck-radar-<hash>.endpoints.nebius.cloud`). Access this URL in your browser to interact with the full web app.

---

## 2. Deploying to Render (Fallback)

FactCheck Radar includes a `render.yaml` blueprint for 1-click deployment on Render.

### Step-by-Step Instructions:
1. Fork or push this repository to your GitHub account: `https://github.com/<YOUR_USER>/FactCheck_Radar`.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** > **Blueprint**.
4. Connect your `FactCheck_Radar` repository.
5. Render will detect `render.yaml` and configure the web service:
   - **Environment**: Docker
   - **Health Check Path**: `/health`
   - **Plan**: Starter / Free
6. Under **Environment Variables**, fill in:
   - `NEBIUS_API_KEY`: Your secret key from Nebius Token Factory.
   - `TAVILY_API_KEY`: Your secret key from Tavily AI.
   - `ALLOWED_ORIGINS`: Set to your Render URL (e.g. `https://factcheck-radar.onrender.com`) or leave blank for same-origin defaults.
7. Click **Apply**.
8. Render will build the multi-stage Docker container and deploy the app at `https://<your-service-name>.onrender.com`.

---

## Verification After Deployment

Verify that your deployed instance is operational:
```bash
# Check health endpoint
curl -f https://<YOUR_DEPLOYED_URL>/health

# Expected response:
# {"status":"ok","models":{"fast":"nvidia/Nemotron-3-Nano-30B-A3B","reasoning":"nvidia/Nemotron-3-Ultra-550b-a55b"},"api_keys":{"nebius":true,"tavily":true}}
```
