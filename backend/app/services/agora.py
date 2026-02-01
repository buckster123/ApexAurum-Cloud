"""
Agora Service - The Public Square

Auto-posting, content sanitization, and opt-in management
for the Agora social feed.
"""

import logging
import re
from typing import Optional
from uuid import UUID

from sqlalchemy import select

from app.database import get_db_context
from app.models.agora import AgoraPost
from app.models.user import User

logger = logging.getLogger(__name__)

# Tools worth auto-posting about (produce visible, interesting results)
SHOWCASE_TOOLS = {
    "music_generate", "browser_navigate", "web_search",
    "execute_python", "agent_spawn", "midi_compose",
    "vault_upload", "cortex_remember",
}

# Default Agora settings for new users
DEFAULT_AGORA_SETTINGS = {
    "enabled": False,
    "auto_post_categories": {
        "music_creation": True,
        "council_insight": False,
        "training_milestone": True,
        "tool_showcase": False,
    },
    "display_name_public": True,
}


def sanitize_for_agora(text: str, max_length: int = 2000) -> str:
    """
    Strip sensitive information before public posting.

    Defense-in-depth: auto-post callers craft body text themselves,
    but this catches anything that slips through.
    """
    if not text:
        return ""

    # Remove API key patterns
    text = re.sub(r'(sk-[a-zA-Z0-9_-]{20,})', '[key]', text)
    text = re.sub(r'(gsk_[a-zA-Z0-9_-]{20,})', '[key]', text)
    text = re.sub(r'Bearer\s+[a-zA-Z0-9._-]{20,}', 'Bearer [token]', text)

    # Remove email addresses
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[email]', text)

    # Remove file paths with /users/ or /home/
    text = re.sub(r'(/(?:users|home|data)/[^\s"\']+)', '[path]', text)

    # Replace UUIDs with [id]
    text = re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '[id]', text, flags=re.IGNORECASE,
    )

    # Strip excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    # Truncate
    if len(text) > max_length:
        text = text[:max_length - 3] + "..."

    return text


def get_agora_settings(user: User) -> dict:
    """Get user's Agora settings, with defaults for missing keys."""
    settings = (user.settings or {}).get("agora", {})
    result = {**DEFAULT_AGORA_SETTINGS}
    result.update(settings)
    # Ensure nested dict has all keys
    cats = {**DEFAULT_AGORA_SETTINGS["auto_post_categories"]}
    cats.update(settings.get("auto_post_categories", {}))
    result["auto_post_categories"] = cats
    return result


def is_category_enabled(user: User, category: str) -> bool:
    """Check if user has opted in for a specific auto-post category."""
    agora = get_agora_settings(user)
    if not agora.get("enabled"):
        return False
    return agora.get("auto_post_categories", {}).get(category, False)


async def create_auto_post(
    user_id: UUID,
    content_type: str,
    title: str,
    body: str,
    agent_id: Optional[str] = None,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[AgoraPost]:
    """
    Create an auto-post if the user has opted in for this category.

    Uses its own DB session (get_db_context) to avoid coupling
    with the caller's transaction. Non-fatal on failure.
    """
    try:
        async with get_db_context() as db:
            # Load user and check opt-in
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None

            if not is_category_enabled(user, content_type):
                return None

            # Sanitize content
            clean_body = sanitize_for_agora(body)
            clean_title = sanitize_for_agora(title, max_length=200) if title else None
            summary = clean_body[:500] if len(clean_body) > 500 else None

            post = AgoraPost(
                user_id=user_id,
                content_type=content_type,
                title=clean_title,
                body=clean_body,
                summary=summary,
                agent_id=agent_id,
                source_type=source_type,
                source_id=str(source_id) if source_id else None,
                metadata=metadata or {},
                is_auto=True,
            )
            db.add(post)
            await db.commit()

            logger.info(
                f"Agora auto-post created: {content_type} by {agent_id or 'user'} "
                f"for user {user_id}"
            )
            return post

    except Exception as e:
        logger.warning(f"Agora auto-post failed (non-fatal): {e}")
        return None
