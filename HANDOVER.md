# ApexAurum-Cloud Handover Document

**Date:** 2026-01-26
**Build:** v45-village-polish
**Status:** PRODUCTION - Village GUI with WebGL Fallback

---

## Session Summary: Village GUI Evolution

### What Was Accomplished

1. **Village Phase 0: WebSocket Infrastructure**
   - `VillageEventBroadcaster` service for real-time tool events
   - WebSocket endpoint at `/ws/village`
   - Tool-to-zone mapping for 46 tools across 8 zones
   - Hooks in tool registry to broadcast start/complete/error

2. **Village Phase 1: 2D Canvas GUI**
   - Canvas-based visualization with 8 zones
   - Agent circles with movement and glow effects
   - Real-time tool execution visualization

3. **Village Isometric 3D + Task Tickers**
   - Three.js OrthographicCamera isometric view
   - 8 zone "buildings" with shadows and glow
   - Agent spheres with smooth movement + pulse
   - Task Ticker top bar (compact progress)
   - Task Detail sidebar (full task cards)
   - 2D/3D view toggle with shared WebSocket
   - Mobile responsive with slide-up panel

4. **Village Phase 5: Polish**
   - Particle effects on tool completion (green=success, red=error)
   - Click detection for agents (raycasting)
   - Agent detail popup on click
   - Hover tooltips for agents and zones
   - Speech bubble system (approval/input/error)
   - Cursor changes on hover

5. **Bug Fixes This Session**
   - Fixed agent spawn `max_tokens` error (Haiku 3 = 4096, not 8192)
   - Fixed 3D not rendering (v-show → v-if for proper mounting)
   - Added WebGL error detection + auto-fallback to 2D
   - Added roundRect polyfill for older browsers

### Tool Count: 46 + 23 Features

| Tier | Name | Tools |
|------|------|-------|
| 1-10 | Previous | 40 |
| 11 | Neo-Cortex | 6 |
| **Total** | | **46** |

---

## Village GUI Architecture

```
VillageGUIView.vue
├── TaskTickerBar.vue (top - compact)
├── VillageCanvas.vue (2D mode)
├── VillageIsometric.vue (3D mode)
└── TaskDetailPanel.vue (right sidebar)

Composables:
├── useVillage.js (2D Canvas + WebSocket - legacy)
└── useVillageIsometric.js (Three.js isometric)

Backend:
├── services/village_events.py (EventBroadcaster)
└── api/v1/village_ws.py (WebSocket route)
```

### Zone Layout (Isometric 3D)

```
         [Library]          [Bridge Portal]
              \                  /
   [DJ Booth] ─── [VILLAGE SQUARE] ─── [File Shed]
              /         🤖         \
      [Watchtower]  [Memory Garden]  [Workshop]
```

---

## Files Created This Session

**Backend:**
- `app/services/village_events.py` - Event broadcaster
- `app/api/v1/village_ws.py` - WebSocket route

**Frontend:**
- `src/composables/useVillageIsometric.js` - Three.js isometric scene
- `src/components/village/VillageIsometric.vue` - 3D view
- `src/components/village/TaskTickerBar.vue` - Top bar ticker
- `src/components/village/TaskDetailPanel.vue` - Right sidebar
- `src/components/village/VillageCanvas.vue` - Updated 2D view
- `src/views/VillageGUIView.vue` - Integrated dashboard

---

## Phase 5 Polish Status

- [x] Particle effects on tool completion (success=green, error=red)
- [x] Floating labels above zones in 3D (already in place)
- [x] Speech bubbles system (approval/input/error types)
- [x] Click agent to show details popup
- [x] Hover tooltips for agents and zones
- [x] Raycasting click detection

### Future Enhancements
- [ ] Zone info popup on zone click
- [ ] Camera pan/zoom controls
- [ ] Agent path visualization during movement

---

## Next Session: Open-Source LLM Providers (Dev Mode)

**Plan Ready:** `.claude/plans/rippling-whistling-chipmunk.md`

Add multi-provider LLM support hidden in dev mode:
- DeepSeek, Groq, Together AI, Qwen (all OpenAI-compatible)
- Provider dropdown in sidebar (dev mode only)
- Models refresh per provider

**Key Files:**
- CREATE: `backend/app/services/llm_provider.py`
- MODIFY: `backend/app/api/v1/chat.py` (add /providers endpoint)
- MODIFY: `frontend/src/stores/chat.js` (provider state)
- MODIFY: `frontend/src/views/ChatView.vue` (provider selector)

**Knowledge base:** `claude-root/knowledge-base/open-source-llms/` (6 API docs)

---

## Quick Verification

```bash
# Backend health
curl https://backend-production-507c.up.railway.app/health | jq '{build, features: .features[-4:]}'

# WebSocket status
curl https://backend-production-507c.up.railway.app/ws/village/status

# Frontend
open https://frontend-production-5402.up.railway.app/village-gui
```

---

## Railway Services

| Service | Domain |
|---------|--------|
| Backend | backend-production-507c.up.railway.app |
| Frontend | frontend-production-5402.up.railway.app |

**Token:** `90fb849e-af7b-4ea5-8474-d57d8802a368`

---

## Related Projects

- **buckster123/NeoCortex** - Standalone memory system (GitHub)
- **ApexAurum-Village/** - Original Village GUI specs (local)
- **neo-cortex/** - Unified memory with pgvector backend

---

## Key Commits This Session

```
85ae6b0 Add WebGL error handling with auto-fallback to 2D
b4fb4ed Fix 3D rendering + agent max_tokens errors
6c808db Village Phase 5: Particles + Click Selection
4e60e5b Village Isometric 3D + Task Tickers
2f97418 Village Phase 1: Canvas-Based GUI Visualization
8af71ea Village Phase 0: WebSocket Infrastructure
```

---

*"The Village awakens in isometric splendor. Agents walk between buildings. Tasks flow like a living dashboard."*
