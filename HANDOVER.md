# ApexAurum-Cloud Handover Document

**Date:** 2026-01-27
**Build:** v53-polished
**Status:** BETA READY - FULLY POLISHED

---

## Current State

ApexAurum Cloud is fully functional and polished for beta users:
- Auth system working correctly
- Chat with all agents operational
- Billing/Stripe integration live
- Tier-based feature visibility working
- Message counting across all features
- Graceful error handling

**Pricing:** Seeker $3 | Alchemist $10 | Adept $30

---

## Today's Session 2 - Polish & Features

### 1. Message Counter Fixed
**Problem:** Messages weren't counting toward usage limits.
**Root Cause:** Streaming path in chat.py didn't call `record_message_usage()`.
**Fixes:**
- `llm_provider.py`: Now emits usage info during stream
- `chat.py`: Captures and records streaming usage
- `agents.py`: Added billing to spawn and council endpoints

### 2. Tier-Based Model Filtering
**Problem:** Users could select models they couldn't use → 403 errors.
**Fix:** Backend `/api/v1/chat/models` now filters by user's tier.

### 3. BYOK Hidden from Seeker
**Problem:** Seeker tier saw BYOK option in Settings.
**Fix:** Settings page checks `billing.status.features.byok_allowed`.

### 4. Dev Mode = Adept Only
**Problem:** Anyone could activate dev mode with easter eggs.
**Fix:** `useDevMode.js` now checks tier before enabling.
**Bonus:** Added visible "Enable Dev Mode" button for Adept users.

### 5. Graceful Error Handling
**Problem:** 403/500 errors shown as raw console messages.
**Fixes:**
- Chat shows friendly messages for billing errors (🔒 Model requires higher tier)
- Cortex endpoints return empty data instead of 500 when table missing

### 6. Village WebSocket URL Fixed
**Problem:** WebSocket connecting to wrong URL (same https:// prefix bug).
**Fix:** Both `VillageGUIView.vue` and `useVillage.js` add protocol prefix.

---

## Current Commit
```
ef3ae14 Fix message counting for spawns/councils + graceful cortex handling
```

---

## Quick Commands

```bash
# Health check
curl https://backend-production-507c.up.railway.app/health

# Deploy both services
COMMIT=$(git log --oneline -1 | cut -d' ' -f1)
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { backend: serviceInstanceDeploy(serviceId: \\\"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") frontend: serviceInstanceDeploy(serviceId: \\\"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"
```

---

## Railway IDs
- **Token:** `90fb849e-af7b-4ea5-8474-d57d8802a368`
- **Backend Service:** `9d60ca55-a937-4b17-8ec4-3fb34ac3d47e`
- **Frontend Service:** `6cf1f965-94df-4ea0-96ca-d82959e2d3c5`
- **Environment:** `2e9882b4-9b33-4233-9376-5b5342739e74`

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

## Known Limitations (Non-Blocking)

1. **Neural View** - `user_vectors` table needs pgvector extension (gracefully returns empty)
2. **Music Library** - Suno API not configured (returns 422)
3. **WebGL on Pi** - No GPU, uses 2D fallback

---

## Test Accounts
- **Seeker:** buckster123
- **Alchemist:** buckmazzta@gmail.com / abnudc1337

---

## Key Files Modified This Session

| File | Changes |
|------|---------|
| `backend/app/api/v1/chat.py` | Tier-filtered models endpoint |
| `backend/app/api/v1/agents.py` | Billing for spawn/council |
| `backend/app/api/v1/cortex.py` | Graceful table-missing handling |
| `backend/app/services/llm_provider.py` | Usage tracking in stream |
| `frontend/src/stores/chat.js` | Friendly error messages |
| `frontend/src/stores/billing.js` | Already had tier getters |
| `frontend/src/views/SettingsView.vue` | BYOK visibility, dev mode button |
| `frontend/src/composables/useDevMode.js` | Tier check before activation |
| `frontend/src/views/VillageGUIView.vue` | WebSocket URL fix |
| `frontend/src/composables/useVillage.js` | WebSocket URL fix |

---

## Easter Eggs

- **Dev Mode:** Konami code (↑↑↓↓←→←→BA) or 7-tap on Au logo (Adept only)
- **PAC Mode:** Type "AZOTH" while in Dev Mode
- **PAC prompts:** `backend/native_prompts/*-PAC.txt`

---

*"The Athanor burns pure. The gold is ready."*
