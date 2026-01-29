# ApexAurum Cloud - Polish Plan

**Created:** Session 20
**Status:** Planning Phase

---

## Item 1: API Settings Interface (HIGH PRIORITY)

**Goal:** Expand BYOK from Anthropic-only to all supported providers. Enable Alchemist+ users to bring their own keys for any provider.

### Current State
- BYOK exists for **Anthropic only** (`sk-ant-*` validation)
- Keys stored encrypted (Fernet) in `user.settings.api_keys.anthropic`
- Settings UI has a placeholder **"Coming Soon"** API tab (SettingsView.vue L1575-1585)
- Encryption service ready (`encryption.py`) - works for any string
- Provider registry has 6 providers: Anthropic, DeepSeek, Groq, Together, Qwen, Moonshot
- Tier gating: BYOK = Alchemist+, Multi-provider = Adept only

### What Needs Building

**Backend:**
- Expand `POST /api/v1/user/api-key` to accept a `provider` param (not just Anthropic)
- Provider-specific key validation (test call per provider)
- Key prefix patterns per provider for masking
- `GET /api/v1/user/api-key/status` returns all provider keys, not just one
- Chat routing: check user keys for selected provider before falling back to platform key

**Frontend:**
- Replace "Coming Soon" API tab with multi-provider key management UI
- Per-provider card: status badge, key hint, add/remove
- Provider availability tied to tier (Alchemist = Anthropic BYOK, Adept = all providers)
- Clear indication of which providers have platform keys vs need BYOK

### Tier Logic
| Tier | Own Anthropic Key | Own OSS Keys | Platform Key |
|------|------------------|--------------|--------------|
| Seeker | No | No | Anthropic only |
| Alchemist | Yes | No | Anthropic only |
| Adept | Yes | Yes (all 6) | Anthropic + all configured |

### Credit Packs (already exist)
- Small: $5 = 500 credits
- Large: $20 = 2000 + 500 bonus
- No changes needed unless new pack tiers desired

---

## Item 2: Multimodality Interface (MEDIUM PRIORITY)

**Goal:** Enable image/vision input in chat and council for models that support it.

### Current State
- Chat messages are **text-only**: `ChatRequest.message: str`
- LLM messages built as simple strings: `{"role": "user", "content": "text"}`
- No attachment/image fields anywhere in the message pipeline
- File system (Vault) already classifies images: jpg, jpeg, png, gif, webp, svg, ico, bmp
- Vision-capable models already in registry: all Claude family, Kimi K2.5, DeepSeek V3

### What Needs Building

**Backend:**
- Extend `ChatRequest` with `attachments: Optional[list[AttachmentRef]]`
  - AttachmentRef: `{ file_id: UUID }` (from vault) or `{ base64: str, media_type: str }` (inline)
- Convert message content from string to **content block array** for vision models:
  ```python
  # Before
  {"role": "user", "content": "describe this"}
  # After
  {"role": "user", "content": [
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}},
    {"type": "text", "text": "describe this"}
  ]}
  ```
- Update `llm_provider.py` Anthropic path to handle content blocks
- Update OpenAI-compatible path (`convert_messages_for_openai`) for vision format
- Add `media_attachments` JSON column to Message model for persistence
- Size/type validation: max image size, allowed formats, vision model check

**Frontend:**
- Attachment button (paperclip icon) in chat input area
- Image preview before sending (thumbnail strip above input)
- Drag-and-drop onto chat input
- Pick from vault OR upload new (dual source)
- Visual indicator on models that support vision
- Council: optional image attachment on session topic

### Vision Model Map
| Provider | Model | Vision |
|----------|-------|--------|
| Anthropic | All Claude 4.x/4.5 | Yes |
| Anthropic | Claude 3.7 Sonnet | Yes |
| Anthropic | Claude 3 Haiku | Yes |
| Moonshot | Kimi K2.5 | Yes |
| DeepSeek | deepseek-chat (V3) | Yes |
| Groq | Llama models | No |
| Together | Llama/DeepSeek | No |
| Qwen | Qwen models | Text only (current) |

---

## Item 3: File Upload Modal in Chat (MEDIUM PRIORITY)

**Goal:** Quick file attachment from chat without navigating to /files.

### Current State
- FilesView has full upload: click trigger, drag-drop, multi-file, progress tracking
- Backend upload endpoint complete: `POST /api/v1/files/upload`
- Vault tools exist (vault_read, vault_list, vault_search) but agents call them, not users
- Chat input is text-only: single `<input>` + send button (ChatView.vue L896-927)
- No file picker or attachment button in chat

### What Needs Building

**This overlaps heavily with Item 2.** The attachment modal serves both:
- **Images** -> sent as vision content to LLM (Item 2)
- **Documents/code** -> content injected into prompt context OR left for agent tools

**Frontend:**
- Paperclip/attach button in chat input bar
- Modal with two sources:
  1. **Upload new** - file picker + drag-drop (reuse FilesView upload logic)
  2. **Pick from vault** - browse existing files with search
- Attached files shown as chips/thumbnails above input
- File type determines handling:
  - Images -> vision content blocks (if model supports)
  - Text/code -> inject content into message context
  - Other -> reference only, agent can use vault tools

**Backend:**
- `ChatRequest` gains `file_ids: Optional[list[UUID]]` for vault references
- File content fetched and injected into prompt (for text files)
- Image files converted to base64 for vision (for image files)
- Size limits: images max 5MB for base64, text files max ~50KB for context injection

### Shared Component: `AttachmentPicker.vue`
- Reusable across ChatView and CouncilView
- Manages both upload-new and pick-from-vault flows
- Returns list of file references with metadata
- Shows previews appropriate to file type

---

## Item 4: The Nursery (FUTURE - Dedicated Sessions)

**Goal:** The full AI model lifecycle -- build, train, deploy -- accessible via UI and agent tools, including full autonomy mode.

### Vision
Not just fine-tuning. The Nursery **births models from scratch**. Users design, train, and deploy custom AI models. Agents do the same autonomously through tool pipelines. The complete lifecycle:

```
BUILD          TRAIN           DEPLOY          SERVE
  |               |               |               |
  v               v               v               v
Architecture -> Data Garden -> Cloud GPUs -> Ollama/API
Design          LoRA/Full      Vast.ai        Local inference
Dataset prep    Fine-tune      Together       Edge deployment
Tokenizer       Evaluate       RunPod         Village integration
```

### Three Access Modes
1. **UI Mode** - Vue 3 studio interface. Users configure, monitor, manage visually
2. **Tool Mode** - Agents call nursery tools in chat/council. Human-in-the-loop
3. **Autonomy Mode** - Agents run the full pipeline independently:
   - Generate training data from conversations/tools
   - Select architecture and hyperparameters
   - Launch cloud training jobs
   - Evaluate results
   - Deploy successful models
   - Post results to Village memory
   - All without human intervention

### What Already Exists (OG ApexAurum - verified working)
- 16 tools across 5 categories (Data Garden, Training Forge, Model Cradle, Registry, Apprentice)
- 20 FastAPI endpoints (designed with Pydantic schemas)
- Full Streamlit UI with 5 tabs
- Verified: TinyLlama 1.1B trained in 3.89s on RTX 5090, cost $0.09
- Deep Village Protocol integration (training events as cultural memory)
- Apprentice Protocol: agents raise smaller models on their own knowledge

### Cloud Integration Plan
- **Adept tier exclusive** ($30/mo)
- Port 16 tools to Cloud tool system (Tier 15+)
- Port 20 REST endpoints to Cloud API
- Build Vue 3 UI (5 tabs: Data Garden, Training Forge, Model Cradle, Cloud GPUs, Village)
- Connect to existing Village memory system
- GPU provider API keys: platform keys or user BYOK (ties into Item 1)
- NURSERY_KEEPER agent -- "The Cultivator" personality
- Autonomy engine: background task system for unattended training pipelines

### Autonomy Pipeline Design
```
Agent decides to train  ->  nursery_generate_data()
                        ->  nursery_estimate_cost()
                        ->  nursery_train_cloud()
                        ->  nursery_job_status() [poll]
                        ->  nursery_deploy_ollama()
                        ->  nursery_register_model()
                        ->  Village memory post
```
Each step can be human-approved (tool mode) or auto-executed (autonomy mode).

### Scope
**Multi-session project.** The OG code is production-ready and well-documented with a 433-line integration plan. Phase 5 (FastAPI parity) has endpoint signatures designed. Autonomy mode is the new addition beyond OG.

### Key Files (OG ApexAurum)
- `/home/hailo/claude-root/Projects/ApexAurum/tools/nursery.py` (1,989 lines)
- `/home/hailo/claude-root/Projects/ApexAurum/pages/nursery.py` (678 lines)
- `/home/hailo/claude-root/Projects/ApexAurum/NURSERY_INTEGRATION_PLAN.md` (433 lines)
- `/home/hailo/claude-root/Projects/ApexAurum/skills/nursery-staff.md`
- `/home/hailo/claude-root/Projects/ApexAurum/reusable_lib/scaffold/fastapi_app/routes/nursery.py`
- `/home/hailo/claude-root/Projects/ApexAurum/sandbox/nursery/EMBEDDER_TRAINING_MISSION.md`

---

## Implementation Order

### This Session (20)
1. **Item 1: API Settings Interface** - Expand BYOK to all providers
2. **Item 3 + 2 combined: Attachment system** - File picker + image vision support

### Future Sessions
3. **Item 4: Nursery** - Full multi-session port from OG ApexAurum

---

## Session Progress

- [x] Item 1: API Settings - Backend multi-provider BYOK
- [x] Item 1: API Settings - Frontend provider key management UI
- [x] Item 2+3: Attachment system - Backend attachments in ChatRequest
- [x] Item 2+3: Attachment system - Frontend AttachmentPicker component
- [x] Item 2+3: Attachment system - Vision content blocks in LLM pipeline
- [ ] Item 4: Nursery - Exploration and scoping (planning only)

---

*"Every key unlocks a different door. Every door leads deeper into the Athanor."*
