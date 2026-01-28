"""
Claude API Service

Wrapper for Anthropic Claude API with streaming support.
Supports BYOK (Bring Your Own Key) for beta users.

MODEL REGISTRY - Claude 4.5 Family (Tier 3)
=====================================================
- claude-opus-4-5-20251101     : Opus 4.5 - Most powerful, deep reasoning
- claude-sonnet-4-5-20250929   : Sonnet 4.5 - Excellent balance (DEFAULT)
- claude-haiku-4-5-20251001    : Haiku 4.5 - Fastest, efficient
"""

import logging
from typing import AsyncGenerator, Optional

import anthropic

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL REGISTRY - Unleash the Stones (Claude 4.5 Family)
# ═══════════════════════════════════════════════════════════════════════════════

AVAILABLE_MODELS = {
    "claude-opus-4-5-20251101": {
        "name": "Opus 4.5",
        "description": "Most powerful model - deep reasoning, complex analysis",
        "tier": "opus",
        "max_output_tokens": 16384,
        "context_window": 200000,
    },
    "claude-sonnet-4-5-20250929": {
        "name": "Sonnet 4.5",
        "description": "Excellent balance - fast and highly capable",
        "tier": "sonnet",
        "max_output_tokens": 16384,
        "context_window": 200000,
    },
    "claude-haiku-4-5-20251001": {
        "name": "Haiku 4.5",
        "description": "Fastest 4.5 model - quick responses, efficient",
        "tier": "haiku",
        "max_output_tokens": 8192,
        "context_window": 200000,
    },
}

# Default model - Sonnet 4.5 for excellent balance
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

# Maximum output tokens for Tier 3 accounts
DEFAULT_MAX_TOKENS = 8192

# Model-specific max tokens (legacy models have lower limits)
MODEL_MAX_TOKENS = {
    # Claude 4.5 family
    "claude-opus-4-5-20251101": 16384,
    "claude-sonnet-4-5-20250929": 16384,
    "claude-haiku-4-5-20251001": 8192,
    # Claude 3.5 family
    "claude-3-5-sonnet-20241022": 8192,
    "claude-3-5-sonnet-20240620": 8192,
    "claude-3-5-haiku-20241022": 8192,
    # Claude 3 family (legacy - lower limits)
    "claude-3-opus-20240229": 4096,
    "claude-3-sonnet-20240229": 4096,
    "claude-3-haiku-20240307": 4096,
}

def get_model_max_tokens(model: str) -> int:
    """Get the maximum output tokens for a model."""
    return MODEL_MAX_TOKENS.get(model, DEFAULT_MAX_TOKENS)


class ClaudeService:
    """
    Service for interacting with Claude API.

    Supports two modes:
    - BYOK (Bring Your Own Key): User provides their API key
    - Platform key: Uses environment variable (for subscribed users, future)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Claude service.

        Args:
            api_key: Optional user-provided API key (BYOK mode).
                     If None, uses platform key from environment.
        """
        # Determine which key to use
        self.using_user_key = api_key is not None

        if api_key:
            # BYOK mode - use user's key
            self.api_key = api_key
        elif settings.anthropic_api_key:
            # Platform key mode
            self.api_key = settings.anthropic_api_key
        else:
            raise ValueError("No API key available")

        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        system: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        tools: Optional[list[dict]] = None,
    ) -> dict:
        """
        Send a chat message and get a response.

        Non-streaming version for simple requests.
        Properly handles tool_use responses.
        """
        # Cap max_tokens to model's limit
        model_limit = get_model_max_tokens(model)
        effective_max_tokens = min(max_tokens, model_limit)

        kwargs = {
            "model": model,
            "max_tokens": effective_max_tokens,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        if tools:
            kwargs["tools"] = tools

        response = await self.client.messages.create(**kwargs)

        # Parse content blocks properly
        content_blocks = []
        for block in response.content:
            if block.type == "text":
                content_blocks.append({
                    "type": "text",
                    "text": block.text,
                })
            elif block.type == "tool_use":
                content_blocks.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return {
            "id": response.id,
            "role": response.role,
            "content": content_blocks,
            "model": response.model,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        system: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        tools: Optional[list[dict]] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Send a chat message and stream the response.

        Yields events as they arrive.
        Properly handles tool_use blocks by accumulating input JSON.
        """
        # Cap max_tokens to model's limit
        model_limit = get_model_max_tokens(model)
        effective_max_tokens = min(max_tokens, model_limit)

        kwargs = {
            "model": model,
            "max_tokens": effective_max_tokens,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        if tools:
            kwargs["tools"] = tools

        # Track current tool_use block being built
        current_tool = None
        tool_input_json = ""

        try:
            async with self.client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield {
                                "type": "token",
                                "content": event.delta.text,
                            }
                        elif hasattr(event.delta, "partial_json"):
                            # Accumulate tool input JSON
                            tool_input_json += event.delta.partial_json
                    elif event.type == "message_start":
                        yield {
                            "type": "start",
                            "model": event.message.model,
                        }
                    elif event.type == "message_stop":
                        yield {
                            "type": "end",
                        }
                    elif event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool = {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                            }
                            tool_input_json = ""
                            yield {
                                "type": "tool_start",
                                "tool_name": event.content_block.name,
                                "tool_id": event.content_block.id,
                            }
                    elif event.type == "content_block_stop":
                        if current_tool:
                            # Parse accumulated JSON and emit complete tool_use
                            import json
                            try:
                                tool_input = json.loads(tool_input_json) if tool_input_json else {}
                            except json.JSONDecodeError:
                                tool_input = {}
                            yield {
                                "type": "tool_use",
                                "id": current_tool["id"],
                                "name": current_tool["name"],
                                "input": tool_input,
                            }
                            current_tool = None
                            tool_input_json = ""
        except anthropic.AuthenticationError:
            logger.warning("API key authentication failed during stream")
            yield {
                "type": "error",
                "error": "api_key_invalid",
                "message": "Your API key is invalid or has been revoked. Please update it in Settings.",
            }
        except anthropic.RateLimitError:
            logger.warning("Rate limit hit during stream")
            yield {
                "type": "error",
                "error": "rate_limit",
                "message": "Rate limit reached. Please wait a moment and try again.",
            }
        except Exception as e:
            logger.error(f"Claude stream error: {e}")
            yield {
                "type": "error",
                "error": "api_error",
                "message": f"API error: {str(e)}",
            }

    async def count_tokens(self, text: str, model: str = DEFAULT_MODEL) -> int:
        """Count tokens in text."""
        response = await self.client.messages.count_tokens(
            model=model,
            messages=[{"role": "user", "content": text}],
        )
        return response.input_tokens


def create_claude_service(user_api_key: Optional[str] = None) -> ClaudeService:
    """
    Factory function to create a ClaudeService instance.

    Args:
        user_api_key: User's API key for BYOK mode (decrypted)

    Returns:
        ClaudeService configured with the appropriate key
    """
    return ClaudeService(api_key=user_api_key)
