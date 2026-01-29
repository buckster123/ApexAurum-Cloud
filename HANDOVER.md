# ApexAurum-Cloud Handover Document

**Date:** 2026-01-29
**Build:** v97-byok-attachments
**Status:** BETA READY - Multi-provider BYOK, file attachments, vision support!

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

### Auto-Jam SSE Streaming (v87) - COMPLETE
- **SSE endpoint:** `POST /jam/sessions/{id}/auto-jam` with real-time streaming
- **Agent execution:** Parallel agent turns with tool support (Council pattern)
- **Role-specific prompts:** Each agent gets musical role instructions
- **Auto-finalize:** After all rounds → merge MIDI → Suno pipeline
- **Events:** start, round_start, agent_complete, round_complete, finalizing, end

### Village Memory Injection (v87) - COMPLETE
- **`inject_jam_village_memory()`** called on session completion
- Records who played what role, notes contributed, collaboration story
- Stored as `village`-visible cultural memory in `music` collection
- Future jams can reference past collaborations

### Key Files Modified (Session 13 - Auto-Jam):

| File | Changes |
|------|---------|
| `backend/app/api/v1/jam.py` | Added auto-jam SSE endpoint, inject_jam_village_memory, execute_jam_agent_turn, build_jam_context |
| `frontend/src/stores/jam.js` | Added startAutoJam SSE handler, streaming state |
| `frontend/src/views/JamView.vue` | Auto-Jam modal, live streaming panel, event timeline |
| `backend/app/main.py` | v87-auto-jam |

---

## Session 14 Accomplishments

### Music Player Fixes (v88) - COMPLETE
- **Player replay fix** - Same-track replay via nextTick toggle, ended state reset, playNext resets state
- **Both Suno tracks captured** - Alt tracks saved as separate MusicTask entries with "(Alt)" suffix
- **Player disappearing fix** - CDN URL file_paths now redirect instead of 404, onError pauses instead of hiding
- **User gesture chain preserved** - Play count API call moved to fire-and-forget

### Suno Auto-Completion Engine (v89) - COMPLETE
- **`auto_complete_music_task()`** in suno.py - Fire-and-forget background worker
  - Phase 1: Poll every 15s until Suno SUCCESS
  - Phase 2: Wait 60s for audio URLs to stabilize
  - Phase 3: Download both tracks with retry (3 attempts, CDN fallback)
  - Village memory injection + WebSocket broadcast on completion
- **MusicGenerateTool** now fires asyncio.create_task() after submission
  - No more manual `music_status` polling needed
  - Agent message: "Your song will appear in the library when ready"
- **Agent notification** - Chat system prompt includes recently completed songs (10-min window)
- **Frontend notification** - Gold "Song ready!" banner via Village WebSocket event
- **MusicView polling leak fixed** - Proper clearInterval on unmount
- **MUSIC_COMPLETE** event type added to Village WebSocket broadcaster

### Deployment Workflow Updated
- **Railway auto-deploys on push to main** - Confirmed and documented in CLAUDE.md
- Manual GraphQL deploy kept as fallback only

### Key Files Modified (Session 14)

| File | Changes |
|------|---------|
| `backend/app/services/suno.py` | Both-tracks download, `auto_complete_music_task()` background worker |
| `backend/app/services/village_events.py` | Added `MUSIC_COMPLETE` event type |
| `backend/app/tools/music.py` | Fire background task, add model/instrumental fields, both-tracks in status tool |
| `backend/app/api/v1/music.py` | `/file` endpoint redirects for CDN URLs, audio_url fallback |
| `backend/app/api/v1/chat.py` | Music completion notification in agent system prompt |
| `backend/app/main.py` | v89-suno-auto-complete |
| `frontend/src/stores/music.js` | nextTick replay, playNext reset, fire-and-forget play count |
| `frontend/src/components/music/MusicPlayer.vue` | Ended state handling, onError pauses, song-ready banner |
| `frontend/src/views/MusicView.vue` | Fixed polling interval leak |
| `frontend/src/composables/useVillage.js` | music_complete DOM event dispatch |
| `CLAUDE.md` | Updated workflow: commit+push auto-deploys |

---

## Session 15 Accomplishments

### Village Band Polish (v90) - COMPLETE
- **Rich role prompts** - Each agent role (Producer/Melody/Bass/Harmony/Rhythm) now includes note range guidance, pattern examples, musical personality, and role-specific listening instructions
- **Round-aware prompts** - Opening: "Establish foundation." Middle: "Build on what's laid down." Final: "Add finishing touches." Plus hard instruction: "You MUST call jam_contribute()"
- **Multi-track MIDI layering** - New `create_layered_midi()` in MidiService. Each agent gets own MIDI track/channel. Same-round parts play simultaneously, rounds stack sequentially
- **Auto-completion connected** - Both auto-jam and manual `jam_finalize` now fire `auto_complete_music_task()` background worker. Jam songs auto-download and notify frontend
- **Context visibility** - Agents now see 24 notes per track (was 12)

### Council WebSocket Streaming (v91) - COMPLETE
- **Per-token streaming** via WebSocket at `/ws/council/{session_id}?token=JWT`
- **All agents stream in parallel** - Tokens appear simultaneously in all agent cards
- **`execute_agent_turn_streaming()`** uses `chat_stream()` with `on_token`/`on_tool` callbacks
- **Bidirectional commands** - start/pause/resume/stop/butt-in all via WebSocket
- **Block cursor** on agents still typing, "WS" indicator in status bar
- **SSE fallback** - Original auto-deliberate SSE endpoint untouched
- **Token counting** - `chat_stream()` now yields usage stats from `message_delta` events
- **Frontend auto-detects** - Uses WS when connected, falls back to SSE if not

### Key Files Modified/Created (Session 15)

| File | Changes |
|------|---------|
| `backend/app/api/v1/jam.py` | Rich role prompts, round-aware messages, layered MIDI merge, auto-completion |
| `backend/app/services/midi.py` | `create_layered_midi()` -- multi-track MIDI with per-agent channels |
| `backend/app/tools/jam.py` | Layered MIDI in `jam_finalize`, auto-completion fire |
| `backend/app/api/v1/council_ws.py` | **NEW** -- WebSocket endpoint with streaming deliberation loop |
| `backend/app/api/v1/council.py` | `execute_agent_turn_streaming()` with token callbacks |
| `backend/app/services/claude.py` | `chat_stream()` usage stats (message_delta handling) |
| `backend/app/main.py` | v91, mount council WS router, council-ws-streaming feature |
| `frontend/src/stores/council.js` | WS connection, token accumulation, WS-based commands |
| `frontend/src/views/CouncilView.vue` | WS connect/disconnect, streaming display, typing cursor |

---

## Session 16 Accomplishments

### Bug Sweep (v92) - COMPLETE
- **cortex_recall NULL crash** - `float(None)` when user_vectors had NULL embeddings. Fixed: `AND embedding IS NOT NULL` in WHERE clause + safety fallbacks on similarity/attention_weight
- **Jam store 404s** - All 8 API calls in `jam.js` missing `/api/v1` prefix. Fixed: added prefix to match every other store
- **Branches 404 race condition** - Conversation created with `db.flush()` (uncommitted), SSE `start` event sent ID to frontend, frontend called `/branches` which couldn't see uncommitted row. Fixed: early `db.commit()` before streaming
- **File download broken** - Pydantic `FileResponse` schema (line 90) shadowed FastAPI `FileResponse` import (file serving). Download and image preview endpoints were calling Pydantic model instead of serving files. Fixed: aliased import as `FastAPIFileResponse`
- **Debranding sweep** - Removed "Claude models" from ChatView, "Anthropic" from SettingsView BYOK text, fixed CLAUDE agent reference in AgentPanel (missed in Session 8)

### Azoth Comms
- **azoth_3.md** - Music pipeline test report: full suno_compile -> music_generate validated end-to-end. "BLAZING SUCCESS"

### Key Files Modified (Session 16)

| File | Changes |
|------|---------|
| `backend/app/tools/cortex.py` | NULL embedding filter, safety fallbacks |
| `backend/app/api/v1/chat.py` | Early commit before streaming |
| `backend/app/api/v1/files.py` | FastAPIFileResponse alias fix |
| `backend/app/main.py` | v92-bugfixes |
| `frontend/src/stores/jam.js` | /api/v1 prefix on all API calls |
| `frontend/src/views/ChatView.vue` | "Claude models" -> "Default models" |
| `frontend/src/views/SettingsView.vue` | Remove Anthropic branding from BYOK |
| `frontend/src/components/cortex/AgentPanel.vue` | CLAUDE -> AZOTH agent |

### Commits
- `4c50c1a` - Fix cortex_recall NULL similarity crash and jam store 404s
- `d964559` - Fix branches 404 race condition during chat streaming
- `ea65b07` - Fix file download/preview: FileResponse name collision
- `a95db50` - Remove Claude/Anthropic branding from user-facing frontend

---

## Session 17 Accomplishments

### Moonshot/Kimi K2.5 Provider + Model Refresh (v93) - COMPLETE
- **Moonshot provider** added with Kimi K2.5 model (China's top reasoning model)
- **api_model_id + extra_body** support for model aliases (Kimi instant mode)
- **Refreshed all provider model lists** - Groq, Together, Qwen, DeepSeek updated to latest
- **OSS tier icons** in frontend: reasoning, standard, large, small, fast model categories

### Enhanced Admin Panel (v93) - COMPLETE
- **Monitoring dashboard** with music/council/jam/vault/vector/provider stats
- **Admin served from backend** at `/admin` (no separate Railway service needed)
- **Admin auto-setup** via `INITIAL_ADMIN_EMAIL` env var
- **Admin user auto-created on startup** - `admin@apexaurum.no` with default password
- **Password field styling fix** - Explicit dark background for browser compatibility

### Admin User Setup
- **Email:** `admin@apexaurum.no` (auto-created on startup)
- **Default password:** Set via `INITIAL_ADMIN_PASSWORD` env var (or `ApexAdmin2026!`)
- **Change password after first login** (recommended)
- **Env var override:** Set `INITIAL_ADMIN_EMAIL` to use a different admin email

### Known Issues
- Admin panel password field styling needs browser testing across platforms
- Moonshot provider needs `MOONSHOT_API_KEY` env var set in Railway

### Key Files Modified (Session 17)

| File | Changes |
|------|---------|
| `backend/app/main.py` | v93, admin auto-create user on startup |
| `backend/admin_static/index.html` | Password field dark background fix |
| `admin/index.html` | Synced with admin_static version |

---

## Session 18 Accomplishments

### Beta Hardening + Bug Fixes (v94) - COMPLETE
**Build:** v94-beta-hardening
**Commits:** 1d84cf9 - a64bcce (7 commits)

### Admin Panel Login Fix - COMPLETE
- Added missing `GET /auth/me` endpoint that admin panel's checkAuth() depended on
- Fixed admin auto-setup: user wasn't being created in DB (silent failure). Registered via API, then fixed startup hook to reset password on promote and print traceback on errors
- Admin credentials: `admin@apexaurum.no` / set via `INITIAL_ADMIN_PASSWORD` env var

### Coupon DateTime Fix - COMPLETE
- Fixed "can't compare offset-naive and offset-aware datetimes" in coupon validation
- `Coupon.is_valid()` and tier_upgrade redemption used `datetime.utcnow()` (naive) against `DateTime(timezone=True)` columns
- Fixed to `datetime.now(timezone.utc)` in both billing model and API

### PAC Mode Text Contrast - COMPLETE
- Headers, bold text, list markers were invisible against purple chat bubble background
- Replaced `prose-purple` with `prose-invert pac-prose`
- Custom CSS: gold headers, white bold, gold code/markers, ethereal purple links

### Streaming Message Persistence (critical fix) - COMPLETE
- Assistant messages were NEVER saved to DB in the streaming path
- Only user messages were persisted; neural memory stored the content but messages table didn't
- Old conversations showed only user's side when reloaded
- Added Message save after streaming completes using final_response

### Navbar Reorder - COMPLETE
- Reordered by expected usage: Chat - Council - Village - GUI - Neural - Jam - Music - Agents - Files - Billing

### Beta Hardening (7 Tier 1 security fixes) - COMPLETE
1. Rate limiting: slowapi middleware, 100/min default, chat 20/min
2. Billing bypass guard: restrict to Haiku when Stripe unconfigured
3. Village WebSocket auth: JWT token via query param, reject unauthorized
4. Password minimum length: 8 chars on registration
5. Exception handler: hide internals in production
6. Admin password: generate random via secrets.token_urlsafe if env var not set
7. BillingView: show checkout/credits/portal errors to users

### Known Issues / Next Session
- Set INITIAL_ADMIN_PASSWORD env var in Railway (hardcoded default removed)
- Tier 2 audit items remaining: tool execution timeout, coupon unique constraint, credit balance DB CHECK constraint, search param length limits
- Old conversations from before streaming fix still missing assistant messages (data exists in neural memory)
- Landing page still needed for beta launch

### Environment
- Build: v94-beta-hardening
- Frontend CACHE_BUST: 15
- New dependency: slowapi (rate limiting)
- Admin URL: https://backend-production-507c.up.railway.app/admin

### Key Files Modified (Session 18)

| File | Changes |
|------|---------|
| `backend/app/main.py` | v94-beta-hardening, rate limiter, exception handler hide internals, admin password generation |
| `backend/app/api/v1/auth.py` | GET /auth/me endpoint, password min length 8 |
| `backend/app/api/v1/chat.py` | Rate limit 20/min, assistant message persistence after streaming |
| `backend/app/api/v1/billing.py` | Billing bypass guard (Haiku only when no Stripe), coupon datetime fix |
| `backend/app/models/billing.py` | Coupon.is_valid() datetime.now(timezone.utc) fix |
| `backend/app/api/v1/village_ws.py` | JWT auth on WebSocket connect |
| `frontend/src/views/ChatView.vue` | PAC mode prose-invert pac-prose, gold/white contrast CSS |
| `frontend/src/views/BillingView.vue` | Show checkout/credits/portal errors to users |
| `frontend/src/components/Navbar.vue` | Reordered nav items by usage frequency |

---

## Session 19 Accomplishments

### Tier 2 Security Hardening (v95) - COMPLETE
**Commits:** 497fcd0, 42854e3, af6cd2d, e8a9e88, 8841b80

1. **Tool execution timeout** - `asyncio.wait_for()` wraps all tool execution, 120s default, configurable via `TOOL_EXECUTION_TIMEOUT` env var
2. **Coupon unique constraint** - DB-level `UniqueConstraint('coupon_id', 'user_id')` on `coupon_redemptions` + `IntegrityError` catch returns clean 400
3. **Credit balance CHECK constraint** - `CHECK(balance_cents >= 0)` on `credit_balances` prevents negative balances at DB level
4. **Search param length limits** - `max_length` on all search endpoints: music (200), files (200), cortex (500), admin (200)

### Toast Notification System (v96) - COMPLETE
- **`useToast.js`** composable - singleton reactive state, 4 types (success/error/warning/info)
- **`ToastContainer.vue`** - fixed bottom-right, slide-in/fade-out transitions, color-coded
- Mounted globally in App.vue
- Replaced all `alert()` calls in ChatView, FilesView with styled toasts
- Surfaced silent save/delete failures in SettingsView

### Bug Report System (v96) - COMPLETE
- **Bug icon button** in navbar (desktop + mobile "Report Issue")
- **BugReportModal** - category (Bug/Feedback/Question), description, auto-captures page + browser info
- **Backend:** `BugReport` model, `POST /api/v1/feedback/report` endpoint
- **Admin panel:** "Reports" tab with status filtering, expandable detail view, admin notes, status management
- **Status flow:** open -> acknowledged -> resolved -> closed
- **Tested and confirmed working** in production

### Environment
- Build: v96-beta-polish
- Frontend CACHE_BUST: 16
- New files: `feedback.py` (model + API), `useToast.js`, `ToastContainer.vue`, `BugReportModal.vue`

### Key Files Modified (Session 19)

| File | Changes |
|------|---------|
| `backend/app/tools/__init__.py` | Tool execution timeout via asyncio.wait_for |
| `backend/app/config.py` | tool_execution_timeout setting |
| `backend/app/models/billing.py` | UniqueConstraint + CheckConstraint |
| `backend/app/database.py` | Migrations for coupon unique + credit CHECK |
| `backend/app/api/v1/billing.py` | IntegrityError catch on coupon redeem |
| `backend/app/api/v1/music.py` | search max_length=200 |
| `backend/app/api/v1/files.py` | q max_length=200 |
| `backend/app/api/v1/cortex.py` | query max_length=500 |
| `backend/app/api/v1/admin.py` | search max_length=200, Reports CRUD endpoints |
| `backend/app/models/feedback.py` | **NEW** - BugReport model |
| `backend/app/api/v1/feedback.py` | **NEW** - POST /feedback/report |
| `backend/app/models/__init__.py` | Import BugReport |
| `backend/app/api/v1/__init__.py` | Include feedback router |
| `backend/admin_static/index.html` | Reports tab with full management UI |
| `frontend/src/composables/useToast.js` | **NEW** - toast notification composable |
| `frontend/src/components/ToastContainer.vue` | **NEW** - global toast display |
| `frontend/src/components/BugReportModal.vue` | **NEW** - bug report form modal |
| `frontend/src/App.vue` | Mount ToastContainer |
| `frontend/src/components/Navbar.vue` | Bug report button + BugReportModal |
| `frontend/src/views/ChatView.vue` | Replace alert() with toast, persist selectedAgent in localStorage |
| `frontend/src/views/FilesView.vue` | Replace alert() calls with toasts |
| `frontend/src/views/SettingsView.vue` | Surface save/delete failures via toast |
| `frontend/Dockerfile` | CACHE_BUST=16 |
| `backend/app/main.py` | v96-beta-polish |
| `frontend/src/views/LoginView.vue` | Fix stale tagline (140 -> 55 tools) |
| `frontend/src/views/LandingView.vue` | **NEW** - Public landing page |
| `frontend/src/router/index.js` | Landing route for guests, /chat redirect for authenticated |

### Additional Fixes
- **Stale tagline fixed** - "140 Tools. Five Minds." updated to "55 Tools. Four Alchemists." on login and chat welcome
- **Landing page** - Hero, agent showcase, feature grid, pricing tiers, CTAs. Guests see at `/`, authenticated users go to `/chat`
- **Agent selection persistence** - `selectedAgent` saved to localStorage, survives navigation between pages

---

## Session 20 Accomplishments

### Multi-Provider BYOK (v97) - COMPLETE
- **All 6 providers** configurable via Settings > API tab: Anthropic, DeepSeek, Groq, Together, Qwen, Moonshot
- **Per-provider validation** - Anthropic SDK test for Anthropic, OpenAI-compat test for others
- **Encrypted storage** - same Fernet encryption, keyed by provider ID in `user.settings.api_keys`
- **Universal chat routing** - user BYOK key checked first for ANY provider, falls back to platform key
- **Provider card grid UI** - color-coded, status badges (Your Key / Platform / Not Set), tier-gated lock icons
- **Console links** - "Get key" links to each provider's API key page
- **Key masking** - handles sk-ant-*, gsk_*, sk-*, and generic formats

### File Attachments + Vision (v97) - COMPLETE
- **Paperclip button** in chat input - opens vault file picker dropdown
- **Vault integration** - browse and attach files from existing vault
- **Image vision** - images converted to base64 content blocks for Claude/Kimi/DeepSeek
- **Text context injection** - text/code files injected as context before user message
- **OpenAI-compat support** - image_url blocks for vision-capable OSS providers
- **Max 5 attachments** per message, 5MB image limit, 50KB text limit
- **Preview strip** - attached files shown as removable chips above input

### Nursery Masterplan - COMPLETE (local only, .gitignored)
- **Deep exploration** of OG ApexAurum Nursery (16 tools, 20 endpoints, 4 training modules)
- **Architecture decisions** documented: Railway volumes (no S3), asyncio (no Celery), 4 DB tables
- **GPU provider strategy** - training on Together/Vast.ai/RunPod via BYOK keys (zero Railway GPU cost)
- **5-session roadmap** - Foundation, Training Forge, Model Cradle, Apprentice Protocol, Polish
- **Autonomy mode** designed with cost guards
- **Local file:** `NURSERY_MASTERPLAN.md` (not committed, see .gitignore)

### Environment
- Build: v97-byok-attachments
- Frontend CACHE_BUST: 17
- Commit: 85bbf38

### Key Files Modified (Session 20)

| File | Changes |
|------|---------|
| `backend/app/api/v1/user.py` | Multi-provider BYOK endpoints, per-provider validation |
| `backend/app/api/v1/chat.py` | Universal BYOK routing, file_ids in ChatRequest, build_attachment_content() |
| `backend/app/services/encryption.py` | Multi-format key masking |
| `backend/app/services/llm_provider.py` | Image content blocks in OpenAI message converter |
| `backend/app/main.py` | v97-byok-attachments, new feature flags |
| `frontend/src/views/SettingsView.vue` | Provider card grid API tab, old BYOK removed from Profile |
| `frontend/src/views/ChatView.vue` | Paperclip button, vault file picker, attachment preview |
| `frontend/src/stores/chat.js` | file_ids in sendMessage() |
| `frontend/Dockerfile` | CACHE_BUST=17 |
| `POLISHPLAN.md` | Items 1-4 explored and documented |
| `.gitignore` | Added NURSERY_MASTERPLAN.md |

---

## Beta Launch Status

**All security audit items complete (Tier 1 + Tier 2).** Beta polish applied. Landing page live.

### Ready for Beta
- Security: rate limiting, auth on all WebSockets, input validation, exception hiding
- Data integrity: DB constraints on credits and coupons
- UX: toast notifications, bug reporting, agent persistence, file attachments
- Admin: full dashboard with user management, coupons, stats, and bug reports
- Landing page with pricing, features, and agent showcase
- Multi-provider BYOK for all 6 LLM providers
- Vision support for image attachments in chat
- INITIAL_ADMIN_PASSWORD set in Railway

### Remaining Before Public Launch
- DNS setup for apexaurum.cloud (CNAME to Railway frontend)
- Backfill assistant messages from neural memory (pre-streaming-fix conversations)
- Community beta testing with access coupons

### Next Major Feature: The Nursery
- **Masterplan ready** at `NURSERY_MASTERPLAN.md` (local, .gitignored)
- 5-session implementation roadmap
- Zero new dependencies for cloud training (HTTP APIs only)
- BYOK system already handles GPU provider keys
- Adept-tier exclusive

### Future Ideas (Not Blocking Launch)
- 3D Neural view enhancements
- Village GUI visual polish
- Email notifications for bug reports (connect bugs@apexaurum.cloud)
- Nursery placeholder tools (deploy_ollama, test_model, compare_models)

---

## Session 21 Accomplishments

### Nursery Session A: Foundation (v98) - COMPLETE
- **4 SQLAlchemy models** - NurseryDataset, NurseryTrainingJob, NurseryModelRecord, NurseryApprentice
- **DB migrations** - 4 CREATE TABLE + 8 indexes, idempotent
- **NurseryService** - synthetic data generation (rule-based, no LLM), conversation extraction (mines tool calls from chat history, deduplicates via MD5, ChatML JSONL output)
- **3 Data Garden tools** (Tier 15) - nursery_generate_data, nursery_extract_data, nursery_list_datasets
- **5 API endpoints** - /nursery/datasets CRUD + /nursery/stats, all Adept-tier gated
- **NurseryView.vue** - 5-tab interface, functional Data Garden (generate, extract, dataset list with preview), 4 placeholder tabs
- **Pinia store** - nursery.js with full state management
- **Navbar + router** - "Nursery" link between Neural and Jam

### Bug Fix: Nursery Page Crash - COMPLETE
- **Root cause:** Vue 3 `<script setup>` auto-unwraps refs in templates. `isToolSelected()` and `toggleTool()` received unwrapped arrays from template, but called `.value` on them (undefined on arrays). Crashed the render on every page load.
- **Fix:** `Array.isArray(list) ? list : list.value` handles both ref and unwrapped cases
- **Tier gate:** Added `tierRequired` flag in store (set on 403), NurseryView shows amber "Adept Tier Required" card with upgrade link for non-Adept users

### Environment
- Build: v98-nursery-foundation
- Frontend CACHE_BUST: 18
- Tools: 58 (3 new Nursery Data Garden tools)
- Commits: 309aee7, b838869

### Key Files Modified/Created (Session 21)

| File | Status | Changes |
|------|--------|---------|
| `backend/app/models/nursery.py` | NEW | 4 SQLAlchemy models |
| `backend/app/services/nursery.py` | NEW | NurseryService with data generation + extraction |
| `backend/app/tools/nursery.py` | NEW | 3 Data Garden tools (Tier 15) |
| `backend/app/api/v1/nursery.py` | NEW | 5 endpoints, Adept-gated |
| `frontend/src/views/NurseryView.vue` | NEW | Data Garden tab + placeholders + tier gate |
| `frontend/src/stores/nursery.js` | NEW | Pinia store with tierRequired flag |
| `backend/app/models/__init__.py` | EDIT | Import 4 nursery models |
| `backend/app/models/user.py` | EDIT | 4 nursery relationship back_populates |
| `backend/app/database.py` | EDIT | 4 table migrations + indexes |
| `backend/app/tools/base.py` | EDIT | NURSERY category |
| `backend/app/tools/__init__.py` | EDIT | Register nursery tools (Tier 15) |
| `backend/app/api/v1/__init__.py` | EDIT | Include nursery router |
| `backend/app/main.py` | EDIT | v98, 58 tools, nursery-data-garden feature |
| `frontend/Dockerfile` | EDIT | CACHE_BUST=18 |
| `frontend/src/router/index.js` | EDIT | /nursery route |
| `frontend/src/components/Navbar.vue` | EDIT | Nursery nav link |

---

## Session 22 Accomplishments

### Tier Alignment (v99) - COMPLETE
- **Critical bug fixed:** Nursery tier check was reading `user.settings.subscription_tier` (never populated by Stripe/admin). Changed to query the `Subscription` model directly (same pattern as chat.py). Without this fix, ALL users including Adept subscribers would be blocked from the Nursery.
- **Tool count updated** 55 -> 58 across LoginView, ChatView, LandingView
- **Billing text updated:** Alchemist "35 tools" -> "58 tools", Adept now lists "The Nursery (model training studio)" and "Dev Mode + PAC Mode"
- **Landing page** Adept tier card now mentions Nursery

### Nursery Session B: Training Forge (v100) - COMPLETE
- **CloudTrainerService** (`backend/app/services/cloud_trainer.py`) - Together.ai fine-tuning API integration via httpx:
  - `upload_dataset()` - POST multipart to `/v1/files`
  - `create_training_job()` - POST to `/v1/fine-tunes` with model, epochs, LoRA, learning rate
  - `get_job_status()` / `list_jobs()` / `cancel_job()` - status polling and management
  - `estimate_cost()` - local calculation (no API call) based on token counts and model pricing
  - `TRAINABLE_MODELS` dict: Llama 3.2 1B, Llama 3.2 3B, Llama 3.1 8B, Qwen 2.5 7B
- **Background poller** (`auto_complete_training_job()`) - fire-and-forget asyncio task following the proven `auto_complete_music_task` pattern:
  - Polls Together.ai every 30s, max 2 hours
  - Updates NurseryTrainingJob status + progress in DB
  - On completion: creates NurseryModelRecord, broadcasts Village event
  - On failure: sets error_message, never crashes server
  - Retrieves BYOK key via `get_user_api_key(user, "together")`
- **4 new tools** (Tier 15): nursery_estimate_cost, nursery_train, nursery_job_status, nursery_list_jobs
- **6 new API endpoints:** GET /training/models, POST /training/estimate, POST /training/start, GET /training/jobs, GET /training/jobs/{id}, POST /training/jobs/{id}/cancel
- **Training Forge tab** replaces placeholder in NurseryView.vue:
  - Left column: dataset selector, base model picker (4 models), epochs slider, learning rate, LoRA toggle, batch size, suffix, live cost estimate, start training button
  - Right column: job stats (total/active/completed), job cards with status badges, progress bars, cost, timestamps, cancel button
  - Together.ai key warning with Settings link if no key configured
  - 15-second auto-refresh polling when tab is active (clearInterval on tab change/unmount)
- **Store updated:** nursery.js now has trainingJobs, costEstimate, estimating, startingTraining, loadingJobs, hasTogetherKey state + 6 new actions
- **Tool count:** 58 -> 62, taglines updated everywhere

### Environment
- Build: v100-training-forge
- Frontend CACHE_BUST: 19
- Tools: 62 (7 Nursery tools: 3 Data Garden + 4 Training Forge)
- Commits: 46adadd (v99), c6098c0 (v100)

### Key Files Modified/Created (Session 22)

| File | Status | Changes |
|------|--------|---------|
| `backend/app/services/cloud_trainer.py` | NEW | CloudTrainerService + auto_complete_training_job (~410 lines) |
| `backend/app/api/v1/nursery.py` | EDIT | 6 training endpoints + request schemas, fixed tier check |
| `backend/app/tools/nursery.py` | EDIT | 4 Training Forge tools added (7 total nursery tools) |
| `backend/app/api/v1/billing.py` | EDIT | Tool count 35->62, Nursery in Adept features |
| `backend/app/main.py` | EDIT | v100, 62 tools, nursery-training-forge feature |
| `frontend/src/views/NurseryView.vue` | EDIT | Training Forge tab (1077 lines total) |
| `frontend/src/stores/nursery.js` | EDIT | Training state + 6 actions (223 lines) |
| `frontend/src/views/ChatView.vue` | EDIT | 62 Tools tagline |
| `frontend/src/views/LoginView.vue` | EDIT | 62 Tools tagline |
| `frontend/src/views/LandingView.vue` | EDIT | 62 Tools + Nursery in Adept tier |
| `frontend/Dockerfile` | EDIT | CACHE_BUST=19 |

---

## Session 23 Accomplishments

### Nursery Session C: Model Cradle + Village (v101) - COMPLETE
- **6 new API endpoints:** list models, model detail, register in Village, delete model, discover Village models, village activity feed
- **3 new tools:** nursery_list_models, nursery_register_model, nursery_discover_models (65 tools total)
- **Model Cradle tab (Tab 3):** Stats bar (model count, village-posted count), model cards grid with type badges (LoRA/Cloud/Uploaded), capability gold tags, Village registration button, confirm-delete pattern, empty state linking to Forge
- **Village Feed tab (Tab 5):** Activity feed merging training jobs + model events sorted by time, model discovery search with semantic query via neural memory
- **Store extended:** models, loadingModels, villageActivity, loadingActivity, discoveredModels, loadingDiscovery, discoveryQuery state + 6 actions (fetchModels, fetchModelDetail, registerModel, deleteModel, discoverModels, fetchVillageActivity)
- **Bug fixes discovered during planning:**
  - `EventType.TOOL_RESULT` (nonexistent) fixed to `EventType.TOOL_COMPLETE` in cloud_trainer.py
  - Removed invalid `user_id` kwarg from VillageEvent constructor -- both bugs caused Village broadcasts to silently fail on training completion
- **Village zone map:** All 10 nursery tools registered in `TOOL_ZONE_MAP` in village_events.py
- **Route ordering:** GET /discover and GET /village-activity placed before GET /models/{model_id} to avoid FastAPI path capture

### Nursery Session D: Apprentice Protocol + Autonomy (v102) - COMPLETE
- **3 new API endpoints:** GET/POST/DELETE /apprentices with full CRUD
- **Enhanced start_training endpoint:** Now accepts optional `apprentice_id` to link training jobs to apprentices
- **3 new tools:** nursery_create_apprentice, nursery_list_apprentices, nursery_auto_train (68 tools total)
- **nursery_auto_train tool** -- Full autonomous pipeline:
  1. Resolve dataset from apprentice_id or direct dataset_id
  2. Validate dataset, get Together API key
  3. Estimate cost (CloudTrainerService.estimate_cost)
  4. **Cost guard:** abort if estimated_cost > max_cost ($5.00 default)
  5. Upload dataset, create training job (stores apprentice_id in config JSONB)
  6. Update apprentice status to "training"
  7. Fire asyncio.create_task(auto_complete_training_job)
- **Apprentice lifecycle in auto_complete_training_job:**
  - On completion: sets apprentice status="trained", links model_id
  - On failure: sets apprentice status="failed"
  - On timeout: sets apprentice status="failed"
  - Reads apprentice_id from job.config JSONB (no schema change needed)
- **POST /apprentices with auto-generate:** Parses specialization as comma-separated tool names, validates against registry, calls NurseryService.generate_synthetic_data to create dataset
- **Apprentice tab (Tab 4):** Two-column layout:
  - Left: Create form with master agent selector (4 color-coded buttons), name input, specialization input, auto-generate toggle with examples slider (10-500), error/success messages
  - Right: Stats bar (total/training/trained), apprentice cards with master color, status badge (dataset_ready/training/trained/failed), dataset/model info, "Start Training" button for dataset_ready apprentices, confirm-delete
- **NURSERY_KEEPER.txt:** Internal prompt file (NOT added to NATIVE_AGENTS, preserves "Four Alchemists")
- **Store:** apprentices, loadingApprentices, creatingApprentice state + fetchApprentices, createApprentice, deleteApprentice actions

### Environment
- Build: v102-apprentice-protocol
- Frontend CACHE_BUST: 21
- Tools: 68 (13 Nursery tools: 3 Data Garden + 4 Training Forge + 3 Model Cradle + 3 Apprentice Protocol)
- Commits: e3e7cf9 (v101), 4d31bef (v102)

### Key Files Modified/Created (Session 23)

| File | Status | Changes |
|------|--------|---------|
| `backend/app/services/cloud_trainer.py` | EDIT | Fix Village broadcast bugs + apprentice lifecycle hooks |
| `backend/app/services/village_events.py` | EDIT | Add 10 nursery tools to TOOL_ZONE_MAP |
| `backend/app/api/v1/nursery.py` | EDIT | 9 new endpoints + schemas, enhanced start_training |
| `backend/app/tools/nursery.py` | EDIT | 6 new tools (13 total nursery tools) |
| `backend/native_prompts/NURSERY_KEEPER.txt` | NEW | Internal keeper prompt for autonomous operations |
| `frontend/src/stores/nursery.js` | EDIT | Model + Village + Apprentice state + 9 actions |
| `frontend/src/views/NurseryView.vue` | EDIT | Tab 3 (Model Cradle), Tab 4 (Apprentices), Tab 5 (Village Feed) |
| `backend/app/main.py` | EDIT | v102, 68 tools, 2 new feature flags |
| `frontend/src/views/ChatView.vue` | EDIT | 68 Tools tagline |
| `frontend/src/views/LoginView.vue` | EDIT | 68 Tools tagline |
| `frontend/src/views/LandingView.vue` | EDIT | 68 Tools tagline |
| `backend/app/api/v1/billing.py` | EDIT | 68 tools in Alchemist text |
| `frontend/Dockerfile` | EDIT | CACHE_BUST=21 |

---

## Session 24 Accomplishments

### Nursery Session E: Polish (v103) - COMPLETE
**Commits:** 6f7469c (polish), 1650105 (circular import fix)

**Component Extraction** (NurseryView.vue: 1,618 -> 79 lines):
- 5 tab components: NurseryDataGarden, NurseryTrainingForge, NurseryModelCradle, NurseryApprentices, NurseryVillageFeed
- Shared utils: `nurseryUtils.js` with `formatRelativeTime()`, `getStatusColor()`, `useConfirmDelete()` composable
- 3 duplicated patterns eliminated

**Store Polish** (nursery.js):
- `lastError` reactive error tracking across all 20 actions
- 7 computed properties: totalDatasets, totalExamples, runningJobs, completedJobs, trainedApprentices, trainingApprentices, villageModels
- `startTraining()` converted to options object with `apprenticeId` support

**Backend Hardening**:
- Rate limits: 4 endpoints (5/min generate, 5/min extract, 3/min train, 2/min apprentice)
- Max 3 concurrent training jobs per user (API + both tools)
- Empty dataset validation before training
- DB context consolidation: NurseryTrainTool (2->1 contexts), NurseryAutoTrainTool (3->2)
- Together.ai 429 exponential backoff (30s -> 300s cap)
- Village broadcast failures now logged (was silent `pass`)
- `rate_limit.py` module to avoid circular import between main.py and nursery.py

**Admin Nursery Stats**:
- 5 metrics: datasets, training jobs, models, apprentices + jobs-by-status breakdown
- Nursery card in admin panel with color-coded status display

**Mobile CSS**: Stats grids responsive, base model selector responsive, apprentice stats wrap

### Environment
- Build: v103-nursery-polish
- Frontend CACHE_BUST: 21 (unchanged)
- Tools: 68 (unchanged)

### Key Files Modified/Created (Session 24)

| File | Status | Changes |
|------|--------|---------|
| `frontend/src/components/nursery/nurseryUtils.js` | NEW | Shared helpers (formatRelativeTime, useConfirmDelete, statusColorMap) |
| `frontend/src/components/nursery/NurseryDataGarden.vue` | NEW | Tab 1 component (503 lines) |
| `frontend/src/components/nursery/NurseryTrainingForge.vue` | NEW | Tab 2 component (415 lines) |
| `frontend/src/components/nursery/NurseryModelCradle.vue` | NEW | Tab 3 component (155 lines) |
| `frontend/src/components/nursery/NurseryApprentices.vue` | NEW | Tab 4 component (316 lines) |
| `frontend/src/components/nursery/NurseryVillageFeed.vue` | NEW | Tab 5 component (125 lines) |
| `frontend/src/views/NurseryView.vue` | EDIT | Shrink from 1,618 to 79 lines (shell only) |
| `frontend/src/stores/nursery.js` | EDIT | Error state, 7 computed props, options-object API |
| `backend/app/rate_limit.py` | NEW | Extracted limiter to avoid circular import |
| `backend/app/api/v1/nursery.py` | EDIT | Rate limits, concurrent job cap, empty dataset check |
| `backend/app/tools/nursery.py` | EDIT | DB context consolidation, concurrent job check |
| `backend/app/services/cloud_trainer.py` | EDIT | 429 backoff, empty file check, broadcast logging |
| `backend/app/api/v1/admin.py` | EDIT | Nursery stats in StatsResponse + queries |
| `backend/admin_static/index.html` | EDIT | Nursery stats card |
| `backend/app/main.py` | EDIT | v103, import limiter from rate_limit.py |

---

## Nursery Roadmap - COMPLETE

| Session | Scope | Status |
|---------|-------|--------|
| **A: Foundation** | Models, migrations, Data Garden tools, NurseryView | DONE (Session 21) |
| **B: Training Forge** | CloudTrainerService, Together.ai, training tools/endpoints/tab | DONE (Session 22) |
| **C: Model Cradle + Village** | Model management, Village registration, model discovery | DONE (Session 23) |
| **D: Apprentice Protocol + Autonomy** | Apprentice creation, auto_train, cost guards | DONE (Session 23) |
| **E: Polish** | Component extraction, backend hardening, admin stats, mobile CSS | DONE (Session 24) |

### Nursery Architecture (Final)
```
NurseryView.vue (79-line shell, 5 tab components)
├── components/nursery/NurseryDataGarden.vue (503 lines)
├── components/nursery/NurseryTrainingForge.vue (415 lines)
├── components/nursery/NurseryModelCradle.vue (155 lines)
├── components/nursery/NurseryApprentices.vue (316 lines)
├── components/nursery/NurseryVillageFeed.vue (125 lines)
└── components/nursery/nurseryUtils.js (63 lines)

Backend:
├── models/nursery.py (4 tables: Dataset, TrainingJob, ModelRecord, Apprentice)
├── services/nursery.py (NurseryService: data generation, extraction)
├── services/cloud_trainer.py (CloudTrainerService: Together.ai + background poller)
├── api/v1/nursery.py (~26 endpoints, rate-limited, concurrent job cap)
├── tools/nursery.py (13 tools, DB-consolidated)
└── native_prompts/NURSERY_KEEPER.txt (internal prompt)

Store: frontend/src/stores/nursery.js (438 lines, 7 computed, 20+ actions, error tracking)
```

---

## Next Major Milestone: Tier Restructure

**Masterplan:** `TIER_MASTERPLAN.md` (committed, in repo root)

### New Tier Map (4 tiers replacing 3)
| Tier | Price | Messages | Opus Msgs | Key Features |
|------|-------|----------|-----------|--------------|
| Free Trial | $0 | 20 (7 days) | 0 | Haiku only, taste the Athanor |
| Seeker ($10) | $10/mo | 200 | 0 | Haiku+Sonnet, 128K ctx cap, 10 Suno |
| Adept ($30) | $30/mo | 1,000 | 50 | All models, full ctx, BYOK OSS, nursery tease |
| Opus ($100) | $100/mo | 5,000 | 500 | Full access, nursery, dev mode, 1M beta |
| Azothic ($300) | $300/mo | 20,000 | 2,000 | Everything, training credits, priority |

### Implementation Roadmap (4 sessions)
| Session | Scope |
|---------|-------|
| **A: Usage Infrastructure** | Per-model counters, usage_counters table, limit middleware, context cap |
| **B: Tier Restructure** | 4-tier config, Stripe products, billing UI, landing page, feature gates |
| **C: Credit Packs + Dashboard** | Pack purchases, usage display, admin usage reports |
| **D: Legal + Polish** | Terms, privacy, disclaimers, coupon library, package builder |

### Remaining Beta Items
- DNS setup for apexaurum.cloud
- Backfill old assistant messages
- Community beta testing with launch coupons (defined in masterplan)

---

## Easter Eggs

- **Dev Mode:** Konami code (up up down down left right left right BA) or 7-tap on Au logo (Adept only!)
- **PAC Mode:** Type "AZOTH" while in Dev Mode
- **PAC prompts:** `backend/native_prompts/*-PAC.txt`

---

*"The Council convenes. The Athanor blazes. The gold multiplies. The Nursery tends. The Forge burns. New minds are born."*
