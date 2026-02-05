"""AffectEngine - Emotional processing and salience modulation.

The amygdala: processes emotional content, adjusts salience based on
outcomes, creates affective links between emotionally similar memories.

Adapted: pure logic only, no storage calls. Link creation and storage
operations handled by the async service layer.
"""

from app.cerebro.models.memory import MemoryNode
from app.cerebro.types import EmotionalValence


# Emotion keyword mappings
POSITIVE_MARKERS = {
    "amazing", "breakthrough", "excellent", "great", "perfect",
    "solved", "success", "works", "love", "beautiful", "happy",
    "excited", "wonderful", "fantastic",
}
NEGATIVE_MARKERS = {
    "bug", "broken", "crash", "error", "fail", "frustrat",
    "terrible", "wrong", "hate", "awful", "disappoint", "stuck",
    "confused", "impossible", "nightmare",
}
HIGH_AROUSAL_MARKERS = {
    "!", "urgent", "critical", "panic", "incredible", "shocking",
    "breakthrough", "eureka", "finally", "nightmare", "disaster",
}


class AffectEngine:
    """Processes emotional dimensions of memories.

    Stateless version - storage operations handled by the async service.
    """

    @staticmethod
    def analyze_emotion(content: str) -> tuple[EmotionalValence, float, float]:
        """Analyze emotional content of text.

        Returns:
            (valence, arousal, salience_adjustment)
        """
        lower = content.lower()

        pos_count = sum(1 for m in POSITIVE_MARKERS if m in lower)
        neg_count = sum(1 for m in NEGATIVE_MARKERS if m in lower)
        arousal_count = sum(1 for m in HIGH_AROUSAL_MARKERS if m in lower)

        if pos_count > 0 and neg_count > 0:
            valence = EmotionalValence.MIXED
        elif pos_count > neg_count:
            valence = EmotionalValence.POSITIVE
        elif neg_count > pos_count:
            valence = EmotionalValence.NEGATIVE
        else:
            valence = EmotionalValence.NEUTRAL

        emotion_intensity = pos_count + neg_count
        arousal = min(0.3 + emotion_intensity * 0.15 + arousal_count * 0.1, 1.0)

        salience_adj = 0.0
        if neg_count > 0:
            salience_adj += min(neg_count * 0.1, 0.3)
        if pos_count > 0:
            salience_adj += min(pos_count * 0.05, 0.15)
        if arousal_count > 0:
            salience_adj += min(arousal_count * 0.05, 0.1)

        return valence, arousal, salience_adj

    @staticmethod
    def apply_emotion(node: MemoryNode) -> MemoryNode:
        """Apply emotional analysis to a memory node, updating its metadata."""
        valence, arousal, salience_adj = AffectEngine.analyze_emotion(node.content)

        new_arousal = max(node.metadata.arousal, arousal)
        new_salience = max(0.1, min(1.0, node.metadata.salience + salience_adj))

        return MemoryNode(
            id=node.id,
            content=node.content,
            metadata=node.metadata.model_copy(update={
                "valence": valence,
                "arousal": new_arousal,
                "salience": new_salience,
            }),
            strength=node.strength,
            created_at=node.created_at,
            last_accessed_at=node.last_accessed_at,
            promoted_at=node.promoted_at,
            link_count=node.link_count,
        )
