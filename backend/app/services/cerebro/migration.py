"""CerebroCortex data migration.

Migrates existing data from user_vectors and agent_memories into cerebro_memory_nodes.
Also creates associative links from responding_to and conversation_thread relationships.
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# message_type -> memory_type mapping
MESSAGE_TYPE_MAP = {
    "observation": "semantic",
    "insight": "semantic",
    "fact": "semantic",
    "discovery": "semantic",
    "decision": "procedural",
    "question": "episodic",
    "dialogue": "episodic",
    "response": "episodic",
    "task": "prospective",
    "preference": "procedural",
    "context": "episodic",
    "relationship": "affective",
}

# old visibility -> new visibility
VISIBILITY_MAP = {
    "private": "private",
    "village": "shared",
    "bridge": "thread",
    "shared": "shared",
    "thread": "thread",
}

# agent_memories.memory_type -> cerebro memory_type
AGENT_MEM_TYPE_MAP = {
    "fact": "semantic",
    "preference": "procedural",
    "context": "episodic",
    "relationship": "affective",
}


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


async def migrate_user_vectors(db: AsyncSession, user_id: Optional[UUID] = None) -> dict:
    """Migrate user_vectors rows into cerebro_memory_nodes.

    Args:
        db: Database session
        user_id: If provided, only migrate for this user. Otherwise migrate all.

    Returns:
        Dict with counts: migrated, skipped, errors
    """
    where = ""
    params: dict = {}
    if user_id:
        where = "WHERE uv.user_id = :user_id"
        params["user_id"] = str(user_id)

    # Get rows not yet migrated (by checking id not already in cerebro)
    result = await db.execute(
        text(f"""
            SELECT uv.*
            FROM user_vectors uv
            LEFT JOIN cerebro_memory_nodes cmn
                ON cmn.id = uv.id::text AND cmn.user_id = uv.user_id
            WHERE cmn.id IS NULL
            {"AND uv.user_id = :user_id" if user_id else ""}
            ORDER BY uv.created_at ASC
        """),
        params,
    )
    rows = result.mappings().all()

    migrated = 0
    skipped = 0
    errors = 0

    for row in rows:
        try:
            content = row["content"]
            if not content or len(content.strip()) < 5:
                skipped += 1
                continue

            content_hash = _content_hash(content)
            msg_type = row.get("message_type", "observation") or "observation"
            memory_type = MESSAGE_TYPE_MAP.get(msg_type, "semantic")
            layer = row.get("layer", "working") or "working"
            agent_id = row.get("agent_id") or "AZOTH"
            visibility = VISIBILITY_MAP.get(row.get("visibility", "private"), "private")
            attention_weight = float(row.get("attention_weight", 1.0) or 1.0)
            access_count = int(row.get("access_count", 0) or 0)

            # Build access_timestamps from last_accessed_at
            last_accessed = row.get("last_accessed_at")
            access_timestamps = []
            if last_accessed:
                if hasattr(last_accessed, 'timestamp'):
                    access_timestamps = [last_accessed.timestamp()]
                else:
                    access_timestamps = [time.time()]

            # Parse JSONB fields
            tags = row.get("tags", [])
            if isinstance(tags, str):
                tags = json.loads(tags)
            responding_to = row.get("responding_to", [])
            if isinstance(responding_to, str):
                responding_to = json.loads(responding_to)
            related_agents = row.get("related_agents", [])
            if isinstance(related_agents, str):
                related_agents = json.loads(related_agents)

            # Try to extract concepts from metadata
            metadata = row.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            concepts = metadata.get("concepts", []) if isinstance(metadata, dict) else []

            # Clamp values
            salience = min(max(attention_weight, 0.0), 1.0)
            arousal = min(max(attention_weight / 2.0, 0.0), 1.0)

            node_id = str(row["id"])
            uid = str(row["user_id"])

            insert_params = {
                "id": node_id,
                "user_id": uid,
                "content": content,
                "content_hash": content_hash,
                "memory_type": memory_type,
                "layer": layer,
                "agent_id": agent_id,
                "visibility": visibility,
                "stability": 1.0,
                "difficulty": 5.0,
                "access_count": access_count,
                "access_timestamps_json": json.dumps(access_timestamps),
                "compressed_count": 0,
                "compressed_avg_interval": 0.0,
                "last_retrievability": 1.0,
                "last_activation": 0.0,
                "valence": "neutral",
                "arousal": arousal,
                "salience": salience,
                "conversation_thread": row.get("conversation_thread"),
                "tags": json.dumps(tags),
                "concepts": json.dumps(concepts),
                "responding_to": json.dumps(responding_to),
                "related_agents": json.dumps(related_agents),
                "source": "neo_cortex_migration",
                "derived_from": json.dumps([]),
                "created_at": row["created_at"].isoformat() if row.get("created_at") else datetime.now().isoformat(),
                "last_accessed_at": last_accessed.isoformat() if last_accessed else None,
            }

            # Check if embedding exists
            has_embedding = row.get("embedding") is not None

            if has_embedding:
                await db.execute(
                    text("""
                        INSERT INTO cerebro_memory_nodes (
                            id, user_id, content, content_hash, memory_type, layer, agent_id, visibility,
                            stability, difficulty, access_count, access_timestamps_json,
                            compressed_count, compressed_avg_interval,
                            last_retrievability, last_activation,
                            valence, arousal, salience,
                            conversation_thread,
                            tags, concepts, responding_to, related_agents,
                            source, derived_from,
                            created_at, last_accessed_at, embedding
                        )
                        SELECT
                            :id, :user_id::uuid, :content, :content_hash, :memory_type, :layer, :agent_id, :visibility,
                            :stability, :difficulty, :access_count, :access_timestamps_json::jsonb,
                            :compressed_count, :compressed_avg_interval,
                            :last_retrievability, :last_activation,
                            :valence, :arousal, :salience,
                            :conversation_thread,
                            :tags::jsonb, :concepts::jsonb, :responding_to::jsonb, :related_agents::jsonb,
                            :source, :derived_from::jsonb,
                            :created_at, :last_accessed_at, uv.embedding
                        FROM user_vectors uv
                        WHERE uv.id = :src_id::uuid AND uv.user_id = :user_id::uuid
                    """),
                    {**insert_params, "src_id": node_id},
                )
            else:
                await db.execute(
                    text("""
                        INSERT INTO cerebro_memory_nodes (
                            id, user_id, content, content_hash, memory_type, layer, agent_id, visibility,
                            stability, difficulty, access_count, access_timestamps_json,
                            compressed_count, compressed_avg_interval,
                            last_retrievability, last_activation,
                            valence, arousal, salience,
                            conversation_thread,
                            tags, concepts, responding_to, related_agents,
                            source, derived_from,
                            created_at, last_accessed_at
                        ) VALUES (
                            :id, :user_id::uuid, :content, :content_hash, :memory_type, :layer, :agent_id, :visibility,
                            :stability, :difficulty, :access_count, :access_timestamps_json::jsonb,
                            :compressed_count, :compressed_avg_interval,
                            :last_retrievability, :last_activation,
                            :valence, :arousal, :salience,
                            :conversation_thread,
                            :tags::jsonb, :concepts::jsonb, :responding_to::jsonb, :related_agents::jsonb,
                            :source, :derived_from::jsonb,
                            :created_at, :last_accessed_at
                        )
                    """),
                    insert_params,
                )

            migrated += 1

        except Exception as e:
            logger.error(f"Failed to migrate user_vector {row.get('id')}: {e}")
            errors += 1

    if migrated > 0:
        await db.commit()

    return {"migrated": migrated, "skipped": skipped, "errors": errors}


async def migrate_agent_memories(db: AsyncSession, user_id: Optional[UUID] = None) -> dict:
    """Migrate agent_memories rows into cerebro_memory_nodes.

    Agent memories are key-value pairs stored by agents (facts, preferences, etc).
    They get a 'am_' prefix on their ID to avoid collisions with user_vectors.
    """
    params: dict = {}
    user_filter = ""
    if user_id:
        user_filter = "AND am.user_id = :user_id"
        params["user_id"] = str(user_id)

    result = await db.execute(
        text(f"""
            SELECT am.*
            FROM agent_memories am
            LEFT JOIN cerebro_memory_nodes cmn
                ON cmn.id = 'am_' || am.id::text AND cmn.user_id = am.user_id
            WHERE cmn.id IS NULL {user_filter}
            ORDER BY am.created_at ASC
        """),
        params,
    )
    rows = result.mappings().all()

    migrated = 0
    skipped = 0
    errors = 0

    for row in rows:
        try:
            key = row.get("key", "") or ""
            value = row.get("value", "") or ""
            content = f"{key}: {value}" if key else value

            if len(content.strip()) < 5:
                skipped += 1
                continue

            content_hash = _content_hash(content)
            am_type = row.get("memory_type", "fact") or "fact"
            memory_type = AGENT_MEM_TYPE_MAP.get(am_type, "semantic")
            confidence = float(row.get("confidence", 0.8) or 0.8)
            layer = "long_term" if confidence >= 0.9 else "working"
            agent_id = row.get("agent_id") or "AZOTH"
            access_count = int(row.get("access_count", 0) or 0)

            last_accessed = row.get("last_accessed")
            access_timestamps = []
            if last_accessed:
                if hasattr(last_accessed, 'timestamp'):
                    access_timestamps = [last_accessed.timestamp()]

            valence = "positive" if am_type == "relationship" else "neutral"

            # Source conversation as derived_from
            src_conv = row.get("source_conversation_id")
            derived_from = [str(src_conv)] if src_conv else []

            node_id = f"am_{row['id']}"
            uid = str(row["user_id"])

            await db.execute(
                text("""
                    INSERT INTO cerebro_memory_nodes (
                        id, user_id, content, content_hash, memory_type, layer, agent_id, visibility,
                        stability, difficulty, access_count, access_timestamps_json,
                        compressed_count, compressed_avg_interval,
                        last_retrievability, last_activation,
                        valence, arousal, salience,
                        tags, concepts, responding_to, related_agents,
                        source, derived_from,
                        created_at, last_accessed_at
                    ) VALUES (
                        :id, :user_id::uuid, :content, :content_hash, :memory_type, :layer, :agent_id, :visibility,
                        :stability, :difficulty, :access_count, :access_timestamps_json::jsonb,
                        :compressed_count, :compressed_avg_interval,
                        :last_retrievability, :last_activation,
                        :valence, :arousal, :salience,
                        :tags::jsonb, :concepts::jsonb, :responding_to::jsonb, :related_agents::jsonb,
                        :source, :derived_from::jsonb,
                        :created_at, :last_accessed_at
                    )
                """),
                {
                    "id": node_id,
                    "user_id": uid,
                    "content": content[:2000],
                    "content_hash": content_hash,
                    "memory_type": memory_type,
                    "layer": layer,
                    "agent_id": agent_id,
                    "visibility": "private",
                    "stability": confidence,
                    "difficulty": 5.0,
                    "access_count": access_count,
                    "access_timestamps_json": json.dumps(access_timestamps),
                    "compressed_count": 0,
                    "compressed_avg_interval": 0.0,
                    "last_retrievability": 1.0,
                    "last_activation": 0.0,
                    "valence": valence,
                    "arousal": 0.5,
                    "salience": confidence,
                    "tags": json.dumps([am_type]),
                    "concepts": json.dumps([key] if key else []),
                    "responding_to": json.dumps([]),
                    "related_agents": json.dumps([]),
                    "source": "agent_memory_migration",
                    "derived_from": json.dumps(derived_from),
                    "created_at": row["created_at"].isoformat() if row.get("created_at") else datetime.now().isoformat(),
                    "last_accessed_at": last_accessed.isoformat() if last_accessed else None,
                },
            )
            migrated += 1

        except Exception as e:
            logger.error(f"Failed to migrate agent_memory {row.get('id')}: {e}")
            errors += 1

    if migrated > 0:
        await db.commit()

    return {"migrated": migrated, "skipped": skipped, "errors": errors}


async def create_responding_to_links(db: AsyncSession, user_id: Optional[UUID] = None) -> int:
    """Create CONTEXTUAL links from responding_to arrays in migrated memories."""
    params: dict = {}
    user_filter = ""
    if user_id:
        user_filter = "AND cmn.user_id = :user_id"
        params["user_id"] = str(user_id)

    # Find memories with non-empty responding_to arrays
    result = await db.execute(
        text(f"""
            SELECT cmn.id, cmn.user_id, cmn.responding_to
            FROM cerebro_memory_nodes cmn
            WHERE jsonb_array_length(cmn.responding_to) > 0
              AND cmn.source IN ('neo_cortex_migration', 'agent_memory_migration')
              {user_filter}
        """),
        params,
    )
    rows = result.mappings().all()

    link_count = 0
    for row in rows:
        responding_to = row["responding_to"]
        if isinstance(responding_to, str):
            responding_to = json.loads(responding_to)

        for ref_id in responding_to:
            if not ref_id:
                continue
            try:
                link_id = _content_hash(f"{ref_id}->{row['id']}:contextual")
                await db.execute(
                    text("""
                        INSERT INTO cerebro_associative_links (
                            id, user_id, source_id, target_id, link_type, weight,
                            activation_count, source_reason, evidence, created_at
                        ) VALUES (
                            :id, :user_id, :source_id, :target_id, 'contextual', 0.5,
                            1, 'migration', 'responding_to relationship', NOW()
                        )
                        ON CONFLICT ON CONSTRAINT uq_cerebro_link DO NOTHING
                    """),
                    {
                        "id": link_id,
                        "user_id": str(row["user_id"]),
                        "source_id": str(ref_id),
                        "target_id": row["id"],
                    },
                )
                link_count += 1
            except Exception as e:
                logger.debug(f"Link creation skipped for {ref_id}->{row['id']}: {e}")

    if link_count > 0:
        await db.commit()
    return link_count


async def create_thread_links(db: AsyncSession, user_id: Optional[UUID] = None) -> int:
    """Create TEMPORAL links between memories in the same conversation_thread."""
    params: dict = {}
    user_filter = ""
    if user_id:
        user_filter = "AND cmn.user_id = :user_id"
        params["user_id"] = str(user_id)

    # Get distinct threads with multiple memories
    result = await db.execute(
        text(f"""
            SELECT cmn.user_id, cmn.conversation_thread, array_agg(cmn.id ORDER BY cmn.created_at) as node_ids
            FROM cerebro_memory_nodes cmn
            WHERE cmn.conversation_thread IS NOT NULL
              AND cmn.source IN ('neo_cortex_migration', 'agent_memory_migration')
              {user_filter}
            GROUP BY cmn.user_id, cmn.conversation_thread
            HAVING COUNT(*) > 1
        """),
        params,
    )
    rows = result.mappings().all()

    link_count = 0
    for row in rows:
        node_ids = row["node_ids"]
        uid = str(row["user_id"])

        # Create temporal links between sequential pairs
        for i in range(len(node_ids) - 1):
            try:
                link_id = _content_hash(f"{node_ids[i]}->{node_ids[i+1]}:temporal")
                await db.execute(
                    text("""
                        INSERT INTO cerebro_associative_links (
                            id, user_id, source_id, target_id, link_type, weight,
                            activation_count, source_reason, evidence, created_at
                        ) VALUES (
                            :id, :user_id, :source_id, :target_id, 'temporal', 0.4,
                            1, 'migration', 'Same conversation thread', NOW()
                        )
                        ON CONFLICT ON CONSTRAINT uq_cerebro_link DO NOTHING
                    """),
                    {
                        "id": link_id,
                        "user_id": uid,
                        "source_id": node_ids[i],
                        "target_id": node_ids[i + 1],
                    },
                )
                link_count += 1
            except Exception as e:
                logger.debug(f"Thread link skipped: {e}")

    if link_count > 0:
        await db.commit()
    return link_count


async def register_default_agents(db: AsyncSession, user_id: UUID) -> int:
    """Register the four ApexAurum agents for a user."""
    from app.cerebro.config import AGENT_PROFILES

    registered = 0
    for agent_id, profile in AGENT_PROFILES.items():
        try:
            await db.execute(
                text("""
                    INSERT INTO cerebro_agents (
                        id, user_id, display_name, generation, lineage, specialization,
                        origin_story, color, symbol, registered_at
                    ) VALUES (
                        :id, :user_id, :display_name, :generation, :lineage, :specialization,
                        :origin_story, :color, :symbol, NOW()
                    )
                    ON CONFLICT (id, user_id) DO NOTHING
                """),
                {
                    "id": agent_id,
                    "user_id": str(user_id),
                    "display_name": profile["display_name"],
                    "generation": profile["generation"],
                    "lineage": profile["lineage"],
                    "specialization": profile["specialization"],
                    "origin_story": profile.get("origin_story", ""),
                    "color": profile["color"],
                    "symbol": profile["symbol"],
                },
            )
            registered += 1
        except Exception as e:
            logger.debug(f"Agent registration skipped for {agent_id}: {e}")

    if registered > 0:
        await db.commit()
    return registered


async def run_full_migration(db: AsyncSession, user_id: Optional[UUID] = None) -> dict:
    """Run the complete migration pipeline.

    Steps:
    1. Migrate user_vectors -> cerebro_memory_nodes
    2. Migrate agent_memories -> cerebro_memory_nodes
    3. Create CONTEXTUAL links from responding_to
    4. Create TEMPORAL links from conversation threads
    5. Register default agents (per user)

    Returns:
        Dict with complete migration report.
    """
    logger.info(f"Starting CerebroCortex migration (user_id={user_id or 'ALL'})")

    report = {
        "user_vectors": {"migrated": 0, "skipped": 0, "errors": 0},
        "agent_memories": {"migrated": 0, "skipped": 0, "errors": 0},
        "contextual_links": 0,
        "temporal_links": 0,
        "agents_registered": 0,
    }

    # Step 1: Migrate user_vectors
    try:
        report["user_vectors"] = await migrate_user_vectors(db, user_id)
        logger.info(f"user_vectors: {report['user_vectors']}")
    except Exception as e:
        logger.error(f"user_vectors migration failed: {e}")
        report["user_vectors"]["errors"] = -1

    # Step 2: Migrate agent_memories
    try:
        report["agent_memories"] = await migrate_agent_memories(db, user_id)
        logger.info(f"agent_memories: {report['agent_memories']}")
    except Exception as e:
        logger.error(f"agent_memories migration failed: {e}")
        report["agent_memories"]["errors"] = -1

    # Step 3: Create responding_to links
    try:
        report["contextual_links"] = await create_responding_to_links(db, user_id)
        logger.info(f"contextual_links: {report['contextual_links']}")
    except Exception as e:
        logger.error(f"Contextual link creation failed: {e}")

    # Step 4: Create thread links
    try:
        report["temporal_links"] = await create_thread_links(db, user_id)
        logger.info(f"temporal_links: {report['temporal_links']}")
    except Exception as e:
        logger.error(f"Thread link creation failed: {e}")

    # Step 5: Register agents
    if user_id:
        try:
            report["agents_registered"] = await register_default_agents(db, user_id)
        except Exception as e:
            logger.error(f"Agent registration failed: {e}")
    else:
        # Register for all users who have data
        try:
            r = await db.execute(
                text("SELECT DISTINCT user_id FROM cerebro_memory_nodes")
            )
            user_ids = [row[0] for row in r]
            for uid in user_ids:
                count = await register_default_agents(db, uid)
                report["agents_registered"] += count
        except Exception as e:
            logger.error(f"Bulk agent registration failed: {e}")

    logger.info(f"CerebroCortex migration complete: {report}")
    return report
