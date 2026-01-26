# CLAUDE.md - ApexAurum Cloud

This file provides guidance to Claude Code when working with this repository.

## Project Overview

ApexAurum Cloud is the cloud-deployed version of ApexAurum, a production-grade AI chat interface. This repo contains ONLY the cloud deployment code - clean, minimal, Railway-ready.

**Stack:**
- **Backend:** FastAPI + PostgreSQL + Claude API (Anthropic)
- **Frontend:** Vue 3 + Vite + TailwindCSS + Pinia
- **Deployment:** Railway (PostgreSQL, Backend, Frontend services)

## 🔥 SESSION START PROTOCOL

**ALWAYS read HANDOVER.md first!** It contains:
- Current deployment state
- Railway IDs and tokens
- What's working vs pending
- Exact commands to deploy and verify

```bash
# Quick status check
curl https://backend-production-507c.up.railway.app/health
```

## Project Structure

```
ApexAurum-Cloud/
├── backend/
│   ├── Dockerfile           # Production Dockerfile (relative paths!)
│   ├── requirements.txt     # Python dependencies
│   ├── railway.toml         # Railway build config
│   ├── alembic/             # Database migrations
│   └── app/
│       ├── main.py          # FastAPI app entry
│       ├── config.py        # Settings from env vars
│       ├── database.py      # Async SQLAlchemy setup
│       ├── api/v1/          # API endpoints
│       │   ├── auth.py      # Login/register/refresh
│       │   ├── chat.py      # Chat with Claude (KEY FILE)
│       │   └── ...
│       ├── auth/            # JWT authentication
│       ├── models/          # SQLAlchemy models
│       ├── schemas/         # Pydantic schemas
│       └── services/
│           └── claude.py    # Claude API wrapper
├── frontend/
│   ├── Dockerfile           # Production Dockerfile
│   ├── package.json
│   ├── railway.toml
│   └── src/
│       ├── App.vue
│       ├── main.js
│       ├── router/index.js  # Vue Router (auth guards)
│       ├── stores/
│       │   ├── auth.js      # Auth state (Pinia)
│       │   └── chat.js      # Chat state (KEY FILE)
│       ├── services/
│       │   └── api.js       # Axios with interceptors
│       └── views/
│           ├── ChatView.vue # Main chat interface
│           ├── LoginView.vue
│           └── ...
├── HANDOVER.md              # Session continuity (READ FIRST!)
└── CLAUDE.md                # This file
```

## Critical Knowledge: Railway Deployment

### Railway Does NOT Auto-Deploy!

This is the #1 gotcha. When you push to GitHub, Railway does NOT automatically deploy. You MUST trigger manually with the commit SHA:

```bash
# Get latest commit
git log --oneline -1

# Deploy backend
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { serviceInstanceDeploy(serviceId: \"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\", environmentId: \"2e9882b4-9b33-4233-9376-5b5342739e74\", commitSha: \"HASH\") }"}'

# Deploy frontend
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { serviceInstanceDeploy(serviceId: \"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\", environmentId: \"2e9882b4-9b33-4233-9376-5b5342739e74\", commitSha: \"HASH\") }"}'
```

### Railway IDs Reference

```
Token: 90fb849e-af7b-4ea5-8474-d57d8802a368
Project: b54d0339-8443-4a9e-b5a0-92ed7d25f349
Environment: 2e9882b4-9b33-4233-9376-5b5342739e74
Backend: 9d60ca55-a937-4b17-8ec4-3fb34ac3d47e
Frontend: 6cf1f965-94df-4ea0-96ca-d82959e2d3c5
Postgres: f557140e-349b-4c84-8260-4a0edcc07e6b
```

### Dockerfile Paths Must Be Relative!

Railway uses `rootDirectory` setting. When `rootDirectory=backend`:
- Build context IS `backend/`
- ✅ `COPY requirements.txt .`
- ❌ `COPY backend/requirements.txt .` (tries backend/backend/)

### Check What's Actually Deployed

```bash
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "query { deployments(first: 1, input: { serviceId: \"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\" }) { edges { node { status meta } } } }"}' \
  | jq '.data.deployments.edges[0].node | {status, commit: .meta.commitHash}'
```

## Key Files to Know

### Backend

**`app/api/v1/chat.py`** - The chat endpoint
- Uses `get_current_user_optional` for auth bypass (testing)
- Calls Claude via `ClaudeService`
- Saves messages to PostgreSQL (when authenticated)

**`app/services/claude.py`** - Claude API wrapper
- Model: `claude-3-haiku-20240307` (fast, cheap for testing)
- Supports streaming and non-streaming

**`app/main.py`** - FastAPI app
- Health check at `/health` (add build tag to verify deploys!)
- CORS configured for frontend
- Docs disabled in production (`settings.debug`)

### Frontend

**`src/stores/chat.js`** - Chat state management
- `sendMessage()` calls backend API
- Model default must match valid Claude model ID!

**`src/router/index.js`** - Route guards
- `requiresAuth: true/false` controls access
- Auth bypass for `/chat` during testing

**`src/services/api.js`** - Axios interceptor
- Auto-adds JWT token
- Redirects to `/login` on 401

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Not authenticated" | Auth required | Use `get_current_user_optional` |
| Build fails "file not found" | Wrong Dockerfile paths | Use relative paths |
| Deploy succeeds but old code | Railway cached old commit | Use `commitSha` in deploy |
| UI goes black on send | Backend error | Check backend logs in Railway |
| Health check missing build tag | Deploy didn't take | Verify commit hash in deployment meta |
| SQLAlchemy MissingGreenlet | Async lazy-load | Use `selectinload()` |
| Invalid model ID | Wrong Claude model | Use `claude-3-haiku-20240307` |

## Development Workflow

### Making Changes

1. Edit files in this repo
2. Commit and push:
   ```bash
   git add -A && git commit -m "Description" && git push
   ```
3. Get commit hash:
   ```bash
   git log --oneline -1
   ```
4. Deploy with commit hash (see commands above)
5. Wait 2-3 min for build
6. Verify deployment:
   ```bash
   curl https://backend-production-507c.up.railway.app/health
   ```

### Testing Chat API

```bash
# Without auth (after auth bypass)
curl -X POST "https://backend-production-507c.up.railway.app/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "stream": false}'
```

### Checking Logs

Railway dashboard → Service → Deployments → View Logs

Or save logs locally for analysis.

## The Athanor's Hands - Tool System

ApexAurum Cloud has a comprehensive tool system with **35 tools across 9 tiers**:

| Tier | Name | Tools | Description |
|------|------|-------|-------------|
| 1 | Utilities | 6 | Time, calculator, random, words, UUID, JSON |
| 2 | Web | 2 | Fetch URLs, DuckDuckGo search |
| 3 | Vault | 5 | File CRUD, search, storage stats |
| 4 | Knowledge | 4 | KB search, lookup, topics, answer |
| 5 | Memory | 4 | Session scratch storage |
| 6 | Code | 2 | Python execution, eval |
| 7 | Agents | 3 | Spawn, status, result |
| 8 | Vectors | 5 | Semantic memory (pgvector) |
| 9 | Music | 4 | Suno AI generation |

**Key Tool Files:**
- `backend/app/tools/base.py` - BaseTool, ToolSchema, ToolResult, ToolContext
- `backend/app/tools/__init__.py` - Registry and registration
- `backend/app/services/tool_executor.py` - Execution with context
- `TOOLS_MASTERPLAN.md` - Complete roadmap and progress tracker

**Future Tiers (planned):**
- Tier 10: Browser (Browserbase)
- Tier 11: Email
- Tier 12: Calendar
- Tier 13: Image (DALL-E)

## Environment Variables

**Set in Railway, not in code:**

- `DATABASE_URL` - PostgreSQL connection (uses Railway reference)
- `ANTHROPIC_API_KEY` - Claude API key
- `JWT_SECRET` - For token signing
- `VITE_API_URL` - Frontend → Backend URL
- `OPENAI_API_KEY` - For vector embeddings (Tier 8)
- `SUNO_API_KEY` - For music generation (Tier 9)

## URLs

- **Frontend:** https://frontend-production-5402.up.railway.app
- **Backend:** https://backend-production-507c.up.railway.app
- **Backend Health:** https://backend-production-507c.up.railway.app/health

## Easter Eggs & Hidden Features

### Two-Layer System
- **Layer 1 (Dev Mode)**: Konami code (↑↑↓↓←→←→BA) or 7-tap on Au logo
- **Layer 2 (PAC Mode)**: Type "AZOTH" while in Dev Mode

### Key Files
- `frontend/src/composables/useDevMode.js` - Easter egg detection logic
- `frontend/src/components/AlchemicalParticles.vue` - Floating symbols
- `frontend/src/assets/main.css` - PAC mode theme (190+ lines)

### PAC Prompts
- Located in `backend/native_prompts/`
- PAC versions use `-PAC.txt` suffix (e.g., `∴AZOTH∴-PAC.txt`)
- Loaded via `?prompt_type=pac` query parameter

## Import/Export

### Export
```bash
GET /api/v1/chat/conversations/{id}/export?format=json|markdown|txt
```

### Import (from local ApexAurum)
```bash
POST /api/v1/import/conversations  # Upload conversations.json
POST /api/v1/import/memory         # Upload memory.json
```

Supports multiple formats with forgiving parsing:
- Array format (Streamlit)
- Dict keyed by ID
- Structured content arrays `[{type: "text", text: "..."}]`

## Mobile Responsiveness

Key responsive features:
- `Navbar.vue`: Hamburger menu (`md:hidden` / `hidden md:flex`)
- `ChatView.vue`: Slide-in sidebar with backdrop
- `SettingsView.vue`: Horizontally scrollable tabs

Breakpoint: `md` = 768px (Tailwind default)

## Parent Project

This is the cloud deployment of ApexAurum. The full local version lives at:
`/home/hailo/claude-root/Projects/ApexAurum/`

That version has 106+ tools, Village Protocol, music generation, etc. The cloud version is rapidly catching up with its own tool system!

**Import compatible**: Cloud can import `sandbox/conversations.json` and `sandbox/memory.json` from local app.

**Code reuse**: Music tools and other features are adapted from the local version's implementations.

---

**Last Updated:** 2026-01-26
**Build:** v38-music-generation
**Status:** PRODUCTION READY - 35 Tools Across 9 Tiers
