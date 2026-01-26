# The Athanor's Hands - Grand Masterplan

**"Every alchemist needs hands to work the Great Work"**

This document tracks the complete tool system implementation for ApexAurum Cloud.
Each tool gives Claude's agents the ability to interact with the world.

---

## Progress Overview

| Tier | Name | Tools | Status |
|------|------|-------|--------|
| 1 | Utilities | 6 | ✅ COMPLETE |
| 2 | Web | 2 | ✅ COMPLETE |
| 3 | Vault | 5 | ✅ COMPLETE |
| 4 | Knowledge Base | 4 | ✅ COMPLETE |
| 5 | Session Memory | 4 | ✅ COMPLETE |
| 6 | Code Execution | 2 | ✅ COMPLETE |
| 7 | Agents | 3 | ✅ COMPLETE |
| **Total** | | **26** | **26/26 ✅** |

---

## Tier 1: Utilities (The Simple Hands) ✅

**Status:** COMPLETE - Deployed v28-athanors-hands

Basic stateless tools that require no external services.

| Tool | Description | Status |
|------|-------------|--------|
| `get_current_time` | Current date/time in various formats | ✅ |
| `calculator` | Safe math expression evaluation | ✅ |
| `random_number` | Random integers or floats | ✅ |
| `count_words` | Text analysis (words, chars, sentences) | ✅ |
| `uuid_generate` | UUID v1/v4 generation | ✅ |
| `json_format` | Parse, validate, pretty-print JSON | ✅ |

**Files:**
- `backend/app/tools/base.py` - Base classes
- `backend/app/tools/utilities.py` - Tool implementations
- `backend/app/tools/__init__.py` - Registry

---

## Tier 2: Web Tools (The Reaching Hands) ✅

**Status:** COMPLETE - Deployed v29

Fetch content and search the web. Pure HTTP - no API keys needed.

| Tool | Description | Status |
|------|-------------|--------|
| `web_fetch` | Fetch content from any URL | ✅ |
| `web_search` | Search via DuckDuckGo Instant Answers | ✅ |

**Implementation Notes:**
- Use `httpx` (async) or `requests` for HTTP
- Rate limiting recommended
- Respect robots.txt for good citizenship
- Max content length: 50KB default
- Timeout: 30s default

**Source Reference:**
- `/home/hailo/claude-root/Projects/ApexAurum/tools/web.py`

---

## Tier 3: Vault Tools (The Crafting Hands) ✅

**Status:** COMPLETE - All 5 tools deployed v36

File operations mapped to existing Vault API. User-scoped, quota-enforced.

| Tool | Description | Maps To | Status |
|------|-------------|---------|--------|
| `vault_list` | List files in a folder | SQLAlchemy direct | ✅ |
| `vault_read` | Read file content | SQLAlchemy + filesystem | ✅ |
| `vault_write` | Write/update file | SQLAlchemy + filesystem | ✅ |
| `vault_search` | Search file contents | SQLAlchemy + filesystem | ✅ |
| `vault_info` | Get storage stats | SQLAlchemy direct | ✅ |

**Implementation Notes:**
- Requires authenticated user context
- All operations scoped to user's vault
- Respects file size and quota limits
- Text files only for read/write (security)

**Existing Backend:**
- `backend/app/api/v1/files.py` - Full CRUD already exists

---

## Tier 4: Knowledge Base (The Knowing Hands) ✅

**Status:** COMPLETE - Deployed v31

Bridge to MCP Knowledge Base or external KB service. Semantic search over docs.

| Tool | Description | MCP Equivalent | Status |
|------|-------------|----------------|--------|
| `kb_search` | Semantic search across KB | `kb_search` | ✅ |
| `kb_lookup` | Quick term/concept lookup | `kb_quick_lookup` | ✅ |
| `kb_topics` | List available topics | `kb_list_topics` | ✅ |
| `kb_answer` | Get context to answer questions | `kb_answer` | ✅ |

**Implementation Notes:**
- MCP server already running at localhost
- Bridge via HTTP to MCP or direct ChromaDB access
- Topics: railway, vue3, fastapi, stripe, mcp, langgraph, etc.

**MCP Reference:**
- Server: `apex-knowledge-base`
- Tools: `kb_search`, `kb_quick_lookup`, `kb_get_document`, etc.

---

## Tier 5: Session Memory (The Remembering Hands) ✅

**Status:** COMPLETE - Deployed v32

Per-conversation scratchpad for multi-step reasoning.

| Tool | Description | Status |
|------|-------------|--------|
| `scratch_store` | Store key-value in conversation | ✅ |
| `scratch_get` | Retrieve value by key | ✅ |
| `scratch_list` | List all keys in session | ✅ |
| `scratch_clear` | Clear all session data | ✅ |

**Implementation Notes:**
- Stored in conversation metadata (JSONB)
- Scoped to current conversation only
- Auto-cleared when conversation deleted
- Max 100 keys, 10KB per value

**Database:**
- Add `scratch_data JSONB` to conversations table
- Or use existing `metadata` field

---

## Tier 6: Code Execution (The Making Hands) ✅

**Status:** COMPLETE - Deployed v33

Execute Python code in sandboxed environment.

| Tool | Description | Status |
|------|-------------|--------|
| `code_run` | Execute Python code with output capture | ✅ |
| `code_eval` | Evaluate single expression | ✅ |

**Implementation Notes:**
- Map to existing `POST /files/{id}/execute`
- Supported: Python, JavaScript (Node), Shell/Bash
- Limits: 10s timeout, 100KB output
- Sandboxed subprocess execution

**Existing Backend:**
- `backend/app/api/v1/files.py` - `execute_file()` endpoint

---

## Tier 7: Agent Tools (The Spawning Hands) ✅

**Status:** COMPLETE - Deployed v34

Multi-agent capabilities - spawn sub-agents for complex tasks.

| Tool | Description | Status |
|------|-------------|--------|
| `agent_spawn` | Spawn background agent | ✅ |
| `agent_status` | Check agent progress | ✅ |
| `agent_result` | Get completed result | ✅ |

**Implementation Notes:**
- Async task queue (Redis/Celery or simple DB queue)
- Agent runs with own conversation context
- Returns task ID for polling
- Max concurrent agents per user: 3

**Future Enhancements:**
- `socratic_council` - Multi-agent debate
- `agent_delegate` - Hand off to specialist agent

---

---

# FUTURE TIERS - The Expanding Athanor

*"The Great Work never ends. New hands emerge from the crucible."*

## Progress Overview (Future)

| Tier | Name | Tools | Status | Priority |
|------|------|-------|--------|----------|
| 8 | Vector Search | 5 | ✅ COMPLETE | 🔴 HIGH |
| 9 | Music | 4 | ⬜ PLANNED | 🟡 MEDIUM |
| 10 | Browser | 5 | ⬜ PLANNED | 🟡 MEDIUM |
| 11 | Email | 4 | ⬜ PLANNED | 🟢 LOW |
| 12 | Calendar | 4 | ⬜ PLANNED | 🟢 LOW |
| 13 | Image | 4 | ⬜ PLANNED | 🟡 MEDIUM |
| **Future Total** | | **26** | | |

---

## Tier 8: Vector Search (The Remembering Deep) ✅

**Status:** COMPLETE - Deployed v37-vector-search
**Requires:** pgvector extension + OpenAI API key for embeddings

Semantic search over user content. Enables "remember this" and intelligent retrieval.

| Tool | Description | Status |
|------|-------------|--------|
| `vector_store` | Store text with embedding | ✅ |
| `vector_search` | Semantic similarity search | ✅ |
| `vector_delete` | Remove vectors by ID | ✅ |
| `vector_list` | List stored vectors | ✅ |
| `vector_stats` | Collection statistics | ✅ |

**Implementation Notes:**
- Use pgvector extension for PostgreSQL
- Embedding model: `text-embedding-3-small` (OpenAI) or local
- Dimension: 1536 (OpenAI) or 384 (local)
- Collections scoped per user
- Auto-embed on store, return with similarity score

**Database Schema:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE user_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    collection VARCHAR(100) DEFAULT 'default',
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_vectors_user ON user_vectors(user_id);
CREATE INDEX idx_vectors_collection ON user_vectors(user_id, collection);
CREATE INDEX idx_vectors_embedding ON user_vectors USING ivfflat (embedding vector_cosine_ops);
```

**Use Cases:**
- "Remember that I prefer Python over JavaScript"
- "What did we discuss about the API design?"
- "Find similar code to this function"
- Per-user semantic memory layer

**Dependencies:**
- OpenAI API key for embeddings (or local model)
- pgvector extension enabled

---

## Tier 9: Music (The Creative Hands) ⬜

**Priority:** 🟡 MEDIUM - Creative feature, already in local ApexAurum
**Requires:** Suno API key

AI music generation via Suno API.

| Tool | Description | Status |
|------|-------------|--------|
| `music_generate` | Generate track from prompt | ⬜ |
| `music_status` | Check generation status | ⬜ |
| `music_list` | List user's generated tracks | ⬜ |
| `music_download` | Get track URL/file | ⬜ |

**Implementation Notes:**
- Async generation (returns task ID)
- Poll for completion
- Store metadata in database
- Audio files in Vault or external storage
- Rate limit: 5 generations per hour

**Source Reference:**
- `/home/hailo/claude-root/Projects/ApexAurum/tools/music.py`

**Database Schema:**
```sql
CREATE TABLE music_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    suno_id VARCHAR(100),
    title VARCHAR(255),
    prompt TEXT,
    style VARCHAR(100),
    duration_seconds INTEGER,
    audio_url TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

---

## Tier 10: Browser (The Exploring Hands) ⬜

**Priority:** 🟡 MEDIUM - Powerful but complex
**Requires:** Browserbase API or Playwright cloud

Headless browser automation for web interaction.

| Tool | Description | Status |
|------|-------------|--------|
| `browser_open` | Open URL in session | ⬜ |
| `browser_screenshot` | Capture page screenshot | ⬜ |
| `browser_click` | Click element by selector | ⬜ |
| `browser_type` | Type text into input | ⬜ |
| `browser_extract` | Extract text/data from page | ⬜ |

**Implementation Notes:**
- Session-based (persistent browser context)
- Screenshot returns base64 or Vault file
- Selector support: CSS, XPath, text content
- Timeout: 30s per action
- Max sessions per user: 2

**Options:**
1. **Browserbase** - Managed browser API (easiest)
2. **Playwright** - Self-hosted (more control)
3. **Puppeteer Cloud** - Google's option

**Use Cases:**
- Fill out forms
- Extract data from dynamic pages
- Take screenshots for verification
- Automate repetitive web tasks

---

## Tier 11: Email (The Messenger Hands) ⬜

**Priority:** 🟢 LOW - Useful but security-sensitive
**Requires:** SMTP credentials or email API (SendGrid, Resend)

Send and draft emails on behalf of user.

| Tool | Description | Status |
|------|-------------|--------|
| `email_send` | Send email (requires confirmation) | ⬜ |
| `email_draft` | Create draft without sending | ⬜ |
| `email_template` | Use saved template | ⬜ |
| `email_history` | List sent emails | ⬜ |

**Implementation Notes:**
- ALWAYS require user confirmation before send
- Store drafts in database
- Rate limit: 10 emails per hour
- Template variables: {{name}}, {{date}}, etc.
- HTML and plain text support

**Security:**
- User must configure their SMTP/API credentials
- Never store full credentials, use encrypted vault
- Log all sent emails

---

## Tier 12: Calendar (The Scheduling Hands) ⬜

**Priority:** 🟢 LOW - Integration-dependent
**Requires:** Google Calendar API or CalDAV

Calendar management for scheduling.

| Tool | Description | Status |
|------|-------------|--------|
| `calendar_list` | List upcoming events | ⬜ |
| `calendar_create` | Create new event | ⬜ |
| `calendar_update` | Modify existing event | ⬜ |
| `calendar_delete` | Remove event | ⬜ |

**Implementation Notes:**
- OAuth2 for Google Calendar
- CalDAV for self-hosted calendars
- Timezone-aware
- Recurring event support
- Reminder integration

---

## Tier 13: Image (The Seeing Hands) ⬜

**Priority:** 🟡 MEDIUM - Visual capabilities
**Requires:** OpenAI DALL-E API or Stability AI

Image generation and analysis.

| Tool | Description | Status |
|------|-------------|--------|
| `image_generate` | Generate image from prompt | ⬜ |
| `image_edit` | Edit/inpaint existing image | ⬜ |
| `image_analyze` | Describe image contents | ⬜ |
| `image_variation` | Create variations of image | ⬜ |

**Implementation Notes:**
- DALL-E 3 for generation
- Claude Vision for analysis (already available)
- Store in Vault
- Size options: 256, 512, 1024
- Style options: vivid, natural

---

## Future Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Tool Tiers (Complete)                       │
├─────────────────────────────────────────────────────────────────┤
│  Tier 1-7: Utilities, Web, Vault, KB, Memory, Code, Agents      │
│            26 tools ✅                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Tool Tiers (Future)                          │
├─────────────────────────────────────────────────────────────────┤
│  Tier 8:  Vectors   │ Semantic memory, RAG foundation           │
│  Tier 9:  Music     │ AI music generation (Suno)                │
│  Tier 10: Browser   │ Web automation (Browserbase)              │
│  Tier 11: Email     │ Communication (SMTP/API)                  │
│  Tier 12: Calendar  │ Scheduling (Google/CalDAV)                │
│  Tier 13: Image     │ Visual generation (DALL-E)                │
│           26 more tools planned                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Grand Total: 52 Tools                         │
│            "The Athanor grows ever more powerful"                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Foundation (Next)
- [ ] Tier 8: Vector Search - Enables semantic memory
- [ ] Enable pgvector on Railway PostgreSQL
- [ ] Choose embedding provider (OpenAI vs local)

### Phase 2: Creative
- [ ] Tier 9: Music - Port from local ApexAurum
- [ ] Tier 13: Image - DALL-E integration

### Phase 3: Automation
- [ ] Tier 10: Browser - Web automation
- [ ] Tier 11: Email - Communication

### Phase 4: Integration
- [ ] Tier 12: Calendar - External services

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Claude API                           │
│                   (with tools)                          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  Tool Registry                          │
│              (app/tools/__init__.py)                    │
│                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Tier 1  │ │ Tier 2  │ │ Tier 3  │ │ Tier 4  │  ...  │
│  │Utilities│ │  Web    │ │  Vault  │ │   KB    │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 Tool Executor                           │
│          (app/services/tool_executor.py)                │
│                                                         │
│  - Context injection (user, conversation, agent)        │
│  - Validation & error handling                          │
│  - Execution timing                                     │
│  - Result formatting for Claude                         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

### Infrastructure ✅
- [x] Base tool classes (`BaseTool`, `SyncTool`, `AsyncTool`)
- [x] Tool registry (singleton pattern)
- [x] Tool executor with context
- [x] Claude API integration (tools param)
- [x] Agentic loop (max 5 turns)
- [x] SSE events for tool execution
- [x] Frontend tools toggle
- [x] Frontend execution indicators

### Per-Tier Checklist Template
For each tier:
- [ ] Create tool file (`app/tools/{tier}.py`)
- [ ] Implement tool classes
- [ ] Add schemas (Claude format)
- [ ] Register in `__init__.py`
- [ ] Test locally
- [ ] Deploy to Railway
- [ ] Verify live endpoints
- [ ] Update HANDOVER.md

---

## Alchemical Naming

Each tier has a poetic name reflecting its nature:

| Tier | Name | Meaning |
|------|------|---------|
| 1 | Simple Hands | Basic operations, no dependencies |
| 2 | Reaching Hands | Extend into the web |
| 3 | Crafting Hands | Shape and mold files |
| 4 | Knowing Hands | Access stored knowledge |
| 5 | Remembering Hands | Hold context across steps |
| 6 | Making Hands | Create and execute |
| 7 | Spawning Hands | Birth new agents |

---

## Changelog

### 2026-01-26 - v37-vector-search
- Completed Tier 8: Vector Search (5 tools) - FIRST FUTURE TIER DONE!
- `vector_store` - Store text with semantic embedding
- `vector_search` - Find similar content by meaning
- `vector_delete` - Remove memories
- `vector_list` - Browse collections
- `vector_stats` - Storage statistics
- Added pgvector extension to database migrations
- Created EmbeddingService with OpenAI/Voyage support
- Total tools: 31 (26 core + 5 vectors)

### 2026-01-26 - v36-vault-complete
- Completed Tier 3: All 5 Vault tools now working!
- `vault_write` - Create new files or update existing
  - Quota enforcement
  - Safe filename handling
  - 1MB content limit per write
  - Requires confirmation
- `vault_search` - Search file contents
  - Case-insensitive pattern matching
  - Context lines (before/after)
  - Max 5 matches per file, 50 files total
- **ALL 26 TOOLS COMPLETE!**

### 2026-01-26 - v35-vault-fix
- Fixed vault tools import error (`app.models.file` not `files`)
- Fixed File model attributes (`name` not `filename`, `size_bytes` not `size`)
- Added Tools Panel to Settings:
  - Shows tool count badge
  - Expandable list grouped by category
  - Category icons (Utilities, Web, Vault, Memory, Knowledge, Agents)
  - Tooltip descriptions on hover
- All 24 tools now loading correctly

### 2026-01-26 - v34-spawning-hands
- Completed Tier 7: Agent Tools (3 tools) - FINAL TIER!
- `agent_spawn` - Spawn background agents (research, code, writer, analyst)
- `agent_status` - Check agent progress
- `agent_result` - Get completed agent output
- Max 3 concurrent agents per user
- All 7 Tiers complete!
- Total tools: 24/26 (2 vault tools pending service layer)

### 2026-01-26 - v33-making-hands
- Completed Tier 6: Code Execution Tools (2 tools)
- `code_run` - Execute Python with stdout/stderr capture
- `code_eval` - Evaluate single expressions
- Sandboxed with safe builtins only
- Available modules: math, random, datetime, json, re, etc.
- Limits: 10s timeout, 100KB output
- Total tools: 21/26

### 2026-01-26 - v32-remembering-hands
- Completed Tier 5: Session Memory Tools (4 tools)
- `scratch_store` - Store key-value pairs (10KB/value, 100KB total)
- `scratch_get` - Retrieve stored values
- `scratch_list` - List all keys with metadata
- `scratch_clear` - Clear all or specific keys
- In-memory per-conversation storage
- Total tools: 19/26

### 2026-01-26 - v31-knowing-hands
- Completed Tier 4: Knowledge Base Tools (4 tools)
- `kb_search` - Semantic search with topic filtering
- `kb_lookup` - Quick term/concept lookup
- `kb_topics` - List available documentation topics
- `kb_answer` - Get context for answering questions
- Graceful fallback when KB server not configured
- Total tools: 15/26

### 2026-01-26 - v30-crafting-hands
- Completed Tier 3 partial: Vault Tools (3/5)
- `vault_list` - List files and folders
- `vault_read` - Read text file content
- `vault_info` - Storage usage statistics
- Uses SQLAlchemy models directly (requires auth)
- Total tools: 11/26

### 2026-01-26 - v29-reaching-hands
- Completed Tier 2: Web Tools (2 tools)
- `web_fetch` - Fetch any URL with httpx
- `web_search` - DuckDuckGo Instant Answers
- Total tools: 8/26

### 2026-01-26 - v28-athanors-hands
- Created Grand Masterplan
- Completed Tier 1: Utilities (6 tools)
- Established tool architecture
- Deployed to Railway

---

*"The Athanor burns eternal. The hands multiply. The Great Work continues."*

