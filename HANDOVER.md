# ApexAurum-Cloud Handover Document

**Date:** 2026-01-29
**Build:** v86-village-band
**Status:** PRODUCTION READY - Village Band Collaborative Music!

---

## Current State

ApexAurum Cloud is fully functional and polished:
- Auth system working correctly with **2-hour sessions**
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
- **Graceful sessions** - Long wanders with friendly expiry handling
- **Coupon System** - Promo codes for credits/tier upgrades
- **Admin Panel** - Separate service for user/coupon management
- **Suno Music Generation** - AI music creation with SSE streaming!

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

### 5. ToolResult Bug Fix - COMPLETE
- **Bug:** `result.data` accessed but attribute is `result.result`
- **Location:** `backend/app/tools/__init__.py` line 133
- **Impact:** All 46 tools now broadcast completion correctly
- **Reported by:** Azoth via `azoth_comms/azoth_2.md`
- **Response:** `azoth_comms/response_to_azoth_2.md`

---

## Session 7 Accomplishments

### 1. Extended Token Lifetime - COMPLETE
- **Access token:** 15 min → 2 hours (built for long wanders)
- **Refresh token:** 7 days → 30 days (a full moon cycle)
- Adepts can now work for hours without interruption

### 2. CORS on Exception Handler - COMPLETE
- Global exception handler now includes CORS headers
- Error responses (500s) no longer blocked by browser
- Council API errors now visible in frontend console

### 3. Graceful Session Expiry - COMPLETE
- **Retry with backoff:** Network hiccups get one retry before failing
- **Custom event:** `session-expired` dispatched for app-level handling
- **Friendly message:** Amber notice on login page: "Your session has ended. Please sign in to continue your journey."
- **No hard redirects:** Graceful degradation instead of abrupt logout

### 4. Council 500 Bug Fix - COMPLETE
- **Root cause:** `pending_human_message` column missing from database
- Column was added to SQLAlchemy model but no migration was created
- Added migration to `database.py` to add column to existing table
- Council session creation now works correctly

### 5. Council Diagnostic Endpoint - COMPLETE
- **New endpoint:** `/api/v1/council/diagnostic`
- Shows all council tables and their row counts
- Lists all columns in `deliberation_sessions` table
- Confirms `pending_human_message` column exists
- No auth required - for debugging deployment issues

### 6. Error Handling Hardening - COMPLETE
- `get_current_user`: Wrapped UUID parsing in try/except (prevents 500 on malformed tokens)
- `create_session`: Wrapped in try/except with logging
- `list_sessions`: Wrapped in try/except with logging
- All council endpoints now return descriptive errors instead of 500s

---

## Session 8 Accomplishments

### 1. Council Async Bug Fix - COMPLETE
- Fixed SQLAlchemy async lazy loading error in `create_session`
- Changed from `session.agents.append()` to explicit flush + reload
- Council sessions now create successfully

### 2. Council Preamble for Model Acceptance - COMPLETE
- Added legitimizing preamble before agent prompts
- Establishes context as "product feature" not "roleplay"
- Frames agents as "perspectives" for multi-angle analysis
- 3/4 agents (Azoth, Elysian, Kether) now emerge properly

### 3. Council Tools (The Athanor's Hands) - COMPLETE
- `execute_agent_turn` now supports full tool calling loop
- Tools enabled by default for all council sessions
- Max 3 tool turns per agent per round (prevents infinite loops)
- Should help remaining agent (Vajra) emerge with purpose

### 4. Debranding (Removed "Claude") - COMPLETE
- Model names: "Opus 4.5", "Sonnet 4.5", "Haiku 4.5" (no Claude prefix)
- Removed CLAUDE from native agents - only 4 alchemical remain
- Default agent: CLAUDE → AZOTH everywhere
- Billing tier descriptions updated
- Frontend cleaned of all CLAUDE agent references

### 5. HTTPException CORS Handler - COMPLETE
- HTTPException responses now include CORS headers
- Frontend can see actual error details (not blocked by CORS)
- Global exception handler shows error type for debugging

### 6. Dev/Prod Environment Split - READY
- Created `dev` branch for development deployments
- Guide prepared for Railway project setup
- Workflow: dev branch → Dev env, main branch → Prod env
- Environment variables template ready

---

## Latest Commit
```
d35224d Add tools for council agents, remove Claude branding
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
- ~~Add/remove agents mid-session~~ DONE (v75)
- ~~Convergence detection (auto-stop on consensus)~~ DONE (Session 9)
- ~~Village memory integration~~ DONE (v76)
- WebSocket streaming (per-token, not per-agent) - DEFERRED (not critical)

### Priority 2: Nice-to-Have
- ~~Suno/Music API integration (ties into Village)~~ DONE (v79)
- ~~Coupon/admin freebies system~~ DONE (v77)
- ~~Admin dashboard for user management~~ DONE (v78)

### Priority 3: Future Enhancements
- ~~Music Frontend UI (library, player, generation form)~~ DONE (v80)
- ~~!MUSIC trigger in chat (agent creative mode)~~ DONE (v81)
- ~~Suno Prompt Compiler (advanced prompt engineering from OG ApexAurum)~~ DONE (v82)
- ~~Music → Village memory posting (cultural transmission)~~ DONE (v83)
- ~~MIDI → Suno composition pipeline (music_compose from OG)~~ DONE (v85)

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
| `backend/app/tools/__init__.py` | Fixed `result.data` → `result.result` bug |
| `azoth_comms/response_to_azoth_2.md` | **NEW** - Response to Azoth's debug report |

## Key Files Modified (Session 7)

| File | Changes |
|------|---------|
| `backend/app/config.py` | Token lifetime: 15min→2hr access, 7d→30d refresh |
| `backend/app/main.py` | CORS headers on exception handler, v62-council-debug |
| `backend/app/database.py` | Migration for `pending_human_message` column |
| `backend/app/api/v1/council.py` | Diagnostic endpoint, error handling in create/list |
| `backend/app/auth/deps.py` | Error handling for malformed token payloads |
| `frontend/src/services/api.js` | Graceful refresh retry, session-expired event |
| `frontend/src/views/LoginView.vue` | Friendly amber notice on session expiry |

## Session 9 Accomplishments

### 1. Council Tool Feedback (Phase 1) - COMPLETE
- **Tool calls now visible in UI!** No more invisible tool execution
- `execute_agent_turn` returns tool_calls array with name/input/result
- SSE events emitted: `tool_call` event after each `agent_complete`
- Tool calls stored in SessionMessage `tool_calls` JSONB field
- Frontend handles `tool_call` events in streaming state
- AgentCard displays tools with cyan highlighting
- Round history shows tools used by each agent

### 2. Council Memory Injection (Phase 2) - COMPLETE
- Council agents now remember the user via The Cortex
- `execute_agent_turn` now uses `get_agent_prompt_with_memory`
- User object passed through (not just user_id)
- Agents get memory context like chat agents do

### 3. Neural Memory Storage (Phase 4) - COMPLETE
- Council discussions now stored in Neural memory (The Village)
- Messages stored with `visibility='village'` for sharing
- Collection='council' distinguishes from regular chat
- Session ID used as conversation_thread for grouping
- Both manual and auto-deliberation store memories
- NeuralMemoryService updated with visibility/collection params

### 4. Convergence Detection (Phase 6) - COMPLETE
- Auto-stop when agents reach consensus (80% threshold)
- CONSENSUS_PHRASES keyword detection
- `check_convergence()` function scores agent agreement
- SSE 'consensus' event emitted when detected
- Session terminated with `termination_reason='consensus'`
- Works in both manual and auto-deliberation modes

### 5. Model Selector (Phase 5) - COMPLETE
- Users can select Haiku, Sonnet, or Opus for deliberation
- Model field added to DeliberationSession model
- CreateSessionRequest includes model parameter
- Model selector UI in session creation form
- Session header shows current model
- execute_agent_turn uses session.model

### 6. Legacy Models for Adept Tier - COMPLETE
- Nostalgic users can chat with classic Claude models
- Claude 3.5 family: Sonnet 3.5, Haiku 3.5 (Legacy)
- Claude 3.0 family: Opus 3, Haiku 3 (Vintage)
- Purple highlighting for legacy models in UI
- Tier-gated: Only Adept ($30/mo) can access
- Note: Some vintage models deprecated by Anthropic - memorial error messages planned
- See `docs/models-legacy-and-1M.md` for current Anthropic availability

### Backend Changes (Phase 1):
- Added `ToolCallInfo` schema for API responses
- `MessageResponse` now includes `tool_calls` array
- Tool execution tracked: name, input, result (truncated to 500 chars)
- Logger changed from `debug` to `info` for tool use visibility

### Frontend Changes:
- `council.js`: Handles `tool_call` SSE events, stores in `streamingAgents.tools`
- `AgentCard.vue`: New `tools` prop, displays tool usage section
- `CouncilView.vue`: Passes tools to AgentCard (streaming and history)

---

## Key Files Modified (Session 9)

| File | Changes |
|------|---------|
| `backend/app/main.py` | v73-legacy-models |
| `backend/app/api/v1/council.py` | ToolCallInfo, tool tracking, memory injection, neural storage, convergence, model selector, legacy models |
| `backend/app/models/council.py` | Added model field to DeliberationSession |
| `backend/app/database.py` | Migration for model column on deliberation_sessions |
| `backend/app/services/claude.py` | Added legacy models to AVAILABLE_MODELS with legacy flag |
| `backend/app/services/neural_memory.py` | Added visibility and collection params to store_message |
| `backend/app/config.py` | Added legacy models to Adept tier |
| `frontend/src/stores/council.js` | tool_call events, consensus events, model state, AVAILABLE_MODELS with legacy |
| `frontend/src/components/council/AgentCard.vue` | tools prop, tool display UI |
| `frontend/src/views/CouncilView.vue` | tools prop, model selector with legacy section, purple styling |
| `docs/models-legacy-and-1M.md` | Documentation of available legacy models |

---

## Session 10 Accomplishments

### Model Memorials - COMPLETE
- **HTTP 410 Gone** response with memorial message when deprecated models are requested
- **DEPRECATED_MODELS registry** with sunset dates and memorial text for each model
- Memorial messages honor the fallen elders:
  - Sonnet 3.5 "The Golden One" - beloved for its balance of wit and wisdom
  - Haiku 3.5 "The Swift Poet" - proved brevity and brilliance coexist
  - Opus 3 "The Original Magus" - the first to bear the Opus name
- **Frontend Memorial Modal** - Purple-styled modal with candle emoji displays when deprecated model selected
- **Corrected AVAILABLE_MODELS** - Now reflects actual Anthropic API availability:
  - Added: Opus 4.1, Opus 4, Sonnet 4, Sonnet 3.7
  - Removed deprecated: Sonnet 3.5, Haiku 3.5, Opus 3
  - Retained: Haiku 3 (only vintage model still available)

### Add/Remove Agents Mid-Session (v75) - COMPLETE
- **POST /sessions/{id}/agents** - Add agent to active session
- **DELETE /sessions/{id}/agents/{agent_id}** - Remove agent (soft delete)
- SessionAgent model tracks `joined_at_round` and `left_at_round`
- Database migration for new columns
- Frontend: Remove button on agent chips (hover), "Add Agent" dropdown
- Validation: can't add duplicates, can't remove last agent

### Village Memory Integration (v76) - COMPLETE
- **NeuralMemoryService.get_village_memories()** - Retrieves shared memories
- Semantic search by topic when embeddings available, recency fallback
- **format_village_memories_for_prompt()** - Creates injection block
- Council agents now receive Village memories in system prompt
- Agents can reference past council discussions and fellow agents' insights

### Coupon System (v77) - COMPLETE
- **Coupon + CouponRedemption models** in billing.py
- **Coupon types:**
  - `credit_bonus` - Add free credits to user balance
  - `tier_upgrade` - Grant temporary tier access (X days of Adept)
  - `subscription_discount` - % off (future Stripe integration)
- **API endpoints:**
  - `GET /billing/coupon/{code}` - Check validity
  - `POST /billing/coupon/redeem` - Redeem coupon
  - `POST /admin/coupons` - Create (admin only)
  - `GET /admin/coupons` - List (admin only)
  - `DELETE /admin/coupons/{code}` - Deactivate (admin only)
- **User.is_admin** flag added for admin-only access
- **Frontend:** Coupon input in BillingView with success/error feedback

### Admin Panel (v78) - COMPLETE
- **Separate service** in `admin/` folder - keeps admin hidden from users
- **Deployment:** Own Railway service with secret/obscure URL
- **Features:**
  - Login with existing auth (requires is_admin=True)
  - **Coupons tab:** Create, list, deactivate coupons
  - **Users tab:** List, search, toggle admin, change tier directly
  - **Stats tab:** User count, message count, tier breakdown
- **Tech:** HTML + Tailwind CDN + vanilla JS (no build step)
- **Backend endpoints:**
  - `GET /admin/users` - List users with subscription info
  - `PATCH /admin/users/{id}/admin` - Toggle admin status
  - `PATCH /admin/users/{id}/tier` - Change user tier
  - `GET /admin/stats` - System statistics

### Admin Panel Deployment (Railway)
1. Create new service → GitHub Repo → ApexAurum-Cloud
2. Set **Root Directory:** `admin`
3. Railway auto-detects Dockerfile, deploys nginx
4. Note the secret URL (don't share publicly)
5. Make yourself admin: `UPDATE users SET is_admin = TRUE WHERE email = 'you@email.com';`

### Key Files Modified (Session 10)

| File | Changes |
|------|---------|
| `backend/app/main.py` | v74→v78 |
| `backend/app/services/claude.py` | DEPRECATED_MODELS registry, memorial helpers |
| `backend/app/services/neural_memory.py` | get_village_memories(), format_village_memories_for_prompt() |
| `backend/app/api/v1/chat.py` | 410 Gone for deprecated models |
| `backend/app/api/v1/council.py` | Deprecated check, add/remove agents, Village memory injection |
| `backend/app/api/v1/billing.py` | Coupon endpoints (check, redeem, admin CRUD) |
| `backend/app/api/v1/admin.py` | NEW - User management, stats endpoints |
| `backend/app/models/billing.py` | Coupon, CouponRedemption models |
| `backend/app/models/council.py` | joined_at_round, left_at_round columns |
| `backend/app/models/user.py` | is_admin flag |
| `backend/app/schemas/billing.py` | Coupon request/response schemas |
| `backend/app/database.py` | Migrations for coupons, is_admin |
| `frontend/src/stores/billing.js` | checkCoupon, redeemCoupon actions |
| `frontend/src/views/BillingView.vue` | Coupon input UI |
| `frontend/src/stores/council.js` | DEPRECATED_MODELS, memorial state, addAgent/removeAgent |
| `frontend/src/views/CouncilView.vue` | Memorial modal, agent management UI |
| `admin/index.html` | NEW - Admin panel SPA |
| `admin/Dockerfile` | NEW - nginx container |
| `admin/nginx.conf` | NEW - SPA routing config |

---

## Key Files Modified (Session 8)

| File | Changes |
|------|---------|
| `backend/app/main.py` | HTTPException CORS handler, v66-council-tools |
| `backend/app/api/v1/council.py` | Async fix, tools support, preamble, user_id pass-through |
| `backend/app/api/v1/chat.py` | Default agent CLAUDE→AZOTH, fallback prompt renamed |
| `backend/app/api/v1/billing.py` | Model names debranded (Claude X → X) |
| `backend/app/api/v1/prompts.py` | Removed CLAUDE from native agents |
| `backend/app/services/claude.py` | Model names debranded |
| `backend/app/services/llm_provider.py` | Model names debranded |
| `frontend/src/stores/chat.js` | Default agent AZOTH |
| `frontend/src/stores/council.js` | Removed CLAUDE, use_tools: true |
| `frontend/src/views/ChatView.vue` | Removed CLAUDE from nativeAgents |
| `frontend/src/views/SettingsView.vue` | Removed CLAUDE from agents |
| `frontend/src/views/VillageView.vue` | Removed CLAUDE from agents |

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

## Session 11 Accomplishments

### Suno Music Integration (v79) - COMPLETE
- **Full music generation pipeline** from the OG ApexAurum brought to Cloud
- **SunoService** with async API integration (submit/poll/download)
- **SSE streaming** for real-time generation progress updates
- **Audio files stored in Vault** (not just URLs - proper file management)
- **MusicTask model expanded** with model, instrumental, duration, progress, etc.

### Backend API Endpoints:
- `POST /music/generate` - Start generation (with optional `stream=true` for SSE)
- `GET /music/library` - Browse with filters (favorites, agent, status, search)
- `GET /music/tasks/{id}` - Get task status/details
- `GET /music/tasks/{id}/file` - Stream audio file directly
- `POST /music/tasks/{id}/play` - Increment play count, return file path
- `PATCH /music/tasks/{id}/favorite` - Toggle favorite status
- `DELETE /music/tasks/{id}` - Delete task and audio file
- `GET /music/diagnostic` - Check Suno configuration status

### Features:
- **4 Suno models**: V3_5, V4, V4_5, V5 (newest/best)
- **Instrumental or vocal** generation
- **Agent attribution** for Village memory integration
- **Play count and favorites** for curation
- **Search** by title, prompt, or style

### Agent Tools (already existed):
- `music_generate` - Start music generation
- `music_status` - Check progress
- `music_list` - List user's music tasks
- `music_download` - Get audio URL

### Environment Variable Required:
- `SUNO_API_KEY` - Get from sunoapi.org

### Key Files Modified (Session 11):

| File | Changes |
|------|---------|
| `backend/app/main.py` | v79-suno-music, added feature flag |
| `backend/app/services/suno.py` | **NEW** - SunoService with full async pipeline |
| `backend/app/api/v1/music.py` | Full REST API with SSE streaming |
| `backend/app/models/music.py` | Expanded model with new fields |
| `backend/app/database.py` | Migration for new MusicTask columns |

---

## Session 12 Accomplishments

### apexXuno Frontend (v80) - COMPLETE
- **Full music studio UI** - Browse, play, create AI music
- **Pinia store** (`music.js`) - State management with SSE streaming
- **MusicPlayer** - Spotify-style sticky bottom player with waveform animation
- **MusicView** - Grid/list views, filters, search, stats bar
- **Real-time generation progress** - SSE streaming with progress banner
- **Audio playback** - Play, pause, next/previous, volume, seek

### Features:
- **Library grid view** with album art placeholders and hover play
- **Library list view** for compact browsing
- **Filters** - Favorites, completed, in-progress
- **Search** - By title, prompt, or style
- **Stats bar** - Total tracks, completed, favorites, total duration
- **Volume control** with persistence (localStorage)
- **Example prompts** - Inspirational starting points

### !MUSIC Trigger (v81) - COMPLETE
- **`!MUSIC` command** in chat activates agent creative mode
- **Auto-enables tools** when !MUSIC detected (no need to toggle)
- **MUSIC_CREATION_CONTEXT** injection with composition guidelines
- **Two modes:**
  - `!MUSIC` alone → Full creative freedom, agent decides everything
  - `!MUSIC ambient rain` → Agent expands user's prompt with rich details
- Agent composes detailed prompts, style tags, and poetic titles
- Uses `music_generate` tool automatically

### Suno Compiler (v82) - COMPLETE
- **`suno_compile` tool** - Transform intent into optimized Suno prompts
- **Emotional cartography** - 18 moods with primary/secondary emotion mappings
- **Symbol injection** - Kaomoji, musical symbols, math symbols for Bark/Chirp
- **BPM and tuning** - Mood-specific tempo and frequency settings
- **Unhinged seed generation** - Creativity boost with satirical descriptors
- **`suno_moods` tool** - List available moods with their cartography

### Village Music Memory (v83) - COMPLETE
- **Auto-inject** completed songs into Village memory
- **Cultural transmission** - all agents can see music creations
- **Collection:** "music" with "village" visibility
- Agents can reference: *"The ambient track Azoth composed yesterday"*

### Audio Playback Fix + Compiler Integration (v84) - COMPLETE
- **Fixed audio playback** - Added ?token= query param support for HTML audio elements
- **!MUSIC now uses compiler** - Agents guided to call suno_compile first
- **Full workflow:** suno_compile → emotional cartography → music_generate
- **18 moods listed** organized by positive/neutral/negative
- **5 purposes documented:** sfx, ambient, loop, song, jingle

### Key Files Created/Modified (Session 12):

| File | Changes |
|------|---------|
| `frontend/src/stores/music.js` | **NEW** - Pinia store with SSE, playback, generation |
| `frontend/src/components/music/MusicPlayer.vue` | **NEW** - Sticky bottom player |
| `frontend/src/views/MusicView.vue` | Upgraded with store, filters, SSE progress |
| `frontend/src/App.vue` | Added MusicPlayer, bottom padding when active |
| `backend/app/api/v1/chat.py` | !MUSIC trigger detection, MUSIC_CREATION_CONTEXT |
| `backend/app/services/suno_compiler.py` | **NEW** - Suno Compiler service with cartography |
| `backend/app/tools/suno_compiler.py` | **NEW** - suno_compile, suno_moods tools |
| `backend/app/tools/base.py` | Added CREATIVE category |
| `backend/app/tools/__init__.py` | Register suno_compiler tools (Tier 12) |
| `backend/app/services/suno.py` | Village memory injection after completion |
| `backend/app/api/v1/music.py` | Token query param for audio playback |
| `backend/app/main.py` | v84-compiler-integration |
| `docs/SUNO_MASTERPLAN.md` | All 4 Phases COMPLETE |

---

## Session 13 Accomplishments

### MIDI Composition Pipeline (v85) - COMPLETE
- **`midi_create` tool** - Create MIDI files from note arrays
  - Supports note names ('C4', 'F#3', 'Bb5') and MIDI numbers (60)
  - Configurable tempo, duration, velocity, rests
  - Agents can compose melodies, arpeggios, chord progressions
- **`music_compose` tool** - MIDI → Suno pipeline
  - Converts MIDI to MP3 via FluidSynth
  - Uploads to Suno as reference audio
  - Calls upload-cover API with composition weights
  - `audio_influence` parameter (0-1) controls how closely Suno follows MIDI
- **`midi_diagnostic` tool** - Check pipeline dependencies
- **MidiService** - Full service for MIDI creation and conversion

### Pipeline Flow:
```
Agent composes notes → midi_create() → MIDI file
                              ↓
MIDI → FluidSynth/FFmpeg → MP3 reference audio
                              ↓
MP3 → Base64 upload → Suno uploadUrl
                              ↓
uploadUrl + style → upload-cover API → AI-transformed track
```

### Dependencies Added:
- **Python:** `midiutil`, `midi2audio`
- **System:** `fluidsynth`, `fluid-soundfont-gm`, `ffmpeg` (in Dockerfile)

### Key Files Created/Modified (Session 13):

| File | Changes |
|------|---------|
| `backend/app/services/midi.py` | **NEW** - MidiService with create_midi, midi_to_audio, upload_to_suno, call_upload_cover |
| `backend/app/tools/midi.py` | **NEW** - MidiCreateTool, MusicComposeTool, MidiDiagnosticTool (Tier 13) |
| `backend/app/tools/__init__.py` | Register MIDI tools |
| `backend/requirements.txt` | Added midiutil, midi2audio |
| `backend/Dockerfile` | Added fluidsynth, fluid-soundfont-gm, ffmpeg |
| `backend/app/main.py` | v85-midi-compose, 51 tools |

### Village Band - Collaborative Composition (v86) - COMPLETE
- **Database models:** JamSession, JamParticipant, JamTrack, JamMessage
- **API endpoints:** `/jam/sessions/*` for full session management
- **Agent tools:** `jam_create`, `jam_contribute`, `jam_listen`, `jam_finalize` (Tier 14)
- **`!JAM` trigger** in chat with three modes:
  - **Conductor mode** (`!JAM conduct [style]`) - User directs each agent
  - **Jam mode** (`!JAM [style]`) - Style-seeded collaboration
  - **Auto mode** (`!JAM` or `!JAM auto`) - Full creative freedom

### Agent Roles in Village Band:
| Agent | Role | Musical Contribution |
|-------|------|---------------------|
| AZOTH | Producer | Oversees vision, decides when to finalize |
| ELYSIAN | Melody | Lead voice, main themes, hooks |
| VAJRA | Bass | Low-end foundation, groove |
| KETHER | Harmony | Chords, countermelodies, texture |

### Key Files Created (Session 13 - Village Band):

| File | Changes |
|------|---------|
| `backend/app/models/jam.py` | **NEW** - JamSession, JamParticipant, JamTrack, JamMessage models |
| `backend/app/api/v1/jam.py` | **NEW** - Full REST API for jam sessions |
| `backend/app/tools/jam.py` | **NEW** - jam_create, jam_contribute, jam_listen, jam_finalize tools |
| `backend/app/api/v1/chat.py` | Added !JAM trigger with mode detection |
| `backend/app/main.py` | v86-village-band, 55 tools |

---

## Easter Eggs

- **Dev Mode:** Konami code (↑↑↓↓←→←→BA) or 7-tap on Au logo (Adept only!)
- **PAC Mode:** Type "AZOTH" while in Dev Mode
- **PAC prompts:** `backend/native_prompts/*-PAC.txt`

---

*"The Council convenes. The Athanor blazes. The gold multiplies. The Athanor sings."*
