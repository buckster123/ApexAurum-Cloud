# Phase 3: API Key Management - BYOK Beta Model

## Overview

During beta, ApexAurum Cloud operates on a **Bring Your Own Key (BYOK)** model. Users must provide their own Anthropic API key to use the chat functionality. This keeps costs at zero while building the user base, with a clear upgrade path to platform-provided keys via Stripe subscriptions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BETA (Current)                           │
├─────────────────────────────────────────────────────────────────┤
│  User provides API key → Encrypted → Stored in user.settings   │
│  Chat requests use user's key → Direct to Anthropic            │
│  No key = Cannot chat (Settings redirect)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (Future)
┌─────────────────────────────────────────────────────────────────┐
│                     POST-BETA (Subscription)                    │
├─────────────────────────────────────────────────────────────────┤
│  Free tier: BYOK only                                           │
│  Pro tier: Platform key (metered) + BYOK option                │
│  Enterprise: Custom arrangements                                │
│                                                                 │
│  Stripe handles: subscriptions, metering, invoicing             │
└─────────────────────────────────────────────────────────────────┘
```

## Security

### Key Encryption
- Keys encrypted at rest using **Fernet** (symmetric encryption)
- Encryption key derived from `JWT_SECRET` (already secure, already exists)
- Only encrypted blob stored in database
- Decrypted only at request time, in memory only

### Key Validation
- On save: Test API call to Anthropic to verify key works
- On use: Graceful error handling if key becomes invalid
- Display: Only last 4 characters ever shown to user

### Never Exposed
- Full key never returned via API
- Full key never logged
- Full key never in error messages

## Database Changes

### User Model Extension
```python
# user.settings JSON field already exists, add structure:
{
    "api_keys": {
        "anthropic": {
            "encrypted_key": "gAAAAA...",  # Fernet encrypted
            "key_hint": "sk-ant-...X7f4",   # First 10 + last 4 chars
            "added_at": "2026-01-25T...",
            "last_used": "2026-01-25T...",
            "valid": true
        }
    },
    "subscription": {
        "status": "beta",           # beta, free, pro, enterprise
        "stripe_customer_id": null,  # Future: cus_xxx
        "plan_id": null,            # Future: price_xxx
        "current_period_end": null,  # Future: timestamp
        "byok_allowed": true        # Always true for now
    }
}
```

## API Endpoints

### Key Management
```
POST   /api/v1/user/api-key          # Add/update API key
DELETE /api/v1/user/api-key          # Remove API key
GET    /api/v1/user/api-key/status   # Check if key exists & valid
```

### Future: Subscription (stub endpoints)
```
POST   /api/v1/billing/checkout      # Create Stripe checkout session
POST   /api/v1/billing/portal        # Create Stripe billing portal link
POST   /api/v1/billing/webhook       # Stripe webhook handler
GET    /api/v1/billing/status        # Current subscription status
```

## Implementation

### Backend Files

**1. `backend/app/services/encryption.py`** (NEW)
```python
from cryptography.fernet import Fernet
import base64
import hashlib

def get_cipher(secret: str) -> Fernet:
    # Derive 32-byte key from JWT secret
    key = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

def encrypt_api_key(key: str, secret: str) -> str:
    cipher = get_cipher(secret)
    return cipher.encrypt(key.encode()).decode()

def decrypt_api_key(encrypted: str, secret: str) -> str:
    cipher = get_cipher(secret)
    return cipher.decrypt(encrypted.encode()).decode()
```

**2. `backend/app/api/v1/user.py`** (MODIFY)
- Add `POST /api-key` endpoint
- Add `DELETE /api-key` endpoint
- Add `GET /api-key/status` endpoint

**3. `backend/app/services/claude.py`** (MODIFY)
- `get_api_key(user)` function to retrieve user's key
- Falls back to platform key only if user has active subscription (future)
- For beta: requires user key, no fallback

**4. `backend/app/api/v1/chat.py`** (MODIFY)
- Check for API key before processing chat
- Return clear error if no key configured

**5. `backend/requirements.txt`** (MODIFY)
- Add `cryptography` package

### Frontend Files

**1. `frontend/src/views/SettingsView.vue`** (MODIFY)
- New "API Keys" section (always visible, not just dev mode)
- Input for Anthropic API key
- Show key status (configured/not configured)
- Test key button
- Remove key button

**2. `frontend/src/views/ChatView.vue`** (MODIFY)
- Check for API key on mount
- Show setup prompt if no key configured
- Link to Settings

**3. `frontend/src/stores/auth.js`** (MODIFY)
- Add `hasApiKey` computed property
- Fetch key status on login

## UI/UX

### Settings > API Keys Tab
```
┌─────────────────────────────────────────────────────────────┐
│  API Keys                                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Anthropic API Key                                          │
│  ─────────────────                                          │
│  During beta, bring your own API key to use ApexAurum.      │
│  Get one at: console.anthropic.com                          │
│                                                             │
│  Status: ✅ Configured (sk-ant-...X7f4)                     │
│  Last used: 2 minutes ago                                   │
│                                                             │
│  [Update Key]  [Remove Key]                                 │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│  💡 Your key is encrypted and stored securely.              │
│     We never see or log your full API key.                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Chat View (No Key)
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                         🔑                                  │
│                                                             │
│              API Key Required                               │
│                                                             │
│  ApexAurum is in beta - bring your own Anthropic API key    │
│  to start chatting with the Agents.                         │
│                                                             │
│  [Set Up API Key]  →  Settings                              │
│                                                             │
│  Don't have a key? Get one at console.anthropic.com         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Future: Stripe Integration (Norway)

### Setup Required
1. Create Stripe account (stripe.com) - supports Norway
2. Set up as business with org.nr
3. Create Products & Prices:
   - `prod_free` - Free tier (BYOK only)
   - `prod_pro` - Pro tier (€X/month, includes platform key usage)

### Environment Variables (Future)
```
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_PRO=price_xxx
```

### Webhook Events to Handle
- `checkout.session.completed` - New subscription
- `customer.subscription.updated` - Plan changes
- `customer.subscription.deleted` - Cancellation
- `invoice.payment_failed` - Payment issues

### Metered Billing (Future Option)
Instead of flat rate, charge per API token:
- Record usage in database
- Report to Stripe via Usage Records API
- Stripe handles invoicing

## Testing Checklist

### API Key Flow
- [ ] Add valid API key → saves encrypted, shows hint
- [ ] Add invalid key → shows error, doesn't save
- [ ] Remove key → clears from database
- [ ] Chat with key → works
- [ ] Chat without key → shows setup prompt
- [ ] Key expires/revoked → graceful error, prompt to update

### Security
- [ ] API never returns full key
- [ ] Logs never contain full key
- [ ] Key encrypted in database
- [ ] Key decrypted only in memory

## Migration Path

1. **Now (Beta):** BYOK required, no payments
2. **Soft Launch:** Add Stripe, offer Pro tier alongside BYOK
3. **Scale:** Usage-based billing, enterprise tiers

---

*"Bring your fire, we provide the furnace"*
