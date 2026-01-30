"""
ApexAurum Cloud - Configuration

All settings loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # App
    app_name: str = "ApexAurum Cloud"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    allowed_origins: str = "http://localhost:3000,https://frontend-production-5402.up.railway.app"

    # Database (Railway provides postgresql://, we convert to asyncpg)
    database_url: str = "postgresql://apex:apex@localhost:5432/apex"

    @property
    def async_database_url(self) -> str:
        """Convert standard postgres URL to async format."""
        url = self.database_url
        # Handle both postgres:// and postgresql://
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # S3/MinIO
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_bucket: str = "apex-storage"

    # Anthropic
    anthropic_api_key: Optional[str] = None

    # Optional APIs
    voyage_api_key: Optional[str] = None
    suno_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Steel Browser
    steel_url: Optional[str] = None  # e.g., https://steel-browser-production-d237.up.railway.app

    # Stripe (Billing & Monetization)
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # Stripe Price IDs (create these in Stripe Dashboard)
    stripe_price_seeker_monthly: Optional[str] = None  # $3/mo subscription
    stripe_price_pro_monthly: Optional[str] = None  # $10/mo subscription
    stripe_price_opus_monthly: Optional[str] = None  # $30/mo subscription
    stripe_price_credits_500: Optional[str] = None  # $5 for 500 credits
    stripe_price_credits_2500: Optional[str] = None  # $20 for 2500 credits

    # Embedding config (for vector search)
    # Providers: "local" (FastEmbed), "openai", or "voyage"
    embedding_provider: str = "local"  # Default to local for privacy
    embedding_model: str = "BAAI/bge-small-en-v1.5"  # Local model (384 dims)
    # For OpenAI: "text-embedding-3-small" (1536 dims)
    # For local: "BAAI/bge-small-en-v1.5" (384), "BAAI/bge-base-en-v1.5" (768)
    embedding_dimensions: int = 384  # Match local model dimensions

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120  # 2 hours - built for long wanders
    refresh_token_expire_days: int = 30  # A full moon cycle

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # The Vault - File Storage
    # Tool execution
    tool_execution_timeout: int = 120  # seconds

    # Mount path is /data on Railway volume - use directly to avoid permission issues
    vault_path: str = "/data"
    max_file_size_bytes: int = 104_857_600  # 100MB
    default_quota_bytes: int = 5_368_709_120  # 5GB per user

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into list."""
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# ═══════════════════════════════════════════════════════════════════════════════
# TIER CONFIGURATION - Feature limits by subscription tier
# ═══════════════════════════════════════════════════════════════════════════════

TIER_LIMITS = {
    "free": {
        "name": "Seeker",
        "messages_per_month": 50,
        "models": ["claude-haiku-4-5-20251001"],
        "tools_enabled": False,
        "multi_provider": False,
        "byok_allowed": False,
        "api_access": False,
        "context_token_limit": 128_000,  # 128K cap for Seeker tier
    },
    "pro": {
        "name": "Alchemist",
        "messages_per_month": 1000,
        "models": [
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250929",
        ],
        "tools_enabled": True,
        "multi_provider": False,
        "byok_allowed": True,
        "api_access": False,
        "context_token_limit": None,  # No cap
    },
    "opus": {
        "name": "Adept",
        "messages_per_month": None,  # Unlimited
        "models": [
            # Current 4.5 family
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-5-20251101",
            # Legacy 4.x family (still available on Anthropic API)
            "claude-opus-4-1-20250805",
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            # Claude 3.7 (still available)
            "claude-3-7-sonnet-20250219",
            # Vintage 3.0 (only Haiku still available)
            "claude-3-haiku-20240307",
        ],
        # Deprecated models - kept for memorial messages
        "deprecated_models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
        ],
        "tools_enabled": True,
        "multi_provider": True,
        "byok_allowed": True,
        "api_access": True,
        "context_token_limit": None,  # No cap
    },
}

# Credit packs available for purchase
CREDIT_PACKS = {
    "small": {
        "price_usd": 5.00,
        "credits": 500,
        "bonus": 0,
    },
    "large": {
        "price_usd": 20.00,
        "credits": 2000,
        "bonus": 500,  # 25% bonus = 2500 total
    },
}
