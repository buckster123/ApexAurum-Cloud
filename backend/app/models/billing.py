"""
Billing Models - Subscriptions, Credits, and Transactions

ApexAurum monetization infrastructure with Stripe integration.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Subscription(Base):
    """
    User subscription synced with Stripe.

    Tiers:
    - free: 50 messages/month, Haiku only, no tools
    - pro: 1000 messages/month, Sonnet + Haiku, all tools, BYOK
    - opus: Unlimited, all models including Opus, multi-provider, API access
    """

    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # User relationship (one subscription per user)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )

    # Stripe identifiers
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Subscription status
    tier: Mapped[str] = mapped_column(String(20), default="free")  # free, pro, opus
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, past_due, canceled, trialing

    # Billing period (from Stripe)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

    # Usage tracking (reset each billing period)
    messages_used: Mapped[int] = mapped_column(Integer, default=0)
    messages_limit: Mapped[int] = mapped_column(Integer, default=50)  # Based on tier

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationship
    user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription {self.tier} for user {self.user_id}>"


class CreditBalance(Base):
    """
    User credit balance for pay-per-use after subscription limits.

    Credits are stored in cents (1 credit = 1 cent = $0.01)
    - $5 purchase = 500 credits
    - $20 purchase = 2500 credits (25% bonus)
    """

    __tablename__ = "credit_balances"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # User relationship (one balance per user)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )

    # Balance in cents ($0.01 = 1 cent)
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)

    # Lifetime totals for analytics
    total_purchased_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_used_cents: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationship
    user = relationship("User", back_populates="credit_balance")

    def __repr__(self):
        return f"<CreditBalance ${self.balance_cents/100:.2f} for user {self.user_id}>"


class CreditTransaction(Base):
    """
    Audit log for all credit transactions.

    Transaction types:
    - purchase: User bought credits via Stripe
    - usage: Credits deducted for AI usage
    - refund: Credits refunded
    - bonus: Promotional credits added
    - subscription_bonus: Credits from subscription perks
    """

    __tablename__ = "credit_transactions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # User reference
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    # Transaction details
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)  # Positive or negative
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)  # Balance after transaction

    # Type and description
    transaction_type: Mapped[str] = mapped_column(String(50))  # purchase, usage, refund, bonus
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # External references
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255))
    message_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL")
    )

    # Metadata (model used, tokens, etc.)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True
    )

    def __repr__(self):
        return f"<CreditTransaction {self.transaction_type} {self.amount_cents}c for user {self.user_id}>"


class WebhookEvent(Base):
    """
    Stripe webhook event log for idempotency.

    Stores the Stripe event ID to prevent duplicate processing.
    Also keeps payload for debugging.
    """

    __tablename__ = "webhook_events"

    # Stripe event ID as primary key (ensures uniqueness)
    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Processing timestamp
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )

    # Full payload for debugging
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)

    def __repr__(self):
        return f"<WebhookEvent {self.id} {self.event_type}>"
