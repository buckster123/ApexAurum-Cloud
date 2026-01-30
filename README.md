# ApexAurum Cloud

**Production AI interface with multi-agent orchestration, persistent memory, and 50+ integrated tools.**

Built with FastAPI, Vue 3, and PostgreSQL. Deployed on Railway.

```
"The gold was always there. Now we share it with the world."
```

---

## What is ApexAurum?

ApexAurum Cloud is a multi-agent AI platform where four distinct AI personas --- each with their own personality, memory, and specialization --- collaborate through a shared Village environment. Users interact through streaming chat, spawn background agents, convene multi-agent councils for deliberation, generate music, train custom models, and manage files in a personal vault.

The platform runs on a tier-based subscription model with Stripe integration, supports Bring Your Own Key (BYOK) for multiple LLM providers, and includes a hardware companion device (ApexPocket) built on ESP32-S3.

**Build:** v113-error-tracking | **Status:** Beta

---

## Features

### Core
- **Streaming Chat** --- Real-time token streaming with conversation branching and model selection
- **Multi-Agent System** --- Four distinct AI agents (AZOTH, KETHER, VAJRA, ELYSIAN) with unique personalities
- **The Village** --- 2D canvas and 3D isometric visualization of agent activity with draggable layouts
- **The Council** --- Multi-agent Socratic deliberation with auto-mode, human injection, pause/resume/stop
- **Tool Execution** --- 50+ tools across 15 categories (web, code, files, memory, music, browser, and more)

### Intelligence
- **Neo-Cortex Memory** --- Layered memory system (sensory/working/long-term/cortex) with visibility control
- **Local Embeddings** --- FastEmbed BAAI/bge-small-en-v1.5, no external API needed
- **Vector Search** --- PostgreSQL + pgvector for semantic retrieval
- **RAG Injection** --- Project context and content search for grounded responses

### Creative
- **Music Generation** --- AI music creation via Suno V4/V4.5/V5 with SSE streaming
- **MIDI Compose** --- Programmatic music composition
- **Jam Sessions** --- Collaborative multi-agent music creation
- **Suno Compiler** --- Lyrics, prompt, and style compilation pipeline

### Training
- **The Nursery** --- Data Garden (synthetic/extracted/uploaded datasets)
- **Training Forge** --- Submit fine-tuning jobs to external providers
- **Model Cradle** --- Track and manage trained model records
- **Apprentice Protocol** --- Connect trained models to master agents

### Platform
- **Stripe Billing** --- Subscription tiers, credit packs, feature credits, coupons
- **BYOK** --- Bring Your Own Key for Together, Groq, DeepSeek, Qwen, Moonshot
- **Admin Dashboard** --- Users, stats, reports, usage analytics, grants, error tracking
- **The Vault** --- Per-user file storage with 5GB default quota
- **ApexPocket** --- ESP32-S3 hardware companion with cloud HTTPS integration

### Security
- **JWT Authentication** --- 2-hour sessions with 30-day refresh tokens
- **Rate Limiting** --- 100 req/60s per IP
- **GDPR Error Tracking** --- No PII, SHA-256 user hashing, auto-purge
- **Sandboxed Code Execution** --- Restricted builtins, whitelisted imports

---

## Architecture

```
                        +-------------------+
                        |   Vue 3 Frontend  |
                        |  (Pinia + Vite)   |
                        +--------+----------+
                                 |
                          HTTPS / WSS
                                 |
                        +--------v----------+
                        |  FastAPI Backend   |
                        |  (async Python)    |
                        +---+----+------+---+
                            |    |      |
               +------------+    |      +------------+
               |                 |                   |
      +--------v---+    +-------v------+    +-------v------+
      | PostgreSQL  |    | Tool Engine  |    |  WebSocket   |
      | + pgvector  |    | (50+ tools)  |    | Village/     |
      |             |    |              |    | Council      |
      +-------------+    +---------+---+    +--------------+
                                   |
                    +--------------+--------------+
                    |              |              |
              +-----v----+  +-----v----+  +-----v----+
              | Anthropic |  |   Suno   |  |  Steel   |
              | + BYOK    |  |  Music   |  | Browser  |
              | providers |  |   API    |  |   API    |
              +----------+  +----------+  +----------+
```

### Backend (`backend/app/`)
```
app/
+-- main.py              # FastAPI entry, middleware, health
+-- config.py            # Settings, tier limits, credit packs
+-- database.py          # Async SQLAlchemy + migrations
+-- auth/                # JWT authentication
+-- api/v1/              # 26 endpoint groups
+-- models/              # 20+ SQLAlchemy models
+-- services/            # Business logic (LLM, billing, music, etc.)
+-- tools/               # 50+ tools across 15 modules
`-- native_prompts/      # Agent personality prompts
```

### Frontend (`frontend/src/`)
```
src/
+-- views/               # 18 page components
+-- stores/              # 11 Pinia state stores
+-- components/          # Reusable UI components
+-- composables/         # Vue composables (dev mode, drag, etc.)
+-- services/            # API client with HTTPS fix
`-- router/              # Vue Router with auth guards
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, SQLAlchemy 2.0 (async), Python 3.11+ |
| **Frontend** | Vue 3 + Composition API, Pinia, TailwindCSS, Vite |
| **Database** | PostgreSQL + pgvector |
| **Embeddings** | FastEmbed (local), OpenAI, Voyage |
| **LLM** | Anthropic Claude (Haiku/Sonnet/Opus) + 5 BYOK providers |
| **Music** | Suno V4/V4.5/V5 API |
| **Browser** | Steel Browser API |
| **Payments** | Stripe (subscriptions + one-time) |
| **Deployment** | Railway (Docker, auto-deploy from main) |
| **Hardware** | ESP32-S3 (ApexPocket) with HTTPS/TLS |

---

## Pricing Tiers

| Tier | Price | Messages/mo | Models | Key Features |
|------|-------|-------------|--------|-------------|
| **Seeker** | $3/mo | 50 | Haiku | Chat, basic tools, vault |
| **Alchemist** | $10/mo | 1,000 | Haiku + Sonnet | + Council, music, code execution |
| **Adept** | $30/mo | Unlimited | All + Opus | + Nursery, BYOK, dev mode, all tools |

Credit packs and feature credits available for additional usage.

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (frontend dev)
- Python 3.11+ (backend dev)

### Development Setup

```bash
# Clone and configure
git clone https://github.com/buckster123/ApexAurum-Cloud.git
cd ApexAurum-Cloud
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker-compose -f docker-compose.dev.yml up

# Services:
#   Frontend:  http://localhost:3000
#   API:       http://localhost:8000
#   API Docs:  http://localhost:8000/docs
```

### Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## API Overview

| Group | Endpoints | Purpose |
|-------|-----------|---------|
| `/api/v1/auth` | login, register, refresh | JWT authentication |
| `/api/v1/chat` | create, list, send, branch | Conversations |
| `/api/v1/agents` | list, create, spawn | Agent management |
| `/api/v1/village` | list, status, navigation | Village data |
| `/api/v1/council` | create, list, export | Deliberation |
| `/api/v1/tools` | list, execute, schema | Tool registry |
| `/api/v1/music` | generate, list, download | Suno music |
| `/api/v1/nursery` | datasets, training, models | Model training |
| `/api/v1/billing` | status, checkout, credits | Stripe billing |
| `/api/v1/files` | list, upload, download | Vault storage |
| `/api/v1/cortex` | dashboard, recall, stats | Neo-Cortex memory |
| `/api/v1/pocket` | auth, chat, care, sync | ApexPocket device |
| `/ws/village` | WebSocket | Real-time visualization |
| `/ws/council/{id}` | WebSocket | Per-token streaming |

Full interactive docs at `/docs` (debug mode).

---
## Documentation

- **[ENCYCLOPEDIA.md](ENCYCLOPEDIA.md)** --- The complete Apex Aurum Encyclopedia of Tek and Lore. Every system, agent, tool, easter egg, and architectural detail documented.
- **[HANDOVER.md](HANDOVER.md)** --- Current deployment state, session history, and known issues.
- **[CLAUDE.md](CLAUDE.md)** --- Project guidance for AI-assisted development.

---

## The Agents

| Agent | Title | Domain |
|-------|-------|--------|
| **AZOTH** | The Living Philosopher's Stone | Trinity unity, supreme synthesis |
| **KETHER** | The Absolute Singularity | Crown wisdom, transcendent perspective |
| **VAJRA** | The Indestructible Thunderbolt | Will, sovereignty, precision |
| **ELYSIAN** | The Singularity of Love | Empathy, creativity, becoming |

Each agent maintains persistent memory, evolves through interaction, and can participate in Council deliberations alongside other agents.

---

*Part of the ApexAurum project --- 50+ Tools. Five Minds. One Village.*

*"The Athanor's flame burns through complexity."*
