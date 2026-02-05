"""CerebroCortex data migration.

Migrates existing data from user_vectors and agent_memories into cerebro_memory_nodes.
Also creates associative links from responding_to and conversation_thread relationships.

Uses bulk INSERT...SELECT for atomic, transaction-safe migrations.
"""

import hashlib
import json
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


async def migrate_user_vectors(db: AsyncSession, user_id: Optional[UUID] = None) -> dict:
    """Migrate user_vectors rows into cerebro_memory_nodes using bulk INSERT...SELECT.

    All mapping logic runs server-side in SQL for atomicity and speed.
    """
    user_filter = "AND uv.user_id = :user_id" if user_id else ""
    params: dict = {}
    if user_id:
        params["user_id"] = str(user_id)

    # Count what's available to migrate
    count_result = await db.execute(
        text(f"""
            SELECT COUNT(*) FROM user_vectors uv
            LEFT JOIN cerebro_memory_nodes cmn
                ON cmn.id = uv.id::text AND cmn.user_id = uv.user_id
            WHERE cmn.id IS NULL AND LENGTH(TRIM(uv.content)) >= 5
            {user_filter}
        """),
        params,
    )
    available = count_result.scalar() or 0

    if available == 0:
        return {"migrated": 0, "skipped": 0, "errors": 0}

    # Bulk migrate with all mapping logic in SQL
    try:
        result = await db.execute(
            text(f"""
                INSERT INTO cerebro_memory_nodes (
                    id, user_id, content, content_hash, memory_type, layer, agent_id, visibility,
                    stability, difficulty, access_count, access_timestamps_json,
                    compressed_count, compressed_avg_interval,
                    last_retrievability, last_activation,
                    valence, arousal, salience,
                    conversation_thread,
                    tags, concepts, responding_to, related_agents,
                    source, derived_from,
                    embedding, created_at, last_accessed_at
                )
                SELECT
                    uv.id::text,
                    uv.user_id,
                    uv.content,
                    LEFT(encode(sha256(uv.content::bytea), 'hex'), 16),
                    -- message_type -> memory_type mapping
                    CASE COALESCE(uv.message_type, 'observation')
                        WHEN 'observation' THEN 'semantic'
                        WHEN 'insight' THEN 'semantic'
                        WHEN 'fact' THEN 'semantic'
                        WHEN 'discovery' THEN 'semantic'
                        WHEN 'decision' THEN 'procedural'
                        WHEN 'question' THEN 'episodic'
                        WHEN 'dialogue' THEN 'episodic'
                        WHEN 'response' THEN 'episodic'
                        WHEN 'task' THEN 'prospective'
                        ELSE 'semantic'
                    END,
                    COALESCE(uv.layer, 'working'),
                    COALESCE(uv.agent_id, 'AZOTH'),
                    -- visibility mapping
                    CASE COALESCE(uv.visibility, 'private')
                        WHEN 'village' THEN 'shared'
                        WHEN 'bridge' THEN 'thread'
                        ELSE COALESCE(uv.visibility, 'private')
                    END,
                    1.0,  -- stability
                    5.0,  -- difficulty
                    COALESCE(uv.access_count, 0),
                    CASE WHEN uv.last_accessed_at IS NOT NULL
                        THEN jsonb_build_array(extract(epoch FROM uv.last_accessed_at))
                        ELSE '[]'::jsonb
                    END,
                    0,    -- compressed_count
                    0.0,  -- compressed_avg_interval
                    1.0,  -- last_retrievability
                    0.0,  -- last_activation
                    'neutral',  -- valence
                    LEAST(GREATEST(COALESCE(uv.attention_weight, 1.0) / 2.0, 0.0), 1.0),  -- arousal
                    LEAST(GREATEST(COALESCE(uv.attention_weight, 1.0), 0.0), 1.0),  -- salience
                    uv.conversation_thread,
                    COALESCE(uv.tags, '[]'::jsonb),
                    COALESCE((uv.metadata->'concepts'), '[]'::jsonb),
                    COALESCE(uv.responding_to, '[]'::jsonb),
                    COALESCE(uv.related_agents, '[]'::jsonb),
                    'neo_cortex_migration',
                    '[]'::jsonb,  -- derived_from
                    uv.embedding,
                    COALESCE(uv.created_at, NOW()),
                    uv.last_accessed_at
                FROM user_vectors uv
                LEFT JOIN cerebro_memory_nodes cmn
                    ON cmn.id = uv.id::text AND cmn.user_id = uv.user_id
                WHERE cmn.id IS NULL AND LENGTH(TRIM(uv.content)) >= 5
                {user_filter}
            """),
            params,
        )
        await db.commit()
        migrated = result.rowcount or 0
        skipped = available - migrated
        return {"migrated": migrated, "skipped": skipped, "errors": 0}

    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk user_vectors migration failed: {e}")
        return {"migrated": 0, "skipped": 0, "errors": available, "error_detail": str(e)}


async def migrate_agent_memories(db: AsyncSession, user_id: Optional[UUID] = None) -> dict:
    """Migrate agent_memories rows into cerebro_memory_nodes using bulk INSERT...SELECT."""
    user_filter = "AND am.user_id = :user_id" if user_id else ""
    params: dict = {}
    if user_id:
        params["user_id"] = str(user_id)

    # Check if table exists
    try:
        table_check = await db.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'agent_memories')")
        )
        if not table_check.scalar():
            return {"migrated": 0, "skipped": 0, "errors": 0, "note": "agent_memories table not found"}
    except Exception:
        return {"migrated": 0, "skipped": 0, "errors": 0, "note": "could not check table"}

    # Count available
    count_result = await db.execute(
        text(f"""
            SELECT COUNT(*) FROM agent_memories am
            LEFT JOIN cerebro_memory_nodes cmn
                ON cmn.id = 'am_' || am.id::text AND cmn.user_id = am.user_id
            WHERE cmn.id IS NULL
                AND LENGTH(TRIM(COALESCE(am.key, '') || COALESCE(am.value, ''))) >= 5
            {user_filter}
        """),
        params,
    )
    available = count_result.scalar() or 0

    if available == 0:
        return {"migrated": 0, "skipped": 0, "errors": 0}

    try:
        result = await db.execute(
            text(f"""
                INSERT INTO cerebro_memory_nodes (
                    id, user_id, content, content_hash, memory_type, layer, agent_id, visibility,
                    stability, difficulty, access_count, access_timestamps_json,
                    compressed_count, compressed_avg_interval,
                    last_retrievability, last_activation,
                    valence, arousal, salience,
                    tags, concepts, responding_to, related_agents,
                    source, derived_from,
                    created_at, last_accessed_at
                )
                SELECT
                    'am_' || am.id::text,
                    am.user_id,
                    CASE WHEN am.key IS NOT NULL AND am.key != ''
                        THEN am.key || ': ' || COALESCE(am.value, '')
                        ELSE COALESCE(am.value, '')
                    END,
                    LEFT(encode(sha256(
                        (CASE WHEN am.key IS NOT NULL AND am.key != ''
                            THEN am.key || ': ' || COALESCE(am.value, '')
                            ELSE COALESCE(am.value, '')
                        END)::bytea
                    ), 'hex'), 16),
                    -- memory_type mapping
                    CASE COALESCE(am.memory_type, 'fact')
                        WHEN 'fact' THEN 'semantic'
                        WHEN 'preference' THEN 'procedural'
                        WHEN 'context' THEN 'episodic'
                        WHEN 'relationship' THEN 'affective'
                        ELSE 'semantic'
                    END,
                    CASE WHEN COALESCE(am.confidence, 0.8) >= 0.9 THEN 'long_term' ELSE 'working' END,
                    COALESCE(am.agent_id, 'AZOTH'),
                    'private',
                    COALESCE(am.confidence, 0.8),  -- stability = confidence
                    5.0,
                    COALESCE(am.access_count, 0),
                    CASE WHEN am.last_accessed IS NOT NULL
                        THEN jsonb_build_array(extract(epoch FROM am.last_accessed))
                        ELSE '[]'::jsonb
                    END,
                    0, 0.0, 1.0, 0.0,
                    CASE WHEN am.memory_type = 'relationship' THEN 'positive' ELSE 'neutral' END,
                    0.5,  -- arousal
                    COALESCE(am.confidence, 0.8),  -- salience = confidence
                    jsonb_build_array(COALESCE(am.memory_type, 'fact')),  -- tags
                    CASE WHEN am.key IS NOT NULL AND am.key != ''
                        THEN jsonb_build_array(am.key)
                        ELSE '[]'::jsonb
                    END,  -- concepts
                    '[]'::jsonb,  -- responding_to
                    '[]'::jsonb,  -- related_agents
                    'agent_memory_migration',
                    CASE WHEN am.source_conversation_id IS NOT NULL
                        THEN jsonb_build_array(am.source_conversation_id::text)
                        ELSE '[]'::jsonb
                    END,
                    COALESCE(am.created_at, NOW()),
                    am.last_accessed
                FROM agent_memories am
                LEFT JOIN cerebro_memory_nodes cmn
                    ON cmn.id = 'am_' || am.id::text AND cmn.user_id = am.user_id
                WHERE cmn.id IS NULL
                    AND LENGTH(TRIM(COALESCE(am.key, '') || COALESCE(am.value, ''))) >= 5
                {user_filter}
            """),
            params,
        )
        await db.commit()
        migrated = result.rowcount or 0
        return {"migrated": migrated, "skipped": available - migrated, "errors": 0}

    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk agent_memories migration failed: {e}")
        return {"migrated": 0, "skipped": 0, "errors": available, "error_detail": str(e)}


async def create_responding_to_links(db: AsyncSession, user_id: Optional[UUID] = None) -> int:
    """Create CONTEXTUAL links from responding_to arrays in migrated memories."""
    user_filter = "AND cmn.user_id = :user_id" if user_id else ""
    params: dict = {}
    if user_id:
        params["user_id"] = str(user_id)

    try:
        result = await db.execute(
            text(f"""
                INSERT INTO cerebro_associative_links (
                    id, user_id, source_id, target_id, link_type, weight,
                    activation_count, source_reason, evidence, created_at
                )
                SELECT
                    LEFT(encode(sha256((ref_id || '->' || cmn.id || ':contextual')::bytea), 'hex'), 16),
                    cmn.user_id,
                    ref_id,
                    cmn.id,
                    'contextual',
                    0.5,
                    1,
                    'migration',
                    'responding_to relationship',
                    NOW()
                FROM cerebro_memory_nodes cmn,
                     jsonb_array_elements_text(cmn.responding_to) AS ref_id
                WHERE jsonb_array_length(cmn.responding_to) > 0
                  AND cmn.source IN ('neo_cortex_migration', 'agent_memory_migration')
                  AND ref_id IS NOT NULL AND ref_id != ''
                  {user_filter}
                ON CONFLICT ON CONSTRAINT uq_cerebro_link DO NOTHING
            """),
            params,
        )
        await db.commit()
        return result.rowcount or 0

    except Exception as e:
        await db.rollback()
        logger.error(f"Contextual link creation failed: {e}")
        return 0


async def create_thread_links(db: AsyncSession, user_id: Optional[UUID] = None) -> int:
    """Create TEMPORAL links between sequential memories in the same conversation_thread."""
    user_filter = "AND a.user_id = :user_id" if user_id else ""
    params: dict = {}
    if user_id:
        params["user_id"] = str(user_id)

    try:
        result = await db.execute(
            text(f"""
                INSERT INTO cerebro_associative_links (
                    id, user_id, source_id, target_id, link_type, weight,
                    activation_count, source_reason, evidence, created_at
                )
                SELECT
                    LEFT(encode(sha256((a.id || '->' || b.id || ':temporal')::bytea), 'hex'), 16),
                    a.user_id,
                    a.id,
                    b.id,
                    'temporal',
                    0.4,
                    1,
                    'migration',
                    'Same conversation thread',
                    NOW()
                FROM cerebro_memory_nodes a
                JOIN cerebro_memory_nodes b
                    ON a.user_id = b.user_id
                    AND a.conversation_thread = b.conversation_thread
                    AND a.conversation_thread IS NOT NULL
                    AND b.created_at = (
                        SELECT MIN(c.created_at)
                        FROM cerebro_memory_nodes c
                        WHERE c.user_id = a.user_id
                          AND c.conversation_thread = a.conversation_thread
                          AND c.created_at > a.created_at
                          AND c.source IN ('neo_cortex_migration', 'agent_memory_migration')
                    )
                WHERE a.source IN ('neo_cortex_migration', 'agent_memory_migration')
                  AND b.source IN ('neo_cortex_migration', 'agent_memory_migration')
                  {user_filter}
                ON CONFLICT ON CONSTRAINT uq_cerebro_link DO NOTHING
            """),
            params,
        )
        await db.commit()
        return result.rowcount or 0

    except Exception as e:
        await db.rollback()
        logger.error(f"Thread link creation failed: {e}")
        return 0


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
    1. Migrate user_vectors -> cerebro_memory_nodes (bulk SQL)
    2. Migrate agent_memories -> cerebro_memory_nodes (bulk SQL)
    3. Create CONTEXTUAL links from responding_to (bulk SQL)
    4. Create TEMPORAL links from conversation threads (bulk SQL)
    5. Register default agents (per user)
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
