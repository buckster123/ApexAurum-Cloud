# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ApexAurum Cloud is a production AI chat interface deployed on Railway. FastAPI backend + Vue 3 frontend + PostgreSQL.

**Always read `HANDOVER.md` first for current deployment state and known issues.**

## Quick Commands

```bash
# Health check
curl https://backend-production-507c.up.railway.app/health

# Test chat API (no auth)
curl -X POST "https://backend-production-507c.up.railway.app/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "stream": false}'
```

## Local Development

```bash
# Docker (recommended)
docker-compose -f docker-compose.dev.yml up
# Frontend: http://localhost:3000 | API: http://localhost:8000

# Without Docker - Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Without Docker - Frontend
cd frontend
npm install && npm run dev

# Database migrations
cd backend && alembic upgrade head
cd backend && alembic revision --autogenerate -m "description"

# Frontend linting
cd frontend && npm run lint
```

## Railway Deployment

**Railway does NOT auto-deploy from GitHub.** Trigger manually:

```bash
# Get latest commit
COMMIT=$(git log --oneline -1 | cut -d' ' -f1)

# Deploy backend
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"

# Deploy frontend
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"

# Check deployed commit
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "query { deployments(first: 1, input: { serviceId: \"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\" }) { edges { node { status meta } } } }"}' \
  | jq '.data.deployments.edges[0].node | {status, commit: .meta.commitHash}'
```

**Railway IDs:** Token `90fb849e-af7b-4ea5-8474-d57d8802a368` | Backend `9d60ca55-a937-4b17-8ec4-3fb34ac3d47e` | Frontend `6cf1f965-94df-4ea0-96ca-d82959e2d3c5`

## Architecture

```
backend/app/
├── main.py              # FastAPI entry, /health endpoint
├── config.py            # Settings from env vars
├── database.py          # Async SQLAlchemy setup
├── api/v1/
│   ├── chat.py          # Chat endpoint (KEY FILE) - calls ClaudeService
│   ├── auth.py          # JWT login/register/refresh
│   ├── billing.py       # Stripe integration
│   └── webhooks.py      # Stripe webhooks
├── services/
│   ├── claude.py        # Claude API wrapper
│   ├── llm_provider.py  # Multi-provider LLM (Anthropic, DeepSeek, Groq, etc.)
│   ├── billing.py       # Usage tracking
│   └── tool_executor.py # Tool execution with context
├── tools/               # 40+ tools across 10 tiers
│   ├── base.py          # BaseTool, ToolSchema, ToolResult
│   ├── utilities.py     # Tier 1: time, calc, uuid, etc.
│   ├── web.py           # Tier 2: fetch, search
│   ├── vault.py         # Tier 3: file CRUD
│   └── ...
└── models/              # SQLAlchemy models

frontend/src/
├── stores/
│   ├── chat.js          # Chat state (KEY FILE) - sendMessage()
│   ├── auth.js          # Auth state (Pinia)
│   └── billing.js       # Billing state
├── views/
│   ├── ChatView.vue     # Main chat interface
│   └── BillingView.vue  # Pricing tiers
├── services/api.js      # Axios with JWT interceptor
└── router/index.js      # Route guards (requiresAuth)
```

## Key Patterns

**Auth bypass for testing:** `get_current_user_optional` instead of `get_current_user` in endpoints.

**Async SQLAlchemy:** Use `selectinload()` for relationships to avoid MissingGreenlet errors.

**Dockerfile paths:** Railway uses `rootDirectory`, so paths must be relative (e.g., `COPY requirements.txt .` not `COPY backend/requirements.txt .`).

**Claude models:** Use `claude-3-haiku-20240307` (fast/cheap) or `claude-sonnet-4-20250514` (capable).

## Tool System

40+ tools across 10 tiers (see `TOOLS_MASTERPLAN.md`):
- Tier 1-7: Utilities, Web, Vault, Knowledge, Memory, Code, Agents (26 tools)
- Tier 8: Vector Search (pgvector + OpenAI embeddings)
- Tier 9: Music (Suno API)
- Tier 10: Browser (Steel Browser - self-hosted)

**Key files:** `backend/app/tools/base.py` (BaseTool class), `backend/app/tools/__init__.py` (registry)

## Easter Eggs

- **Dev Mode:** Konami code (↑↑↓↓←→←→BA) or 7-tap on Au logo
- **PAC Mode:** Type "AZOTH" while in Dev Mode
- **PAC prompts:** `backend/native_prompts/*-PAC.txt`

## Common Issues

| Issue | Solution |
|-------|----------|
| "Not authenticated" | Use `get_current_user_optional` |
| Build fails "file not found" | Use relative Dockerfile paths |
| Deploy succeeds but old code | Verify commit hash in deploy mutation |
| SQLAlchemy MissingGreenlet | Use `selectinload()` for relationships |
| Invalid model ID | Check valid Claude model IDs |
| TDZ error in frontend | Move function definitions before watchers with `immediate: true` |

## URLs

- Frontend: https://frontend-production-5402.up.railway.app
- Backend: https://backend-production-507c.up.railway.app
- API Docs (dev only): http://localhost:8000/docs
