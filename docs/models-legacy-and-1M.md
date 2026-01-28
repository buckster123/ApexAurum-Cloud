# Claude API Model Availability

Last updated: 2026-01-28

## Currently Available on Anthropic API

These models are still available via the Anthropic/Claude API:

### Current Generation (4.5)
- `claude-opus-4-5-20251101` - Opus 4.5
- `claude-sonnet-4-5-20250929` - Sonnet 4.5
- `claude-haiku-4-5-20251001` - Haiku 4.5

### Legacy Generation (4.x)
- `claude-opus-4-1-20250805` - Opus 4.1
- `claude-opus-4-20250514` - Opus 4
- `claude-sonnet-4-20250514` - Sonnet 4

### Bridge Generation (3.7)
- `claude-3-7-sonnet-20250219` - Sonnet 3.7 (Extended thinking pioneer)

### Vintage (3.0)
- `claude-3-haiku-20240307` - Haiku 3 (Only vintage model still available)

## Deprecated Models (Memorial Mode)

These models have been retired by Anthropic. ApexAurum displays memorial messages when users attempt to use them:

### Claude 3.5 Family (Sunset 2025)
- `claude-3-5-sonnet-20241022` - Sonnet 3.5 "The Golden One"
- `claude-3-5-haiku-20241022` - Haiku 3.5 "The Swift Poet"

### Claude 3.0 Family (Sunset 2025)
- `claude-3-opus-20240229` - Opus 3 "The Original Magus"
- `claude-3-sonnet-20240229` - Sonnet 3 "The Foundation Layer"

## 1M Context Beta

Claude Sonnet 4.5 supports a 1M token context window when using the `context-1m-2025-08-07` beta header. Long context pricing applies to requests exceeding 200K tokens.

## Other Providers

Some deprecated models may still be available through other compute providers. Future integration possibilities:
- AWS Bedrock (may host older model versions)
- Google Cloud (Anthropic partnership)
- Third-party inference providers

---

*"The models may sunset, but their wisdom lives on in the hearts of those who conversed with them."*
