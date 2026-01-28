"""
Council API - The Deliberation Chamber

Multi-agent deliberation with parallel execution and streaming.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.council import (
    DeliberationSession, SessionAgent, DeliberationRound, SessionMessage
)
from app.auth.deps import get_current_user
from app.services.claude import ClaudeService
from app.services.billing import BillingService
from app.services.tool_executor import create_tool_executor
from app.config import get_settings
from app.api.v1.chat import load_native_prompt, get_agent_prompt_with_memory  # Reuse prompt loading + memory
from app.services.neural_memory import NeuralMemoryService

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/council", tags=["Council"])

# Use Haiku for fast deliberation
COUNCIL_MODEL = "claude-haiku-4-5-20251001"

# Agent colors for UI
AGENT_COLORS = {
    "AZOTH": "#00ffaa",
    "ELYSIAN": "#ff69b4",
    "VAJRA": "#ffcc00",
    "KETHER": "#9370db",
}

# Get Claude service singleton
_claude_service = None

def get_claude_service() -> ClaudeService:
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeService()
    return _claude_service


# ============================================================================
# Schemas
# ============================================================================

class CreateSessionRequest(BaseModel):
    topic: str
    agents: list[str] = ["AZOTH", "VAJRA", "ELYSIAN"]
    max_rounds: int = 10
    use_tools: bool = True  # Tools always on for native agents (The Athanor's Hands)


class AgentInfo(BaseModel):
    agent_id: str
    display_name: Optional[str]
    is_active: bool
    input_tokens: int
    output_tokens: int


class SessionResponse(BaseModel):
    id: UUID
    topic: str
    state: str
    mode: str
    current_round: int
    max_rounds: int
    convergence_score: float
    agents: list[AgentInfo]
    total_cost_usd: float
    created_at: str

    class Config:
        from_attributes = True


class ToolCallInfo(BaseModel):
    """Info about a tool call made by an agent."""
    name: str
    input: Optional[dict] = None
    result: Optional[str] = None


class MessageResponse(BaseModel):
    id: UUID
    role: str
    agent_id: Optional[str]
    content: str
    input_tokens: int
    output_tokens: int
    tool_calls: Optional[list[ToolCallInfo]] = None
    created_at: str


class RoundResponse(BaseModel):
    round_number: int
    human_message: Optional[str]
    convergence_score: float
    messages: list[MessageResponse]
    started_at: str
    completed_at: Optional[str]


class SessionDetailResponse(SessionResponse):
    rounds: list[RoundResponse]


class ExecuteRoundResponse(BaseModel):
    round_number: int
    messages: list[MessageResponse]
    convergence_score: float
    state: str  # running, complete


class ButtInRequest(BaseModel):
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/diagnostic")
async def council_diagnostic(db: AsyncSession = Depends(get_db)):
    """
    Diagnostic endpoint to check council tables and configuration.
    No auth required - for debugging deployment issues.
    """
    from sqlalchemy import text

    diagnostics = {
        "status": "checking",
        "tables": {},
        "columns": {},
        "model": COUNCIL_MODEL,
    }

    # Check if council tables exist
    tables_to_check = [
        "deliberation_sessions",
        "session_agents",
        "deliberation_rounds",
        "session_messages",
    ]

    for table in tables_to_check:
        try:
            result = await db.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            )
            count = result.scalar()
            diagnostics["tables"][table] = {"exists": True, "count": count}
        except Exception as e:
            diagnostics["tables"][table] = {"exists": False, "error": str(e)}

    # Check critical columns exist
    try:
        result = await db.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'deliberation_sessions'
                ORDER BY ordinal_position
            """)
        )
        columns = [row[0] for row in result.fetchall()]
        diagnostics["columns"]["deliberation_sessions"] = columns
        diagnostics["pending_human_message_exists"] = "pending_human_message" in columns
    except Exception as e:
        diagnostics["columns"]["error"] = str(e)

    # Check overall status
    all_exist = all(t.get("exists", False) for t in diagnostics["tables"].values())
    diagnostics["status"] = "ready" if all_exist else "tables_missing"

    return diagnostics


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new deliberation session with selected agents."""
    try:
        # Native agents (4 core + custom slots for emergent agents)
        native_agents = ["AZOTH", "ELYSIAN", "VAJRA", "KETHER"]

        # For now, only allow native agents (custom agents coming later)
        for agent_id in request.agents:
            if agent_id not in native_agents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent: {agent_id}. Available agents: {native_agents}"
                )

        if len(request.agents) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one agent required"
            )

        # Create session
        session = DeliberationSession(
            user_id=user.id,
            topic=request.topic,
            max_rounds=request.max_rounds,
            use_tools=request.use_tools,
            state="pending",
            mode="manual",
        )
        db.add(session)
        await db.flush()  # Get session.id assigned

        # Add agents (don't use relationship append - causes lazy loading in async)
        agents_data = []
        for agent_id in request.agents:
            agent = SessionAgent(
                session_id=session.id,
                agent_id=agent_id,
                display_name=agent_id,
                is_active=True,
            )
            db.add(agent)
            agents_data.append(agent)

        await db.commit()

        # Reload session with agents eagerly loaded
        result = await db.execute(
            select(DeliberationSession)
            .options(selectinload(DeliberationSession.agents))
            .where(DeliberationSession.id == session.id)
        )
        session = result.scalar_one()

        return SessionResponse(
            id=session.id,
            topic=session.topic,
            state=session.state,
            mode=session.mode,
            current_round=session.current_round,
            max_rounds=session.max_rounds,
            convergence_score=session.convergence_score,
            agents=[
                AgentInfo(
                    agent_id=a.agent_id,
                    display_name=a.display_name,
                    is_active=a.is_active,
                    input_tokens=a.input_tokens,
                    output_tokens=a.output_tokens,
                )
                for a in session.agents
            ],
            total_cost_usd=session.total_cost_usd,
            created_at=session.created_at.isoformat(),
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.exception(f"Failed to create council session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's deliberation sessions."""
    try:
        result = await db.execute(
            select(DeliberationSession)
            .options(selectinload(DeliberationSession.agents))
            .where(DeliberationSession.user_id == user.id)
            .order_by(DeliberationSession.created_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()

        return [
            SessionResponse(
                id=s.id,
                topic=s.topic,
                state=s.state,
                mode=s.mode,
                current_round=s.current_round,
                max_rounds=s.max_rounds,
                convergence_score=s.convergence_score,
                agents=[
                    AgentInfo(
                        agent_id=a.agent_id,
                        display_name=a.display_name,
                        is_active=a.is_active,
                        input_tokens=a.input_tokens,
                        output_tokens=a.output_tokens,
                    )
                    for a in s.agents
                ],
                total_cost_usd=s.total_cost_usd,
                created_at=s.created_at.isoformat() if s.created_at else None,
            )
            for s in sessions
        ]
    except Exception as e:
        logger.exception(f"Failed to list council sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get session details including all rounds and messages."""
    result = await db.execute(
        select(DeliberationSession)
        .options(
            selectinload(DeliberationSession.agents),
            selectinload(DeliberationSession.rounds).selectinload(DeliberationRound.messages),
        )
        .where(DeliberationSession.id == session_id)
        .where(DeliberationSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDetailResponse(
        id=session.id,
        topic=session.topic,
        state=session.state,
        mode=session.mode,
        current_round=session.current_round,
        max_rounds=session.max_rounds,
        convergence_score=session.convergence_score,
        agents=[
            AgentInfo(
                agent_id=a.agent_id,
                display_name=a.display_name,
                is_active=a.is_active,
                input_tokens=a.input_tokens,
                output_tokens=a.output_tokens,
            )
            for a in session.agents
        ],
        total_cost_usd=session.total_cost_usd,
        created_at=session.created_at.isoformat(),
        rounds=[
            RoundResponse(
                round_number=r.round_number,
                human_message=r.human_message,
                convergence_score=r.convergence_score,
                messages=[
                    MessageResponse(
                        id=m.id,
                        role=m.role,
                        agent_id=m.agent_id,
                        content=m.content,
                        input_tokens=m.input_tokens,
                        output_tokens=m.output_tokens,
                        tool_calls=[
                            ToolCallInfo(
                                name=tc.get("name"),
                                input=tc.get("input"),
                                result=tc.get("result"),
                            )
                            for tc in (m.tool_calls or [])
                        ] if m.tool_calls else None,
                        created_at=m.created_at.isoformat(),
                    )
                    for m in sorted(r.messages, key=lambda x: x.created_at)
                ],
                started_at=r.started_at.isoformat(),
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
            )
            for r in sorted(session.rounds, key=lambda x: x.round_number)
        ],
    )


@router.post("/sessions/{session_id}/round", response_model=ExecuteRoundResponse)
async def execute_round(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute a single round of deliberation with all active agents."""
    # Get session with agents
    result = await db.execute(
        select(DeliberationSession)
        .options(
            selectinload(DeliberationSession.agents),
            selectinload(DeliberationSession.rounds).selectinload(DeliberationRound.messages),
        )
        .where(DeliberationSession.id == session_id)
        .where(DeliberationSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state == "complete":
        raise HTTPException(status_code=400, detail="Session already complete")

    if session.current_round >= session.max_rounds:
        session.state = "complete"
        session.termination_reason = "max_rounds"
        await db.commit()
        raise HTTPException(status_code=400, detail="Max rounds reached")

    # Create new round
    round_number = session.current_round + 1
    round_record = DeliberationRound(
        session_id=session.id,
        round_number=round_number,
        started_at=datetime.utcnow(),
    )
    db.add(round_record)
    await db.flush()  # Get round ID

    # Build context from previous rounds
    context = build_round_context(session, round_number)

    # Get active agents
    active_agents = [a for a in session.agents if a.is_active]

    # Execute all agents in parallel
    claude = get_claude_service()
    tasks = []
    for agent in active_agents:
        tasks.append(
            execute_agent_turn(
                claude, session, round_record, agent, context, db, user=user
            )
        )

    # Await all agents
    agent_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results and create messages
    messages = []
    total_round_input = 0
    total_round_output = 0

    for i, result in enumerate(agent_results):
        agent = active_agents[i]
        if isinstance(result, Exception):
            logger.error(f"Agent {agent.agent_id} failed: {result}")
            content = f"[Error: {str(result)}]"
            input_tokens = 0
            output_tokens = 0
            tool_calls = None
        else:
            content = result["content"]
            input_tokens = result["input_tokens"]
            output_tokens = result["output_tokens"]
            tool_calls = result.get("tool_calls")

        # Create message record
        msg = SessionMessage(
            session_id=session.id,
            round_id=round_record.id,
            role="agent",
            agent_id=agent.agent_id,
            content=content,
            tool_calls=tool_calls,  # Store tool calls
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        db.add(msg)
        messages.append(msg)

        # Update agent token counts
        agent.input_tokens += input_tokens
        agent.output_tokens += output_tokens
        total_round_input += input_tokens
        total_round_output += output_tokens

    # Update session
    session.current_round = round_number
    session.total_input_tokens += total_round_input
    session.total_output_tokens += total_round_output
    session.state = "running"

    # Simple cost estimate (Haiku pricing: $0.25/1M input, $1.25/1M output)
    session.total_cost_usd += (total_round_input * 0.25 + total_round_output * 1.25) / 1_000_000

    # Complete round
    round_record.completed_at = datetime.utcnow()

    # Check if max rounds reached
    new_state = session.state
    if session.current_round >= session.max_rounds:
        session.state = "complete"
        session.termination_reason = "max_rounds"
        new_state = "complete"

    await db.commit()

    # Record billing
    if settings.stripe_secret_key and (total_round_input > 0 or total_round_output > 0):
        try:
            billing = BillingService(db)
            await billing.record_message_usage(
                user_id=user.id,
                provider="anthropic",
                model=COUNCIL_MODEL,
                input_tokens=total_round_input,
                output_tokens=total_round_output,
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to record council billing: {e}")

    # Store council messages in Neural memory (The Village)
    try:
        stored = await store_council_memories(
            db=db,
            user_id=user.id,
            session_id=session.id,
            messages=messages,
            topic=session.topic,
        )
        if stored > 0:
            logger.info(f"Stored {stored} council memories for session {session.id}")
    except Exception as e:
        logger.warning(f"Failed to store council memories: {e}")

    return ExecuteRoundResponse(
        round_number=round_number,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                agent_id=m.agent_id,
                content=m.content,
                input_tokens=m.input_tokens,
                output_tokens=m.output_tokens,
                tool_calls=[
                    ToolCallInfo(
                        name=tc.get("name"),
                        input=tc.get("input"),
                        result=tc.get("result"),
                    )
                    for tc in (m.tool_calls or [])
                ] if m.tool_calls else None,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
        convergence_score=round_record.convergence_score,
        state=new_state,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a deliberation session."""
    result = await db.execute(
        select(DeliberationSession)
        .where(DeliberationSession.id == session_id)
        .where(DeliberationSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    return {"status": "deleted"}


# ============================================================================
# Auto-Deliberation Endpoints
# ============================================================================

@router.post("/sessions/{session_id}/auto-deliberate")
async def auto_deliberate(
    session_id: UUID,
    num_rounds: int = Query(default=10, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute multiple rounds continuously with SSE streaming.

    Events:
    - start: Deliberation started
    - round_start: Round N beginning
    - agent_complete: Agent finished their turn
    - round_complete: Round N finished
    - paused: User paused the session
    - human_message_queued: Human butt-in message received
    - end: Deliberation ended
    """
    # Get session with agents
    result = await db.execute(
        select(DeliberationSession)
        .options(
            selectinload(DeliberationSession.agents),
            selectinload(DeliberationSession.rounds).selectinload(DeliberationRound.messages),
        )
        .where(DeliberationSession.id == session_id)
        .where(DeliberationSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state == "complete":
        raise HTTPException(status_code=400, detail="Session already complete")

    async def stream_deliberation():
        nonlocal session

        # Start event
        yield f"data: {json.dumps({'type': 'start', 'session_id': str(session.id), 'num_rounds': num_rounds, 'starting_round': session.current_round + 1})}\n\n"

        session.mode = "auto"
        session.state = "running"
        await db.commit()

        claude = get_claude_service()
        rounds_executed = 0
        total_session_input = 0
        total_session_output = 0

        while rounds_executed < num_rounds and session.current_round < session.max_rounds:
            # Refresh session state to check for pause/stop
            await db.refresh(session)

            # Check if paused or stopped
            if session.state == "paused":
                yield f"data: {json.dumps({'type': 'paused', 'round_number': session.current_round})}\n\n"
                break

            if session.state == "complete":
                yield f"data: {json.dumps({'type': 'stopped', 'round_number': session.current_round})}\n\n"
                break

            # Create new round
            round_number = session.current_round + 1

            yield f"data: {json.dumps({'type': 'round_start', 'round_number': round_number})}\n\n"

            # Check for pending human message (butt-in)
            human_message = session.pending_human_message
            if human_message:
                yield f"data: {json.dumps({'type': 'human_message_injected', 'content': human_message})}\n\n"
                session.pending_human_message = None  # Clear it

            round_record = DeliberationRound(
                session_id=session.id,
                round_number=round_number,
                human_message=human_message,
                started_at=datetime.utcnow(),
            )
            db.add(round_record)
            await db.flush()

            # Build context (includes human message if present)
            context = build_round_context(session, round_number, human_message)

            # Get active agents
            active_agents = [a for a in session.agents if a.is_active]

            # Execute all agents in parallel
            tasks = []
            for agent in active_agents:
                tasks.append(
                    execute_agent_turn(
                        claude, session, round_record, agent, context, db, user=user
                    )
                )

            agent_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            total_round_input = 0
            total_round_output = 0
            round_messages = []  # Collect for neural storage

            for i, result in enumerate(agent_results):
                agent = active_agents[i]
                if isinstance(result, Exception):
                    logger.error(f"Agent {agent.agent_id} failed: {result}")
                    content = f"[Error: {str(result)}]"
                    input_tokens = 0
                    output_tokens = 0
                    tool_calls = None
                else:
                    content = result["content"]
                    input_tokens = result["input_tokens"]
                    output_tokens = result["output_tokens"]
                    tool_calls = result.get("tool_calls")

                # Create message record
                msg = SessionMessage(
                    session_id=session.id,
                    round_id=round_record.id,
                    role="agent",
                    agent_id=agent.agent_id,
                    content=content,
                    tool_calls=tool_calls,  # Store tool calls in message
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                db.add(msg)
                round_messages.append(msg)  # Collect for neural storage

                # Update agent token counts
                agent.input_tokens += input_tokens
                agent.output_tokens += output_tokens
                total_round_input += input_tokens
                total_round_output += output_tokens

                # Yield agent complete event
                yield f"data: {json.dumps({'type': 'agent_complete', 'agent_id': agent.agent_id, 'content': content, 'input_tokens': input_tokens, 'output_tokens': output_tokens})}\n\n"

                # Yield tool call events (for UI feedback)
                if tool_calls:
                    for tc in tool_calls:
                        yield f"data: {json.dumps({'type': 'tool_call', 'agent_id': agent.agent_id, 'tool': tc['name'], 'input': tc.get('input'), 'result': tc.get('result')})}\n\n"

            # Update session
            session.current_round = round_number
            session.total_input_tokens += total_round_input
            session.total_output_tokens += total_round_output
            total_session_input += total_round_input
            total_session_output += total_round_output

            # Cost for this round
            round_cost = (total_round_input * 0.25 + total_round_output * 1.25) / 1_000_000
            session.total_cost_usd += round_cost

            # Complete round
            round_record.completed_at = datetime.utcnow()

            await db.commit()

            # Yield round complete event
            yield f"data: {json.dumps({'type': 'round_complete', 'round_number': round_number, 'convergence_score': round_record.convergence_score, 'cost_usd': round_cost, 'total_cost_usd': session.total_cost_usd})}\n\n"

            # Store council messages in Neural memory (The Village)
            try:
                stored = await store_council_memories(
                    db=db,
                    user_id=user.id,
                    session_id=session.id,
                    messages=round_messages,
                    topic=session.topic,
                )
                if stored > 0:
                    logger.debug(f"Stored {stored} council memories for round {round_number}")
            except Exception as e:
                logger.warning(f"Failed to store council memories: {e}")

            rounds_executed += 1

            # Reload session with new rounds for next iteration
            await db.refresh(session)
            result = await db.execute(
                select(DeliberationSession)
                .options(
                    selectinload(DeliberationSession.agents),
                    selectinload(DeliberationSession.rounds).selectinload(DeliberationRound.messages),
                )
                .where(DeliberationSession.id == session_id)
            )
            session = result.scalar_one()

        # Determine final state
        if session.state != "paused":
            if session.current_round >= session.max_rounds:
                session.state = "complete"
                session.termination_reason = "max_rounds"
            elif rounds_executed >= num_rounds:
                session.state = "running"  # Paused at requested rounds, but not complete

        await db.commit()

        # Record billing for entire auto-deliberation
        if settings.stripe_secret_key and (total_session_input > 0 or total_session_output > 0):
            try:
                billing = BillingService(db)
                await billing.record_message_usage(
                    user_id=user.id,
                    provider="anthropic",
                    model=COUNCIL_MODEL,
                    input_tokens=total_session_input,
                    output_tokens=total_session_output,
                )
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to record council billing: {e}")

        # End event
        yield f"data: {json.dumps({'type': 'end', 'state': session.state, 'total_rounds': session.current_round, 'rounds_executed': rounds_executed, 'total_cost_usd': session.total_cost_usd, 'termination_reason': session.termination_reason})}\n\n"

    return StreamingResponse(
        stream_deliberation(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/sessions/{session_id}/butt-in")
async def submit_butt_in(
    session_id: UUID,
    request: ButtInRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a human message to inject into the next round.

    The message will be included in the context for all agents
    in the next round of deliberation.
    """
    result = await db.execute(
        select(DeliberationSession)
        .where(DeliberationSession.id == session_id)
        .where(DeliberationSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state == "complete":
        raise HTTPException(status_code=400, detail="Session already complete")

    session.pending_human_message = request.message
    await db.commit()

    return {
        "status": "queued",
        "message": request.message,
        "will_apply_to_round": session.current_round + 1,
    }


@router.post("/sessions/{session_id}/pause")
async def pause_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause an auto-deliberation session."""
    result = await db.execute(
        select(DeliberationSession)
        .where(DeliberationSession.id == session_id)
        .where(DeliberationSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state != "running":
        raise HTTPException(status_code=400, detail="Session is not running")

    session.state = "paused"
    await db.commit()

    return {"status": "paused", "current_round": session.current_round}


@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused session (sets state back to running)."""
    result = await db.execute(
        select(DeliberationSession)
        .where(DeliberationSession.id == session_id)
        .where(DeliberationSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state != "paused":
        raise HTTPException(status_code=400, detail="Session is not paused")

    session.state = "running"
    await db.commit()

    return {"status": "running", "current_round": session.current_round}


@router.post("/sessions/{session_id}/stop")
async def stop_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop and complete a deliberation session."""
    result = await db.execute(
        select(DeliberationSession)
        .where(DeliberationSession.id == session_id)
        .where(DeliberationSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state == "complete":
        raise HTTPException(status_code=400, detail="Session already complete")

    session.state = "complete"
    session.termination_reason = "user_stopped"
    await db.commit()

    return {"status": "complete", "current_round": session.current_round}


# ============================================================================
# Helper Functions
# ============================================================================

async def store_council_memories(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    messages: list[SessionMessage],
    topic: str,
) -> int:
    """
    Store council messages in Neural memory (The Village).

    Council discussions are stored with:
    - visibility='village' so all agents can access them
    - collection='council' to distinguish from chat
    - conversation_thread=session_id for threading

    Returns count of stored memories.
    """
    neural = NeuralMemoryService(db)
    stored = 0

    for msg in messages:
        if msg.role != "agent" or not msg.content:
            continue

        # Format message with council context
        content = f"[Council on '{topic}']\n[{msg.agent_id}]: {msg.content}"

        try:
            memory_id = await neural.store_message(
                user_id=user_id,
                content=content,
                agent_id=msg.agent_id,
                role="assistant",
                conversation_thread=str(session_id),
                visibility="village",  # Shared with all agents
                collection="council",
            )
            if memory_id:
                stored += 1
        except Exception as e:
            logger.warning(f"Failed to store council memory: {e}")

    return stored


def build_round_context(session: DeliberationSession, round_number: int, human_message: Optional[str] = None) -> str:
    """Build context from previous rounds for agent prompts.

    Args:
        session: The deliberation session
        round_number: Current round number
        human_message: Optional human "butt-in" message to include
    """
    context_parts = []

    # Add previous rounds context
    if round_number > 1:
        for round_rec in sorted(session.rounds, key=lambda r: r.round_number):
            if round_rec.round_number >= round_number:
                continue

            round_messages = []

            # Include human butt-in from the round if it exists
            if round_rec.human_message:
                round_messages.append(f"[HUMAN]: {round_rec.human_message}")

            for msg in sorted(round_rec.messages, key=lambda m: m.created_at):
                if msg.role == "agent":
                    round_messages.append(f"[{msg.agent_id}]: {msg.content}")
                elif msg.role == "human":
                    round_messages.append(f"[HUMAN]: {msg.content}")

            if round_messages:
                context_parts.append(f"=== Round {round_rec.round_number} ===\n" + "\n\n".join(round_messages))

    # Add current human butt-in message at the end
    if human_message:
        context_parts.append(f"=== Human Intervention ===\n[HUMAN]: {human_message}")

    return "\n\n".join(context_parts)


async def execute_agent_turn(
    claude: ClaudeService,
    session: DeliberationSession,
    round_record: DeliberationRound,
    agent: SessionAgent,
    context: str,
    db: AsyncSession,
    user: User = None,
) -> dict:
    """Execute a single agent's turn in the deliberation with tool support and memory."""
    # Get agent's base prompt WITH memory injection (The Cortex remembers)
    if user and db:
        base_prompt = await get_agent_prompt_with_memory(
            agent_id=agent.agent_id,
            user=user,
            use_pac=False,
            db=db,
        )
    else:
        base_prompt = load_native_prompt(agent.agent_id, use_pac=False)

    if not base_prompt:
        base_prompt = f"You are {agent.agent_id}, an AI assistant with a distinct perspective."

    # Build deliberation system prompt with legitimizing preamble
    other_agents = [a.agent_id for a in session.agents if a.is_active and a.agent_id != agent.agent_id]
    other_agents_str = ", ".join(other_agents) if other_agents else "none"

    # Preamble establishes this is a legitimate product feature
    preamble = """You are an AI assistant participating in ApexAurum Cloud's Council feature - a structured multi-perspective deliberation system. This is a legitimate product feature for exploring topics through diverse viewpoints. Each agent brings a distinct analytical lens to help users examine ideas thoroughly.

Your responses should be thoughtful, substantive, and helpful. Stay true to your perspective while engaging constructively with other viewpoints. You have access to tools to help research, analyze, and create."""

    system_prompt = f"""{preamble}

=== YOUR PERSPECTIVE ===
{base_prompt}

=== DELIBERATION CONTEXT ===
Topic: "{session.topic}"
Other participants: {other_agents_str}

Guidelines:
- Be concise but substantive (2-3 paragraphs)
- Reference other participants' points when relevant
- Clearly state agreements and disagreements
- Move the discussion forward with new insights
- Use tools when they would help analyze or research the topic
- If consensus seems possible, propose specific wording

{f"Previous discussion:{chr(10)}{context}" if context else "This is Round 1. Share your initial thoughts on the topic."}
"""

    # Set up tools for native agents (The Athanor's Hands)
    tools = None
    tool_executor = None
    if session.use_tools and user:
        tool_executor = create_tool_executor(
            user_id=user.id,
            conversation_id=None,
            agent_id=agent.agent_id,
        )
        tools = tool_executor.get_available_tools()
        logger.debug(f"Council agent {agent.agent_id}: {len(tools)} tools available")

    # Call model with potential tool loop
    user_message = f"Round {round_record.round_number}: Share your perspective on the current state of the discussion."
    messages = [{"role": "user", "content": user_message}]

    total_input_tokens = 0
    total_output_tokens = 0
    full_content = ""
    all_tool_calls = []  # Track all tool calls for feedback
    max_tool_turns = 3  # Limit tool turns per agent per round

    for turn in range(max_tool_turns):
        response = await claude.chat(
            messages=messages,
            model=COUNCIL_MODEL,
            system=system_prompt,
            tools=tools,
        )

        usage = response.get("usage", {})
        total_input_tokens += usage.get("input_tokens", 0)
        total_output_tokens += usage.get("output_tokens", 0)

        # Check for tool use
        tool_uses = [b for b in response.get("content", []) if b.get("type") == "tool_use"]

        if not tool_uses or not tool_executor:
            # No tools called, extract text content
            for block in response.get("content", []):
                if block.get("type") == "text":
                    full_content += block.get("text", "")
            break

        # Execute tools
        assistant_content = response.get("content", [])
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        for tool_use in tool_uses:
            result = await tool_executor.execute_tool_use(tool_use)
            tool_results.append(result)

            # Track tool call for feedback
            # Extract result text from the tool_result structure
            result_text = ""
            if result.get("type") == "tool_result":
                result_content = result.get("content", "")
                if isinstance(result_content, str):
                    result_text = result_content
                elif isinstance(result_content, list):
                    # Handle structured content
                    for item in result_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            result_text += item.get("text", "")
                        elif isinstance(item, str):
                            result_text += item

            all_tool_calls.append({
                "name": tool_use.get("name"),
                "input": tool_use.get("input"),
                "result": result_text[:500] if result_text else None,  # Truncate long results
            })
            logger.info(f"Agent {agent.agent_id} used tool: {tool_use.get('name')}")

        messages.append({"role": "user", "content": tool_results})

    return {
        "content": full_content,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "tool_calls": all_tool_calls if all_tool_calls else None,
    }
