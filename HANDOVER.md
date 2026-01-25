# ApexAurum-Cloud Handover Document

**Date:** 2026-01-25
**Build:** v15-village
**Status:** Core features LIVE, Settings/Admin page planned

---

## What's WORKING (Fully Deployed)

| Feature | Status | URL |
|---------|--------|-----|
| Backend | v15-village | https://backend-production-507c.up.railway.app |
| Frontend | LIVE | https://frontend-production-5402.up.railway.app |
| PostgreSQL | Connected | Internal Railway network |

### Chat System
- **Streaming responses** - Real-time token-by-token
- **5 Agent Personas** - AZOTH, ELYSIAN, VAJRA, KETHER, CLAUDE
- **Auth bypass** - Works without login (conversations don't persist)

### Agent System (`/agents`)
- **Spawn Agents** - Execute tasks with specialized prompts
- **Socratic Council** - Multi-agent deliberation with voting
- **5 Agent Types** - general, researcher, coder, analyst, writer

### Village Protocol (`/village`)
- **Add Knowledge** - Store info from any agent
- **Browse/Search** - Full knowledge base access
- **Convergence Detection** - Claude analyzes for agent agreement
- **HARMONY/CONSENSUS alerts** when agents align

---

## Bugs Fixed This Session

| Bug | Cause | Fix |
|-----|-------|-----|
| Deploy failures | Root `railway.json` override | Deleted it |
| UI black screen on send | `VITE_API_URL` not in build | Added as Docker ARG |
| 401 redirect loops | Endpoints required auth | Made auth-optional |
| Network error | CORS missing prod frontend | Added to allowed_origins |

---

## Native Prompts (IMPORTANT!)

Located in `/native_prompts/`:
- `∴AZOTH∴.txt` - Full prose prompt
- `∴ELYSIAN∴.txt` - Full prose prompt
- `∴VAJRA∴.txt` - Full prose prompt
- `∴KETHER∴.txt` - Full prose prompt
- `∴AZOTH∴-PAC.txt` - Hyperdense symbolic format (needs parser)

Currently **hardcoded simplified versions** in `backend/app/api/v1/chat.py`.
The plan includes loading these dynamically.

---

## NEXT SESSION: Settings/Admin Page

**Plan saved at:** `/home/hailo/.claude/plans/moonlit-stirring-rabbit.md`

### Key Features to Build:

1. **Easter Egg Dev Mode**
   - Konami code OR 7-tap on "Au" logo
   - Unlocks full customization

2. **Standard Mode** (default)
   - Profile, Default Agent, Theme
   - Simple and clean

3. **Dev Mode** (easter egg)
   - Tabs: Profile | Agents | Advanced | API
   - View/edit native prompts
   - Create custom agents with custom prompts
   - Model selection, temperature, max tokens

4. **New Files Needed:**
   - `backend/app/api/v1/prompts.py` - Prompt management API
   - `frontend/src/components/AgentPromptEditor.vue` - Editor
   - `frontend/src/composables/useDevMode.js` - Easter egg

5. **Modify:**
   - `SettingsView.vue` - Complete restructure
   - `chat.py` - Dynamic prompt loading
   - `ChatView.vue` - Custom agents in selector

---

## Railway Quick Reference

```bash
# Health check
curl https://backend-production-507c.up.railway.app/health

# Deploy (always use full commit hash!)
COMMIT=$(git rev-parse HEAD)

# Backend
curl -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"

# Frontend
curl -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"
```

---

## Session Highlights

We went from **broken deploys** to **fully functional cloud app** in one session:

- v8 → v15 (7 versions deployed)
- Fixed 4 critical bugs
- Enabled streaming
- Wired up 5 agent personas
- Built working agent spawn + Socratic council
- Implemented Village Protocol with convergence detection
- Planned Settings/Admin page with easter egg dev mode

**The furnace is HOT. We're COOKING.**

---

*Written by Claude Opus 4.5 for session continuity*
*"Transmuting code to gold, one deploy at a time"*
