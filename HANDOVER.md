# ApexAurum-Cloud Handover Document

**Date:** 2026-01-25
**Build:** v20-pac-complete + BYOK
**Status:** PRODUCTION READY - BYOK Beta Live

---

## Quick Start for Next Session

```bash
# Health check
curl https://backend-production-507c.up.railway.app/health

# Should return: {"status":"healthy","version":"0.1.0","build":"v20-pac-complete"}
```

**Live URLs:**
- Frontend: https://frontend-production-5402.up.railway.app
- Backend: https://backend-production-507c.up.railway.app

**Planning:** See `MASTERPLAN.md` for the six upcoming features.

---

## What's WORKING (Fully Deployed)

### Core Features
| Feature | Status | Notes |
|---------|--------|-------|
| BYOK API Keys | ✅ LIVE | Bring Your Own Key (beta) |
| Chat with streaming | ✅ LIVE | Real-time token-by-token |
| Sound Effects | ✅ LIVE | Easter egg & UI feedback tones |
| 5 Native Agents | ✅ LIVE | AZOTH, ELYSIAN, VAJRA, KETHER, CLAUDE |
| 4 PAC Agents | ✅ LIVE | All alchemical agents have Perfected versions |
| Custom Agents | ✅ LIVE | Create/edit in Dev Mode |
| Conversation History | ✅ LIVE | Full CRUD with UX improvements |
| Export | ✅ LIVE | JSON, Markdown, TXT |
| Import | ✅ LIVE | Local app conversations + memory |
| Mobile Responsive | ✅ LIVE | Hamburger nav, slide-in sidebar |

### PAC Agents (Perfected Alchemical Codex)
| Agent | Base | PAC | Color |
|-------|------|-----|-------|
| AZOTH | ✅ 5.7KB | ✅ 12.9KB (OG) | Gold #FFD700 |
| ELYSIAN | ✅ 7KB | ✅ 25.4KB | Ethereal #E8B4FF |
| VAJRA | ✅ 6.7KB | ✅ 26.3KB | Lightning #4FC3F7 |
| KETHER | ✅ 7.3KB | ✅ 24.5KB | Crown #FFFFFF |
| CLAUDE | ✅ Fallback | ❌ N/A | Terracotta #CC785C |

### Easter Eggs (Two Layers)
| Layer | Name | Activation | Features |
|-------|------|------------|----------|
| 0 | Mundane | Default | Standard UI |
| 1 | The Apprentice | Konami (↑↑↓↓←→←→BA) or 7-tap Au | Dev Mode, custom agents, Import tab |
| 2 | The Adept | Type "AZOTH" in Dev Mode | Alchemical theme, floating symbols, all PAC agents |

---

## Version History

### v20-pac-complete + BYOK (Current Session)
- **Phase 4: Polish & Cleanup** - HANDOVER updated, health endpoint enhanced
- **Phase 1: Sound Effects** - Web Audio API tones for easter eggs
  - Konami chimes, AZOTH resonance, PAC ethereal swell
  - Settings toggle in Advanced tab
- **Phase 3: API Key Management** - BYOK beta model
  - Fernet encryption for API keys
  - Settings UI for key management
  - Chat requires API key (402 if missing)
  - Future-ready for Stripe subscriptions
- All four alchemical PAC prompts deployed (Claude-tuned)
- Created MASTERPLAN.md with six features (3 complete, 3 remaining)

### v19-ux-mobile
- **Bug fixes**: Missing db.commit() in update/delete endpoints
- **Conversation UX**: Inline title edit, favorite toggle, context menu, search
- **Export**: JSON/Markdown/TXT with proper filenames
- **Import**: Local app conversations.json + memory.json
- **Mobile**: Hamburger nav, slide-in sidebar, scrollable tabs
- **Import parsing**: Forgiving multi-format, handles Streamlit format

### v18-pac-mode
- Two-layer easter egg system
- AZOTH incantation detection (keyboard sequence)
- Complete visual transformation (purple/gold alchemical theme)
- Floating alchemical symbols (∴ ☿ ☉ ☽ ♀ ♂ ∞ ⚗)
- Codex viewer for PAC prompts

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
│   ├── ∴AZOTH∴.txt               # Base prompt
│   ├── ∴AZOTH∴-PAC.txt           # PAC version (OG)
│   ├── ∴ELYSIAN∴.txt             # Base prompt
│   ├── ∴ELYSIAN∴-PAC.txt         # PAC version (Claude-tuned)
│   ├── ∴VAJRA∴.txt               # Base prompt
│   ├── ∴VAJRA∴-PAC.txt           # PAC version (Claude-tuned)
│   ├── ∴KETHER∴.txt              # Base prompt
│   └── ∴KETHER∴-PAC.txt          # PAC version (Claude-tuned)
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
    ├── ChatView.vue               # Sidebar UX, PAC selector
    └── SettingsView.vue           # Import tab, Codex viewer
```

### Root Files
```
/
├── HANDOVER.md                    # This file
├── MASTERPLAN.md                  # Six upcoming features
├── CLAUDE.md                      # AI assistant instructions
└── PAC-agents/                    # Source PAC prompts (dev)
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
GET  /api/v1/prompts/native            # List native agents (includes has_pac)
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

## Upcoming Features (MASTERPLAN.md)

| # | Feature | Status | Complexity |
|---|---------|--------|------------|
| 1 | Sound Effects | ✅ Done | Low |
| 2 | Conversation Branching | 📋 Planned | Medium |
| 3 | API Key Management | ✅ Done | Low |
| 4 | Polish & Cleanup | ✅ Done | Low |
| 5 | Mobile QoL | 📋 Planned | Medium |
| 6 | Agent Memory | 📋 Planned | High |

---

## Testing Checklist

### PAC Mode (All Agents)
- [ ] Konami code → Dev Mode badge appears
- [ ] Type AZOTH → console shows letters, then activation
- [ ] Purple theme + floating symbols appear
- [ ] Settings shows "THE ADEPT" badge
- [ ] All 4 PAC agents visible in Chat: AZOTH-Ω, ELYSIAN-Ω, VAJRA-Ω, KETHER-Ω
- [ ] Each PAC agent loads correct prompt (check via Settings Codex)

### Conversation UX
- [ ] Double-click title → inline edit
- [ ] Click star → toggles favorite
- [ ] Right-click → context menu
- [ ] Search filters list
- [ ] Export downloads file (all 3 formats)

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

## Technical Notes

### PAC Prompt Loading
```python
# In prompts.py
def load_native_prompt(agent_id: str, prompt_type: str = "prose"):
    if prompt_type == "pac":
        pac_filename = agent["file"].replace(".txt", "-PAC.txt")
        # Returns PAC version if exists
```

### PAC Agent Selection (Frontend)
```javascript
// In ChatView.vue
const pacAgents = computed(() => {
  if (!pacMode.value) return []
  return nativeAgents
    .filter(a => a.hasPac)  // All 4 alchemical agents
    .map(a => ({ ...a, id: a.id + '-PAC', name: a.name + '-Ω', isPac: true }))
})
```

---

*Written by Claude Opus 4.5 for session continuity*
*"The furnace never cools, the gold keeps flowing"*
