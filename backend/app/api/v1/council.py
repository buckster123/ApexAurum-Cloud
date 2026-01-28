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
from app.config import get_settings
from app.api.v1.chat import load_native_prompt  # Reuse prompt loading

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
    "CLAUDE": "#4fc3f7",
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
    use_tools: bool = False


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


class MessageResponse(BaseModel):
    id: UUID
    role: str
    agent_id: Optional[str]
    content: str
    input_tokens: int
    output_tokens: int
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
        # Validate agents
        valid_agents = ["AZOTH", "ELYSIAN", "VAJRA", "KETHER", "CLAUDE"]
        for agent_id in request.agents:
            if agent_id not in valid_agents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent: {agent_id}. Valid agents: {valid_agents}"
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

        # Add agents
        for agent_id in request.agents:
            agent = SessionAgent(
                session_id=session.id,
                agent_id=agent_id,
                display_name=agent_id,  # Could enhance with custom names
                is_active=True,
            )
            db.add(agent)
            session.agents.append(agent)

        await db.commit()
        await db.refresh(session)

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
                claude, session, round_record, agent, context, db
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
        else:
            content = result["content"]
            input_tokens = result["input_tokens"]
            output_tokens = result["output_tokens"]

        # Create message record
        msg = SessionMessage(
            session_id=session.id,
            round_id=round_record.id,
            role="agent",
            agent_id=agent.agent_id,
            content=content,
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
                        claude, session, round_record, agent, context, db
                    )
                )

            agent_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            total_round_input = 0
            total_round_output = 0

            for i, result in enumerate(agent_results):
                agent = active_agents[i]
                if isinstance(result, Exception):
                    logger.error(f"Agent {agent.agent_id} failed: {result}")
                    content = f"[Error: {str(result)}]"
                    input_tokens = 0
                    output_tokens = 0
                else:
                    content = result["content"]
                    input_tokens = result["input_tokens"]
                    output_tokens = result["output_tokens"]

                # Create message record
                msg = SessionMessage(
                    session_id=session.id,
                    round_id=round_record.id,
                    role="agent",
                    agent_id=agent.agent_id,
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                db.add(msg)

                # Update agent token counts
                agent.input_tokens += input_tokens
                agent.output_tokens += output_tokens
                total_round_input += input_tokens
                total_round_output += output_tokens

                # Yield agent complete event
                yield f"data: {json.dumps({'type': 'agent_complete', 'agent_id': agent.agent_id, 'content': content, 'input_tokens': input_tokens, 'output_tokens': output_tokens})}\n\n"

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
) -> dict:
    """Execute a single agent's turn in the deliberation."""
    # Get agent's base prompt
    base_prompt = load_native_prompt(agent.agent_id, use_pac=False)

    # Build deliberation system prompt
    other_agents = [a.agent_id for a in session.agents if a.is_active and a.agent_id != agent.agent_id]
    other_agents_str = ", ".join(other_agents) if other_agents else "none"

    system_prompt = f"""{base_prompt}

=== DELIBERATION MODE ===
You are participating in a group deliberation on this topic:
"{session.topic}"

Other agents in this discussion: {other_agents_str}

Guidelines:
- Be concise but substantive (2-3 paragraphs)
- Reference other agents' points by name when relevant
- Clearly state agreements and disagreements
- Move the discussion forward with new insights
- If consensus seems possible, propose specific wording

{f"Previous discussion:{chr(10)}{context}" if context else "This is Round 1. Share your initial thoughts on the topic."}
"""

    # Call Claude
    user_message = f"Round {round_record.round_number}: Share your perspective on the current state of the discussion."

    response = await claude.chat(
        messages=[{"role": "user", "content": user_message}],
        model=COUNCIL_MODEL,
        system=system_prompt,
    )

    # Extract content
    content = ""
    for block in response.get("content", []):
        if block.get("text"):
            content += block["text"]

    usage = response.get("usage", {})

    return {
        "content": content,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }
