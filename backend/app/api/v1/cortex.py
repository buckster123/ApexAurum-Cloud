"""
CerebroCortex Dashboard API

Endpoints for the 3D Neural Space memory visualization dashboard.
Now powered by CerebroCortex with associative links, memory types, and ACT-R scoring.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.auth.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cortex", tags=["CerebroCortex"])


# =============================================================================
# Schemas
# =============================================================================

class MemoryNode(BaseModel):
    """Memory for visualization."""
    id: str
    content: str
    agent_id: Optional[str] = "AZOTH"
    visibility: str = "private"
    layer: str = "working"
    message_type: str = "semantic"  # Now memory_type from CerebroCortex
    memory_type: Optional[str] = None
    salience: float = 0.5
    arousal: float = 0.5
    valence: str = "neutral"
    attention_weight: float = 1.0  # Backwards compat, mapped from salience
    access_count: int = 0
    tags: List[str] = []
    concepts: List[str] = []
    responding_to: List[str] = []
    related_agents: List[str] = []
    conversation_thread: Optional[str] = None
    link_count: int = 0
    created_at: Optional[str] = None
    last_accessed_at: Optional[str] = None


class GraphEdge(BaseModel):
    """Relationship edge for visualization."""
    source: str
    target: str
    type: str  # Link type from CerebroCortex
    weight: float = 0.5


class GraphData(BaseModel):
    """Graph data for 3D visualization."""
    nodes: List[MemoryNode]
    edges: List[GraphEdge]


class CortexStats(BaseModel):
    """Memory statistics."""
    total: int
    by_layer: dict
    by_visibility: dict
    by_agent: dict
    by_message_type: dict
    by_memory_type: Optional[dict] = None
    links: int = 0
    link_types: Optional[dict] = None
    episodes: int = 0


class SearchRequest(BaseModel):
    """Search request body."""
    query: str = Field(..., max_length=500)
    layers: Optional[List[str]] = None
    visibility: Optional[str] = None
    agent_id: Optional[str] = None
    memory_types: Optional[List[str]] = None
    min_salience: float = 0.0
    limit: int = 50


class LayerUpdateRequest(BaseModel):
    """Request to change memory layer."""
    layer: str  # sensory | working | long_term | cortex


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/diagnostic")
async def diagnostic(
    db=Depends(get_db),
):
    """
    Diagnostic endpoint to check CerebroCortex system status.
    No auth required - useful for troubleshooting.
    """
    from app.config import get_settings
    settings = get_settings()

    if settings.embedding_provider == "local":
        embedding_available = True
    elif settings.embedding_provider == "openai":
        embedding_available = bool(settings.openai_api_key)
    elif settings.embedding_provider == "voyage":
        embedding_available = bool(settings.voyage_api_key)
    else:
        embedding_available = False

    result = {
        "engine": "cerebrocortex",
        "pgvector_extension": False,
        "cerebro_tables": False,
        "legacy_table": False,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "embedding_dimensions": settings.embedding_dimensions,
        "embedding_available": embedding_available,
        "cerebro_nodes": 0,
        "cerebro_links": 0,
        "cerebro_episodes": 0,
        "legacy_vectors": 0,
        "errors": [],
        "notes": [],
    }

    try:
        ext_check = await db.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        result["pgvector_extension"] = ext_check.scalar()

        # Check CerebroCortex tables
        cerebro_check = await db.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cerebro_memory_nodes')")
        )
        result["cerebro_tables"] = cerebro_check.scalar()

        if result["cerebro_tables"]:
            count = await db.execute(text("SELECT COUNT(*) FROM cerebro_memory_nodes"))
            result["cerebro_nodes"] = count.scalar() or 0

            link_count = await db.execute(text("SELECT COUNT(*) FROM cerebro_associative_links"))
            result["cerebro_links"] = link_count.scalar() or 0

            ep_count = await db.execute(text("SELECT COUNT(*) FROM cerebro_episodes"))
            result["cerebro_episodes"] = ep_count.scalar() or 0

        # Check legacy table
        legacy_check = await db.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_vectors')")
        )
        result["legacy_table"] = legacy_check.scalar()
        if result["legacy_table"]:
            lc = await db.execute(text("SELECT COUNT(*) FROM user_vectors"))
            result["legacy_vectors"] = lc.scalar() or 0

    except Exception as e:
        result["errors"].append(str(e))

    result["ready"] = result["pgvector_extension"] and result["cerebro_tables"]

    if not result["embedding_available"]:
        result["notes"].append(f"No {settings.embedding_provider.upper()}_API_KEY - memories store without embeddings")

    if result["legacy_vectors"] > 0 and result["cerebro_nodes"] == 0:
        result["notes"].append(f"{result['legacy_vectors']} legacy memories in user_vectors - run migration to import")

    return result


@router.get("/memories", response_model=List[MemoryNode])
async def list_memories(
    layer: Optional[str] = Query(None, description="Filter by layer"),
    visibility: Optional[str] = Query(None, description="Filter by visibility"),
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    message_type: Optional[str] = Query(None, description="Filter by memory type (legacy alias)"),
    limit: int = Query(100, le=500, description="Max results"),
    offset: int = Query(0, description="Offset for pagination"),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
) -> List[MemoryNode]:
    """List memories with optional filters."""
    try:
        from app.services.cerebro.pg_graph_store import PgGraphStore

        store = PgGraphStore(db)
        effective_type = memory_type or message_type
        nodes = await store.get_memories(
            user.id, limit=limit, offset=offset,
            layer=layer, visibility=visibility,
            agent_id=agent_id, memory_type=effective_type,
        )
        return [_node_to_response(n) for n in nodes]
    except Exception as e:
        logger.error(f"Cortex memories error: {e}")
        return []


@router.get("/memories/{memory_id}", response_model=MemoryNode)
async def get_memory(
    memory_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
) -> MemoryNode:
    """Get a single memory by ID."""
    from app.services.cerebro.pg_graph_store import PgGraphStore

    store = PgGraphStore(db)
    node = await store.get_node(user.id, memory_id)
    if not node:
        raise HTTPException(status_code=404, detail="Memory not found")
    return _node_to_response(node)


@router.get("/graph", response_model=GraphData)
async def get_graph_data(
    layer: Optional[str] = Query(None),
    visibility: Optional[str] = Query(None),
    limit: int = Query(200, le=1000),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
) -> GraphData:
    """Get graph data with real associative links for 3D visualization."""
    try:
        from app.services.cerebro.pg_graph_store import PgGraphStore

        store = PgGraphStore(db)
        nodes = await store.get_memories(
            user.id, limit=limit, layer=layer, visibility=visibility,
        )
        response_nodes = [_node_to_response(n) for n in nodes]

        # Get real associative links between these nodes
        node_ids = [n.id for n in nodes]
        links = await store.get_links_for_graph(user.id, node_ids)

        edges = [
            GraphEdge(
                source=link["source_id"],
                target=link["target_id"],
                type=link["link_type"],
                weight=float(link.get("weight", 0.5)),
            )
            for link in links
        ]

        return GraphData(nodes=response_nodes, edges=edges)
    except Exception as e:
        logger.error(f"Cortex graph error: {e}")
        return GraphData(nodes=[], edges=[])


@router.get("/stats", response_model=CortexStats)
async def get_stats(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
) -> CortexStats:
    """Get memory statistics for the dashboard."""
    try:
        from app.services.cerebro import get_cerebro_service

        service = get_cerebro_service()
        stats = await service.stats(db, user.id)

        return CortexStats(
            total=stats.get("nodes", 0),
            by_layer=stats.get("layers", {}),
            by_visibility=stats.get("visibility", {}),
            by_agent=stats.get("agents", {}),
            by_message_type=stats.get("memory_types", {}),
            by_memory_type=stats.get("memory_types", {}),
            links=stats.get("links", 0),
            link_types=stats.get("link_types", {}),
            episodes=stats.get("episodes", 0),
        )
    except Exception as e:
        logger.error(f"Cortex stats error: {e}")
        return CortexStats(
            total=0,
            by_layer={"error": "CerebroCortex unavailable"},
            by_visibility={},
            by_agent={},
            by_message_type={},
        )


@router.post("/search", response_model=List[MemoryNode])
async def search_memories(
    request: SearchRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
) -> List[MemoryNode]:
    """Semantic search using CerebroCortex recall pipeline."""
    from app.services.cerebro import get_cerebro_service

    service = get_cerebro_service()
    results = await service.recall(
        db=db,
        user_id=user.id,
        query=request.query,
        top_k=request.limit,
        memory_types=request.memory_types,
        min_salience=request.min_salience,
        visibility=request.visibility,
        agent_id=request.agent_id,
    )

    return [
        MemoryNode(
            id=r.memory_id,
            content=r.content[:500],
            agent_id=r.agent_id,
            visibility="private",
            layer=r.layer,
            message_type=r.memory_type,
            memory_type=r.memory_type,
            salience=r.salience,
            attention_weight=r.final_score,  # Map final_score to attention_weight for compat
            access_count=r.access_count,
            tags=r.tags,
            valence=r.valence,
            created_at=r.created_at,
        )
        for r in results
    ]


@router.get("/neighbors/{memory_id}")
async def get_neighbors(
    memory_id: str,
    max_results: int = Query(10, le=50),
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get associative neighbors of a memory."""
    from app.services.cerebro import get_cerebro_service

    service = get_cerebro_service()
    neighbors = await service.get_neighbors(db, user.id, memory_id, max_results)
    return {"memory_id": memory_id, "neighbors": neighbors}


@router.patch("/memories/{memory_id}/layer")
async def update_memory_layer(
    memory_id: str,
    request: LayerUpdateRequest,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Promote or demote a memory's layer."""
    valid_layers = ["sensory", "working", "long_term", "cortex"]
    if request.layer not in valid_layers:
        raise HTTPException(status_code=400, detail=f"Invalid layer. Must be one of: {valid_layers}")

    from app.services.cerebro.pg_graph_store import PgGraphStore

    store = PgGraphStore(db)
    success = await store.update_node_metadata(user.id, memory_id, layer=request.layer)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {"success": True, "layer": request.layer}


@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete a memory."""
    result = await db.execute(
        text("DELETE FROM cerebro_memory_nodes WHERE id = :id AND user_id = :user_id RETURNING id"),
        {"id": memory_id, "user_id": user.id}
    )
    await db.commit()

    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Memory not found")

    return {"success": True, "deleted": memory_id}


# =============================================================================
# Helpers
# =============================================================================

def _node_to_response(node) -> MemoryNode:
    """Convert CerebroCortex MemoryNode to API response."""
    from app.cerebro.types import EmotionalValence

    valence = node.metadata.valence
    if isinstance(valence, EmotionalValence):
        valence = valence.value

    return MemoryNode(
        id=node.id,
        content=node.content[:500] if node.content else "",
        agent_id=node.metadata.agent_id or "AZOTH",
        visibility=node.metadata.visibility.value if hasattr(node.metadata.visibility, 'value') else node.metadata.visibility,
        layer=node.metadata.layer.value if hasattr(node.metadata.layer, 'value') else node.metadata.layer,
        message_type=node.metadata.memory_type.value if hasattr(node.metadata.memory_type, 'value') else node.metadata.memory_type,
        memory_type=node.metadata.memory_type.value if hasattr(node.metadata.memory_type, 'value') else node.metadata.memory_type,
        salience=node.metadata.salience,
        arousal=node.metadata.arousal,
        valence=valence,
        attention_weight=node.metadata.salience,  # Map salience to attention_weight for compat
        access_count=node.strength.access_count,
        tags=node.metadata.tags,
        concepts=node.metadata.concepts,
        responding_to=node.metadata.responding_to,
        related_agents=node.metadata.related_agents,
        conversation_thread=node.metadata.conversation_thread,
        link_count=node.link_count,
        created_at=node.created_at.isoformat() if node.created_at else None,
        last_accessed_at=node.last_accessed_at.isoformat() if node.last_accessed_at else None,
    )
