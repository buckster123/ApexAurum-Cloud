# ApexAurum-Cloud Handover Document

**Date:** 2026-01-27
**Build:** v51-byok-removal
**Status:** 🧪 TESTING - Removed BYOK, simplified to auth-based access

---

## Current Session Summary

### Problem Being Fixed
UI shows "logged in" state (Navbar with Logout visible) even on fresh page loads with cleared localStorage/incognito. Billing page crashes. Auth state is inconsistent.

### What We Tried
1. Fixed TDZ error in `loadBranchInfo` (function defined after watcher that calls it)
2. Fixed api.js refresh loop (created separate `refreshClient` without interceptors)
3. Rolled back to "working" commit - same issue persisted
4. Found console error via user's log file - TDZ error still happening

### Current Fix (Just Deployed - `be6d9da`)
**Removed BYOK requirement entirely.** The `hasApiKey` check was adding complexity and may have been contributing to the auth state issues.

Changes made:
- Removed `hasApiKey`, `checkingApiKey` refs from ChatView
- Removed `checkApiKeyStatus()` function and API call
- Replaced "API Key Required" prompt with "Login Required" prompt
- Input now disabled based on `!auth.isAuthenticated` instead of `!hasApiKey`
- Added `useAuthStore` import to ChatView

### The Mystery
Even with all fixes, fresh incognito shows Navbar with "Logout" button. This SHOULD NOT happen because:
- `isAuthenticated = computed(() => !!accessToken.value)`
- `accessToken = ref(localStorage.getItem('accessToken'))`
- In incognito, localStorage is empty, so accessToken should be null, so isAuthenticated should be false
- App.vue only renders `<Navbar v-if="auth.isAuthenticated" />`

Something is making `isAuthenticated` return `true` when it shouldn't.

### Theories to Investigate
1. **Railway caching** - Maybe old JS bundle is cached?
2. **Build issue** - Check the actual deployed JS for the auth logic
3. **Pinia initialization** - Something odd in store creation?
4. **Custom domain leftover** - User mentioned setting up apexaurum.no domain

---

## Current Commit
```
be6d9da Remove BYOK requirement - simplify to auth-based access
```

---

## Files Changed Today

**ChatView.vue:**
- Added `useAuthStore` import
- Removed BYOK-related code (hasApiKey, checkingApiKey, checkApiKeyStatus)
- Changed to auth-based access control
- Moved `loadBranchInfo` before watcher (TDZ fix)

**api.js:**
- Added `refreshClient` axios instance (has baseURL, no interceptors)
- Token refresh now uses `refreshClient` to avoid infinite 401 loop

---

## Quick Test Commands

```bash
# Check backend health
curl https://backend-production-507c.up.railway.app/health

# Check frontend deployment
curl -s https://frontend-production-5402.up.railway.app/ | head -20

# Deploy frontend manually
COMMIT=$(git log --oneline -1 | cut -d' ' -f1)
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"
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

## User's Log File Location
`railway_logs/ape-logs/ape_log_1.log` - Contains console errors from testing

---

## BYOK Notes
BYOK (Bring Your Own Key) was removed as a beta workaround. It will return later as a Pro+ tier feature. For now:
- Free tier: 50 messages/month with Haiku
- Pro tier: 1000 messages + future BYOK
- Opus tier: Unlimited

---

## Next Steps
1. Test the current deployment - does BYOK removal fix the auth weirdness?
2. If still broken, investigate:
   - Check actual deployed JS for auth logic
   - Check Railway build cache (may need to bust it)
   - Check if there's something in Pinia store initialization
3. Once auth is working, test full flow: login → chat → billing → logout

---

## Key Files for Debugging

| File | Purpose |
|------|---------|
| `frontend/src/stores/auth.js` | Auth state - isAuthenticated computed |
| `frontend/src/App.vue` | Navbar conditional render |
| `frontend/src/views/ChatView.vue` | Main chat view |
| `frontend/src/services/api.js` | Axios interceptors, token refresh |
| `frontend/src/router/index.js` | Route guards |

---

*"The Athanor's flame burns through complexity."*
