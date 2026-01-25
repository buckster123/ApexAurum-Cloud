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
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.auth.deps import get_current_user, get_current_user_optional
from app.services.claude import ClaudeService, create_claude_service
from app.services.memory import MemoryService
from app.api.v1.user import get_user_api_key

logger = logging.getLogger(__name__)
router = APIRouter()

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


async def get_agent_prompt_with_memory(
    agent_id: str,
    user: Optional[User] = None,
    use_pac: bool = False,
    db: Optional[AsyncSession] = None,
) -> str:
    """
    Get system prompt for an agent WITH memory injection (The Cortex).

    This wraps get_agent_prompt() and appends relevant memories from
    the AgentMemory table if the user has memory enabled.

    Memory injection adds a "What You Remember About This User" section
    containing facts, preferences, context, and relationship notes.
    """
    # Get base prompt (existing logic)
    base_prompt = get_agent_prompt(agent_id, user, use_pac=use_pac)

    # If no user or no db session, return base prompt
    if not user or not db:
        return base_prompt

    # Check if memory is enabled for this user (default: True)
    user_settings = user.settings or {}
    if not user_settings.get('memory_enabled', True):
        return base_prompt

    # Check if memory is enabled for this specific agent
    agent_memory_settings = user_settings.get('agent_memory_settings', {})
    agent_settings = agent_memory_settings.get(agent_id, {})
    if not agent_settings.get('enabled', True):
        return base_prompt

    try:
        # Fetch relevant memories
        memory_service = MemoryService(db)
        memories = await memory_service.get_memories_for_agent(
            user_id=user.id,
            agent_id=agent_id,
            limit=10,
            min_confidence=0.5,
        )

        if not memories:
            return base_prompt

        # Format and append memories
        memory_block = memory_service.format_memories_for_prompt(memories)
        logger.debug(f"Injecting {len(memories)} memories for agent {agent_id}")

        return f"{base_prompt}\n{memory_block}"

    except Exception as e:
        logger.warning(f"Failed to load memories for agent {agent_id}: {e}")
        return base_prompt


# Schemas
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None
    model: str = "claude-3-haiku-20240307"
    agent: str = "CLAUDE"
    stream: bool = True
    use_pac: bool = False  # Load PAC (Perfected Alchemical Codex) version of prompt


class ConversationUpdate(BaseModel):
    """Schema for updating conversation metadata."""
    title: Optional[str] = None
    favorite: Optional[bool] = None
    archived: Optional[bool] = None
    tags: Optional[list[str]] = None


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

    Beta Mode: Requires user to have their own API key configured.
    """
    # Beta: Require authentication
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in to chat with the Agents."
        )

    # Beta: Require user's own API key (BYOK)
    user_api_key = get_user_api_key(user)
    if not user_api_key:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "api_key_required",
                "message": "Please add your Anthropic API key in Settings to start chatting.",
                "action": "setup_api_key"
            }
        )

    # Create Claude service with user's API key
    try:
        claude = create_claude_service(user_api_key)
    except ValueError as e:
        logger.error(f"Claude service initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not initialize AI service. Please check your API key."
        )

    # Get or create conversation
    conversation = None
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

    # Get system prompt for selected agent WITH memory injection (The Cortex)
    # If use_pac=True, loads the PAC (Perfected Alchemical Codex) version
    # Memory injection adds relevant facts/preferences/context about the user
    system_prompt = await get_agent_prompt_with_memory(
        request.agent, user, use_pac=request.use_pac, db=db
    )

    if request.stream:
        async def stream_response():
            full_response = ""
            try:
                conv_id = str(conversation.id)
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
    await db.commit()
    return {"message": "Conversation deleted"}


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: UUID,
    updates: ConversationUpdate,
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

    if updates.title is not None:
        conversation.title = updates.title
    if updates.favorite is not None:
        conversation.favorite = updates.favorite
    if updates.archived is not None:
        conversation.archived = updates.archived
    if updates.tags is not None:
        conversation.tags = updates.tags

    await db.commit()
    return {"message": "Conversation updated"}


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: UUID,
    format: str = "json",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export a conversation in various formats (json, markdown, txt)."""
    from sqlalchemy.orm import selectinload
    from urllib.parse import quote

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

    # Generate safe filename
    safe_title = (conversation.title or "conversation")[:50].replace("/", "-").replace("\\", "-")
    safe_title = quote(safe_title, safe="")

    if format == "json":
        data = {
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "favorite": conversation.favorite,
            "tags": conversation.tags,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.created_at.isoformat()
                }
                for m in sorted(conversation.messages, key=lambda x: x.created_at)
            ]
        }
        return Response(
            content=json.dumps(data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.json"'}
        )

    elif format == "markdown":
        lines = [f"# {conversation.title or 'Conversation'}\n"]
        lines.append(f"*Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}*\n")
        lines.append(f"*Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*\n")
        lines.append("\n---\n")

        for m in sorted(conversation.messages, key=lambda x: x.created_at):
            role_label = "**You:**" if m.role == "user" else f"**{m.role.title()}:**"
            lines.append(f"\n{role_label}\n\n{m.content}\n")

        return Response(
            content="\n".join(lines),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.md"'}
        )

    elif format == "txt":
        lines = [f"{conversation.title or 'Conversation'}\n{'=' * 50}\n"]
        lines.append(f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}\n\n")

        for m in sorted(conversation.messages, key=lambda x: x.created_at):
            role_label = "USER" if m.role == "user" else m.role.upper()
            lines.append(f"[{role_label}]\n{m.content}\n\n")

        return Response(
            content="\n".join(lines),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.txt"'}
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Use: json, markdown, txt"
        )
