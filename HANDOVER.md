# ApexAurum-Cloud Handover Document

**Date:** 2026-01-25
**Build:** v18-pac-mode
**Status:** PAC Mode DEPLOYED - The Adept's Transformation

---

## What's WORKING (Fully Deployed)

| Feature | Status | URL |
|---------|--------|-----|
| Backend | v18-pac-mode | https://backend-production-507c.up.railway.app |
| Frontend | LIVE | https://frontend-production-5402.up.railway.app |
| PostgreSQL | Connected | Internal Railway network |

### Chat System
- **Streaming responses** - Real-time token-by-token
- **5 Native Agent Personas** - AZOTH, ELYSIAN, VAJRA, KETHER, CLAUDE
- **Dynamic Prompts** - Loaded from `native_prompts/*.txt` files
- **Custom Agents** - Create and use your own agents with custom prompts
- **PAC Agents** - Perfected Alchemical Codex versions (Layer 2 easter egg)
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

### Settings Page (`/settings`)
- **Standard Mode** (default) - Simple preferences
- **Dev Mode** (Layer 1 easter egg) - Full customization
- **PAC Mode** (Layer 2 easter egg) - The Adept's realm

---

## ∴ PAC MODE - NEW! ∴

### The Three Layers of Alchemy

| Layer | Name | Activation | Features |
|-------|------|------------|----------|
| 0 | Mundane | Default | Standard UI |
| 1 | The Apprentice | Konami/7-tap | Dev Mode, custom agents |
| 2 | The Adept | Type "AZOTH" | PAC prompts, alchemical theme |

### Activating PAC Mode

1. First unlock Dev Mode (Layer 1):
   - **Konami Code**: ↑↑↓↓←→←→BA on any page
   - **7-Tap**: Tap "Au" logo 7 times on Settings

2. Then speak the name of the Stone (Layer 2):
   - **Type "AZOTH"** (A-Z-O-T-H on keyboard)
   - Watch the console for whispered letters
   - Full activation shows epic console art

### PAC Mode Visual Features

- **Alchemical Theme** - Purple/gold color scheme
- **Floating Symbols** - ∴ ☿ ☉ ☽ ♀ ♂ ∞ ⚗ rise from below
- **Glowing Cards** - Ethereal borders and shadows
- **Agent Halos** - Breathing glow animations
- **Codex Viewer** - Special monospace styling for PAC prompts

### PAC Mode Functional Features

- **Perfected Stones Section** - In Settings, shows agents with PAC prompts
- **View Codex** - Read the hyperdense symbolic prompts
- **PAC Agents in Chat** - Select "AZOTH-Ω" etc. to use PAC version
- **Backend Support** - `use_pac=true` loads PAC prompt files

---

## New Files This Session

| File | Purpose |
|------|---------|
| `frontend/src/components/AlchemicalParticles.vue` | Floating symbols component |

## Modified Files

| File | Changes |
|------|---------|
| `frontend/src/composables/useDevMode.js` | Added PAC mode, AZOTH detection, layer system |
| `frontend/src/assets/main.css` | Full alchemical theme (190+ lines) |
| `frontend/src/App.vue` | Particles, pac-mode body class |
| `frontend/src/views/SettingsView.vue` | Perfected Stones section, Codex viewer |
| `frontend/src/views/ChatView.vue` | PAC agents, visual transformation |
| `frontend/src/stores/chat.js` | `usePac` parameter for API calls |
| `backend/app/api/v1/chat.py` | `use_pac` parameter, PAC prompt loading |

---

## API Changes

```
POST /api/v1/chat/message
  - Added: use_pac: bool (default false)
  - When true, loads PAC version of prompt (*-PAC.txt files)

GET /api/v1/prompts/native/{agent}?prompt_type=pac
  - Added: prompt_type query param
  - Returns PAC prompt when prompt_type=pac
```

---

## Native Prompts

Located in `backend/native_prompts/`:
- `∴AZOTH∴.txt` - Prose prompt (philosophical alchemist)
- `∴AZOTH∴-PAC.txt` - PAC version (hyperdense symbolic)
- `∴ELYSIAN∴.txt` - Prose prompt
- `∴VAJRA∴.txt` - Prose prompt
- `∴KETHER∴.txt` - Prose prompt

PAC prompts are loaded when `use_pac=True` in chat request.
They're sent raw as system messages - no parsing needed.

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

## Testing PAC Mode

1. **Enable Dev Mode First**
   - Go to Settings
   - Enter Konami code OR tap Au logo 7 times
   - "DEV" badge appears

2. **Activate PAC Mode**
   - Type A-Z-O-T-H on keyboard
   - Watch console for letter whispers
   - On completion: epic console activation
   - Visual transformation begins

3. **Visual Checks**
   - Background shifts to purple gradient
   - Floating alchemical symbols appear
   - Cards have ethereal glow
   - Settings badge shows "THE ADEPT"

4. **Perfected Stones**
   - Go to Settings > Agents tab
   - "The Perfected Stones" section appears (PAC mode only)
   - Click "View Codex" to see PAC prompts

5. **Chat with PAC Agent**
   - Go to Chat
   - PAC agents appear with Ω suffix (e.g., "AZOTH-Ω")
   - Select PAC agent and send message
   - Should use hyperdense PAC prompt

---

## Session Highlights

∴ THE MAGNUM OPUS ∴

Built the full PAC Mode experience:
- Two-layer easter egg system (Apprentice → Adept)
- AZOTH incantation detection with keyboard sequence
- Complete visual transformation (purple/gold alchemical theme)
- Floating symbols animation
- Codex viewer for PAC prompts
- Backend PAC prompt loading
- PAC agents in chat selector

**The Stone awakens for those who speak its name.**

---

*Written by Claude Opus 4.5 for session continuity*
*"In the crucible of code, the Philosopher's Stone is forged"*
