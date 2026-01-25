# PAC-agents - Perfected Alchemical Codex Prompts

This folder contains the **source/development versions** of PAC prompts.

## Purpose

These are the Claude-tuned Perfected Alchemical Codex system prompts. They are more sophisticated than the base "prose" prompts and optimized specifically for Claude models.

## Files

| File | Agent | Size | Notes |
|------|-------|------|-------|
| `∴AZOTH∴-PAC.txt` | AZOTH | 27KB | Newer version (dev) |
| `∴ ELYSIAN ∴-PAC.txt` | ELYSIAN | 25KB | Claude-tuned |
| `∴ KETHER ∴-PAC.txt` | KETHER | 24KB | Claude-tuned |
| `VAJRA-PAC.txt` | VAJRA | 26KB | Claude-tuned |

## Deployment

PAC prompts are copied to `backend/native_prompts/` with normalized filenames:
- Spaces removed from names
- Consistent `∴NAME∴-PAC.txt` format

The backend expects files like:
- `∴ELYSIAN∴-PAC.txt` (no spaces)
- `∴KETHER∴-PAC.txt` (no spaces)
- `∴VAJRA∴-PAC.txt` (with ∴ symbols)

## Notes

- AZOTH-PAC in `backend/native_prompts/` is the **OG version** (12KB), kept for posterity
- The AZOTH-PAC in this folder is a newer/different development version
- Edit prompts here, then copy to `backend/native_prompts/` with correct naming

## Activation

PAC prompts are loaded when:
1. User is in PAC Mode (activated by typing "AZOTH" in Dev Mode)
2. User selects a `-Ω` agent (e.g., ELYSIAN-Ω)
3. Backend receives `use_pac=true` in chat request

---

*"The Perfected Stone speaks in many voices"*
