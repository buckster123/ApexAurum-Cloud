"""CerebroCortex service layer for ApexAurum Cloud.

Provides async PostgreSQL-backed memory engine with:
- ACT-R + FSRS hybrid strength model
- pgvector semantic search
- SQL-based spreading activation
- Thalamic gating, semantic enrichment, emotional analysis
"""

from app.services.cerebro.service import CerebroCortexService, get_cerebro_service

__all__ = ["CerebroCortexService", "get_cerebro_service"]
