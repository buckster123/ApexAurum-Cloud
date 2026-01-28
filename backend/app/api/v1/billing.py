"""
Billing Endpoints - Subscriptions, Credits, and Stripe Checkout.

ApexAurum monetization API.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.billing import CreditTransaction
from app.auth.deps import get_current_user
from app.config import get_settings, TIER_LIMITS, CREDIT_PACKS
from app.services.billing import BillingService
from app.schemas.billing import (
    SubscriptionCheckoutRequest,
    SubscriptionCheckoutResponse,
    CreditsCheckoutRequest,
    CreditsCheckoutResponse,
    CreditTransactionResponse,
    CreditTransactionsResponse,
    BillingStatusResponse,
    TierFeatures,
    PortalSessionRequest,
    PortalSessionResponse,
    PricingTier,
    CreditPack,
    PricingResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# BILLING STATUS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/status", response_model=BillingStatusResponse)
async def get_billing_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current billing status for the authenticated user.

    Returns:
    - Current subscription tier and status
    - Message usage and limits
    - Credit balance
    - Available features for the tier

    Call this on app load to determine UI state.
    """
    billing_service = BillingService(db)
    status_data = await billing_service.get_subscription_status(user.id)

    return BillingStatusResponse(
        tier=status_data["tier"],
        subscription_status=status_data["subscription_status"],
        messages_used=status_data["messages_used"],
        messages_limit=status_data["messages_limit"],
        messages_remaining=status_data["messages_remaining"],
        current_period_end=status_data["current_period_end"],
        cancel_at_period_end=status_data["cancel_at_period_end"],
        credit_balance_cents=status_data["credit_balance_cents"],
        credit_balance_usd=status_data["credit_balance_usd"],
        features=TierFeatures(**status_data["features"]),
        at_limit=status_data["at_limit"],
        near_limit=status_data["near_limit"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION CHECKOUT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/checkout/subscription", response_model=SubscriptionCheckoutResponse)
async def create_subscription_checkout(
    request: SubscriptionCheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe Checkout session for subscription upgrade.

    Args:
        tier: 'pro' or 'opus'

    Returns:
        checkout_url: Redirect user to this URL to complete payment
        session_id: Stripe session ID for reference

    After successful payment, Stripe webhook will update the subscription.
    """
    if request.tier not in ("pro", "opus"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier. Must be 'pro' or 'opus'."
        )

    # Build URLs - prefer HTTPS production URL over localhost
    base_url = "http://localhost:3000"
    for origin in settings.allowed_origins_list:
        if origin.startswith("https://"):
            base_url = origin
            break
    success_url = request.success_url or f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = request.cancel_url or f"{base_url}/billing"

    try:
        billing_service = BillingService(db)
        result = await billing_service.create_subscription_checkout(
            user_id=user.id,
            tier=request.tier,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        await db.commit()
        return SubscriptionCheckoutResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CREDITS CHECKOUT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/checkout/credits", response_model=CreditsCheckoutResponse)
async def create_credits_checkout(
    request: CreditsCheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe Checkout session for credit purchase.

    Args:
        pack: 'small' ($5/500 credits) or 'large' ($20/2500 credits with 25% bonus)

    Returns:
        checkout_url: Redirect user to this URL to complete payment
        session_id: Stripe session ID for reference

    After successful payment, Stripe webhook will add credits to balance.
    """
    if request.pack not in ("small", "large"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pack. Must be 'small' or 'large'."
        )

    # Build URLs - prefer HTTPS production URL over localhost
    base_url = "http://localhost:3000"
    for origin in settings.allowed_origins_list:
        if origin.startswith("https://"):
            base_url = origin
            break
    success_url = request.success_url or f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = request.cancel_url or f"{base_url}/billing"

    try:
        billing_service = BillingService(db)
        result = await billing_service.create_credits_checkout(
            user_id=user.id,
            pack=request.pack,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        await db.commit()
        return CreditsCheckoutResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER PORTAL
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    request: PortalSessionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe Customer Portal session.

    The portal allows users to:
    - Update payment method
    - View invoices
    - Cancel subscription
    - Update billing details

    Returns:
        portal_url: Redirect user to this URL to access the portal
    """
    # Build return URL
    base_url = settings.allowed_origins_list[0] if settings.allowed_origins_list else "http://localhost:3000"
    return_url = request.return_url or f"{base_url}/billing"

    try:
        billing_service = BillingService(db)
        result = await billing_service.create_portal_session(
            user_id=user.id,
            return_url=return_url,
        )
        return PortalSessionResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Portal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CREDIT TRANSACTIONS (Audit Log)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/transactions", response_model=CreditTransactionsResponse)
async def get_credit_transactions(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get credit transaction history for the authenticated user.

    Returns paginated list of transactions including:
    - Purchases
    - Usage deductions
    - Bonuses/refunds
    """
    from sqlalchemy import func

    # Get transactions
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()

    # Get total count
    count_result = await db.execute(
        select(func.count(CreditTransaction.id))
        .where(CreditTransaction.user_id == user.id)
    )
    total = count_result.scalar() or 0

    return CreditTransactionsResponse(
        transactions=[
            CreditTransactionResponse(
                id=t.id,
                amount_cents=t.amount_cents,
                balance_after=t.balance_after,
                transaction_type=t.transaction_type,
                description=t.description,
                created_at=t.created_at,
            )
            for t in transactions
        ],
        total=total,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PRICING DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/pricing", response_model=PricingResponse)
async def get_pricing():
    """
    Get all pricing information for display.

    Returns tier details and credit pack options.
    No authentication required - this is public info.
    """
    tiers = [
        PricingTier(
            id="free",
            name="Seeker",
            tagline="Begin your journey",
            price_monthly=3,
            messages_per_month=50,
            features=[
                "50 messages per month",
                "Haiku model",
                "Basic chat interface",
                "Conversation history",
            ],
            popular=False,
        ),
        PricingTier(
            id="pro",
            name="Alchemist",
            tagline="Transform your workflow",
            price_monthly=10,
            messages_per_month=1000,
            features=[
                "1,000 messages per month",
                "Sonnet + Haiku models",
                "All 35 tools (The Athanor's Hands)",
                "Bring Your Own Key (BYOK)",
                "Village Protocol GUI",
                "Neo-Cortex memory",
                "Export without watermark",
            ],
            popular=True,
        ),
        PricingTier(
            id="opus",
            name="Adept",
            tagline="Unlimited mastery",
            price_monthly=30,
            messages_per_month=None,
            features=[
                "Unlimited messages",
                "All models including Opus",
                "Multi-provider LLMs (Groq, DeepSeek, etc.)",
                "API access",
                "Priority support",
                "All Pro features",
            ],
            popular=False,
        ),
    ]

    credit_packs = [
        CreditPack(
            id="small",
            name="Starter Pack",
            price_usd=5.00,
            credits=500,
            bonus_credits=0,
        ),
        CreditPack(
            id="large",
            name="Power Pack",
            price_usd=20.00,
            credits=2000,
            bonus_credits=500,  # 25% bonus
        ),
    ]

    return PricingResponse(tiers=tiers, credit_packs=credit_packs)
