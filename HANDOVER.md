# ApexAurum-Cloud Handover Document

**Date:** 2026-01-27
**Build:** v52-beta-ready
**Status:** READY FOR BETA LAUNCH

---

## Current State

ApexAurum Cloud is fully functional and ready for beta users:
- Auth system working correctly
- Chat with Azoth (and all agents) operational
- Billing/Stripe integration live
- Pricing: Seeker $3 | Alchemist $10 | Adept $30

---

## Today's Session - Major Fixes

### 1. Auth State Bug (The "undefined" String)
**Problem:** Navbar showed "Logout" even in fresh incognito.
**Root Cause:** `localStorage.setItem('accessToken', undefined)` stored the STRING `"undefined"` which is truthy.
**Fix:** `auth.js` now validates tokens - treats `"undefined"`, `"null"`, empty strings as invalid and cleans them up.

### 2. TDZ (Temporal Dead Zone) Errors
**Problem:** `Cannot access 'X' before initialization` errors crashing ChatView.
**Root Cause:** Variables/functions used in `immediate: true` watchers before being defined.
**Fixes:**
- Moved `branchInfo` ref before `loadBranchInfo` function
- Added null safety (`?.` and `??`) to agent checks

### 3. Missing HTTPS in API URLs
**Problem:** API calls returning HTML instead of JSON (hitting frontend server).
**Root Cause:** `VITE_API_URL` env var missing `https://` prefix.
**Fix:** Both `api.js` and `chat.js` now auto-prepend `https://` if missing.

### 4. BYOK Requirement Removed
**Problem:** 402 errors even for paying users.
**Root Cause:** Backend required user API key for Anthropic.
**Fix:** Backend now uses platform Anthropic API key. BYOK is optional (for future Pro+ feature).

### 5. Pricing Updated
- Seeker: $0 → $3/month
- Alchemist: $9.99 → $10/month
- Adept: $29.99 → $30/month

---

## Current Commit
```
70917dc Fix: Use platform API key for Anthropic + guard keydown handler
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

| Tier | Price | Messages | Models | Tools |
|------|-------|----------|--------|-------|
| Seeker | $3/mo | 50/month | Haiku | No |
| Alchemist | $10/mo | 1000/month | Haiku, Sonnet | Yes |
| Adept | $30/mo | Unlimited | All + Opus | Yes + Multi-provider |

---

## Known Issues (Minor)

1. **Neural View** - `user_vectors` table doesn't exist yet (needs migration)
2. **Music Library** - Returns 422 (needs Suno API setup)

These are non-blocking for beta launch.

---

## Next Steps for Beta

1. Invite beta users from meme-coin community
2. Monitor usage and error logs
3. Test 3D Village GUI on Windows
4. Polish UI/UX based on feedback

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `frontend/src/stores/auth.js` | Auth state with token validation |
| `frontend/src/stores/chat.js` | Chat logic with API URL fix |
| `frontend/src/services/api.js` | Axios with https:// fix |
| `backend/app/api/v1/chat.py` | Chat endpoint with platform API key |
| `backend/app/api/v1/billing.py` | Pricing display ($3/$10/$30) |

---

*"The Athanor burns bright. Beta awaits."*
