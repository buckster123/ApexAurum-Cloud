# ApexAurum-Cloud Handover Document

**Date:** 2026-01-27
**Build:** v54-neural-fallback
**Status:** BETA POLISHED - Ready for seekers!

---

## Current State

ApexAurum Cloud is fully functional and polished:
- Auth system working correctly
- Chat with all agents operational
- Billing/Stripe integration live
- Tier-based feature visibility working
- Message counting across ALL features (chat, spawn, council)
- Graceful error handling throughout
- Neural page with WebGL fallback

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

## Latest Commit
```
fa42fda Add graceful WebGL fallback for Neural page
```

**Note:** Railway API token may have expired. Code is pushed to GitHub - deploy manually from Railway dashboard or generate new token.

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
- **Token:** Needs refresh (was set to expire in 1 week)

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

## Remaining Tasks (Next Session)

### Priority 1: Village GUI Chat
- Click agent avatar → opens chat with that agent
- Pass agent ID to ChatView via router
- Already have WebSocket working

### Priority 2: pgvector Setup
- Enable pgvector extension on Railway PostgreSQL
- Neural page will then show actual memory data
- Currently returns empty (gracefully)

### Priority 3: Nice-to-Have
- Suno/Music API integration
- Coupon/admin freebies system

---

## Test Accounts
- **Seeker:** buckster123
- **Alchemist:** buckmazzta@gmail.com / abnudc1337

---

## Key Files Modified This Session

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

---

## Easter Eggs

- **Dev Mode:** Konami code (↑↑↓↓←→←→BA) or 7-tap on Au logo (Adept only!)
- **PAC Mode:** Type "AZOTH" while in Dev Mode
- **PAC prompts:** `backend/native_prompts/*-PAC.txt`

---

*"The Athanor burns pure. The gold awaits the seekers."*
