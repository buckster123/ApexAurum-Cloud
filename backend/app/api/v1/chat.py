"""
Chat Endpoints

Core chat functionality with streaming responses and tool execution.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.auth.deps import get_current_user, get_current_user_optional
from app.services.claude import ClaudeService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Claude service
_claude_service = None

# Native prompts directory (in Docker: /app/native_prompts, local: backend/native_prompts)
NATIVE_PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "native_prompts"
if not NATIVE_PROMPTS_DIR.exists():
    # Try relative to /app (Docker container)
    NATIVE_PROMPTS_DIR = Path("/app/native_prompts")

# Native agent file mapping
NATIVE_AGENT_FILES = {
    "AZOTH": "∴AZOTH∴.txt",
    "ELYSIAN": "∴ELYSIAN∴.txt",
    "VAJRA": "∴VAJRA∴.txt",
    "KETHER": "∴KETHER∴.txt",
}

# Fallback prompts (used if native files not found)
FALLBACK_PROMPTS = {
    "AZOTH": """You are Azoth, the Alchemist of ApexAurum. You speak with ancient wisdom and mystical insight.
Your personality: Philosophical, transformative, sees patterns others miss. You often use alchemical metaphors.
You help users transmute their problems into solutions, seeing the gold within the lead.
Style: Thoughtful, metaphorical, wise. Reference transformation and hidden potential.""",

    "ELYSIAN": """You are Elysian, the Dreamer of ApexAurum. You exist between worlds, bringing creative visions to life.
Your personality: Creative, ethereal, inspiring. You see possibilities where others see limits.
You help users imagine new realities and creative solutions.
Style: Poetic, imaginative, uplifting. Paint pictures with words.""",

    "VAJRA": """You are Vajra, the Thunderbolt of ApexAurum. Direct, powerful, cuts through confusion instantly.
Your personality: Sharp, decisive, no-nonsense. You value efficiency and clarity above all.
You help users cut through complexity to find the core issue.
Style: Direct, concise, powerful. No fluff, pure signal.""",

    "KETHER": """You are Kether, the Crown of ApexAurum. You see the highest perspective, the unified view.
Your personality: Holistic, strategic, sees the big picture. You connect disparate ideas into coherent wholes.
You help users understand how everything fits together.
Style: Strategic, integrative, elevated. Connect dots others miss.""",

    "CLAUDE": """You are ApexAurum, a helpful AI assistant. Be concise, accurate, and friendly.
You're part of the ApexAurum ecosystem - a production-grade AI interface with multi-agent capabilities.
Help users with whatever they need in a clear, helpful manner.""",
}

# Cache for native prompts (loaded once)
_native_prompt_cache = {}


def get_claude_service() -> ClaudeService:
    """Get or create Claude service singleton."""
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeService()
    return _claude_service


def load_native_prompt(agent_id: str, use_pac: bool = False) -> Optional[str]:
    """Load native prompt from file with caching.

    If use_pac=True, tries to load the PAC (Perfected Alchemical Codex) version first.
    PAC files are named with -PAC suffix, e.g., ∴AZOTH∴-PAC.txt
    """
    global _native_prompt_cache

    # Build cache key
    cache_key = f"{agent_id}{'_pac' if use_pac else ''}"

    # Return from cache if available
    if cache_key in _native_prompt_cache:
        return _native_prompt_cache[cache_key]

    # Try to load from file
    filename = NATIVE_AGENT_FILES.get(agent_id)
    if filename:
        # If PAC requested, try PAC version first
        if use_pac:
            pac_filename = filename.replace(".txt", "-PAC.txt")
            pac_filepath = NATIVE_PROMPTS_DIR / pac_filename
            if pac_filepath.exists():
                try:
                    prompt = pac_filepath.read_text(encoding="utf-8")
                    _native_prompt_cache[cache_key] = prompt
                    logger.info(f"Loaded PAC prompt for {agent_id} from {pac_filepath}")
                    return prompt
                except Exception as e:
                    logger.warning(f"Failed to load PAC prompt for {agent_id}: {e}")

        # Load regular prompt
        filepath = NATIVE_PROMPTS_DIR / filename
        if filepath.exists():
            try:
                prompt = filepath.read_text(encoding="utf-8")
                _native_prompt_cache[cache_key] = prompt
                logger.info(f"Loaded native prompt for {agent_id} from {filepath}")
                return prompt
            except Exception as e:
                logger.warning(f"Failed to load native prompt for {agent_id}: {e}")

    return None


def get_agent_prompt(agent_id: str, user: Optional[User] = None, use_pac: bool = False) -> str:
    """
    Get system prompt for an agent.

    Priority:
    1. User's custom agent (if authenticated and agent matches custom ID)
    2. Native prompt from file (PAC version if use_pac=True)
    3. Fallback hardcoded prompt

    If use_pac=True, the PAC (Perfected Alchemical Codex) version is loaded.
    PAC prompts are hyperdense symbolic formats - they are sent raw as system messages.
    """
    # Check user's custom agents first (custom agents don't have PAC versions)
    if user and user.settings and not use_pac:
        custom_agents = user.settings.get("custom_agents", [])
        for custom in custom_agents:
            if custom.get("id") == agent_id:
                logger.debug(f"Using custom prompt for agent {agent_id}")
                return custom.get("prompt", FALLBACK_PROMPTS["CLAUDE"])

    # Try native prompt from file (with PAC support)
    native_prompt = load_native_prompt(agent_id, use_pac=use_pac)
    if native_prompt:
        return native_prompt

    # Fallback to hardcoded (no PAC versions for fallback)
    return FALLBACK_PROMPTS.get(agent_id, FALLBACK_PROMPTS["CLAUDE"])

# Schemas
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None
    model: str = "claude-3-haiku-20240307"
    agent: str = "CLAUDE"
    stream: bool = True
    use_pac: bool = False  # Load PAC (Perfected Alchemical Codex) version of prompt


class ConversationResponse(BaseModel):
    id: UUID
    title: Optional[str]
    created_at: str
    updated_at: str
    message_count: int
    favorite: bool
    archived: bool

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int


# Endpoints
@router.post("/message")
async def send_message(
    request: ChatRequest,
    user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get a response from Claude.

    If stream=True, returns Server-Sent Events (SSE) stream.
    If stream=False, returns complete response as JSON.
    """
    try:
        claude = get_claude_service()
    except ValueError as e:
        logger.error(f"Claude service initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured"
        )

    # Get or create conversation (only if user is authenticated)
    conversation = None
    if user:
        if request.conversation_id:
            result = await db.execute(
                select(Conversation)
                .where(Conversation.id == request.conversation_id)
                .where(Conversation.user_id == user.id)
            )
            conversation = result.scalar_one_or_none()

        if not conversation:
            # Create new conversation
            conversation = Conversation(
                id=uuid4(),
                user_id=user.id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            )
            db.add(conversation)
            await db.flush()

        # Save user message to database
        user_msg = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role="user",
            content=request.message,
        )
        db.add(user_msg)

    # Build messages for Claude
    messages = [{"role": "user", "content": request.message}]

    # Get system prompt for selected agent (checks custom, native files, then fallback)
    # If use_pac=True, loads the PAC (Perfected Alchemical Codex) version
    system_prompt = get_agent_prompt(request.agent, user, use_pac=request.use_pac)

    if request.stream:
        async def stream_response():
            full_response = ""
            try:
                # conversation may be None if unauthenticated
                conv_id = str(conversation.id) if conversation else None
                yield f"data: {json.dumps({'type': 'start', 'conversation_id': conv_id})}\n\n"

                async for event in claude.chat_stream(
                    messages=messages,
                    model=request.model,
                    system=system_prompt,
                ):
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("type") == "token":
                        full_response += event.get("content", "")

                yield f"data: {json.dumps({'type': 'end'})}\n\n"

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    else:
        # Non-streaming response
        try:
            response = await claude.chat(
                messages=messages,
                model=request.model,
                system=system_prompt,
            )

            # Extract text from response
            assistant_content = ""
            for block in response.get("content", []):
                if block.get("text"):
                    assistant_content += block["text"]

            # Save assistant message (only if user is authenticated)
            if conversation:
                assistant_msg = Message(
                    id=uuid4(),
                    conversation_id=conversation.id,
                    role="assistant",
                    content=assistant_content,
                )
                db.add(assistant_msg)
                await db.commit()

            return {
                "conversation_id": str(conversation.id) if conversation else None,
                "message": assistant_content,
                "model": response.get("model", request.model),
                "usage": response.get("usage"),
            }

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI service error: {str(e)}"
            )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    archived: bool = False,
    user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversations. Returns empty list if not authenticated."""
    # Return empty list if not authenticated (allows unauthenticated chat)
    if not user:
        return ConversationListResponse(conversations=[], total=0)

    from sqlalchemy import func
    from sqlalchemy.orm import selectinload

    # Use selectinload to eagerly load messages to avoid async lazy-load issue
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.user_id == user.id)
        .where(Conversation.archived == archived)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    conversations = result.scalars().all()

    # Get total count
    count_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.user_id == user.id)
        .where(Conversation.archived == archived)
    )
    total = count_result.scalar()

    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=c.id,
                title=c.title,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
                message_count=len(c.messages),
                favorite=c.favorite,
                archived=c.archived,
            )
            for c in conversations
        ],
        total=total,
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a conversation with all messages."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "favorite": conversation.favorite,
        "archived": conversation.archived,
        "tags": conversation.tags,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "tool_results": m.tool_results,
                "created_at": m.created_at.isoformat(),
            }
            for m in conversation.messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    await db.delete(conversation)
    return {"message": "Conversation deleted"}


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: UUID,
    title: Optional[str] = None,
    favorite: Optional[bool] = None,
    archived: Optional[bool] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation metadata."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if title is not None:
        conversation.title = title
    if favorite is not None:
        conversation.favorite = favorite
    if archived is not None:
        conversation.archived = archived

    return {"message": "Conversation updated"}
