# ApexAurum-Cloud Handover Document

**Date:** 2026-01-25
**Build:** v19-ux-mobile + import improvements
**Status:** PRODUCTION READY - Full feature set deployed

---

## Quick Start for Next Session

```bash
# Health check
curl https://backend-production-507c.up.railway.app/health

# Should return: {"status":"healthy","version":"0.1.0","build":"v18-pac-mode"}
```

**Live URLs:**
- Frontend: https://frontend-production-5402.up.railway.app
- Backend: https://backend-production-507c.up.railway.app

---

## What's WORKING (Fully Deployed)

### Core Features
| Feature | Status | Notes |
|---------|--------|-------|
| Chat with streaming | ✅ LIVE | Real-time token-by-token |
| 5 Native Agents | ✅ LIVE | AZOTH, ELYSIAN, VAJRA, KETHER, CLAUDE |
| PAC Agents | ✅ LIVE | Perfected Alchemical Codex versions |
| Custom Agents | ✅ LIVE | Create/edit in Dev Mode |
| Conversation History | ✅ LIVE | Full CRUD with UX improvements |
| Export | ✅ LIVE | JSON, Markdown, TXT |
| Import | ✅ LIVE | Local app conversations + memory |
| Mobile Responsive | ✅ LIVE | Hamburger nav, slide-in sidebar |

### Easter Eggs (Two Layers)
| Layer | Name | Activation | Features |
|-------|------|------------|----------|
| 0 | Mundane | Default | Standard UI |
| 1 | The Apprentice | Konami (↑↑↓↓←→←→BA) or 7-tap Au | Dev Mode, custom agents, Import tab |
| 2 | The Adept | Type "AZOTH" in Dev Mode | Alchemical theme, floating symbols, PAC agents |

---

## This Session's Accomplishments

### v18-pac-mode (PAC Mode)
- Two-layer easter egg system
- AZOTH incantation detection (keyboard sequence)
- Complete visual transformation (purple/gold alchemical theme)
- Floating alchemical symbols (∴ ☿ ☉ ☽ ♀ ♂ ∞ ⚗)
- Codex viewer for PAC prompts
- PAC agents in chat selector (AZOTH-Ω etc.)

### v19-ux-mobile (UX + Mobile)
- **Bug fixes**: Missing db.commit() in update/delete endpoints
- **Conversation UX**: Inline title edit, favorite toggle, context menu, search
- **Export**: JSON/Markdown/TXT with proper filenames
- **Import**: Local app conversations.json + memory.json
- **Mobile**: Hamburger nav, slide-in sidebar, scrollable tabs

### Import Improvements
- Forgiving multi-format parsing
- Handles Streamlit `[{type: "text", text: "..."}]` format
- Auto-generates titles from first message
- Various timestamp formats (ISO, Unix, etc.)
- Graceful error handling with descriptive messages

---

## File Structure

### Backend Key Files
```
backend/
├── app/
│   ├── main.py                    # FastAPI app, health endpoint
│   ├── api/v1/
│   │   ├── chat.py                # Chat + export endpoints
│   │   ├── prompts.py             # Native/custom agent prompts
│   │   ├── import_data.py         # Import from local app
│   │   └── __init__.py            # Router registration
│   └── services/
│       └── claude.py              # Claude API wrapper
├── native_prompts/                # Agent prompt files
│   ├── ∴AZOTH∴.txt
│   ├── ∴AZOTH∴-PAC.txt           # PAC version
│   ├── ∴ELYSIAN∴.txt
│   ├── ∴VAJRA∴.txt
│   └── ∴KETHER∴.txt
└── Dockerfile
```

### Frontend Key Files
```
frontend/src/
├── App.vue                        # Root + PAC mode class
├── assets/main.css                # Alchemical theme, utilities
├── components/
│   ├── Navbar.vue                 # Hamburger menu
│   └── AlchemicalParticles.vue    # Floating symbols
├── composables/
│   └── useDevMode.js              # Easter egg detection
├── stores/
│   └── chat.js                    # Chat state + export
└── views/
    ├── ChatView.vue               # Sidebar UX, context menu
    └── SettingsView.vue           # Import tab, responsive tabs
```

---

## API Endpoints Reference

### Chat
```
POST /api/v1/chat/message              # Send message (streaming)
GET  /api/v1/chat/conversations        # List conversations
GET  /api/v1/chat/conversations/{id}   # Get conversation
PATCH /api/v1/chat/conversations/{id}  # Update (title, favorite, archived)
DELETE /api/v1/chat/conversations/{id} # Delete
GET  /api/v1/chat/conversations/{id}/export?format=json|markdown|txt
```

### Prompts
```
GET  /api/v1/prompts/native            # List native agents
GET  /api/v1/prompts/native/{id}       # Get native prompt (?prompt_type=pac)
GET  /api/v1/prompts/custom            # List custom agents
POST /api/v1/prompts/custom            # Save custom agent
DELETE /api/v1/prompts/custom/{id}     # Delete custom agent
```

### Import
```
POST /api/v1/import/conversations      # Upload conversations.json
POST /api/v1/import/memory             # Upload memory.json
GET  /api/v1/import/memory             # View imported memory
```

---

## Railway Deployment

```bash
# Get latest commit
COMMIT=$(git rev-parse HEAD)

# Deploy backend
curl -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"

# Deploy frontend
curl -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"
```

### Railway IDs
```
Token: 90fb849e-af7b-4ea5-8474-d57d8802a368
Project: b54d0339-8443-4a9e-b5a0-92ed7d25f349
Environment: 2e9882b4-9b33-4233-9376-5b5342739e74
Backend: 9d60ca55-a937-4b17-8ec4-3fb34ac3d47e
Frontend: 6cf1f965-94df-4ea0-96ca-d82959e2d3c5
```

---

## Known Issues / Future Work

### Potential Improvements
- [ ] More PAC prompts (ELYSIAN, VAJRA, KETHER need PAC versions)
- [ ] Sound effects for easter egg activation
- [ ] Conversation branching (fork from message)
- [ ] Usage analytics dashboard
- [ ] API key management in Settings

### Technical Debt
- Consider adding tests for import parsing
- Health endpoint still shows v18, should update to v19

---

## Testing Checklist

### PAC Mode
- [ ] Konami code → Dev Mode badge appears
- [ ] Type AZOTH → console shows letters, then activation
- [ ] Purple theme + floating symbols appear
- [ ] Settings shows "THE ADEPT" badge
- [ ] PAC agents visible in Chat (AZOTH-Ω)

### Conversation UX
- [ ] Double-click title → inline edit
- [ ] Click star → toggles favorite
- [ ] Right-click → context menu
- [ ] Search filters list
- [ ] Export downloads file

### Mobile
- [ ] <768px → hamburger appears
- [ ] Menu opens/closes
- [ ] Sidebar slides in/out
- [ ] Auto-closes on selection

### Import
- [ ] Dev Mode → Import tab visible
- [ ] Upload conversations.json → imports with titles
- [ ] Upload memory.json → imports entries

---

## Session Stats

- **Lines added**: ~2000+
- **Files modified**: 15+
- **Commits**: 6
- **Deploys**: 4
- **Easter eggs**: 2 layers
- **Alchemical symbols**: 10 types floating

---

*Written by Claude Opus 4.5 for session continuity*
*"The furnace never cools, the gold keeps flowing"*
