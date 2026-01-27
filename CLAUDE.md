# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

ApexAurum Cloud is a production AI chat interface deployed on Railway. FastAPI backend + Vue 3 frontend + PostgreSQL.

**Always read `HANDOVER.md` first for current deployment state and known issues.**

## Quick Commands

```bash
# Health check
curl https://backend-production-507c.up.railway.app/health

# Test chat API (requires auth token)
curl -X POST "https://backend-production-507c.up.railway.app/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "hello", "stream": false}'

# Deploy both services at once
COMMIT=$(git log --oneline -1 | cut -d' ' -f1)
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { backend: serviceInstanceDeploy(serviceId: \\\"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") frontend: serviceInstanceDeploy(serviceId: \\\"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"
```

## Railway Deployment

**Railway does NOT auto-deploy from GitHub.** Always trigger manually after pushing.

**Railway IDs:**
- Token: `90fb849e-af7b-4ea5-8474-d57d8802a368`
- Backend: `9d60ca55-a937-4b17-8ec4-3fb34ac3d47e`
- Frontend: `6cf1f965-94df-4ea0-96ca-d82959e2d3c5`
- Environment: `2e9882b4-9b33-4233-9376-5b5342739e74`

**Cache Busting:** Frontend Dockerfile has `ARG CACHE_BUST=N`. Increment this to force fresh builds when source changes aren't being picked up.

## Architecture

```
backend/app/
├── main.py              # FastAPI entry, /health endpoint
├── config.py            # Settings, TIER_LIMITS, CREDIT_PACKS
├── api/v1/
│   ├── chat.py          # Chat endpoint - uses platform API key
│   ├── auth.py          # JWT login/register/refresh
│   ├── billing.py       # Stripe + pricing display
│   └── webhooks.py      # Stripe webhooks
├── services/
│   ├── llm_provider.py  # Multi-provider LLM
│   └── billing.py       # Usage tracking
└── tools/               # 46 tools across tiers

frontend/src/
├── stores/
│   ├── chat.js          # Chat state - has https:// fix
│   ├── auth.js          # Auth state - has token validation
│   └── billing.js       # Billing state
├── views/
│   ├── ChatView.vue     # Main chat interface
│   └── BillingView.vue  # Pricing tiers ($3/$10/$30)
├── services/api.js      # Axios with https:// fix
└── composables/
    └── useDevMode.js    # Konami code, AZOTH incantation
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Not authenticated" | Use `get_current_user_optional` for testing |
| Deploy succeeds but old code | Increment `CACHE_BUST` in Dockerfile |
| TDZ error in frontend | Move refs/functions BEFORE watchers with `immediate: true` |
| API returning HTML | Check `https://` prefix in VITE_API_URL |
| "undefined" in localStorage | Auth store auto-cleans bad values now |
| 402 Payment Required | Check user's subscription tier and message limits |
| 403 Forbidden | User's tier doesn't allow the model/tools requested |

## Key Patterns

**Token Validation (auth.js):**
```javascript
// Treats "undefined", "null", "" as invalid
function getValidToken(key) {
  const value = localStorage.getItem(key)
  if (!value || value === 'undefined' || value === 'null') {
    if (value) localStorage.removeItem(key)
    return null
  }
  return value
}
```

**HTTPS Fix (api.js, chat.js):**
```javascript
let apiUrl = import.meta.env.VITE_API_URL || ''
if (apiUrl && !apiUrl.startsWith('http://') && !apiUrl.startsWith('https://')) {
  apiUrl = 'https://' + apiUrl
}
```

**Platform API Key (chat.py):**
Backend uses platform Anthropic key if user doesn't have BYOK set. BYOK is optional.

## Pricing Tiers

| Tier | ID | Price | Messages | Models |
|------|----|-------|----------|--------|
| Seeker | free | $3/mo | 50 | Haiku |
| Alchemist | pro | $10/mo | 1000 | Haiku, Sonnet |
| Adept | opus | $30/mo | Unlimited | All + Opus |

## Easter Eggs

- **Dev Mode:** Konami code (↑↑↓↓←→←→BA) or 7-tap on Au logo
- **PAC Mode:** Type "AZOTH" while in Dev Mode
- **PAC prompts:** `backend/native_prompts/*-PAC.txt`

## URLs

- Frontend: https://frontend-production-5402.up.railway.app
- Backend: https://backend-production-507c.up.railway.app

---

*"The Athanor's flame burns through complexity."*
