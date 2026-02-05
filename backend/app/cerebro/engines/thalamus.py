"""GatingEngine - Thalamic sensory gating.

The thalamus: filters incoming information, decides what is worth
remembering, assigns initial memory parameters.

Adapted for async PostgreSQL - dedup check is now async and passed in.
"""

import time
from typing import Optional

from app.cerebro.activation.strength import record_access
from app.cerebro.config import LAYER_CONFIG
from app.cerebro.models.memory import MemoryMetadata, MemoryNode, StrengthState
from app.cerebro.types import MemoryLayer, MemoryType, Visibility


# Minimum content length to be worth storing
MIN_CONTENT_LENGTH = 10

# Keywords that boost salience
HIGH_SALIENCE_KEYWORDS = {
    "important", "critical", "bug", "fix", "error", "breakthrough",
    "discovery", "remember", "never", "always", "warning", "danger",
    "lesson", "learned", "insight",
}


class GatingEngine:
    """Decides what incoming information becomes a memory and how.

    Stateless version - deduplication is handled externally by the async service.
    """

    def evaluate_input(
        self,
        content: str,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[list[str]] = None,
        salience: Optional[float] = None,
        agent_id: str = "AZOTH",
        session_id: Optional[str] = None,
        visibility: Visibility = Visibility.SHARED,
        conversation_thread: Optional[str] = None,
        responding_to: Optional[list[str]] = None,
        related_agents: Optional[list[str]] = None,
        source: str = "user_input",
    ) -> Optional[MemoryNode]:
        """Evaluate incoming content and create a MemoryNode if it passes gating.

        Returns:
            MemoryNode ready for storage, or None if gated out (too short).
            Deduplication is handled by the caller (async DB check).
        """
        if len(content.strip()) < MIN_CONTENT_LENGTH:
            return None

        resolved_type = memory_type or self._classify_type(content)
        resolved_salience = salience if salience is not None else self._estimate_salience(content, tags)
        initial_layer = self._assign_layer(resolved_salience, resolved_type)

        now = time.time()
        metadata = MemoryMetadata(
            agent_id=agent_id,
            visibility=visibility,
            layer=initial_layer,
            memory_type=resolved_type,
            tags=tags or [],
            session_id=session_id,
            conversation_thread=conversation_thread,
            responding_to=responding_to or [],
            related_agents=related_agents or [],
            salience=resolved_salience,
            source=source,
        )

        strength = StrengthState(
            stability=self._initial_stability(resolved_salience),
            access_timestamps=[now],
            access_count=1,
            last_retrievability=1.0,
            last_activation=0.0,
            last_computed_at=now,
        )

        node = MemoryNode(
            content=content,
            metadata=metadata,
            strength=strength,
        )

        return node

    @staticmethod
    def strengthen_existing(strength: StrengthState) -> StrengthState:
        """Strengthen an existing memory instead of creating a duplicate."""
        return record_access(strength, time.time())

    def _classify_type(self, content: str) -> MemoryType:
        """Heuristic memory type classification."""
        lower = content.lower()

        if any(marker in lower for marker in [
            "step 1", "1)", "first,", "when you", "how to",
            "workflow", "procedure", "algorithm", "strategy",
        ]):
            return MemoryType.PROCEDURAL

        if any(marker in lower for marker in [
            "felt", "feeling", "amazing", "frustrat", "excit",
            "disappoint", "breakthrough", "terrible", "love", "hate",
        ]):
            return MemoryType.AFFECTIVE

        if any(marker in lower for marker in [
            "need to", "should", "todo", "plan to", "will",
            "going to", "revisit", "later", "eventually",
        ]):
            return MemoryType.PROSPECTIVE

        if any(marker in lower for marker in [
            "then", "after", "before", "yesterday", "today",
            "session", "deployed", "tried", "encountered",
        ]):
            return MemoryType.EPISODIC

        return MemoryType.SEMANTIC

    def _estimate_salience(self, content: str, tags: Optional[list[str]] = None) -> float:
        """Estimate how important/memorable this content is."""
        score = 0.5

        lower = content.lower()
        keyword_hits = sum(1 for kw in HIGH_SALIENCE_KEYWORDS if kw in lower)
        score += min(keyword_hits * 0.1, 0.3)

        if len(content) > 200:
            score += 0.1
        elif len(content) < 30:
            score -= 0.1

        if tags:
            score += min(len(tags) * 0.05, 0.15)

        if "?" in content:
            score += 0.05
        if "!" in content:
            score += 0.05

        return max(0.1, min(1.0, score))

    def _assign_layer(self, salience: float, memory_type: MemoryType) -> MemoryLayer:
        """Decide initial memory layer based on salience and type."""
        if memory_type in (MemoryType.PROCEDURAL, MemoryType.SCHEMATIC):
            return MemoryLayer.WORKING

        if salience >= 0.7:
            return MemoryLayer.WORKING
        elif salience >= 0.4:
            return MemoryLayer.WORKING
        else:
            return MemoryLayer.SENSORY

    def _initial_stability(self, salience: float) -> float:
        """Set initial FSRS stability based on salience."""
        return 0.5 + salience * 2.5
