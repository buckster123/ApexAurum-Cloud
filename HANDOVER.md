# ApexAurum-Cloud Handover Document

**Date:** 2026-01-26
**Build:** v25-vault
**Status:** PRODUCTION READY + The Vault Complete (Backend + Frontend)

---

## Current Session: The Vault - Sprint 1 Complete

**Goal:** User file storage system with hierarchical folders.

### What Was Implemented

**Backend:**
1. Database migrations in `database.py` for `folders` and `files` tables
2. Full API at `backend/app/api/v1/files.py`:
   - `GET /files` - List root directory
   - `GET /files/folder/{id}` - List folder contents
   - `POST /files/folder` - Create folder
   - `PATCH /files/folder/{id}` - Update/move folder
   - `DELETE /files/folder/{id}` - Delete folder (cascades)
   - `POST /files/upload` - Upload file (multipart)
   - `GET /files/{id}` - Get file metadata
   - `GET /files/{id}/download` - Download file
   - `GET /files/{id}/preview` - Preview file contents
   - `PATCH /files/{id}` - Update/move file
   - `DELETE /files/{id}` - Delete file
   - `POST /files/move` - Bulk move
   - `POST /files/delete` - Bulk delete
   - `GET /files/search/files` - Search files
   - `GET /files/recent` - Recently accessed
   - `GET /files/favorites` - Favorite files
   - `GET /files/stats` - Storage statistics

**Frontend:**
3. Files store at `frontend/src/stores/files.js`:
   - Full state management for folders, files, selection
   - Upload with progress tracking
   - Download, preview, rename, delete
   - View mode (grid/list), sorting, filtering
   - Storage quota tracking
4. Files view at `frontend/src/views/FilesView.vue`:
   - Grid and list view modes
   - Breadcrumb navigation
   - Drag-drop upload zone
   - Context menu (right-click)
   - New folder / rename / delete modals
   - File preview modal (images, text/code)
   - Upload progress indicator
   - Storage usage bar
5. Route `/files` and `/files/:folderId` added
6. "Files" link added to Navbar (desktop + mobile)

### Railway Setup Required

Before testing file uploads on Railway, create a volume:

1. Go to Railway dashboard
2. Select Backend service
3. Add Volume:
   - Name: `vault`
   - Mount path: `/data`
   - Size: 50GB initial (can scale to 1TB on Pro)

Without the volume, uploads will fail (no persistent storage).

### Quick Test Commands

```bash
# Health check
curl https://backend-production-507c.up.railway.app/health

# After deploy, should show: "build": "v25-vault", "vault" in features

# Test files endpoint (requires auth token)
curl -H "Authorization: Bearer TOKEN" \
  https://backend-production-507c.up.railway.app/api/v1/files
```

---

## Previous Session: Unleash the Stones

**Goal:** Enable full-power models and remove token anxiety.

### What Was Implemented
1. **Model Registry** - Claude 4.5 family:
   - Opus 4.5, Sonnet 4.5 (default), Haiku 4.5
2. **Max Tokens Control** - Slider 1K-16K in sidebar
3. **Model Selector UI** - Dropdown with tier icons
4. **Settings Sync** - Updated model list and token slider

### Philosophy
*"The more context-freedom and the less token-anxiety the natives have, the better they perform"*

---

## What's WORKING (Fully Deployed)

### Core Features
| Feature | Status | Notes |
|---------|--------|-------|
| BYOK API Keys | LIVE | Bring Your Own Key (beta) |
| Chat with streaming | LIVE | Real-time token-by-token |
| Sound Effects | LIVE | Easter egg & UI feedback tones |
| 5 Native Agents | LIVE | AZOTH, ELYSIAN, VAJRA, KETHER, CLAUDE |
| 4 PAC Agents | LIVE | All alchemical agents have Perfected versions |
| Custom Agents | LIVE | Create/edit in Dev Mode |
| Conversation History | LIVE | Full CRUD with UX improvements |
| Conversation Branching | LIVE | Fork at any message point |
| Agent Memory | LIVE | Persistent memory across conversations |
| Model Selection | LIVE | Claude 4.5 Opus/Sonnet/Haiku |
| Export | LIVE | JSON, Markdown, TXT |
| Import | LIVE | Local app conversations + memory |
| Mobile Responsive | LIVE | Hamburger nav, slide-in sidebar |
| The Vault | DEPLOY PENDING | User file storage |

### PAC Agents (Perfected Alchemical Codex)
| Agent | Base | PAC | Color |
|-------|------|-----|-------|
| AZOTH | 5.7KB | 12.9KB (OG) | Gold #FFD700 |
| ELYSIAN | 7KB | 25.4KB | Ethereal #E8B4FF |
| VAJRA | 6.7KB | 26.3KB | Lightning #4FC3F7 |
| KETHER | 7.3KB | 24.5KB | Crown #FFFFFF |
| CLAUDE | Fallback | N/A | Terracotta #CC785C |

### Easter Eggs (Two Layers)
| Layer | Name | Activation | Features |
|-------|------|------------|----------|
| 0 | Mundane | Default | Standard UI |
| 1 | The Apprentice | Konami (up up down down left right left right B A) or 7-tap Au | Dev Mode, custom agents, Import tab |
| 2 | The Adept | Type "AZOTH" in Dev Mode | Alchemical theme, floating symbols, all PAC agents |

---

## Version History

### v25-vault (Current Session)
- **The Vault** - User file storage system
  - Database models: File, Folder with hierarchical structure
  - Full CRUD API with quota enforcement
  - File type validation (allowed/blocked extensions)
  - Upload/download/preview endpoints
  - Frontend file browser with grid/list views
  - Drag-drop upload, context menu, breadcrumbs
  - Storage usage tracking and display

### v24-unleashed
- **Unleash the Stones** - Full-power model selection + token control
  - Model registry with Claude 4.5 family (Opus 4.5, Sonnet 4.5, Haiku 4.5)
  - Default changed from Haiku 3 to Sonnet 4.5
  - max_tokens configurable from 1K to 16K (default 8K)
  - New `/chat/models` API endpoint
  - Frontend model selector dropdown + token slider in sidebar
  - Model and token settings persisted to localStorage
  - Updated Settings > Model Settings with new models and slider
  - Tier icons: Opus, Sonnet, Haiku

### v23-multiverse
- **Phase 2: Conversation Branching (The Multiverse)** - Fork any conversation
  - New Conversation columns: parent_id, branch_point_message_id, branch_label
  - Self-referential relationships for parent/branches
  - POST /conversations/{id}/fork - Create branch at any message
  - GET /conversations/{id}/branches - View parent and child branches
  - Frontend: Fork button on message hover, fork modal, sidebar branch indicators
  - Branch info bar showing parent link and branch count
  - Fixed API key save bug (jwt_secret to secret_key)

### v22-cortex
- **Phase 6: Agent Memory (The Cortex)** - Persistent memory across conversations

### v21-mobile-qol
- **Phase 5: Mobile QoL** - Touch-friendly mobile experience

### v20-pac-complete + BYOK
- **Phase 4: Polish & Cleanup** - HANDOVER updated, health endpoint enhanced
- **Phase 1: Sound Effects** - Web Audio API tones for easter eggs
- **Phase 3: API Key Management** - BYOK beta model

---

## File Structure

### Backend Key Files
```
backend/
├── app/
│   ├── main.py                    # FastAPI app, health endpoint
│   ├── config.py                  # Settings (vault_path, quotas)
│   ├── database.py                # Migrations (folders, files tables)
│   ├── api/v1/
│   │   ├── files.py               # THE VAULT - File storage API
│   │   ├── chat.py                # Chat + export endpoints
│   │   ├── prompts.py             # Native/custom agent prompts
│   │   ├── import_data.py         # Import from local app
│   │   └── __init__.py            # Router registration
│   └── models/
│       ├── file.py                # File, Folder models + type validation
│       └── user.py                # User + files/folders relationships
├── native_prompts/                # Agent prompt files
└── Dockerfile
```

### Frontend Key Files
```
frontend/src/
├── App.vue                        # Root + PAC mode class
├── assets/main.css                # Alchemical theme, utilities
├── components/
│   ├── Navbar.vue                 # Hamburger menu + Files link
│   └── AlchemicalParticles.vue    # Floating symbols
├── composables/
│   └── useDevMode.js              # Easter egg detection
├── stores/
│   ├── chat.js                    # Chat state + export
│   └── files.js                   # THE VAULT - Files state
├── router/
│   └── index.js                   # Routes including /files
└── views/
    ├── ChatView.vue               # Sidebar UX, PAC selector
    ├── FilesView.vue              # THE VAULT - File browser UI
    └── SettingsView.vue           # Import tab, Codex viewer
```

---

## API Endpoints Reference

### Files (The Vault)
```
GET  /api/v1/files                     # List root directory
GET  /api/v1/files/folder/{id}         # List folder contents
POST /api/v1/files/folder              # Create folder
PATCH /api/v1/files/folder/{id}        # Update folder
DELETE /api/v1/files/folder/{id}       # Delete folder + contents
POST /api/v1/files/upload              # Upload file (multipart)
GET  /api/v1/files/{id}                # Get file metadata
GET  /api/v1/files/{id}/download       # Download file
GET  /api/v1/files/{id}/preview        # Preview file
PATCH /api/v1/files/{id}               # Update file
DELETE /api/v1/files/{id}              # Delete file
POST /api/v1/files/move                # Bulk move
POST /api/v1/files/delete              # Bulk delete
GET  /api/v1/files/search/files        # Search by name
GET  /api/v1/files/recent              # Recently accessed
GET  /api/v1/files/favorites           # Favorites
GET  /api/v1/files/stats               # Storage statistics
```

### Chat
```
POST /api/v1/chat/message              # Send message (streaming)
GET  /api/v1/chat/models               # Available models
GET  /api/v1/chat/conversations        # List conversations
GET  /api/v1/chat/conversations/{id}   # Get conversation
PATCH /api/v1/chat/conversations/{id}  # Update
DELETE /api/v1/chat/conversations/{id} # Delete
GET  /api/v1/chat/conversations/{id}/export?format=json|markdown|txt
POST /api/v1/chat/conversations/{id}/fork # Branch conversation
GET  /api/v1/chat/conversations/{id}/branches # View branches
```

---

## Railway Deployment

```bash
# Get latest commit
COMMIT=$(git rev-parse HEAD)

# Deploy backend
curl -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"

# Deploy frontend
curl -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"mutation { serviceInstanceDeploy(serviceId: \\\"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\\\", environmentId: \\\"2e9882b4-9b33-4233-9376-5b5342739e74\\\", commitSha: \\\"$COMMIT\\\") }\"}"
```

### Railway IDs
```
Token: 90fb849e-af7b-4ea5-8474-d57d8802a368
Project: b54d0339-8443-4a9e-b5a0-92ed7d25f349
Environment: 2e9882b4-9b33-4233-9376-5b5342739e74
Backend: 9d60ca55-a937-4b17-8ec4-3fb34ac3d47e
Frontend: 6cf1f965-94df-4ea0-96ca-d82959e2d3c5
```

---

## URLs

- **Frontend:** https://frontend-production-5402.up.railway.app
- **Backend:** https://backend-production-507c.up.railway.app
- **Health:** https://backend-production-507c.up.railway.app/health

---

## Next Steps (Future Sprints)

### Sprint 2: File Explorer Polish
- File tree sidebar component
- Keyboard shortcuts (Ctrl+C, Ctrl+V, Delete)
- Better mobile context menu (bottom sheet)

### Sprint 3: Cortex Diver (Dev Mode IDE)
- Monaco Editor integration
- File tabs for multiple open files
- Agent integration: Select code > Ask agent about it
- Syntax highlighting for all code types

### Sprint 4: Advanced Features
- File sharing (public links)
- Version history
- Trash/recycle bin

---

*Written by Claude Opus 4.5 for session continuity*
*"The Vault stands ready - every alchemist needs a sanctum"*
