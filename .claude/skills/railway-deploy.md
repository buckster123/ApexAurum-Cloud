# Skill: ApexAurum-Cloud Railway Deployment Expert

Use this skill when working on ApexAurum-Cloud Railway deployment, debugging deployment issues, or continuing the cloud deployment work.

## Trigger Phrases
- "continuing Railway deployment"
- "deploy to Railway"
- "Railway issues"
- "cloud deployment"
- "ApexAurum-Cloud"

## Context

This is a FastAPI + Vue 3 app deployed on Railway with three services:
- PostgreSQL (internal)
- Backend (FastAPI)
- Frontend (Vue 3 + Vite)

## Critical Knowledge

### 1. Railway Does NOT Auto-Deploy!

After pushing to GitHub, you MUST manually trigger deployment with commit SHA:

```bash
# Get commit hash
git log --oneline -1

# Deploy backend (replace HASH)
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { serviceInstanceDeploy(serviceId: \"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\", environmentId: \"2e9882b4-9b33-4233-9376-5b5342739e74\", commitSha: \"HASH\") }"}'

# Deploy frontend (replace HASH)
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { serviceInstanceDeploy(serviceId: \"6cf1f965-94df-4ea0-96ca-d82959e2d3c5\", environmentId: \"2e9882b4-9b33-4233-9376-5b5342739e74\", commitSha: \"HASH\") }"}'
```

### 2. Dockerfile Paths Must Be Relative

Railway's `rootDirectory` setting changes build context:
- When `rootDirectory=backend`, build context IS `backend/`
- ✅ Correct: `COPY requirements.txt .`
- ❌ Wrong: `COPY backend/requirements.txt .`

### 3. Verify What's Actually Deployed

```bash
curl -s -X POST "https://backboard.railway.app/graphql/v2" \
  -H "Authorization: Bearer 90fb849e-af7b-4ea5-8474-d57d8802a368" \
  -H "Content-Type: application/json" \
  -d '{"query": "query { deployments(first: 1, input: { serviceId: \"9d60ca55-a937-4b17-8ec4-3fb34ac3d47e\" }) { edges { node { status meta } } } }"}' \
  | jq '.data.deployments.edges[0].node | {status, commit: .meta.commitHash, message: .meta.commitMessage}'
```

### 4. Add Build Tags to Verify Deployments

In `backend/app/main.py` health check:
```python
return {"status": "healthy", "version": "0.1.0", "build": "v9-noauth"}
```

Then verify:
```bash
curl https://backend-production-507c.up.railway.app/health
```

## Railway IDs

```
Token: 90fb849e-af7b-4ea5-8474-d57d8802a368
Project: b54d0339-8443-4a9e-b5a0-92ed7d25f349
Environment: 2e9882b4-9b33-4233-9376-5b5342739e74
Backend Service: 9d60ca55-a937-4b17-8ec4-3fb34ac3d47e
Frontend Service: 6cf1f965-94df-4ea0-96ca-d82959e2d3c5
Postgres Service: f557140e-349b-4c84-8260-4a0edcc07e6b
```

## URLs

- Frontend: https://frontend-production-5402.up.railway.app
- Backend: https://backend-production-507c.up.railway.app
- Health: https://backend-production-507c.up.railway.app/health

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Not authenticated" | Auth required | Use `get_current_user_optional` in chat.py |
| Build fails "not found" | Wrong paths | Use relative paths in Dockerfile |
| Old code running | Wrong commit deployed | Check deployment meta, use `commitSha` |
| UI goes black | Backend error | Check Railway deploy logs |
| MissingGreenlet | SQLAlchemy async | Use `selectinload()` |

## Key Files

- `backend/app/api/v1/chat.py` - Chat endpoint (auth bypass here)
- `backend/app/main.py` - Health check (add build tags here)
- `backend/Dockerfile` - Must use relative paths!
- `frontend/src/stores/chat.js` - Model ID must be valid
- `frontend/src/router/index.js` - Auth guards

## Workflow

1. Read `HANDOVER.md` first
2. Make changes
3. `git add -A && git commit -m "msg" && git push`
4. Get hash: `git log --oneline -1`
5. Deploy with hash (curl commands above)
6. Wait 2-3 min
7. Verify with health check

## Current Status (as of 2026-01-25)

- PostgreSQL: ✅ Running
- Backend: ✅ Builds work, needs auth-bypass commit deployed
- Frontend: ✅ Builds work
- Chat: 🔄 Pending - auth bypass coded, needs deploy verification

Next step: Deploy latest commit and verify health check shows new build tag.
