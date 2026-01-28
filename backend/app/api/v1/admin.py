"""
Admin API Endpoints - User management, stats, and system controls.

All endpoints require is_admin=True on the authenticated user.
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.billing import Subscription, CreditBalance, Coupon
from app.models.conversation import Message
from app.auth.deps import get_current_user

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


class StatsResponse(BaseModel):
    total_users: int
    total_messages: int
    active_coupons: int
    users_by_tier: dict


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
    search: Optional[str] = Query(None),
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
            tier=subscription.tier if subscription else "free",
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
    if request.tier not in ["free", "pro", "opus"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tier must be 'free', 'pro', or 'opus'"
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
    tier_limits = {"free": 50, "pro": 1000, "opus": None}
    subscription.messages_limit = tier_limits.get(request.tier)

    await db.commit()

    logger.info(f"Admin {admin.email} set tier={request.tier} for user {user_id}")

    return {"status": "updated", "user_id": str(user_id), "tier": request.tier}


# ═══════════════════════════════════════════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide statistics."""
    # Total users
    user_count = await db.execute(select(func.count(User.id)))
    total_users = user_count.scalar()

    # Total messages
    try:
        msg_count = await db.execute(select(func.count(Message.id)))
        total_messages = msg_count.scalar()
    except Exception:
        total_messages = 0

    # Active coupons
    coupon_count = await db.execute(
        select(func.count(Coupon.id)).where(Coupon.is_active == True)
    )
    active_coupons = coupon_count.scalar()

    # Users by tier
    tier_query = await db.execute(
        select(Subscription.tier, func.count(Subscription.id))
        .group_by(Subscription.tier)
    )
    tier_results = tier_query.fetchall()

    users_by_tier = {"Seeker": 0, "Alchemist": 0, "Adept": 0}
    tier_names = {"free": "Seeker", "pro": "Alchemist", "opus": "Adept"}

    for tier, count in tier_results:
        name = tier_names.get(tier, tier)
        users_by_tier[name] = count

    # Add users without subscriptions as Seeker
    users_with_sub = sum(users_by_tier.values())
    users_by_tier["Seeker"] += total_users - users_with_sub

    return StatsResponse(
        total_users=total_users,
        total_messages=total_messages,
        active_coupons=active_coupons,
        users_by_tier=users_by_tier,
    )
