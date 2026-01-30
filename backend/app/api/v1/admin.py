"""
Admin API Endpoints - User management, stats, and system controls.

All endpoints require is_admin=True on the authenticated user.
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import text

from app.database import get_db
from app.models.user import User
from app.models.billing import Subscription, CreditBalance, Coupon
from app.models.feedback import BugReport
from app.models.conversation import Conversation, Message
from app.auth.deps import get_current_user
from app.services.llm_provider import get_available_providers, PROVIDER_MODELS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


# ═══════════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str]
    tier: str
    messages_used: int
    messages_limit: Optional[int]
    credit_balance: int
    is_admin: bool
    created_at: datetime


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class UpdateAdminRequest(BaseModel):
    is_admin: bool


class UpdateTierRequest(BaseModel):
    tier: str  # free, pro, opus


class ProviderStatus(BaseModel):
    id: str
    name: str
    available: bool
    model_count: int


class StatsResponse(BaseModel):
    # Core
    total_users: int
    total_messages: int
    total_conversations: int
    active_coupons: int
    users_by_tier: dict
    # Features
    total_music_tasks: int
    music_by_status: dict
    total_council_sessions: int
    council_by_state: dict
    total_jam_sessions: int
    # Nursery
    total_nursery_datasets: int = 0
    total_nursery_jobs: int = 0
    nursery_jobs_by_status: dict = {}
    total_nursery_models: int = 0
    total_nursery_apprentices: int = 0
    # Storage
    total_vault_files: int
    total_vault_storage_mb: float
    total_neural_vectors: int
    # Providers
    providers: list[ProviderStatus]


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Check Dependency
# ═══════════════════════════════════════════════════════════════════════════════

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin access."""
    if not getattr(user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# ═══════════════════════════════════════════════════════════════════════════════
# User Management
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/users", response_model=UserListResponse)
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, max_length=200),
):
    """List all users with their subscription info."""
    query = select(User).order_by(User.created_at.desc())

    if search:
        query = query.where(User.email.ilike(f"%{search}%"))

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    # Get subscription and credit info for each user
    user_list = []
    for user in users:
        # Get subscription
        sub_result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = sub_result.scalar_one_or_none()

        # Get credit balance
        credit_result = await db.execute(
            select(CreditBalance).where(CreditBalance.user_id == user.id)
        )
        credit_balance = credit_result.scalar_one_or_none()

        user_list.append(UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            tier=subscription.tier if subscription else "free_trial",
            messages_used=subscription.messages_used if subscription else 0,
            messages_limit=subscription.messages_limit if subscription else 50,
            credit_balance=credit_balance.balance_cents if credit_balance else 0,
            is_admin=user.is_admin,
            created_at=user.created_at,
        ))

    # Get total count
    count_query = select(func.count(User.id))
    if search:
        count_query = count_query.where(User.email.ilike(f"%{search}%"))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return UserListResponse(users=user_list, total=total)


@router.patch("/users/{user_id}/admin")
async def update_user_admin(
    user_id: UUID,
    request: UpdateAdminRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Toggle admin status for a user."""
    # Prevent self-demotion
    if user_id == admin.id and not request.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin status"
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = request.is_admin
    await db.commit()

    logger.info(f"Admin {admin.email} set is_admin={request.is_admin} for user {user.email}")

    return {"status": "updated", "user_id": str(user_id), "is_admin": request.is_admin}


@router.patch("/users/{user_id}/tier")
async def update_user_tier(
    user_id: UUID,
    request: UpdateTierRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's subscription tier (admin override)."""
    if request.tier not in ["free_trial", "seeker", "adept", "opus", "azothic"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tier must be 'free_trial', 'seeker', 'adept', 'opus', or 'azothic'"
        )

    # Get or create subscription
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        # Create subscription for user
        from uuid import uuid4
        subscription = Subscription(
            user_id=user_id,
            stripe_customer_id=f"admin_override_{uuid4().hex[:8]}",
            tier=request.tier,
            status="active",
        )
        db.add(subscription)
    else:
        subscription.tier = request.tier

    # Update message limits based on tier
    from app.config import TIER_LIMITS
    tier_config = TIER_LIMITS.get(request.tier, TIER_LIMITS["free_trial"])
    subscription.messages_limit = tier_config["messages_per_month"]

    await db.commit()

    logger.info(f"Admin {admin.email} set tier={request.tier} for user {user_id}")

    return {"status": "updated", "user_id": str(user_id), "tier": request.tier}


@router.get("/users/{user_id}/usage")
async def get_user_usage(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed usage summary for a specific user (admin only)."""
    from app.services.usage import UsageService, FeatureCreditService, get_current_period
    from app.config import TIER_LIMITS

    # Get user's tier
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = result.scalar_one_or_none()
    tier = subscription.tier if subscription else "free_trial"
    tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free_trial"])

    # Get usage counters
    usage_svc = UsageService(db)
    counters = await usage_svc.get_usage_summary(user_id)

    # Get feature credits
    credit_svc = FeatureCreditService(db)
    feature_credits = await credit_svc.get_credit_summary(user_id)

    return {
        "user_id": str(user_id),
        "tier": tier,
        "period": get_current_period(),
        "counters": counters,
        "feature_credits": feature_credits,
        "tier_limits": {
            "messages_per_month": tier_config.get("messages_per_month"),
            "opus_messages_per_month": tier_config.get("opus_messages_per_month"),
            "council_sessions_per_month": tier_config.get("council_sessions_per_month"),
            "suno_generations_per_month": tier_config.get("suno_generations_per_month"),
            "jam_sessions_per_month": tier_config.get("jam_sessions_per_month"),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide statistics including all platform features."""
    # --- Core counts ---
    user_count = await db.execute(select(func.count(User.id)))
    total_users = user_count.scalar() or 0

    try:
        msg_count = await db.execute(select(func.count(Message.id)))
        total_messages = msg_count.scalar() or 0
    except Exception:
        total_messages = 0

    try:
        conv_count = await db.execute(select(func.count(Conversation.id)))
        total_conversations = conv_count.scalar() or 0
    except Exception:
        total_conversations = 0

    coupon_count = await db.execute(
        select(func.count(Coupon.id)).where(Coupon.is_active == True)
    )
    active_coupons = coupon_count.scalar() or 0

    # --- Users by tier ---
    tier_query = await db.execute(
        select(Subscription.tier, func.count(Subscription.id))
        .group_by(Subscription.tier)
    )
    tier_results = tier_query.fetchall()

    users_by_tier = {"Free Trial": 0, "Seeker": 0, "Adept": 0, "Opus": 0, "Azothic": 0}
    tier_names = {"free_trial": "Free Trial", "seeker": "Seeker", "adept": "Adept", "opus": "Opus", "azothic": "Azothic"}

    for tier, count in tier_results:
        name = tier_names.get(tier, tier)
        if name in users_by_tier:
            users_by_tier[name] = count

    users_with_sub = sum(users_by_tier.values())
    users_by_tier["Free Trial"] += total_users - users_with_sub

    # --- Music tasks ---
    total_music_tasks = 0
    music_by_status = {}
    try:
        from app.models.music import MusicTask
        music_count = await db.execute(select(func.count(MusicTask.id)))
        total_music_tasks = music_count.scalar() or 0

        music_status_query = await db.execute(
            select(MusicTask.status, func.count(MusicTask.id))
            .group_by(MusicTask.status)
        )
        music_by_status = {s: c for s, c in music_status_query.fetchall()}
    except Exception as e:
        logger.debug(f"Music stats unavailable: {e}")

    # --- Council sessions ---
    total_council_sessions = 0
    council_by_state = {}
    try:
        from app.models.council import DeliberationSession
        council_count = await db.execute(select(func.count(DeliberationSession.id)))
        total_council_sessions = council_count.scalar() or 0

        council_state_query = await db.execute(
            select(DeliberationSession.state, func.count(DeliberationSession.id))
            .group_by(DeliberationSession.state)
        )
        council_by_state = {s: c for s, c in council_state_query.fetchall()}
    except Exception as e:
        logger.debug(f"Council stats unavailable: {e}")

    # --- Jam sessions ---
    total_jam_sessions = 0
    try:
        from app.models.jam import JamSession
        jam_count = await db.execute(select(func.count(JamSession.id)))
        total_jam_sessions = jam_count.scalar() or 0
    except Exception as e:
        logger.debug(f"Jam stats unavailable: {e}")

    # --- Nursery ---
    total_nursery_datasets = 0
    total_nursery_jobs = 0
    nursery_jobs_by_status = {}
    total_nursery_models = 0
    total_nursery_apprentices = 0
    try:
        from app.models.nursery import NurseryDataset, NurseryTrainingJob, NurseryModelRecord, NurseryApprentice

        ds_count = await db.execute(select(func.count(NurseryDataset.id)))
        total_nursery_datasets = ds_count.scalar() or 0

        job_count = await db.execute(select(func.count(NurseryTrainingJob.id)))
        total_nursery_jobs = job_count.scalar() or 0

        # Jobs by status breakdown
        job_status_query = await db.execute(
            select(NurseryTrainingJob.status, func.count(NurseryTrainingJob.id))
            .group_by(NurseryTrainingJob.status)
        )
        nursery_jobs_by_status = {status: count for status, count in job_status_query.fetchall()}

        model_count = await db.execute(select(func.count(NurseryModelRecord.id)))
        total_nursery_models = model_count.scalar() or 0

        ap_count = await db.execute(select(func.count(NurseryApprentice.id)))
        total_nursery_apprentices = ap_count.scalar() or 0
    except Exception as e:
        logger.debug(f"Nursery stats unavailable: {e}")

    # --- Vault (files) ---
    total_vault_files = 0
    total_vault_storage_mb = 0.0
    try:
        from app.models.file import File
        file_count = await db.execute(select(func.count(File.id)))
        total_vault_files = file_count.scalar() or 0

        storage_result = await db.execute(select(func.coalesce(func.sum(File.size_bytes), 0)))
        total_bytes = storage_result.scalar() or 0
        total_vault_storage_mb = round(total_bytes / (1024 * 1024), 1)
    except Exception as e:
        logger.debug(f"Vault stats unavailable: {e}")

    # --- Neural vectors (raw SQL - pgvector table) ---
    total_neural_vectors = 0
    try:
        vector_result = await db.execute(text("SELECT COUNT(*) FROM user_vectors"))
        total_neural_vectors = vector_result.scalar() or 0
    except Exception as e:
        logger.debug(f"Neural vector stats unavailable: {e}")

    # --- Provider status ---
    providers_raw = get_available_providers()
    providers = [
        ProviderStatus(
            id=p["id"],
            name=p["name"],
            available=p["available"],
            model_count=len(PROVIDER_MODELS.get(p["id"], {})),
        )
        for p in providers_raw
    ]

    return StatsResponse(
        total_users=total_users,
        total_messages=total_messages,
        total_conversations=total_conversations,
        active_coupons=active_coupons,
        users_by_tier=users_by_tier,
        total_music_tasks=total_music_tasks,
        music_by_status=music_by_status,
        total_council_sessions=total_council_sessions,
        council_by_state=council_by_state,
        total_jam_sessions=total_jam_sessions,
        total_nursery_datasets=total_nursery_datasets,
        total_nursery_jobs=total_nursery_jobs,
        nursery_jobs_by_status=nursery_jobs_by_status,
        total_nursery_models=total_nursery_models,
        total_nursery_apprentices=total_nursery_apprentices,
        total_vault_files=total_vault_files,
        total_vault_storage_mb=total_vault_storage_mb,
        total_neural_vectors=total_neural_vectors,
        providers=providers,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# BUG REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

class AdminReportResponse(BaseModel):
    id: str
    user_email: str
    category: str
    page: Optional[str] = None
    description: str
    browser_info: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class AdminReportListResponse(BaseModel):
    reports: list[AdminReportResponse]
    total: int


class UpdateReportRequest(BaseModel):
    status: Optional[str] = Field(None, pattern="^(open|acknowledged|resolved|closed)$")
    admin_notes: Optional[str] = Field(None, max_length=2000)


@router.get("/reports", response_model=AdminReportListResponse)
async def list_reports(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status", max_length=20),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List bug reports with optional status filter."""
    query = select(BugReport).order_by(BugReport.created_at.desc())

    if status_filter:
        query = query.where(BugReport.status == status_filter)

    # Get total count
    count_query = select(func.count(BugReport.id))
    if status_filter:
        count_query = count_query.where(BugReport.status == status_filter)
    total = await db.scalar(count_query) or 0

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    # Fetch user emails
    user_ids = [r.user_id for r in reports]
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_map = {u.id: u.email for u in users_result.scalars().all()}

    return AdminReportListResponse(
        reports=[
            AdminReportResponse(
                id=str(r.id),
                user_email=users_map.get(r.user_id, "unknown"),
                category=r.category,
                page=r.page,
                description=r.description,
                browser_info=r.browser_info,
                status=r.status,
                admin_notes=r.admin_notes,
                created_at=r.created_at.isoformat(),
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
            for r in reports
        ],
        total=total,
    )


@router.patch("/reports/{report_id}")
async def update_report(
    report_id: UUID,
    request: UpdateReportRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a bug report's status or admin notes."""
    from datetime import timezone

    result = await db.execute(select(BugReport).where(BugReport.id == report_id))
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if request.status is not None:
        report.status = request.status
    if request.admin_notes is not None:
        report.admin_notes = request.admin_notes

    report.updated_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"Report {report_id} updated by {admin.email}: status={report.status}")

    return {"success": True, "status": report.status}
