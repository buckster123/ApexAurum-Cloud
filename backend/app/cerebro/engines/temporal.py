"""SemanticEngine - Semantic knowledge management.

The temporal lobe: manages factual/conceptual memories, extracts concepts,
creates semantic links between related knowledge.

Adapted: concept extraction is pure logic (no storage calls).
Link creation is handled by the async service layer.
"""

import re

from app.cerebro.models.memory import MemoryNode


# Common words to exclude from concept extraction
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "because", "but", "and", "or", "if", "while",
    "that", "this", "these", "those", "it", "its", "i", "you", "he",
    "she", "we", "they", "me", "him", "her", "us", "them", "my", "your",
    "his", "our", "their", "what", "which", "who", "whom",
}


class SemanticEngine:
    """Manages semantic knowledge: concepts, facts, and their relationships.

    Stateless version - storage operations handled by the async service.
    """

    @staticmethod
    def extract_concepts(content: str, max_concepts: int = 10) -> list[str]:
        """Extract key concepts from text content.

        Uses word frequency and simple heuristics.
        """
        words = re.findall(r'[a-z][a-z0-9_-]+', content.lower())
        meaningful = [w for w in words if w not in STOP_WORDS and len(w) > 2]

        freq: dict[str, int] = {}
        for w in meaningful:
            freq[w] = freq.get(w, 0) + 1

        bigrams = re.findall(r'[A-Z][a-z]+\s+[A-Z][a-z]+', content)
        for bg in bigrams:
            key = bg.lower()
            freq[key] = freq.get(key, 0) + 2

        sorted_concepts = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [c[0] for c in sorted_concepts[:max_concepts]]

    @staticmethod
    def enrich_node(node: MemoryNode) -> MemoryNode:
        """Enrich a node with extracted concepts if not already present."""
        if node.metadata.concepts:
            return node

        concepts = SemanticEngine.extract_concepts(node.content)
        return MemoryNode(
            id=node.id,
            content=node.content,
            metadata=node.metadata.model_copy(update={"concepts": concepts}),
            strength=node.strength,
            created_at=node.created_at,
            last_accessed_at=node.last_accessed_at,
            promoted_at=node.promoted_at,
            link_count=node.link_count,
        )
