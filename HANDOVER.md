# ApexAurum-Cloud Handover Document

**Date:** 2026-01-26
**Build:** v47-billing-system
**Status:** PRODUCTION - Billing & Monetization System

---

## Session Summary: Billing & Monetization System

### What Was Accomplished

Implemented the complete billing and monetization infrastructure for ApexAurum:

1. **Database Models** (`app/models/billing.py`)
   - `Subscription` - Stripe subscription sync (tier, status, usage)
   - `CreditBalance` - Pay-per-use credit balances
   - `CreditTransaction` - Audit log for all credit changes
   - `WebhookEvent` - Stripe webhook idempotency

2. **Configuration** (`app/config.py`)
   - Stripe environment variables (secret key, publishable key, webhook secret)
   - Price IDs for subscriptions and credit packs
   - `TIER_LIMITS` dict with tier features and limits
   - `CREDIT_PACKS` dict with credit pack pricing

3. **Services**
   - `app/services/pricing.py` - LLM cost calculation per provider/model
   - `app/services/billing.py` - BillingService for usage tracking and Stripe integration

4. **API Endpoints** (`app/api/v1/billing.py`)
   - `GET /api/v1/billing/status` - Get user's billing status
   - `POST /api/v1/billing/checkout/subscription` - Create subscription checkout
   - `POST /api/v1/billing/checkout/credits` - Create credits checkout
   - `POST /api/v1/billing/portal` - Create Stripe Customer Portal session
   - `GET /api/v1/billing/transactions` - Get credit transaction history
   - `GET /api/v1/billing/pricing` - Get pricing info (public)

5. **Webhook Handler** (`app/api/v1/webhooks.py`)
   - Idempotent Stripe webhook processing
   - Handles checkout completion, subscription lifecycle, invoice events

6. **Chat Integration** (`app/api/v1/chat.py`)
   - Billing checks before message processing
   - Model access enforcement based on tier
   - Tool access enforcement based on tier
   - Multi-provider access enforcement (Opus only)
   - Usage recording after response

7. **Frontend**
   - `src/stores/billing.js` - Billing state management
   - `src/views/BillingView.vue` - Pricing page with tier cards
   - `src/components/billing/UsageMeter.vue` - Usage display for sidebar
   - Router updated with `/billing` routes

### Pricing Tiers

| Tier | Price | Messages | Features |
|------|-------|----------|----------|
| Seeker (Free) | $0 | 50/mo | Haiku only, no tools |
| Alchemist (Pro) | $9.99/mo | 1000/mo | Sonnet + Haiku, all tools, BYOK |
| Adept (Opus) | $29.99/mo | Unlimited | All models, multi-provider, API |

### Credit Packs

| Pack | Price | Credits |
|------|-------|---------|
| Small | $5 | 500 |
| Large | $20 | 2500 (includes 25% bonus) |

### Environment Variables Needed

```bash
# Stripe (add to Railway)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Price IDs (create in Stripe Dashboard first)
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_OPUS_MONTHLY=price_...
STRIPE_PRICE_CREDITS_500=price_...
STRIPE_PRICE_CREDITS_2500=price_...
```

### Files Created

**Backend:**
- `app/models/billing.py` - Database models
- `app/schemas/billing.py` - Pydantic schemas
- `app/services/billing.py` - BillingService
- `app/services/pricing.py` - Cost calculation
- `app/api/v1/billing.py` - Billing endpoints
- `app/api/v1/webhooks.py` - Webhook handler
- `alembic/versions/002_billing_tables.py` - Migration

**Frontend:**
- `src/stores/billing.js` - Billing state
- `src/views/BillingView.vue` - Pricing page
- `src/components/billing/UsageMeter.vue` - Usage meter

### Files Modified

- `app/models/__init__.py` - Added billing model imports
- `app/models/user.py` - Added subscription relationship
- `app/api/v1/__init__.py` - Added billing/webhook routers
- `app/api/v1/chat.py` - Added billing checks
- `app/config.py` - Added Stripe settings and tier limits
- `app/database.py` - Added get_db_context()
- `app/main.py` - Updated build version
- `backend/requirements.txt` - Added stripe package
- `frontend/src/router/index.js` - Added billing routes

---

## Previous Session: Multi-Provider LLM Implementation

### What Was Accomplished

Implemented the full multi-provider LLM system as planned in `.claude/plans/rippling-whistling-chipmunk.md`:

1. **Backend Provider Registry & Service** (`llm_provider.py`)
   - `PROVIDERS` dict with 5 providers: Anthropic, DeepSeek, Groq, Together AI, Qwen
   - `PROVIDER_MODELS` dict with models per provider
   - `MultiProviderLLM` class with unified `chat()` and `chat_stream()` methods
   - Tool format conversion between Anthropic and OpenAI formats
   - Anthropic uses native SDK, others use OpenAI SDK with different base URLs

2. **Backend API Endpoints** (modified `chat.py`)
   - `GET /api/v1/chat/providers` - List available providers with status
   - `GET /api/v1/chat/models?provider=X` - Get models for a provider
   - Modified `ChatRequest` to accept `provider` field
   - Modified `send_message` to use `MultiProviderLLM`

3. **Frontend Provider State** (modified `chat.js`)
   - `selectedProvider` ref with localStorage persistence
   - `availableProviders` ref
   - `fetchProviders()` action
   - `setProvider()` action that refreshes models
   - `sendMessage()` now includes provider

4. **Frontend Provider Selector UI** (modified `ChatView.vue`)
   - Provider dropdown appears in sidebar when `devMode` is active
   - Shows provider availability (no key = disabled)
   - Displays "Uses your BYOK key" for Anthropic, "Uses platform API key" for others

### Provider Details

| Provider | Base URL | Env Var |
|----------|----------|---------|
| Anthropic | native SDK | `ANTHROPIC_API_KEY` (BYOK) |
| DeepSeek | `https://api.deepseek.com` | `DEEPSEEK_API_KEY` |
| Groq | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` |
| Together | `https://api.together.xyz/v1` | `TOGETHER_API_KEY` |
| Qwen | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | `DASHSCOPE_API_KEY` |

### Files Created/Modified

**Backend:**
- `app/services/llm_provider.py` - NEW: Multi-provider LLM service
- `app/api/v1/chat.py` - MODIFIED: Added provider endpoints
- `app/main.py` - MODIFIED: Updated build version

**Frontend:**
- `src/stores/chat.js` - MODIFIED: Added provider state
- `src/views/ChatView.vue` - MODIFIED: Added provider selector

---

## Feature Status: 46 Tools + 24 Features

| Feature | Status |
|---------|--------|
| Multi-Provider LLM | Dev Mode Only |
| Village GUI | Production |
| Neo-Cortex | Production |
| Tool System | Production |

---

## How to Enable Providers

1. **Dev Mode**: Activate via Konami code (↑↑↓↓←→←→BA) or 7-tap on Au logo
2. **Provider dropdown** appears in sidebar above model selector
3. **Add API keys** to Railway environment for other providers:
   ```
   DEEPSEEK_API_KEY=sk-...
   GROQ_API_KEY=gsk_...
   TOGETHER_API_KEY=...
   DASHSCOPE_API_KEY=sk-...
   ```

---

## Quick Verification

```bash
# Backend health
curl https://backend-production-507c.up.railway.app/health | jq '{build, features: .features[-5:]}'

# List providers
curl https://backend-production-507c.up.railway.app/api/v1/chat/providers | jq

# List models for a provider
curl "https://backend-production-507c.up.railway.app/api/v1/chat/models?provider=groq" | jq

# Frontend
open https://frontend-production-5402.up.railway.app
```

---

## Railway Services

| Service | Domain |
|---------|--------|
| Backend | backend-production-507c.up.railway.app |
| Frontend | frontend-production-5402.up.railway.app |

**Token:** `90fb849e-af7b-4ea5-8474-d57d8802a368`

---

## Architecture Summary

```
Frontend (ChatView.vue)
├── Provider Selector (devMode only)
├── Model Selector (per provider)
└── sends { provider, model, message }

Backend (chat.py)
├── GET /providers → list with availability
├── GET /models?provider= → models for provider
└── POST /message → uses MultiProviderLLM

MultiProviderLLM (llm_provider.py)
├── anthropic → Anthropic SDK (native)
└── others → OpenAI SDK (different base_url)
```

---

## Previous Session: Village GUI

The Village GUI with isometric 3D, WebGL fallback, and polish features remains fully functional. See previous commits for details.

---

## Key Commits

```
[PENDING] Multi-Provider LLM Support (dev mode feature)
85ae6b0 Add WebGL error handling with auto-fallback to 2D
b4fb4ed Fix 3D rendering + agent max_tokens errors
2f97418 Village Phase 1: Canvas-Based GUI Visualization
8af71ea Village Phase 0: WebSocket Infrastructure
```

---

*"The Athanor accepts many flames. Each provider, a different path to transmutation."*
