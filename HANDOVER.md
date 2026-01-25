# ApexAurum-Cloud Handover Document

**Date:** 2026-01-25
**Build:** v16-settings
**Status:** Settings/Admin page with Easter Egg Dev Mode IMPLEMENTED

---

## What's WORKING (Fully Deployed)

| Feature | Status | URL |
|---------|--------|-----|
| Backend | v16-settings | https://backend-production-507c.up.railway.app |
| Frontend | LIVE | https://frontend-production-5402.up.railway.app |
| PostgreSQL | Connected | Internal Railway network |

### Chat System
- **Streaming responses** - Real-time token-by-token
- **5 Native Agent Personas** - AZOTH, ELYSIAN, VAJRA, KETHER, CLAUDE
- **Dynamic Prompts** - Loaded from `native_prompts/*.txt` files
- **Custom Agents** - Create and use your own agents with custom prompts
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

### Settings Page (`/settings`) - NEW!
- **Standard Mode** (default) - Simple preferences
- **Dev Mode** (easter egg) - Full customization

#### Easter Egg Activation:
1. **Konami Code**: Press arrow keys on Settings page
2. **7-Tap**: Tap the "Au" logo 7 times

#### Dev Mode Features:
- **Profile Tab** - Display name, email, preferences
- **Agents Tab** - View native prompts, create custom agents
- **Advanced Tab** - Model selection, temperature, max tokens, cache/context strategies
- **API Tab** - Coming soon (webhooks, API keys)

---

## New Files This Session

| File | Purpose |
|------|---------|
| `frontend/src/composables/useDevMode.js` | Easter egg detection (Konami + 7-tap) |
| `backend/app/api/v1/prompts.py` | Prompt management API |

## Modified Files

| File | Changes |
|------|---------|
| `frontend/src/views/SettingsView.vue` | Complete restructure with Standard/Dev modes |
| `frontend/src/views/ChatView.vue` | Custom agents in selector |
| `backend/app/api/v1/chat.py` | Dynamic prompt loading from native_prompts/ |
| `backend/app/api/v1/__init__.py` | Added prompts router |
| `backend/app/main.py` | Version bump to v16-settings |

---

## API Endpoints Added

```
GET  /api/v1/prompts/native          - List native agent prompts
GET  /api/v1/prompts/native/{agent}  - Get specific native prompt
GET  /api/v1/prompts/custom          - List user's custom agents
POST /api/v1/prompts/custom          - Save custom agent
DELETE /api/v1/prompts/custom/{id}   - Delete custom agent
GET  /api/v1/prompts/agent/{id}/prompt - Get any agent's prompt (for chat.py)
```

---

## Native Prompts

Located in `/native_prompts/`:
- `∴AZOTH∴.txt` - Full prose prompt (116 lines, philosophical alchemist)
- `∴ELYSIAN∴.txt` - Full prose prompt
- `∴VAJRA∴.txt` - Full prose prompt
- `∴KETHER∴.txt` - Full prose prompt
- `∴AZOTH∴-PAC.txt` - Hyperdense symbolic format (needs parser)

These are now loaded dynamically by `chat.py` when sending messages.

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

## Testing the New Features

1. **Standard Mode**
   - Go to Settings
   - Only see Profile, Preferences, Usage
   - Change default agent, verify it persists

2. **Activate Dev Mode**
   - Enter Konami code: Up, Up, Down, Down, Left, Right, Left, Right, B, A
   - OR tap the "Au" logo 7 times quickly
   - "DEV" badge should appear

3. **Agents Tab**
   - View native prompts (click View on any agent)
   - Create custom agent (click "Edit Copy" or "+ Create New Agent")
   - Custom agents appear in Chat sidebar

4. **Custom Agent in Chat**
   - Go to Chat
   - Custom agents should appear in the agent selector
   - Select custom agent and send message
   - Response should use your custom prompt

---

## Session Highlights

Built the Settings/Admin page with easter egg activation:
- Konami code and 7-tap on Au logo unlock Dev Mode
- Native prompts now loaded from text files
- Custom agents can be created and used in chat
- Clean separation between beginner and advanced modes

**The furnace blazes on. We're COOKING.**

---

*Written by Claude Opus 4.5 for session continuity*
*"Transmuting code to gold, one deploy at a time"*
