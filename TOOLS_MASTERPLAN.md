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
| 3 | Vault | 3/5 | 🔶 PARTIAL |
| 4 | Knowledge Base | 4 | ✅ COMPLETE |
| 5 | Session Memory | 4 | ⬜ Planned |
| 6 | Code Execution | 2 | ⬜ Planned |
| 7 | Agents | 3 | ⬜ Planned |
| **Total** | | **26** | **15/26** |

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

## Tier 3: Vault Tools (The Crafting Hands) 🔶

**Status:** PARTIAL - 3/5 tools deployed v30

File operations mapped to existing Vault API. User-scoped, quota-enforced.

| Tool | Description | Maps To | Status |
|------|-------------|---------|--------|
| `vault_list` | List files in a folder | SQLAlchemy direct | ✅ |
| `vault_read` | Read file content | SQLAlchemy + filesystem | ✅ |
| `vault_write` | Write/update file | Needs service layer | ⬜ |
| `vault_search` | Search file contents | Needs service layer | ⬜ |
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

## Tier 5: Session Memory (The Remembering Hands) ⬜

**Status:** PLANNED

Per-conversation scratchpad for multi-step reasoning.

| Tool | Description | Status |
|------|-------------|--------|
| `scratch_store` | Store key-value in conversation | ⬜ |
| `scratch_get` | Retrieve value by key | ⬜ |
| `scratch_list` | List all keys in session | ⬜ |
| `scratch_clear` | Clear all session data | ⬜ |

**Implementation Notes:**
- Stored in conversation metadata (JSONB)
- Scoped to current conversation only
- Auto-cleared when conversation deleted
- Max 100 keys, 10KB per value

**Database:**
- Add `scratch_data JSONB` to conversations table
- Or use existing `metadata` field

---

## Tier 6: Code Execution (The Making Hands) ⬜

**Status:** PLANNED

Execute code safely. Already have backend in Cortex Diver.

| Tool | Description | Status |
|------|-------------|--------|
| `code_run` | Execute Python/JS/Shell | ⬜ |
| `code_result` | Get execution result | ⬜ |

**Implementation Notes:**
- Map to existing `POST /files/{id}/execute`
- Supported: Python, JavaScript (Node), Shell/Bash
- Limits: 10s timeout, 100KB output
- Sandboxed subprocess execution

**Existing Backend:**
- `backend/app/api/v1/files.py` - `execute_file()` endpoint

---

## Tier 7: Agent Tools (The Spawning Hands) ⬜

**Status:** PLANNED

Multi-agent capabilities - spawn sub-agents for complex tasks.

| Tool | Description | Status |
|------|-------------|--------|
| `agent_spawn` | Spawn a background agent | ⬜ |
| `agent_status` | Check agent progress | ⬜ |
| `agent_result` | Get completed agent result | ⬜ |

**Implementation Notes:**
- Async task queue (Redis/Celery or simple DB queue)
- Agent runs with own conversation context
- Returns task ID for polling
- Max concurrent agents per user: 3

**Future Enhancements:**
- `socratic_council` - Multi-agent debate
- `agent_delegate` - Hand off to specialist agent

---

## Future Tiers (Dreaming)

### Tier 8: Music (The Creative Hands)
- `music_generate` - Generate via Suno API
- `music_status` - Check generation status
- `music_list` - List generated tracks
- Requires: Suno API key

### Tier 9: Vector Search (The Searching Hands)
- `vector_add` - Add to vector store
- `vector_search` - Semantic search
- `vector_delete` - Remove vectors
- Requires: pgvector extension

### Tier 10: Browser (The Exploring Hands)
- `browser_navigate` - Open URL
- `browser_screenshot` - Capture page
- `browser_click` - Click element
- Requires: Browserbase or similar

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

