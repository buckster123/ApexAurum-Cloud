"""SQL-based spreading activation for CerebroCortex.

Replaces the igraph-based spreading activation with a 2-hop SQL query.
Uses link type weights and decay per hop to propagate activation.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cerebro.config import (
    LINK_TYPE_WEIGHTS,
    SPREADING_ACTIVATION_THRESHOLD,
    SPREADING_DECAY_PER_HOP,
    SPREADING_MAX_ACTIVATED,
    SPREADING_MAX_HOPS,
)
from app.cerebro.types import LinkType

logger = logging.getLogger(__name__)


async def spreading_activation(
    db: AsyncSession,
    user_id: UUID,
    seed_ids: list[str],
    max_hops: int = SPREADING_MAX_HOPS,
    decay_per_hop: float = SPREADING_DECAY_PER_HOP,
    threshold: float = SPREADING_ACTIVATION_THRESHOLD,
    max_activated: int = SPREADING_MAX_ACTIVATED,
) -> dict[str, float]:
    """Perform spreading activation from seed nodes via SQL.

    Args:
        db: Async database session
        user_id: User ID for multi-tenant isolation
        seed_ids: Initial seed memory IDs (from vector search)
        max_hops: Maximum number of hops (default 2)
        decay_per_hop: Activation decay per hop (default 0.6)
        threshold: Minimum activation to continue spreading
        max_activated: Maximum total activated nodes

    Returns:
        Dict mapping memory_id -> activation_score
    """
    if not seed_ids:
        return {}

    # Initialize activation with seeds at 1.0
    activated: dict[str, float] = {sid: 1.0 for sid in seed_ids}
    frontier = set(seed_ids)

    link_type_weights = {lt.value: w for lt, w in LINK_TYPE_WEIGHTS.items()}

    for hop in range(max_hops):
        if not frontier or len(activated) >= max_activated:
            break

        current_decay = decay_per_hop ** (hop + 1)

        # Query all links from current frontier
        frontier_list = list(frontier)
        result = await db.execute(
            text("""
                SELECT source_id, target_id, weight, link_type
                FROM cerebro_associative_links
                WHERE user_id = :user_id
                  AND (source_id = ANY(:frontier) OR target_id = ANY(:frontier))
            """),
            {"user_id": str(user_id), "frontier": frontier_list},
        )
        rows = result.mappings().all()

        next_frontier: set[str] = set()

        for row in rows:
            source = row["source_id"]
            target = row["target_id"]
            weight = float(row["weight"])
            link_type = row["link_type"]

            # Determine which end is the neighbor
            if source in frontier:
                neighbor = target
                parent_activation = activated.get(source, 0)
            else:
                neighbor = source
                parent_activation = activated.get(target, 0)

            # Compute activation: parent * link_weight * link_type_weight * hop_decay
            type_weight = link_type_weights.get(link_type, 0.5)
            activation = parent_activation * weight * type_weight * current_decay

            if activation < threshold:
                continue

            # Accumulate (max, not sum, to avoid double-counting)
            if neighbor not in activated or activation > activated[neighbor]:
                activated[neighbor] = activation
                next_frontier.add(neighbor)

            if len(activated) >= max_activated:
                break

        frontier = next_frontier - set(seed_ids)  # Don't re-spread from seeds

    return activated
