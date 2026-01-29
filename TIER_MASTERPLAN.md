# Tier Restructure Masterplan

## Vision
Four alchemical agents. Four tiers. From Seeker to Azothic -- a progression that mirrors the alchemical journey.

## Current State (v103)
3 tiers: Seeker $3/mo (50 msgs, Haiku) | Alchemist $10/mo (1000 msgs, Haiku+Sonnet) | Adept $30/mo (Unlimited, All models)

**Problems with current tiers:**
- $3 Seeker is too cheap to sustain (margin exists but very little value delivered)
- Adept at $30 with "unlimited" is dangerous -- heavy Opus users cost $90+/1000 msgs
- No per-feature limits (Suno, Council, Nursery all unlimited for Adept)
- No per-model message tracking (can't enforce Opus limits)
- No credit/pack system for compute-heavy features
- Missing: free trial, usage dashboard, legal disclaimers

---

## New Tier Map

### Free Trial (no subscription)
- 7 days, 20 messages total
- Haiku only, 1 agent
- No tools, no Council, no Music, no Nursery
- Purpose: let people feel the Athanor before committing
- Auto-expires, prompts upgrade

### Tier 1: Seeker Alchemist ($10/mo)
- **Messages:** 200/mo
- **Models:** Haiku + Sonnet (no Opus)
- **Context:** 128K cap (all models/providers)
- **Agents:** All 4 agents
- **Council:** 3 sessions/mo, max 10 rounds each
- **Music:** 10 Suno generations/mo
- **Village Band:** No jam sessions
- **Nursery:** No access
- **PAC Mode:** No
- **Dev Mode:** No
- **BYOK:** No
- **Storage:** 100MB vault
- **Credit Packs:** Not available
- **Estimated cost/user:** $1-4

### Tier 2: Adept Alchemist ($30/mo)
- **Messages:** 1,000/mo
- **Opus messages:** 50/mo (subset of total)
- **Models:** All including Opus (limited)
- **Context:** Full model context limits
- **Agents:** All 4 agents
- **Council:** 10 sessions/mo, max 50 rounds each
- **Music:** 50 Suno generations/mo
- **Village Band:** 3 jam sessions/mo
- **Nursery:** View-only tease (Data Garden browse, no training)
- **PAC Mode:** Limited (Haiku-only PAC)
- **Dev Mode:** No
- **BYOK:** OSS providers only (Together, Groq, DeepSeek, Qwen, Moonshot)
- **Storage:** 1GB vault
- **Credit Packs:** Available for purchase
- **Estimated cost/user:** $5-20

### Tier 3: Opus Alchemist ($100/mo)
- **Messages:** 5,000/mo
- **Opus messages:** 500/mo
- **Models:** All + Legacy models
- **Context:** Full + 1M beta (where available)
- **Agents:** All 4 agents
- **Council:** Unlimited sessions, max 200 rounds
- **Music:** 200 Suno generations/mo
- **Village Band:** 20 jam sessions/mo
- **Nursery:** Full access (Data Garden + Training Forge + Model Cradle + Apprentices)
- **PAC Mode:** Full
- **Dev Mode:** Yes
- **BYOK:** All providers
- **Storage:** 5GB vault
- **Credit Packs:** Available at discount (20% off)
- **Estimated cost/user:** $20-60

### Tier 4: Azothic Alchemist ($300/mo)
- **Messages:** 20,000/mo
- **Opus messages:** 2,000/mo
- **Models:** All + Legacy + Priority routing
- **Context:** Full + 1M
- **Agents:** All 4 agents
- **Council:** Unlimited, unlimited rounds
- **Music:** 500 Suno generations/mo
- **Village Band:** Unlimited
- **Nursery:** Full + monthly training credits (5 jobs included)
- **PAC Mode:** Full
- **Dev Mode:** Yes
- **BYOK:** All providers
- **Storage:** 20GB vault
- **Credit Packs:** Monthly credit allowance included
- **Estimated cost/user:** $50-150

---

## Credit Packs

Available to Adept+ tiers. Purchased via Stripe one-time payments.

| Pack | Price | Contents |
|------|-------|----------|
| Spark | $5 | 50 Opus msgs OR 20 Suno gens OR 2 training jobs |
| Flame | $15 | 150 Opus msgs + 50 Suno gens + 5 training jobs |
| Inferno | $40 | 500 Opus msgs + 200 Suno gens + 15 training jobs |

Credits don't expire within the billing cycle. Unused credits roll over once (max 1 month).

---

## Coupon Library

### Beta Launch Coupons
| Code | Type | Value | Purpose |
|------|------|-------|---------|
| BETA_SEEKER | tier_upgrade | 30 days Seeker | Beta tester welcome |
| COUNCIL_TRIAL | tier_upgrade | 7 days Adept + 5 council sessions | Feature showcase |
| MUSIC_MAKER | tier_upgrade | 14 days Adept + 50 Suno gens | Music feature promo |
| NURSERY_PASS | tier_upgrade | 7 days Opus | Nursery access trial |
| FIRST_FLAME | credit_bonus | 1x Flame Pack | Early adopter bonus |

### Competition/Giveaway Coupons
| Code | Type | Value | Purpose |
|------|------|-------|---------|
| AZOTHIC_MONTH | tier_upgrade | 30 days Azothic | Grand prize |
| OPUS_WEEK | tier_upgrade | 7 days Opus | Runner-up prize |
| INFERNO_DROP | credit_bonus | 1x Inferno Pack | Feature competition |

### Referral Coupons (future)
| Code | Type | Value | Purpose |
|------|------|-------|---------|
| REFER_SPARK | credit_bonus | 1x Spark Pack | Referrer + referred both get |

---

## Usage Tracking Requirements

### Per-Feature Counters (new DB table: `usage_counters`)
| Counter | Scope | Reset | Current State |
|---------|-------|-------|---------------|
| messages_haiku | per-user, per-month | Monthly | Partial (total only, no per-model) |
| messages_sonnet | per-user, per-month | Monthly | Not tracked |
| messages_opus | per-user, per-month | Monthly | Not tracked |
| suno_generations | per-user, per-month | Monthly | Not tracked (count exists in music_tasks) |
| council_sessions | per-user, per-month | Monthly | Not tracked (count exists in DB) |
| council_rounds | per-user, per-month | Monthly | Not tracked |
| jam_sessions | per-user, per-month | Monthly | Not tracked |
| nursery_training_jobs | per-user, per-month | Monthly | Not tracked (count exists in DB) |
| vault_storage_bytes | per-user, cumulative | Never | Not tracked (files exist but no sum) |
| context_tokens_used | per-user, per-month | Monthly | Not tracked |

### What Already Exists
- `message_counts` table: tracks total messages per user per month (not per-model)
- Music tasks: `MusicTask` has user_id and created_at (can count)
- Council: `DeliberationSession` has user_id (can count)
- Jam: `JamSession` has user_id (can count)
- Nursery: `NurseryTrainingJob` has user_id (can count)
- Vault: files have user_id and size (can sum)

### What Needs Building
- Per-model message counter (split current counter by model family)
- Monthly usage_counters table with atomic increment
- Usage check middleware (before each API call, check limit)
- Usage dashboard API endpoint (GET /api/v1/usage)
- Frontend usage display (billing page or new dashboard)

---

## Legal Requirements

### Beta Disclaimer (footer + registration)
- "ApexAurum is experimental beta software"
- "No warranty expressed or implied"
- "Service may be interrupted, modified, or discontinued"
- "Data may be lost -- export your important data regularly"

### Terms of Service Page (/terms)
- Acceptable use policy
- No illegal content generation
- No automated abuse / API scraping
- Rate limits and fair use
- Account termination rights
- Limitation of liability
- Norwegian law jurisdiction

### Privacy Policy Page (/privacy)
- What data is collected (email, chat content, API keys)
- How API keys are stored (Fernet encryption at rest)
- Chat content retention policy
- Neural memory data handling
- Third-party services (Anthropic, Together.ai, Suno, Stripe)
- Right to deletion (GDPR)
- No selling of data

### Cookie/Consent
- JWT tokens in localStorage (not cookies -- simpler)
- Registration = consent to terms
- Terms link on registration form

---

## Implementation Roadmap

### Session A: Usage Infrastructure
**Scope:** Per-model counters, usage_counters table, limit checking middleware
- New `UsageCounter` model (user_id, counter_type, period, count, limit)
- Atomic increment function: `increment_usage(user_id, counter_type)`
- Check function: `check_usage_limit(user_id, counter_type)` -> bool
- Split chat message counting by model family (Haiku/Sonnet/Opus)
- Context limit enforcement in chat endpoint (128K cap for Seeker)
- Monthly reset cron or lazy-reset on first access

### Session B: Tier Restructure
**Scope:** 4-tier config, Stripe products, billing UI, landing page
- New `TIER_LIMITS` config with all per-feature limits
- 4 new Stripe subscription products ($10/$30/$100/$300)
- Updated billing page with 4-tier display
- Updated landing page pricing section
- Feature gate updates across all endpoints
- Free trial flow (7-day, 20 messages, auto-expire)
- Migration plan for existing subscribers

### Session C: Credit Packs + Usage Dashboard
**Scope:** Pack purchase flow, usage display, pack management
- 3 Stripe one-time payment products (Spark/Flame/Inferno)
- Credit balance tracking per feature type
- Pack redemption logic (add credits to counters)
- Usage dashboard API: GET /api/v1/usage (all counters + limits + %)
- Frontend usage display in billing page (progress bars, warnings at 80%)
- Pack purchase UI in billing page
- Admin: view user usage in admin panel

### Session D: Legal + Polish
**Scope:** Terms, privacy, disclaimers, coupon library, final polish
- Terms of Service page (/terms)
- Privacy Policy page (/privacy)
- Beta disclaimer in footer + registration
- Registration: checkbox for terms acceptance
- Coupon library: pre-create beta launch coupons
- Package builder UI (optional -- select features, see price)
- Usage warning emails (at 80% and 100% of limits)
- Admin: usage reports, tier breakdown, revenue tracking

---

## Migration Plan (Existing Users)

| Current Tier | New Tier | Action |
|---|---|---|
| Seeker ($3) | Seeker ($10) | Grandfather at $3 for 3 months, then auto-upgrade price |
| Alchemist ($10) | Seeker ($10) | Same price, adjusted limits |
| Adept ($30) | Adept ($30) | Same price, limits now enforced (was "unlimited") |
| No subscription | Free trial | 7-day trial on first visit |

Grandfathering: Early beta users who signed up at $3 keep that price for 90 days. Coupon "BETA_GRANDFATHER" auto-applied.

---

## API Cost Calculations

### Per-Message Costs (avg 2K tokens in, 1K tokens out)
- Haiku: $0.002/msg
- Sonnet: $0.021/msg
- Opus: $0.090/msg

### Per-Feature Costs
- Suno generation: ~$0.05/song
- Council round (4 agents, Haiku): ~$0.008/round
- Council round (4 agents, Sonnet): ~$0.084/round
- Council round (4 agents, Opus): ~$0.360/round
- Together.ai training (1B model, 50 examples, 3 epochs): ~$0.50
- Together.ai training (8B model, 500 examples, 3 epochs): ~$5.00

### Monthly Cost per Tier (estimated average user)
| Tier | Est. Usage | Est. Cost | Revenue | Margin |
|------|-----------|-----------|---------|--------|
| Seeker ($10) | 150 Haiku + 30 Sonnet + 5 Suno | $1.18 | $10 | 88% |
| Adept ($30) | 500 Haiku + 300 Sonnet + 30 Opus + 30 Suno + 5 councils | $12.50 | $30 | 58% |
| Opus ($100) | 1000 Haiku + 2000 Sonnet + 300 Opus + 100 Suno + 3 training | $76 | $100 | 24% |
| Azothic ($300) | 2000 Haiku + 5000 Sonnet + 1000 Opus + 200 Suno + 10 training | $210 | $300 | 30% |

Note: Heavy Opus users at Azothic could exceed cost. The hard limit of 2000 Opus/mo caps cost at ~$180 for Opus alone. Total worst case ~$280 -- still profitable at $300.

---

*"Four agents. Four tiers. The furnace scales with the alchemist's ambition."*
