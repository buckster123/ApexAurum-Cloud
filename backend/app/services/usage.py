"""
Usage Service - Granular usage tracking engine.

Provides atomic increment via PostgreSQL upsert, limit checking,
and usage summary queries. Designed to work alongside the existing
BillingService for fine-grained per-resource tracking.

Usage:
    from app.services.usage import UsageService, COUNTER_MESSAGES_HAIKU

    service = UsageService(db)
    new_count = await service.increment_usage(user_id, COUNTER_MESSAGES_HAIKU)
    allowed, current, limit = await service.check_usage_limit(user_id, COUNTER_MESSAGES_HAIKU, 1000)
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.usage import UsageCounter

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# COUNTER TYPE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

COUNTER_MESSAGES_HAIKU = "messages_haiku"
COUNTER_MESSAGES_SONNET = "messages_sonnet"
COUNTER_MESSAGES_OPUS = "messages_opus"
COUNTER_MESSAGES_OTHER = "messages_other"
COUNTER_SUNO_GENERATIONS = "suno_generations"
COUNTER_COUNCIL_SESSIONS = "council_sessions"
COUNTER_JAM_SESSIONS = "jam_sessions"
COUNTER_NURSERY_TRAINING = "nursery_training_jobs"


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_period() -> str:
    """Return current billing period as YYYY-MM string."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def classify_model_family(provider: str, model: str) -> str:
    """
    Classify a provider/model combination into a counter type.

    Only Anthropic models are classified by family; all other providers
    fall through to COUNTER_MESSAGES_OTHER.
    """
    if provider != "anthropic":
        return COUNTER_MESSAGES_OTHER

    model_lower = model.lower()
    if "opus" in model_lower:
        return COUNTER_MESSAGES_OPUS
    if "sonnet" in model_lower:
        return COUNTER_MESSAGES_SONNET
    if "haiku" in model_lower:
        return COUNTER_MESSAGES_HAIKU

    return COUNTER_MESSAGES_OTHER


# ═══════════════════════════════════════════════════════════════════════════════
# USAGE SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class UsageService:
    """
    Core usage tracking engine.

    Provides atomic counter increments via PostgreSQL upsert,
    limit checking, and usage summary queries.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def increment_usage(
        self,
        user_id: UUID,
        counter_type: str,
        amount: int = 1,
        limit_snapshot: Optional[int] = None,
    ) -> int:
        """
        Atomically increment a usage counter via PostgreSQL upsert.

        If no row exists for (user_id, counter_type, period), one is inserted
        with count=amount. If a row already exists, count is incremented by
        amount and updated_at is refreshed.

        Args:
            user_id: The user whose usage to track.
            counter_type: One of the COUNTER_* constants.
            amount: How much to increment (default 1).
            limit_snapshot: Optional informational snapshot of the limit
                           at the time the counter was created.

        Returns:
            The new count after increment.
        """
        period = get_current_period()

        stmt = pg_insert(UsageCounter).values(
            id=uuid4(),
            user_id=user_id,
            counter_type=counter_type,
            period=period,
            count=amount,
            limit_snapshot=limit_snapshot,
        )

        stmt = stmt.on_conflict_on_constraint(
            'uq_usage_counter_user_type_period'
        ).values(
            count=UsageCounter.count + amount,
            updated_at=datetime.now(timezone.utc),
        )

        stmt = stmt.returning(UsageCounter.count)

        result = await self.db.execute(stmt)
        new_count = result.scalar_one()

        logger.debug(
            f"Usage increment: user={user_id} type={counter_type} "
            f"period={period} amount={amount} new_count={new_count}"
        )

        return new_count

    async def check_usage_limit(
        self,
        user_id: UUID,
        counter_type: str,
        limit: Optional[int],
    ) -> tuple[bool, int, Optional[int]]:
        """
        Check whether a user is within their usage limit.

        Args:
            user_id: The user to check.
            counter_type: One of the COUNTER_* constants.
            limit: The maximum allowed count, or None for unlimited.

        Returns:
            Tuple of (allowed, current_count, limit):
            - allowed: True if usage is permitted.
            - current_count: Current usage count this period.
            - limit: The limit passed in (None means unlimited).
        """
        current = await self.get_current_count(user_id, counter_type)

        if limit is None:
            return (True, current, None)

        return (current < limit, current, limit)

    async def get_current_count(
        self,
        user_id: UUID,
        counter_type: str,
    ) -> int:
        """
        Get the current period's count for a specific counter.

        Returns 0 if no counter row exists for this period.
        """
        period = get_current_period()

        result = await self.db.execute(
            select(UsageCounter.count).where(
                UsageCounter.user_id == user_id,
                UsageCounter.counter_type == counter_type,
                UsageCounter.period == period,
            )
        )

        return result.scalar_one_or_none() or 0

    async def get_usage_summary(
        self,
        user_id: UUID,
        period: Optional[str] = None,
    ) -> dict[str, int]:
        """
        Get all usage counters for a user in a given period.

        Args:
            user_id: The user to query.
            period: Billing period as YYYY-MM string. Defaults to current period.

        Returns:
            Dict mapping counter_type to count, e.g.:
            {"messages_haiku": 42, "suno_generations": 3}
        """
        if period is None:
            period = get_current_period()

        result = await self.db.execute(
            select(UsageCounter.counter_type, UsageCounter.count).where(
                UsageCounter.user_id == user_id,
                UsageCounter.period == period,
            )
        )

        return {row.counter_type: row.count for row in result.all()}
