"""
CerebroCortex Tools - Unified Memory System

Advanced memory operations powered by CerebroCortex engine:
ACT-R + FSRS hybrid strength, pgvector search, spreading activation,
semantic enrichment, emotional analysis, and associative linking.

"The mind that remembers across lifetimes"
"""

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from . import registry
from .base import BaseTool, ToolSchema, ToolResult, ToolContext, ToolCategory

logger = logging.getLogger(__name__)


def _get_service():
    """Lazy import to avoid circular deps."""
    from app.services.cerebro import get_cerebro_service
    return get_cerebro_service()


# =============================================================================
# CORTEX REMEMBER - Store with CerebroCortex pipeline
# =============================================================================

class CortexRememberTool(BaseTool):
    """Store memory through CerebroCortex pipeline."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="cortex_remember",
            description="""Store a memory in CerebroCortex unified memory system.

Incoming memories are processed through:
- **Thalamic gating**: Type classification, salience estimation, deduplication
- **Semantic enrichment**: Concept extraction
- **Emotional analysis**: Valence, arousal, salience adjustment
- **ACT-R + FSRS strength**: Hybrid memory strength model

Memory types: episodic, semantic, procedural, affective, prospective, schematic
Layers: sensory (hours), working (days), long_term (weeks), cortex (permanent)
Visibility: private (agent only), shared (all agents), thread (cross-agent)

Example: cortex_remember(content="User prefers dark mode", tags=["preference"])""",
            category=ToolCategory.MEMORY,
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The memory content to store",
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["episodic", "semantic", "procedural", "affective", "prospective", "schematic"],
                        "description": "Memory type (auto-classified if not provided)",
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["private", "shared", "thread"],
                        "description": "Who can see this memory (default: private)",
                        "default": "private",
                    },
                    "salience": {
                        "type": "number",
                        "description": "Importance 0-1 (auto-estimated if not provided)",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for organization",
                    },
                    "related_agents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Agents involved",
                    },
                },
                "required": ["content"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        content = params.get("content", "").strip()
        if not content:
            return ToolResult(success=False, error="Content is required")
        if len(content) > 50000:
            return ToolResult(success=False, error="Content exceeds 50KB limit")

        try:
            from app.database import async_session

            service = _get_service()
            agent_id = context.metadata.get("agent_id", "AZOTH") if context.metadata else "AZOTH"
            user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

            async with async_session() as db:
                result = await service.remember(
                    db=db,
                    user_id=user_uuid,
                    content=content,
                    memory_type=params.get("memory_type"),
                    tags=params.get("tags"),
                    salience=params.get("salience"),
                    agent_id=agent_id,
                    visibility=params.get("visibility", "private"),
                    related_agents=params.get("related_agents"),
                    source="tool",
                )

            if result is None:
                return ToolResult(success=False, error="Content too short or filtered by gating")

            return ToolResult(
                success=True,
                result={
                    **result,
                    "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
                    "message": f"Memory {result.get('action', 'stored')} ({result.get('memory_type', 'unknown')})",
                },
            )

        except Exception as e:
            logger.exception("Cortex remember error")
            return ToolResult(success=False, error=f"Failed to store: {str(e)}")


# =============================================================================
# CORTEX RECALL - Search with spreading activation
# =============================================================================

class CortexRecallTool(BaseTool):
    """Search memory with CerebroCortex recall pipeline."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="cortex_recall",
            description="""Search CerebroCortex memory using vector search + spreading activation.

Recall pipeline:
1. Vector similarity search (pgvector)
2. Spreading activation through associative links
3. ACT-R + FSRS strength scoring
4. Combined ranking (35% vector + 30% activation + 20% retrievability + 15% salience)
5. Hebbian strengthening of recalled memories

Returns memories ranked by combined score with full scoring breakdown.

Example: cortex_recall(query="user preferences", top_k=5)""",
            category=ToolCategory.MEMORY,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Max results (default: 5)",
                        "default": 5,
                    },
                    "memory_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by memory types",
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["private", "shared", "all"],
                        "description": "Visibility filter (default: all)",
                        "default": "all",
                    },
                    "min_salience": {
                        "type": "number",
                        "description": "Minimum salience (0-1, default: 0.0)",
                        "default": 0.0,
                    },
                },
                "required": ["query"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        query = params.get("query", "").strip()
        if not query:
            return ToolResult(success=False, error="Query is required")

        try:
            from app.database import async_session

            service = _get_service()
            user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id
            visibility = params.get("visibility", "all")

            async with async_session() as db:
                results = await service.recall(
                    db=db,
                    user_id=user_uuid,
                    query=query,
                    top_k=min(params.get("top_k", 5), 20),
                    memory_types=params.get("memory_types"),
                    min_salience=params.get("min_salience", 0.0),
                    visibility=visibility if visibility != "all" else None,
                )

            return ToolResult(
                success=True,
                result={
                    "query": query,
                    "count": len(results),
                    "results": [
                        {
                            "id": r.memory_id,
                            "content": r.content[:500] + ("..." if len(r.content) > 500 else ""),
                            "memory_type": r.memory_type,
                            "layer": r.layer,
                            "final_score": round(r.final_score, 4),
                            "vector_similarity": round(r.vector_similarity, 4),
                            "activation_score": round(r.activation_score, 4),
                            "retrievability": round(r.retrievability, 4),
                            "salience": round(r.salience, 2),
                            "tags": r.tags,
                            "valence": r.valence,
                            "agent_id": r.agent_id,
                            "access_count": r.access_count,
                            "created_at": r.created_at,
                        }
                        for r in results
                    ],
                },
            )

        except Exception as e:
            logger.exception("Cortex recall error")
            return ToolResult(success=False, error=f"Search failed: {str(e)}")


# =============================================================================
# CORTEX VILLAGE - Post to shared knowledge square
# =============================================================================

class CortexVillageTool(BaseTool):
    """Post to the village square (shared agent memory)."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="cortex_village",
            description="""Post a message to the Village Square - shared memory visible to all agents.

The Village is where agents share discoveries, insights, questions,
and dialogue. Messages are stored with 'shared' visibility.

Example: cortex_village(content="Discovered that user prefers concise responses")""",
            category=ToolCategory.MEMORY,
            input_schema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Message to post to the village",
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["episodic", "semantic", "procedural", "affective", "prospective"],
                        "description": "Type of memory (default: auto-classified)",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags",
                    },
                },
                "required": ["content"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        content = params.get("content", "").strip()
        if not content:
            return ToolResult(success=False, error="Content is required")

        try:
            from app.database import async_session

            service = _get_service()
            agent_id = context.metadata.get("agent_id", "AZOTH") if context.metadata else "AZOTH"
            user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

            async with async_session() as db:
                result = await service.remember(
                    db=db,
                    user_id=user_uuid,
                    content=content,
                    memory_type=params.get("memory_type"),
                    tags=params.get("tags"),
                    agent_id=agent_id,
                    visibility="shared",
                    source="village",
                )

            if result is None:
                return ToolResult(success=False, error="Content filtered by gating")

            result["message"] = "Posted to Village Square"
            return ToolResult(success=True, result=result)

        except Exception as e:
            logger.exception("Cortex village error")
            return ToolResult(success=False, error=f"Failed to post: {str(e)}")


# =============================================================================
# CORTEX STATS - Memory system statistics
# =============================================================================

class CortexStatsTool(BaseTool):
    """Get CerebroCortex memory statistics."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="cortex_stats",
            description="""Get statistics about the CerebroCortex memory system.

Returns: total memories, breakdown by memory type, layer, visibility,
link types, episode count, and agent distribution.""",
            category=ToolCategory.MEMORY,
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        try:
            from app.database import async_session

            service = _get_service()
            user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

            async with async_session() as db:
                stats = await service.stats(db, user_uuid)

            return ToolResult(success=True, result=stats)

        except Exception as e:
            logger.exception("Cortex stats error")
            return ToolResult(success=False, error=f"Stats failed: {str(e)}")


# =============================================================================
# CORTEX ASSOCIATE - Create explicit link between memories
# =============================================================================

class CortexAssociateTool(BaseTool):
    """Create an explicit association between two memories."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="cortex_associate",
            description="""Create a typed associative link between two memories.

Link types: temporal, causal, semantic, affective, contextual,
contradicts, supports, derived_from, part_of.

Links affect spreading activation during recall.

Example: cortex_associate(source_id="mem_abc", target_id="mem_xyz", link_type="causal")""",
            category=ToolCategory.MEMORY,
            input_schema={
                "type": "object",
                "properties": {
                    "source_id": {
                        "type": "string",
                        "description": "Source memory ID",
                    },
                    "target_id": {
                        "type": "string",
                        "description": "Target memory ID",
                    },
                    "link_type": {
                        "type": "string",
                        "enum": ["temporal", "causal", "semantic", "affective", "contextual",
                                 "contradicts", "supports", "derived_from", "part_of"],
                        "description": "Type of relationship",
                    },
                    "weight": {
                        "type": "number",
                        "description": "Link strength 0-1 (default: 0.5)",
                        "default": 0.5,
                    },
                    "evidence": {
                        "type": "string",
                        "description": "Why this link exists",
                    },
                },
                "required": ["source_id", "target_id", "link_type"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        try:
            from app.database import async_session

            service = _get_service()
            user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

            async with async_session() as db:
                result = await service.associate(
                    db=db,
                    user_id=user_uuid,
                    source_id=params["source_id"],
                    target_id=params["target_id"],
                    link_type=params["link_type"],
                    weight=params.get("weight", 0.5),
                    evidence=params.get("evidence"),
                )

            if "error" in result:
                return ToolResult(success=False, error=result["error"])

            return ToolResult(success=True, result=result)

        except Exception as e:
            logger.exception("Cortex associate error")
            return ToolResult(success=False, error=f"Associate failed: {str(e)}")


# =============================================================================
# CORTEX NEIGHBORS - Get associative neighbors
# =============================================================================

class CortexNeighborsTool(BaseTool):
    """Get neighbors of a memory in the associative graph."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="cortex_neighbors",
            description="""Get the associative neighbors of a memory.

Returns linked memories with link type and weight.
Useful for exploring the memory graph structure.

Example: cortex_neighbors(memory_id="mem_abc123")""",
            category=ToolCategory.MEMORY,
            input_schema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "Memory ID to get neighbors for",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max neighbors to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["memory_id"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        try:
            from app.database import async_session

            service = _get_service()
            user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

            async with async_session() as db:
                neighbors = await service.get_neighbors(
                    db=db,
                    user_id=user_uuid,
                    memory_id=params["memory_id"],
                    max_results=params.get("max_results", 10),
                )

            return ToolResult(
                success=True,
                result={
                    "memory_id": params["memory_id"],
                    "count": len(neighbors),
                    "neighbors": neighbors,
                },
            )

        except Exception as e:
            logger.exception("Cortex neighbors error")
            return ToolResult(success=False, error=f"Neighbors failed: {str(e)}")


# =============================================================================
# CORTEX EXPORT - Export memory core for transfer
# =============================================================================

class CortexExportTool(BaseTool):
    """Export memory core for transfer between systems."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="cortex_export",
            description="""Export a MemoryCore - portable snapshot of agent memories.

Exports all CerebroCortex memories with metadata and strength state.
Embeddings are NOT included (regenerated on import).

Example: cortex_export(agent_id="AZOTH")""",
            category=ToolCategory.MEMORY,
            input_schema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Export memories for this agent (default: all)",
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Filter by memory type",
                    },
                },
                "required": [],
            },
            requires_auth=True,
            requires_confirmation=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        try:
            from app.database import async_session
            from app.services.cerebro.pg_graph_store import PgGraphStore

            user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

            async with async_session() as db:
                store = PgGraphStore(db)
                nodes = await store.get_memories(
                    user_uuid,
                    limit=5000,
                    agent_id=params.get("agent_id"),
                    memory_type=params.get("memory_type"),
                )

                memories = []
                for node in nodes:
                    memories.append({
                        "id": node.id,
                        "content": node.content,
                        "memory_type": node.metadata.memory_type.value,
                        "layer": node.metadata.layer.value,
                        "visibility": node.metadata.visibility.value,
                        "agent_id": node.metadata.agent_id,
                        "tags": node.metadata.tags,
                        "concepts": node.metadata.concepts,
                        "valence": node.metadata.valence.value if hasattr(node.metadata.valence, 'value') else node.metadata.valence,
                        "arousal": node.metadata.arousal,
                        "salience": node.metadata.salience,
                        "access_count": node.strength.access_count,
                        "stability": node.strength.stability,
                        "difficulty": node.strength.difficulty,
                        "created_at": node.created_at.isoformat() if node.created_at else None,
                    })

            memory_core = {
                "format_version": "2.0",
                "engine": "cerebrocortex",
                "agent_id": params.get("agent_id") or "ALL",
                "exported_at": datetime.utcnow().isoformat(),
                "memories": memories,
                "total": len(memories),
            }

            return ToolResult(
                success=True,
                result={
                    "memory_core": memory_core,
                    "total_exported": len(memories),
                    "message": f"Exported {len(memories)} memories",
                },
            )

        except Exception as e:
            logger.exception("Cortex export error")
            return ToolResult(success=False, error=f"Export failed: {str(e)}")


# =============================================================================
# CORTEX IMPORT - Import memory core
# =============================================================================

class CortexImportTool(BaseTool):
    """Import memory core from another system."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="cortex_import",
            description="""Import a MemoryCore - restore or transfer agent memories.

Imports memories through the CerebroCortex pipeline.
Embeddings are regenerated during import.

Example: cortex_import(memory_core={...})""",
            category=ToolCategory.MEMORY,
            input_schema={
                "type": "object",
                "properties": {
                    "memory_core": {
                        "type": "object",
                        "description": "MemoryCore JSON object to import",
                    },
                },
                "required": ["memory_core"],
            },
            requires_auth=True,
            requires_confirmation=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        memory_core = params.get("memory_core")
        if not memory_core or not isinstance(memory_core, dict):
            return ToolResult(success=False, error="memory_core must be a JSON object")

        try:
            from app.database import async_session

            service = _get_service()
            user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

            memories = memory_core.get("memories", [])
            # Support v1 format
            if not memories:
                collections = memory_core.get("collections", {})
                for coll_memories in collections.values():
                    memories.extend(coll_memories)

            imported_count = 0
            errors = []

            async with async_session() as db:
                for memory in memories:
                    try:
                        content = memory.get("content", "")
                        if not content:
                            continue

                        result = await service.remember(
                            db=db,
                            user_id=user_uuid,
                            content=content,
                            memory_type=memory.get("memory_type"),
                            tags=memory.get("tags"),
                            salience=memory.get("salience"),
                            agent_id=memory.get("agent_id", "AZOTH"),
                            visibility=memory.get("visibility", "private"),
                            source="import",
                        )
                        if result:
                            imported_count += 1

                    except Exception as e:
                        errors.append(f"Error: {str(e)[:50]}")

            result_data = {
                "imported_count": imported_count,
                "source_agent": memory_core.get("agent_id", "unknown"),
                "message": f"Imported {imported_count} memories",
            }
            if errors:
                result_data["errors"] = errors[:5]
                result_data["error_count"] = len(errors)

            return ToolResult(success=True, result=result_data)

        except Exception as e:
            logger.exception("Cortex import error")
            return ToolResult(success=False, error=f"Import failed: {str(e)}")


# =============================================================================
# REGISTER TOOLS
# =============================================================================

registry.register(CortexRememberTool())
registry.register(CortexRecallTool())
registry.register(CortexVillageTool())
registry.register(CortexStatsTool())
registry.register(CortexAssociateTool())
registry.register(CortexNeighborsTool())
registry.register(CortexExportTool())
registry.register(CortexImportTool())
