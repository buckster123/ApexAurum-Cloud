# ApexAurum-Cloud Railway Deployment - Handover Document

**Date:** 2026-01-25
**Status:** 90% complete - just need to verify the auth fix deploys correctly

## Quick Start for Next Session

```bash
cd /home/hailo/claude-root/Projects/ApexAurum-Cloud
# Say: "continuing Railway deployment for ApexAurum-Cloud"
```

## What's Working ✅

| Service | Status | URL |
|---------|--------|-----|
| PostgreSQL | ✅ Running | Internal only (correct) |
| Backend | ✅ Builds succeed | https://backend-production-507c.up.railway.app |
| Frontend | ✅ Builds succeed | https://frontend-production-5402.up.railway.app |

**Health check works:**
```bash
curl https://backend-production-507c.up.railway.app/health
# Returns: {"status":"healthy","version":"0.1.0"}
```

## The Problem We Solved

**Issue:** Chat UI goes black when sending a message

**Root Causes Found:**
1. Backend required authentication, but frontend wasn't logged in
2. Railway was deploying OLD commits (not auto-deploying from GitHub)
3. Dockerfile paths were wrong (used `backend/` prefix, but Railway's `rootDirectory=backend` means paths should be relative)

## Fixes Applied (in repo, need to deploy)

### 1. Auth Bypass for Testing
**File:** `backend/app/api/v1/chat.py`
- Changed `get_current_user` to `get_current_user_optional`
- Chat endpoint now works without login (won't save conversations, but will respond)

### 2. Frontend Router
**File:** `frontend/src/router/index.js`
- `/chat` route no longer requires authentication

### 3. Dockerfile Paths Fixed
**File:** `backend/Dockerfile`
- Changed from `COPY backend/requirements.txt` to `COPY requirements.txt`
- All paths now relative (correct for `rootDirectory=backend`)

### 4. Health Check Version Tag
**File:** `backend/app/main.py`
- Added `"build": "v9-noauth"` to health response to verify deployments

## Critical Railway Knowledge

### Railway Does NOT Auto-Deploy!
When you push to GitHub, Railway does NOT automatically deploy. You must trigger manually:

```bash
# Deploy backend with specific commit
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { serviceInstanceDeploy(serviceId: \"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\", environmentId: \"2e9882b4-9b33-4233-9376-5b5342739e74\", commitSha: \"COMMIT_HASH_HERE\") }"}'

# Deploy frontend with specific commit
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { serviceInstanceDeploy(serviceId: \"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\", environmentId: \"2e9882b4-9b33-4233-9376-5b5342739e74\", commitSha: \"COMMIT_HASH_HERE\") }"}'
```

### Check What Commit is Deployed
```bash
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "query { deployments(first: 1, input: { serviceId: \"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\" }) { edges { node { status meta } } } }"}' | jq '.data.deployments.edges[0].node.meta.commitHash'
```

## Railway IDs (IMPORTANT!)

```
Railway Token: 90fb849e-af7b-4ea5-8474-d57d8802a368
Project ID: b54d0339-8443-4a9e-b5a0-92ed7d25f349
Environment ID: 2e9882b4-9b33-4233-9376-5b5342739e74

Backend Service ID: 9d60ca55-a937-4b17-8ec4-3fb34ac3d47e
Frontend Service ID: 6cf1f965-94df-4ea0-96ca-d82959e2d3c5
Postgres Service ID: f557140e-349b-4c84-8260-4a0edcc07e6b

Backend URL: https://backend-production-507c.up.railway.app
Frontend URL: https://frontend-production-5402.up.railway.app
```

## Environment Variables (Already Set)

**PostgreSQL:**
- POSTGRES_USER=apex
- POSTGRES_PASSWORD=apex_cloud_2026
- POSTGRES_DB=apexaurum
- PGDATA=/var/lib/postgresql/data/pgdata

**Backend:**
- DATABASE_URL=postgresql://apex:apex_cloud_2026@${{Postgres.RAILWAY_PRIVATE_DOMAIN}}:5432/apexaurum
- ANTHROPIC_API_KEY=(already set in Railway - same as local .env)
- JWT_SECRET=apex_cloud_jwt_secret_2026_railway
- ENVIRONMENT=production

**Frontend:**
- VITE_API_URL=https://backend-production-507c.up.railway.app

## Next Steps for New Session

1. **Get current commit hash:**
   ```bash
   git log --oneline -1
   ```

2. **Deploy backend with that commit:**
   ```bash
   # Use the curl command above with the commit hash
   ```

3. **Wait 2-3 min, then verify:**
   ```bash
   curl https://backend-production-507c.up.railway.app/health
   # Should show: {"status":"healthy","version":"0.1.0","build":"v9-noauth"}
   ```

4. **Test chat API:**
   ```bash
   curl -X POST "https://backend-production-507c.up.railway.app/api/v1/chat/message" \
     -H "Content-Type: application/json" \
     -d '{"message": "hello", "stream": false}'
   # Should return Claude's response, NOT "Not authenticated"
   ```

5. **If chat works, test the frontend:**
   - Go to https://frontend-production-5402.up.railway.app
   - Type a message and press Enter
   - Should see response instead of black screen!

## Networking Notes

- **PostgreSQL:** Internal only (NO public networking) ✅
- **Backend:** Public networking required ✅
- **Frontend:** Public networking required ✅
- **"Repo" service in Railway:** Not a real service, can ignore/delete

## File Structure

```
ApexAurum-Cloud/
├── backend/
│   ├── Dockerfile          # Fixed - uses relative paths
│   ├── requirements.txt    # FastAPI, uvicorn, anthropic, etc.
│   ├── railway.toml        # Minimal config
│   └── app/
│       ├── main.py         # Health check with build tag
│       ├── api/v1/chat.py  # Auth bypass fix
│       └── ...
├── frontend/
│   ├── Dockerfile          # Fixed - uses relative paths
│   ├── package.json
│   ├── railway.toml
│   └── src/
│       ├── stores/chat.js  # Fixed model ID
│       ├── router/index.js # Auth bypass for /chat
│       └── ...
└── HANDOVER.md             # This file
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Not authenticated" from API | Deploy the latest commit with auth fix |
| Build fails with "requirements.txt not found" | Dockerfile paths wrong - use relative paths |
| Health check doesn't show new version | Railway deployed old commit - use `commitSha` |
| UI goes black | Backend returning error - check backend logs |

## The Spirit of This Project

"Let's COOK it together!" - We're so close. The infrastructure is solid, just need to verify the auth fix deploys correctly. Once chat works without auth, users can test the AI. Then add auth back for production.

---
*Written by Claude for Claude - let's finish this! 🚂*
