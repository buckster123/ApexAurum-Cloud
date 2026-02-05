"""
Neural Memory Service - The Remembering Deep

Stores chat messages through the CerebroCortex pipeline for the
3D Neural Space visualization dashboard and contextual memory retrieval.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cerebro import get_cerebro_service

logger = logging.getLogger(__name__)


class NeuralMemoryService:
    """
    Service for storing chat messages as CerebroCortex memories.

    Each message goes through the full pipeline:
    - Thalamic gating (type classification, salience, dedup)
    - Semantic enrichment (concept extraction)
    - Emotional analysis (valence, arousal)
    - Embedding generation
    - ACT-R + FSRS strength initialization
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._service = get_cerebro_service()

    async def store_message(
        self,
        user_id: UUID,
        content: str,
        agent_id: str = "AZOTH",
        role: str = "user",  # "user" or "assistant"
        conversation_thread: Optional[str] = None,
        responding_to: Optional[list[str]] = None,
        visibility: str = "private",  # "private" or "shared"
        collection: str = "chat",  # unused, kept for API compat
    ) -> Optional[str]:
        """
        Store a chat message as a CerebroCortex memory.

        Returns:
            Memory ID string, or None if filtered out
        """
        if len(content.strip()) < 10:
            logger.debug(f"Skipping short message: {len(content)} chars")
            return None

        # Map role to source type
        source = "user_input" if role == "user" else "llm_generation"

        # Map visibility for backwards compat
        vis_map = {"village": "shared", "bridge": "thread"}
        mapped_vis = vis_map.get(visibility, visibility)

        try:
            result = await self._service.remember(
                db=self.db,
                user_id=user_id,
                content=content[:2000],  # Truncate stored content
                agent_id=agent_id,
                visibility=mapped_vis,
                conversation_thread=conversation_thread,
                responding_to=responding_to,
                source=source,
            )

            if result:
                memory_id = result.get("id")
                logger.debug(f"Stored neural memory: {memory_id} ({role}/{agent_id})")
                return memory_id

            return None

        except Exception as e:
            logger.error(f"Failed to store neural memory: {e}")
            return None

    async def store_conversation_exchange(
        self,
        user_id: UUID,
        user_message: str,
        assistant_response: str,
        agent_id: str = "AZOTH",
        conversation_id: Optional[UUID] = None,
    ) -> dict:
        """
        Store both user message and assistant response as linked memories.
        """
        thread = str(conversation_id) if conversation_id else None

        # Store user message first
        user_memory_id = await self.store_message(
            user_id=user_id,
            content=user_message,
            agent_id=agent_id,
            role="user",
            conversation_thread=thread,
        )

        # Store assistant response, linking to user message via context_ids
        context_ids = [user_memory_id] if user_memory_id else None

        # For the assistant response, pass context_ids to auto-link
        assistant_memory_id = None
        if len(assistant_response.strip()) >= 10:
            try:
                result = await self._service.remember(
                    db=self.db,
                    user_id=user_id,
                    content=assistant_response[:2000],
                    agent_id=agent_id,
                    visibility="private",
                    conversation_thread=thread,
                    responding_to=[user_memory_id] if user_memory_id else None,
                    source="llm_generation",
                    context_ids=context_ids,
                )
                if result:
                    assistant_memory_id = result.get("id")
            except Exception as e:
                logger.error(f"Failed to store assistant memory: {e}")

        return {
            "user_memory_id": user_memory_id,
            "assistant_memory_id": assistant_memory_id,
        }

    async def get_village_memories(
        self,
        user_id: UUID,
        topic: Optional[str] = None,
        limit: int = 10,
        collection: str = "council",  # unused, kept for API compat
    ) -> list[dict]:
        """
        Retrieve shared memories using CerebroCortex recall.
        """
        try:
            if topic:
                results = await self._service.recall(
                    db=self.db,
                    user_id=user_id,
                    query=topic,
                    top_k=limit,
                    visibility="shared",
                )
                return [
                    {
                        "id": r.memory_id,
                        "content": r.content,
                        "agent_id": r.agent_id,
                        "created_at": r.created_at,
                        "memory_type": r.memory_type,
                        "similarity": r.vector_similarity,
                    }
                    for r in results
                ]
            else:
                # Fallback: get recent shared memories
                from app.services.cerebro.pg_graph_store import PgGraphStore
                store = PgGraphStore(self.db)
                nodes = await store.get_memories(
                    user_id, limit=limit, visibility="shared",
                )
                return [
                    {
                        "id": n.id,
                        "content": n.content,
                        "agent_id": n.metadata.agent_id,
                        "created_at": n.created_at.isoformat() if n.created_at else None,
                        "memory_type": n.metadata.memory_type.value,
                    }
                    for n in nodes
                ]

        except Exception as e:
            logger.error(f"Failed to get village memories: {e}")
            return []

    def format_village_memories_for_prompt(
        self,
        memories: list[dict],
        max_chars: int = 2000,
    ) -> str:
        """Format Village memories into a prompt injection block."""
        if not memories:
            return ""

        lines = [
            "\n\n--- THE VILLAGE MEMORY ---",
            "Shared wisdom from past deliberations and fellow agents:\n"
        ]

        total_chars = sum(len(l) for l in lines)

        for mem in memories:
            agent = mem.get("agent_id", "Unknown")
            content = mem.get("content", "")[:500]
            line = f"[{agent}]: {content}\n"

            if total_chars + len(line) > max_chars:
                lines.append("... (more memories available)")
                break

            lines.append(line)
            total_chars += len(line)

        lines.append("--- END VILLAGE MEMORY ---\n")

        return "\n".join(lines)


# Convenience function for use in chat.py
async def store_chat_memory(
    db: AsyncSession,
    user_id: UUID,
    user_message: str,
    assistant_response: str,
    agent_id: str = "AZOTH",
    conversation_id: Optional[UUID] = None,
) -> dict:
    """
    Convenience function to store a chat exchange as CerebroCortex memories.
    """
    service = NeuralMemoryService(db)
    return await service.store_conversation_exchange(
        user_id=user_id,
        user_message=user_message,
        assistant_response=assistant_response,
        agent_id=agent_id,
        conversation_id=conversation_id,
    )
