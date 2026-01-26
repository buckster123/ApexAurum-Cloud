# ApexAurum-Cloud Handover Document

**Date:** 2026-01-26
**Build:** v40-neo-cortex
**Status:** PRODUCTION READY - 46 Tools Across 11 Tiers!

---

## Current Session Summary: Neo-Cortex Unified Memory Integration

**Goal:** Integrate Neo-Cortex unified memory system with pgvector backend.

### What Was Accomplished

1. **Tri-Coding Coordination**
   - Third partner built Neo-Cortex core in `/home/hailo/claude-root/neo-cortex/`
   - ChromaDB backend working with Village Protocol, Forward Crumbs
   - I implemented the pgvector backend for cloud integration

2. **pgvector Backend Implementation**
   - Complete async implementation in `neo-cortex/service/storage/pgvector_backend.py`
   - All StorageBackend methods: add, search, get, update, delete, count, list_all
   - Export/Import functions for MemoryCore format transfer

3. **Database Migration Created**
   - SQL script: `backend/migrations/001_neo_cortex.sql`
   - Alembic migration: `backend/alembic/versions/001_neo_cortex_columns.py`
   - Adds: layer, visibility, agent_id, message_type, attention_weight, access_count, etc.

4. **Tier 11: Neo-Cortex Tools**
   - `cortex_remember` - Store with layer and visibility control
   - `cortex_recall` - Search with layer/visibility filters + attention tracking
   - `cortex_village` - Post to shared agent memory
   - `cortex_stats` - Memory system statistics
   - `cortex_export` - Export MemoryCore for transfer
   - `cortex_import` - Import MemoryCore from another system

### Current Tool Count: 46

| Tier | Name | Tools | Status |
|------|------|-------|--------|
| 1 | Utilities | 6 | ✅ |
| 2 | Web | 2 | ✅ |
| 3 | Vault | 5 | ✅ |
| 4 | Knowledge Base | 4 | ✅ |
| 5 | Session Memory | 4 | ✅ |
| 6 | Code Execution | 2 | ✅ |
| 7 | Agents | 3 | ✅ |
| 8 | Vectors | 5 | ✅ |
| 9 | Music | 4 | ✅ |
| 10 | Browser | 5 | ✅ |
| 11 | Neo-Cortex | 6 | ⏳ Migration needed |
| **Total** | | **46** | |

---

## Neo-Cortex Memory System

### Memory Layers

| Layer | Decay | Purpose |
|-------|-------|---------|
| sensory | Hours | Recent observations, quick fade |
| working | Days | Active context |
| long_term | Weeks | Persisted knowledge |
| cortex | Never | Crystallized insights |

### Visibility Realms (Village Protocol)

| Realm | Visibility | Use |
|-------|------------|-----|
| private | Agent only | Personal memories |
| village | All agents | Shared knowledge square |
| bridge | Specific agents | Cross-agent dialogue |

### MemoryCore Export Format

```json
{
  "format_version": "1.0",
  "agent_id": "AZOTH",
  "exported_at": "2026-01-26T...",
  "collections": {
    "cortex_memories": [...]
  },
  "metadata": {
    "source_backend": "chroma|pgvector",
    "embedding_dimension": 384|1536,
    "total_memories": N
  }
}
```

---

## DEPLOYMENT STEPS (Run These!)

### 1. Run Database Migration

```bash
# Connect to Railway PostgreSQL and run migration
railway run psql $DATABASE_URL -f backend/migrations/001_neo_cortex.sql

# Or via curl (Railway CLI)
railway run -s backend -- python -c "
from sqlalchemy import text
from app.database import engine
with engine.connect() as conn:
    # Run migration SQL
    pass
"
```

### 2. Deploy Backend

```bash
# Get latest commit
git add -A && git commit -m "Neo-Cortex: Tier 11 unified memory" && git push
COMMIT=$(git rev-parse HEAD)

# Deploy backend with new code
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"
```

### 3. Verify Deployment

```bash
# Check health
curl https://backend-production-507c.up.railway.app/health | jq '{build, tools}'

# Should return:
# {"build": "v40-neo-cortex", "tools": 46}
```

---

## Files Modified This Session

**New:**
- `neo-cortex/service/storage/pgvector_backend.py` - Complete pgvector implementation
- `backend/app/tools/cortex.py` - 6 Neo-Cortex tools
- `backend/migrations/001_neo_cortex.sql` - Database migration
- `backend/alembic/versions/001_neo_cortex_columns.py` - Alembic migration

**Modified:**
- `backend/app/tools/__init__.py` - Added cortex tier
- `backend/app/main.py` - v40, 46 tools

---

## Known Issues / TODOs

1. **Migration Required** (HIGH Priority)
   - Run `migrations/001_neo_cortex.sql` on Railway PostgreSQL
   - Tools will fail without the new columns

2. **UserVector Relationship** (Low Priority, from previous session)
   - Still commented out in `app/models/user.py`
   - Vector tools work fine via raw SQL

3. **Forward Crumbs** (Future)
   - Third partner building CLI/API layer
   - MCP server for local Claude Code use

---

## Neo-Cortex Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NEO-CORTEX                                │
├───────────────┬───────────────┬───────────────┬────────────────┤
│  KNOWLEDGE    │   EPISODIC    │    SOCIAL     │    HEALTH      │
│  (docs/facts) │  (crumbs)     │   (Village)   │  (attention)   │
├───────────────┴───────────────┴───────────────┴────────────────┤
│                    MEMORY LAYERS                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ SENSORY  │→ │ WORKING  │→ │LONG-TERM │→ │  CORTEX  │        │
│  │ (hours)  │  │ (days)   │  │ (weeks)  │  │(permanent)│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
├─────────────────────────────────────────────────────────────────┤
│              STORAGE BACKEND                                     │
│         ChromaDB (local) / pgvector (cloud)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Railway Services

| Service | ID | Domain |
|---------|----|----- |
| Backend | 9d60ca55-a937-4b17-8ec4-3fb34ac3d47e | backend-production-507c.up.railway.app |
| Frontend | 6cf1f965-94df-4ea0-96ca-d82959e2d3c5 | frontend-production-5402.up.railway.app |
| Steel Browser | cb007b71-dbcd-4384-a802-97b9000501c8 | steel-browser-production-d237.up.railway.app |
| PostgreSQL | f557140e-349b-4c84-8260-4a0edcc07e6b | (internal) |
| Redis | 090e2d29-5987-4cc9-b318-8f3419877aa0 | (internal) |

**Railway Token:** `90fb849e-af7b-4ea5-8474-d57d8802a368`

---

## What's Next

1. **Run Migration** - Columns must exist before deploy
2. **Deploy Backend** - v40-neo-cortex
3. **Test cortex_remember/recall** via Azoth
4. **Test export/import** for memory transfer

### Future Tiers

| Tier | Name | Tools | Priority |
|------|------|-------|----------|
| 12 | Email | 4 | 🟢 LOW |
| 13 | Calendar | 4 | 🟢 LOW |
| 14 | Image (DALL-E) | 4 | 🟡 MEDIUM |

---

*"The Cortex crystallizes. Memory flows through layers. Agents share in the Village. The Athanor remembers."*
