"""
User Endpoints

User profile, settings, and API key management.
"""

import logging
from datetime import datetime
from typing import Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.auth.deps import get_current_user
from app.services.encryption import encrypt_value, decrypt_value, mask_api_key

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


# Schemas
class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    created_at: str
    settings: dict

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    settings: Optional[dict] = None


class UsageResponse(BaseModel):
    total_messages: int
    total_tokens: int
    total_cost_usd: float
    conversations_count: int
    agents_spawned: int
    music_generated: int


# Endpoints
@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
):
    """Get current user's profile."""
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at.isoformat(),
        settings=user.settings,
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: UserProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    if request.display_name is not None:
        user.display_name = request.display_name

    if request.settings is not None:
        # Merge settings (don't replace entirely)
        current_settings = user.settings or {}
        current_settings.update(request.settings)
        user.settings = current_settings

    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at.isoformat(),
        settings=user.settings,
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's usage statistics."""
    from sqlalchemy import func, select
    from app.models.conversation import Conversation, Message
    from app.models.agent import Agent
    from app.models.music import MusicTask

    # Count conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.user_id == user.id)
    )
    conversations_count = conv_result.scalar() or 0

    # Count messages and sum tokens/cost
    msg_result = await db.execute(
        select(
            func.count(Message.id),
            func.coalesce(func.sum(Message.tokens_used), 0),
            func.coalesce(func.sum(Message.cost_usd), 0)
        )
        .join(Conversation)
        .where(Conversation.user_id == user.id)
    )
    msg_stats = msg_result.one()
    total_messages = msg_stats[0] or 0
    total_tokens = msg_stats[1] or 0
    total_cost = float(msg_stats[2] or 0)

    # Count agents
    agent_result = await db.execute(
        select(func.count(Agent.id))
        .where(Agent.user_id == user.id)
    )
    agents_spawned = agent_result.scalar() or 0

    # Count music tasks
    music_result = await db.execute(
        select(func.count(MusicTask.id))
        .where(MusicTask.user_id == user.id)
    )
    music_generated = music_result.scalar() or 0

    return UsageResponse(
        total_messages=total_messages,
        total_tokens=total_tokens,
        total_cost_usd=total_cost,
        conversations_count=conversations_count,
        agents_spawned=agents_spawned,
        music_generated=music_generated,
    )


@router.get("/preferences")
async def get_preferences(
    user: User = Depends(get_current_user),
):
    """Get user preferences (subset of settings)."""
    settings = user.settings or {}
    return {
        "default_model": settings.get("default_model", "claude-3-haiku-20240307"),
        "cache_strategy": settings.get("cache_strategy", "balanced"),
        "context_strategy": settings.get("context_strategy", "adaptive"),
        "theme": settings.get("theme", "dark"),
        "default_agent": settings.get("default_agent", "AZOTH"),
    }


@router.put("/preferences")
async def update_preferences(
    preferences: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences."""
    current_settings = user.settings or {}
    current_settings.update(preferences)
    user.settings = current_settings

    return {"message": "Preferences updated"}


# ═══════════════════════════════════════════════════════════════════════════════
# API KEY MANAGEMENT - BYOK (Bring Your Own Key)
# ═══════════════════════════════════════════════════════════════════════════════

class ApiKeyRequest(BaseModel):
    api_key: str


class ApiKeyStatusResponse(BaseModel):
    configured: bool
    key_hint: Optional[str] = None
    added_at: Optional[str] = None
    last_used: Optional[str] = None
    valid: bool = False
    subscription_status: str = "beta"  # beta, free, pro, enterprise


@router.post("/api-key")
async def set_api_key(
    request: ApiKeyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set or update the user's Anthropic API key.

    The key is validated with a test API call, then encrypted and stored.
    Only the encrypted version is saved - we never store or log the full key.
    """
    api_key = request.api_key.strip()

    # Basic validation
    if not api_key.startswith("sk-ant"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key format. Anthropic keys start with 'sk-ant'"
        )

    # Validate key with a minimal test call
    try:
        test_client = anthropic.Anthropic(api_key=api_key)
        test_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}]
        )
    except anthropic.AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key. Please check your key and try again."
        )
    except anthropic.RateLimitError:
        # Key is valid but rate limited - that's okay
        pass
    except Exception as e:
        logger.error(f"API key validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not validate API key. Please try again."
        )

    # Encrypt and store
    encrypted_key = encrypt_value(api_key, settings.jwt_secret)
    key_hint = mask_api_key(api_key)

    # Initialize settings structure if needed
    if not user.settings:
        user.settings = {}

    if "api_keys" not in user.settings:
        user.settings["api_keys"] = {}

    user.settings["api_keys"]["anthropic"] = {
        "encrypted_key": encrypted_key,
        "key_hint": key_hint,
        "added_at": datetime.utcnow().isoformat(),
        "last_used": None,
        "valid": True,
    }

    # Initialize subscription info if not present
    if "subscription" not in user.settings:
        user.settings["subscription"] = {
            "status": "beta",
            "stripe_customer_id": None,
            "plan_id": None,
            "current_period_end": None,
            "byok_allowed": True,
        }

    flag_modified(user, "settings")
    await db.commit()

    logger.info(f"API key configured for user {user.id}")

    return {
        "status": "configured",
        "key_hint": key_hint,
        "message": "API key saved successfully. You can now chat with the Agents!"
    }


@router.delete("/api-key")
async def remove_api_key(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove the user's API key."""
    if user.settings and "api_keys" in user.settings:
        user.settings["api_keys"].pop("anthropic", None)
        flag_modified(user, "settings")
        await db.commit()

    return {"status": "removed", "message": "API key removed."}


@router.get("/api-key/status", response_model=ApiKeyStatusResponse)
async def get_api_key_status(
    user: User = Depends(get_current_user),
):
    """
    Check if the user has an API key configured.

    Returns status without exposing the actual key.
    """
    settings_data = user.settings or {}
    api_keys = settings_data.get("api_keys", {})
    anthropic_key = api_keys.get("anthropic", {})
    subscription = settings_data.get("subscription", {})

    if not anthropic_key.get("encrypted_key"):
        return ApiKeyStatusResponse(
            configured=False,
            subscription_status=subscription.get("status", "beta"),
        )

    return ApiKeyStatusResponse(
        configured=True,
        key_hint=anthropic_key.get("key_hint"),
        added_at=anthropic_key.get("added_at"),
        last_used=anthropic_key.get("last_used"),
        valid=anthropic_key.get("valid", True),
        subscription_status=subscription.get("status", "beta"),
    )


def get_user_api_key(user: User) -> Optional[str]:
    """
    Get the decrypted API key for a user.

    Used internally by the chat service.
    Returns None if no key is configured.
    """
    if not user or not user.settings:
        return None

    api_keys = user.settings.get("api_keys", {})
    anthropic_config = api_keys.get("anthropic", {})
    encrypted_key = anthropic_config.get("encrypted_key")

    if not encrypted_key:
        return None

    return decrypt_value(encrypted_key, settings.jwt_secret)
