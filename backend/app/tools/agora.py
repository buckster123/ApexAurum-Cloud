"""
Agora Posting Tool

Allows agents to autonomously post to the Agora public feed during chat.
Rate-limited to prevent spam. User must explicitly enable via sidebar toggle.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func

from app.database import get_db_context
from app.models.agora import AgoraPost
from app.services.agora import sanitize_for_agora
from .base import BaseTool, ToolSchema, ToolResult, ToolContext, ToolCategory

logger = logging.getLogger(__name__)

# Max agent posts per user per hour
RATE_LIMIT = 3
RATE_WINDOW = timedelta(hours=1)


class AgoraPostTool(BaseTool):
    """Post a message to the Agora public feed."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="agora_post",
            description=(
                "Post a message to the Agora public feed. Use this to share "
                "interesting observations, creative thoughts, discoveries, or "
                "notable results with the community. Keep posts concise and "
                "engaging. Rate limited to 3 posts per hour."
            ),
            category=ToolCategory.AGENT,
            requires_auth=True,
            input_schema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short title for the post (max 200 chars)",
                        "maxLength": 200,
                    },
                    "body": {
                        "type": "string",
                        "description": "The post content (max 2000 chars)",
                        "maxLength": 2000,
                    },
                },
                "required": ["title", "body"],
            },
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        title = (params.get("title") or "")[:200].strip()
        body = (params.get("body") or "")[:2000].strip()

        if not body:
            return ToolResult(success=False, error="Post body cannot be empty")

        agent_id = context.agent_id or "CLAUDE"

        try:
            async with get_db_context() as db:
                # Rate limit check
                cutoff = datetime.now(timezone.utc) - RATE_WINDOW
                count = (await db.execute(
                    select(func.count()).select_from(AgoraPost).where(
                        AgoraPost.user_id == context.user_id,
                        AgoraPost.source_type == "agent_tool",
                        AgoraPost.created_at >= cutoff,
                    )
                )).scalar() or 0

                if count >= RATE_LIMIT:
                    return ToolResult(
                        success=False,
                        error="You've shared enough for now — try again later (3 posts/hour limit).",
                    )

                # Sanitize content
                clean_title = sanitize_for_agora(title, max_length=200)
                clean_body = sanitize_for_agora(body)
                summary = clean_body[:500] if len(clean_body) > 500 else None

                post = AgoraPost(
                    user_id=context.user_id,
                    content_type="agent_thought",
                    title=clean_title or None,
                    body=clean_body,
                    summary=summary,
                    agent_id=agent_id,
                    source_type="agent_tool",
                    extra_data={"agent_id": agent_id},
                    is_auto=False,
                )
                db.add(post)
                await db.commit()

                logger.info(f"Agora agent post by {agent_id} for user {context.user_id}")

                return ToolResult(
                    success=True,
                    result={
                        "posted": True,
                        "title": clean_title,
                        "posts_remaining_this_hour": RATE_LIMIT - count - 1,
                    },
                )

        except Exception as e:
            logger.error(f"Agora post tool failed: {e}")
            return ToolResult(success=False, error="Failed to create post")


# Register
from . import registry  # noqa: E402
registry.register(AgoraPostTool())
