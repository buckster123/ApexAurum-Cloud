"""
ApexAurum Cloud - API v1 Router

All API endpoints are mounted here.
"""

from fastapi import APIRouter

from app.api.v1 import auth, chat, agents, village, tools, music, user, prompts, import_data, memory, files, cortex, billing, webhooks

router = APIRouter()

# Include sub-routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
router.include_router(village.router, prefix="/village", tags=["Village"])
router.include_router(tools.router, prefix="/tools", tags=["Tools"])
router.include_router(music.router, prefix="/music", tags=["Music"])
router.include_router(user.router, prefix="/user", tags=["User"])
router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])
router.include_router(import_data.router, prefix="/import", tags=["Import"])
router.include_router(memory.router, prefix="/memory", tags=["Memory"])
router.include_router(files.router, prefix="/files", tags=["Files"])
router.include_router(cortex.router)  # Neo-Cortex dashboard (prefix already in cortex.py)
router.include_router(billing.router, prefix="/billing", tags=["Billing"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
