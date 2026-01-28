# ApexAurum-Cloud Handover Document

**Date:** 2026-01-28
**Build:** v60-auto-deliberation
**Status:** PRODUCTION READY - Auto-deliberation engine (100+ rounds)!

---

## Current State

ApexAurum Cloud is fully functional and polished:
- Auth system working correctly
- Chat with all agents operational
- Billing/Stripe integration live
- Tier-based feature visibility working
- Message counting across ALL features (chat, spawn, council)
- Graceful error handling throughout
- Neural page with WebGL fallback (3D fix deployed!)
- Local embeddings via FastEmbed (no external API needed)
- **Council deliberation COMPLETE** - Auto-deliberation engine (100+ rounds!)
- **Human butt-in** - Inject messages mid-deliberation
- **Pause/Resume/Stop** - Full control over auto-mode

**Pricing:** Seeker $3 | Alchemist $10 | Adept $30

---

## Session 2 Accomplishments

### 1. Message Counter - COMPLETE
- Streaming chat now records usage via `llm_provider.py` usage events
- Spawn agents record billing after execution
- Socratic councils aggregate all member usage
- All endpoints use Haiku 4.5 model

### 2. Tier-Based Features - COMPLETE
- Models endpoint filters by user's subscription tier
- BYOK hidden from Seeker (only Alchemist+)
- Dev Mode restricted to Adept only
- Visible "Enable Dev Mode" button for Adept users
- Easter eggs show friendly "requires Adept" message

### 3. Error Handling - COMPLETE
- Chat shows friendly 402/403 messages with upgrade suggestions
- Cortex endpoints return empty data gracefully (no 500s)
- Neural page detects WebGL and falls back to list view

### 4. Neural WebGL Fallback - COMPLETE
- `isWebGLAvailable()` utility added to useThreeScene.js
- Store checks WebGL on init, defaults to list if unavailable
- NeuralView only mounts 3D component when WebGL supported
- Shows "3D mode unavailable (no GPU)" notice on fallback
- No more console crashes on devices without GPU

### 5. Village WebSocket - COMPLETE
- URL now builds correctly with https:// prefix
- Connection working: `wss://backend-production-507c.up.railway.app/ws/village`

---

## Session 3 Accomplishments

### 1. Auth Error Polish - COMPLETE
- Login/Register now show friendly error messages
- Session expired → "Your session has expired. Please sign in again."
- Invalid credentials → "Invalid email or password. Please try again."
- Network errors, rate limits, server errors all have clear explanations

### 2. Village GUI → Chat - COMPLETE
- Click agent avatar in Village GUI → navigates to Chat with that agent selected
- Works in both 2D canvas and 3D isometric views
- Agent click detection added to VillageCanvas (checks agents before zones)
- ChatView reads `?agent=ID` query param and selects that agent
- URL cleaned up after selection (removes query param)

### 3. pgvector Setup - COMPLETE
- Added pgvector-enabled PostgreSQL 17 on Railway
- Neural system fully operational
- Diagnostic endpoint: `/api/v1/cortex/diagnostic`
- Setup endpoint: `/api/v1/cortex/setup`
- All Neo-Cortex columns ready for memory visualization

### 4. Neural Memory Storage - COMPLETE
- New `NeuralMemoryService` stores chat messages as vectors
- User messages → sensory layer, assistant → working layer
- Works without OpenAI key (stores without embeddings)
- Chat with agents now populates Neural visualization
- Confirmed: memories being created (1+ vectors in DB)

---

## Session 4 Accomplishments

### 1. Neural 3D View Bug Fix - COMPLETE
- Fixed Vue 3 Proxy conflict with Three.js `modelViewMatrix`
- Changed `ref()` to `shallowRef()` for Three.js objects in `useThreeScene.js`
- Scene, camera, renderer, controls now use shallow reactivity
- Neural 3D visualization works on WebGL-capable PCs now

### 2. Local Embeddings - COMPLETE
- Added FastEmbed library for private, local embeddings (no external API needed)
- Default model: `BAAI/bge-small-en-v1.5` (384 dimensions)
- Config: `EMBEDDING_PROVIDER=local` (now default)
- Updated database to handle configurable vector dimensions
- Diagnostic endpoint shows embedding config and DB dimension status
- Auto-migration handles dimension changes (drops old embeddings if dimension changes)
- **Product vision:** Private memory instances for users' AI systems

### 3. Council Deliberation MVP - COMPLETE
- **Multi-agent group chat from OG ApexAurum brought to Cloud!**
- New models: `DeliberationSession`, `SessionAgent`, `DeliberationRound`, `SessionMessage`
- REST API endpoints for sessions and round execution
- Parallel agent execution using `asyncio.gather`
- Round-based context building (agents see previous discussion)
- Per-agent token tracking and billing integration
- Endpoints:
  - `POST /api/v1/council/sessions` - Create session
  - `GET /api/v1/council/sessions` - List sessions
  - `GET /api/v1/council/sessions/{id}` - Get details with all rounds
  - `POST /api/v1/council/sessions/{id}/round` - Execute deliberation round
  - `DELETE /api/v1/council/sessions/{id}` - Delete session

---

## Session 5 Accomplishments

### 1. Council Frontend UI - COMPLETE
- **`CouncilView.vue`** - Full deliberation interface
  - Session list sidebar with state badges
  - Topic input with agent selection grid
  - Round-based message display
  - Progress bar and cost tracking
  - Agent roster with token counts
- **`council.js`** Pinia store - Full state management
  - Session CRUD operations
  - Round execution
  - Form state for new sessions
  - Computed getters for progress, rounds, etc.
- **`AgentCard.vue`** component
  - Color-coded agent avatars
  - Token count display
  - Markdown-like content formatting
- **Router:** `/council` and `/council/:id` routes
- **Navbar:** Council link in desktop and mobile menus
- **Deployed and working!** Navigate to `/council` to test

---

## Session 6 Accomplishments

### 1. Auto-Deliberation Engine - COMPLETE
- **Run 100+ rounds continuously** without user clicks
- **SSE streaming endpoint** - Real-time round-by-round events
- **Backend endpoints:**
  - `POST /sessions/{id}/auto-deliberate?num_rounds=N` - Stream N rounds
  - `POST /sessions/{id}/butt-in` - Inject human message
  - `POST /sessions/{id}/pause` - Pause auto-mode
  - `POST /sessions/{id}/resume` - Resume from paused
  - `POST /sessions/{id}/stop` - Stop and complete
- **Database:** Added `pending_human_message` field for butt-in queue

### 2. Human Butt-In - COMPLETE
- Textarea to inject thoughts mid-deliberation
- Message queued and included in next round's context
- All agents see `[HUMAN]: message` in their context
- Displayed in round history with amber highlight

### 3. Frontend Auto-Mode UI - COMPLETE
- **Start/Pause/Resume/Stop** control buttons
- **Rounds-to-run input** (1-200 rounds)
- **Real-time streaming display** - Watch agents respond live
- **Placeholder cards** for agents still processing
- **Sticky status bar** during auto-deliberation
- **Paused state** with amber badge

### 4. Enhanced Max Rounds - COMPLETE
- Session creation now supports up to 200 rounds
- Slider updated with 1/100/200 markers
- Adept-tier ready for deep deliberation

---

## Latest Commit
```
e1e3bb8 Add auto-deliberation engine (100+ rounds)
```

**Railway Token:** Working - deploys via API are functioning.

---

## Quick Commands

```bash
# Health check
curl https://backend-production-507c.up.railway.app/health

# Deploy (if token is refreshed)
COMMIT=$(git log --oneline -1 | cut -d' ' -f1)
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer <NEW_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { backend: serviceInstanceDeploy(serviceId: \\\"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") frontend: serviceInstanceDeploy(serviceId: \\\"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"
```

---

## Railway IDs
- **Backend Service:** `9d60ca55-a937-4b17-8ec4-3fb34ac3d47e`
- **Frontend Service:** `6cf1f965-94df-4ea0-96ca-d82959e2d3c5`
- **Environment:** `2e9882b4-9b33-4233-9376-5b5342739e74`
- **Token:** Working (confirmed in Session 3)

---

## URLs
- Frontend: https://frontend-production-5402.up.railway.app
- Backend: https://backend-production-507c.up.railway.app

---

## Subscription Tiers

| Tier | ID | Price | Messages | Models | BYOK | Dev Mode |
|------|----|-------|----------|--------|------|----------|
| Seeker | free | $3/mo | 50 | Haiku | No | No |
| Alchemist | pro | $10/mo | 1000 | Haiku, Sonnet | Yes | No |
| Adept | opus | $30/mo | Unlimited | All + Opus | Yes | Yes |

---

## Remaining Tasks (Future Sessions)

### Priority 1: Council Advanced Features
- ~~Human "butt-in" capability mid-deliberation~~ DONE
- ~~Auto-deliberation mode (N rounds without user input)~~ DONE
- Add/remove agents mid-session
- Convergence detection (auto-stop on consensus)
- Village memory integration
- WebSocket streaming (per-token, not per-agent)

### Priority 2: Nice-to-Have
- Suno/Music API integration (ties into Village)
- Coupon/admin freebies system
- Admin dashboard for user management

---

## Test Accounts
- **Note:** Database was wiped during clean deploy - recreate test accounts
- Previous accounts: buckster123 (Seeker), buckmazzta@gmail.com (Alchemist)

---

## Key Files Modified (Session 2)

| File | Changes |
|------|---------|
| `backend/app/api/v1/chat.py` | Tier-filtered models, streaming billing |
| `backend/app/api/v1/agents.py` | Billing for spawn/council |
| `backend/app/api/v1/cortex.py` | Graceful table-missing handling |
| `backend/app/services/llm_provider.py` | Usage tracking in stream |
| `frontend/src/stores/chat.js` | Friendly error messages |
| `frontend/src/stores/neocortex.js` | WebGL check, fallback mode |
| `frontend/src/views/SettingsView.vue` | BYOK visibility, dev mode button |
| `frontend/src/views/NeuralView.vue` | Conditional 3D mount, fallback notice |
| `frontend/src/composables/useDevMode.js` | Tier check before activation |
| `frontend/src/composables/useThreeScene.js` | WebGL detection, try/catch |
| `frontend/src/composables/useVillage.js` | WebSocket URL fix |
| `frontend/src/views/VillageGUIView.vue` | WebSocket URL fix |

## Key Files Modified (Session 4)

| File | Changes |
|------|---------|
| `frontend/src/composables/useThreeScene.js` | Changed `ref()` to `shallowRef()` for Three.js objects |
| `backend/app/main.py` | Updated version to v58, added council-deliberation feature |
| `backend/app/services/embedding.py` | Added FastEmbed local embedding support |
| `backend/app/config.py` | Changed default to local embeddings (384 dims) |
| `backend/app/database.py` | Dynamic vector dimensions, auto-migration |
| `backend/app/api/v1/cortex.py` | Enhanced diagnostic with embedding config info |
| `backend/requirements.txt` | Added fastembed dependency |
| `backend/app/models/council.py` | **NEW** - Council data models |
| `backend/app/api/v1/council.py` | **NEW** - Council REST endpoints |
| `backend/app/models/user.py` | Added deliberation_sessions relationship |
| `backend/app/models/__init__.py` | Import council models |
| `backend/app/api/v1/__init__.py` | Include council router |

## Key Files Modified (Session 5)

| File | Changes |
|------|---------|
| `frontend/src/stores/council.js` | **NEW** - Pinia store for council state |
| `frontend/src/views/CouncilView.vue` | **NEW** - Main deliberation interface |
| `frontend/src/components/council/AgentCard.vue` | **NEW** - Agent response card component |
| `frontend/src/router/index.js` | Added `/council` and `/council/:id` routes |
| `frontend/src/components/Navbar.vue` | Added Council link (desktop + mobile) |

## Key Files Modified (Session 6)

| File | Changes |
|------|---------|
| `backend/app/api/v1/council.py` | Auto-deliberate SSE endpoint, butt-in/pause/resume/stop endpoints |
| `backend/app/models/council.py` | Added `pending_human_message` field |
| `frontend/src/stores/council.js` | Auto-mode state, SSE handling, control actions |
| `frontend/src/views/CouncilView.vue` | Auto-mode UI, butt-in input, streaming display |

## Key Files Modified (Session 3)

| File | Changes |
|------|---------|
| `frontend/src/views/LoginView.vue` | Friendly auth error messages |
| `frontend/src/views/RegisterView.vue` | Friendly registration error messages |
| `frontend/src/services/api.js` | Better session error message |
| `frontend/src/components/village/VillageCanvas.vue` | Agent click detection |
| `frontend/src/views/VillageGUIView.vue` | Agent click → navigate to chat |
| `frontend/src/views/ChatView.vue` | Read agent from query param |

---

## Easter Eggs

- **Dev Mode:** Konami code (↑↑↓↓←→←→BA) or 7-tap on Au logo (Adept only!)
- **PAC Mode:** Type "AZOTH" while in Dev Mode
- **PAC prompts:** `backend/native_prompts/*-PAC.txt`

---

*"The Council convenes. The Athanor blazes. The gold multiplies."*
