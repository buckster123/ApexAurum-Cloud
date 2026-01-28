"""
Jam Session API - The Athanor's Band Studio

Multi-agent collaborative music composition endpoints.

Endpoints:
- POST /jam/sessions - Create a jam session
- GET /jam/sessions - List user's jam sessions
- GET /jam/sessions/{id} - Get session details with tracks
- POST /jam/sessions/{id}/contribute - Add notes to a track
- POST /jam/sessions/{id}/finalize - Merge tracks and send to Suno
- DELETE /jam/sessions/{id} - Delete a session
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.jam import (
    JamSession, JamParticipant, JamTrack, JamMessage,
    JamMode, JamState, JamRole, DEFAULT_AGENT_ROLES
)
from app.auth.deps import get_current_user
from app.services.midi import MidiService
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/jam", tags=["Jam Sessions"])


# ============================================================================
# Schemas
# ============================================================================

class CreateJamRequest(BaseModel):
    """Request to create a new jam session."""
    title: Optional[str] = "Untitled Jam"
    style: Optional[str] = None  # Target style for Suno
    tempo: int = 120  # BPM
    musical_key: str = "C"  # Musical key
    mode: str = "jam"  # conductor, jam, auto
    agents: List[str] = ["AZOTH", "ELYSIAN", "VAJRA", "KETHER"]
    max_rounds: int = 5
    inspiration: Optional[str] = None  # Initial prompt/seed


class ContributeRequest(BaseModel):
    """Request to contribute notes to a track."""
    agent_id: str
    notes: List[dict]  # [{note: 'C4', time: 0, duration: 0.5, velocity: 100}, ...]
    description: Optional[str] = None  # Agent's description of contribution
    role: Optional[str] = None  # Override role for this contribution


class FinalizeRequest(BaseModel):
    """Request to finalize and generate music."""
    audio_influence: float = 0.5  # How much MIDI affects Suno output
    style_override: Optional[str] = None  # Override session style
    title_override: Optional[str] = None  # Override session title


class NoteInfo(BaseModel):
    """A single note in a track."""
    note: str  # 'C4', 'F#3', etc.
    time: float  # Start time in beats
    duration: float  # Duration in beats
    velocity: int = 100  # 0-127


class TrackResponse(BaseModel):
    """Response for a single track."""
    id: UUID
    agent_id: str
    role: str
    round_number: int
    notes: List[dict]
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ParticipantResponse(BaseModel):
    """Response for a participant."""
    id: UUID
    agent_id: str
    role: str
    display_name: Optional[str]
    contributions: int
    total_notes: int
    is_active: bool

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Response for a jam message."""
    id: UUID
    agent_id: str
    content: str
    round_number: int
    track_id: Optional[UUID]
    created_at: str

    class Config:
        from_attributes = True


class JamSessionResponse(BaseModel):
    """Response for a jam session."""
    id: UUID
    title: str
    style: Optional[str]
    tempo: int
    musical_key: str
    mode: str
    state: str
    current_round: int
    max_rounds: int
    inspiration: Optional[str]
    audio_influence: float
    final_music_task_id: Optional[UUID]
    participants: List[ParticipantResponse]
    tracks: List[TrackResponse]
    messages: List[MessageResponse]
    created_at: str
    completed_at: Optional[str]

    class Config:
        from_attributes = True


class JamSessionListItem(BaseModel):
    """Abbreviated session info for list view."""
    id: UUID
    title: str
    style: Optional[str]
    state: str
    mode: str
    current_round: int
    participant_count: int
    track_count: int
    created_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Helper Functions
# ============================================================================

def assign_roles(agents: List[str]) -> dict:
    """Assign musical roles to agents based on defaults."""
    roles = {}
    for agent in agents:
        roles[agent] = DEFAULT_AGENT_ROLES.get(agent, JamRole.FREE).value
    return roles


def session_to_response(session: JamSession) -> JamSessionResponse:
    """Convert session model to response."""
    return JamSessionResponse(
        id=session.id,
        title=session.title,
        style=session.style,
        tempo=session.tempo,
        musical_key=session.musical_key,
        mode=session.mode,
        state=session.state,
        current_round=session.current_round,
        max_rounds=session.max_rounds,
        inspiration=session.inspiration,
        audio_influence=session.audio_influence,
        final_music_task_id=session.final_music_task_id,
        participants=[
            ParticipantResponse(
                id=p.id,
                agent_id=p.agent_id,
                role=p.role,
                display_name=p.display_name,
                contributions=p.contributions,
                total_notes=p.total_notes,
                is_active=p.is_active,
            )
            for p in session.participants
        ],
        tracks=[
            TrackResponse(
                id=t.id,
                agent_id=t.agent_id,
                role=t.role,
                round_number=t.round_number,
                notes=t.notes or [],
                description=t.description,
                created_at=t.created_at.isoformat(),
            )
            for t in sorted(session.tracks, key=lambda x: (x.round_number, x.created_at))
        ],
        messages=[
            MessageResponse(
                id=m.id,
                agent_id=m.agent_id,
                content=m.content,
                round_number=m.round_number,
                track_id=m.track_id,
                created_at=m.created_at.isoformat(),
            )
            for m in sorted(session.messages, key=lambda x: x.created_at)
        ],
        created_at=session.created_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/sessions", response_model=JamSessionResponse)
async def create_session(
    request: CreateJamRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new jam session.

    Modes:
    - conductor: User directs each agent
    - jam: Style-guided auto-collaboration
    - auto: Full creative freedom
    """
    # Validate mode
    try:
        mode = JamMode(request.mode)
    except ValueError:
        mode = JamMode.JAM

    # Create session
    session = JamSession(
        id=uuid4(),
        user_id=user.id,
        title=request.title or "Untitled Jam",
        style=request.style,
        tempo=request.tempo,
        musical_key=request.musical_key,
        mode=mode.value,
        state=JamState.FORMING.value,
        max_rounds=request.max_rounds,
        inspiration=request.inspiration,
    )
    db.add(session)
    await db.flush()

    # Assign roles and create participants
    roles = assign_roles(request.agents)
    for agent_id in request.agents:
        participant = JamParticipant(
            id=uuid4(),
            session_id=session.id,
            agent_id=agent_id,
            role=roles[agent_id],
            display_name=agent_id,
        )
        db.add(participant)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(JamSession)
        .where(JamSession.id == session.id)
        .options(
            selectinload(JamSession.participants),
            selectinload(JamSession.tracks),
            selectinload(JamSession.messages),
        )
    )
    session = result.scalar_one()

    logger.info(f"Created jam session {session.id} with {len(request.agents)} participants")

    return session_to_response(session)


@router.get("/sessions", response_model=List[JamSessionListItem])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    state: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's jam sessions."""
    query = (
        select(JamSession)
        .where(JamSession.user_id == user.id)
        .options(
            selectinload(JamSession.participants),
            selectinload(JamSession.tracks),
        )
        .order_by(JamSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if state:
        query = query.where(JamSession.state == state)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [
        JamSessionListItem(
            id=s.id,
            title=s.title,
            style=s.style,
            state=s.state,
            mode=s.mode,
            current_round=s.current_round,
            participant_count=len(s.participants),
            track_count=len(s.tracks),
            created_at=s.created_at.isoformat(),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=JamSessionResponse)
async def get_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get jam session details with all tracks and messages."""
    result = await db.execute(
        select(JamSession)
        .where(JamSession.id == session_id)
        .where(JamSession.user_id == user.id)
        .options(
            selectinload(JamSession.participants),
            selectinload(JamSession.tracks),
            selectinload(JamSession.messages),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jam session not found"
        )

    return session_to_response(session)


@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a jam session (transition from forming to jamming)."""
    result = await db.execute(
        select(JamSession)
        .where(JamSession.id == session_id)
        .where(JamSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state != JamState.FORMING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start session in state: {session.state}"
        )

    session.state = JamState.JAMMING.value
    session.started_at = datetime.utcnow()
    session.current_round = 1
    await db.commit()

    return {"message": "Jam session started", "state": session.state, "round": 1}


@router.post("/sessions/{session_id}/contribute")
async def contribute_to_session(
    session_id: UUID,
    request: ContributeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Contribute notes to a jam session.

    Notes format:
    [
        {"note": "C4", "time": 0.0, "duration": 0.5, "velocity": 100},
        {"note": "E4", "time": 0.5, "duration": 0.5, "velocity": 100},
        ...
    ]
    """
    result = await db.execute(
        select(JamSession)
        .where(JamSession.id == session_id)
        .where(JamSession.user_id == user.id)
        .options(selectinload(JamSession.participants))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state not in (JamState.JAMMING.value, JamState.FORMING.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot contribute in state: {session.state}"
        )

    # Auto-start if in forming state
    if session.state == JamState.FORMING.value:
        session.state = JamState.JAMMING.value
        session.started_at = datetime.utcnow()
        session.current_round = 1

    # Find participant
    participant = next(
        (p for p in session.participants if p.agent_id == request.agent_id),
        None
    )
    if not participant:
        raise HTTPException(
            status_code=400,
            detail=f"Agent {request.agent_id} is not a participant"
        )

    # Determine role
    role = request.role or participant.role

    # Create track
    track = JamTrack(
        id=uuid4(),
        session_id=session.id,
        agent_id=request.agent_id,
        role=role,
        round_number=session.current_round,
        notes=request.notes,
        description=request.description,
    )
    db.add(track)

    # Update participant stats
    participant.contributions += 1
    participant.total_notes += len(request.notes)
    participant.last_contribution_at = datetime.utcnow()

    await db.commit()

    logger.info(
        f"Agent {request.agent_id} contributed {len(request.notes)} notes "
        f"to session {session_id} (round {session.current_round})"
    )

    return {
        "success": True,
        "track_id": str(track.id),
        "agent_id": request.agent_id,
        "role": role,
        "note_count": len(request.notes),
        "round": session.current_round,
    }


@router.post("/sessions/{session_id}/next-round")
async def advance_round(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Advance to the next round of the jam session."""
    result = await db.execute(
        select(JamSession)
        .where(JamSession.id == session_id)
        .where(JamSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state != JamState.JAMMING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot advance round in state: {session.state}"
        )

    if session.current_round >= session.max_rounds:
        raise HTTPException(
            status_code=400,
            detail=f"Max rounds ({session.max_rounds}) reached"
        )

    session.current_round += 1
    await db.commit()

    return {
        "message": f"Advanced to round {session.current_round}",
        "round": session.current_round,
        "max_rounds": session.max_rounds,
    }


@router.post("/sessions/{session_id}/finalize")
async def finalize_session(
    session_id: UUID,
    request: FinalizeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Finalize the jam session: merge all tracks into MIDI and send to Suno.

    Returns the music task ID for tracking the generation.
    """
    result = await db.execute(
        select(JamSession)
        .where(JamSession.id == session_id)
        .where(JamSession.user_id == user.id)
        .options(
            selectinload(JamSession.tracks),
            selectinload(JamSession.participants),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.state not in (JamState.JAMMING.value, JamState.FORMING.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot finalize in state: {session.state}"
        )

    if not session.tracks:
        raise HTTPException(
            status_code=400,
            detail="No tracks to finalize. Agents need to contribute first."
        )

    # Update state
    session.state = JamState.FINALIZING.value
    session.audio_influence = request.audio_influence
    await db.commit()

    try:
        # Merge all tracks into a single note list
        all_notes = []
        time_offset = 0.0

        # Group tracks by round, then by role priority
        role_priority = {
            JamRole.BASS.value: 0,
            JamRole.RHYTHM.value: 1,
            JamRole.HARMONY.value: 2,
            JamRole.MELODY.value: 3,
            JamRole.PRODUCER.value: 4,
            JamRole.FREE.value: 5,
        }

        sorted_tracks = sorted(
            session.tracks,
            key=lambda t: (t.round_number, role_priority.get(t.role, 5))
        )

        for track in sorted_tracks:
            if track.notes:
                for note in track.notes:
                    # Adjust time based on track position
                    adjusted_note = note.copy()
                    # Notes within a track are relative; we stack rounds sequentially
                    all_notes.append(adjusted_note)

        if not all_notes:
            raise HTTPException(status_code=400, detail="No notes in tracks")

        # Extract just the note names for midi_create
        note_names = [n.get("note", "C4") for n in all_notes]

        # Calculate average tempo/duration from notes
        avg_duration = sum(n.get("duration", 0.5) for n in all_notes) / len(all_notes)

        # Create MIDI
        midi_service = MidiService()
        midi_result = await midi_service.create_midi(
            notes=note_names,
            tempo=session.tempo,
            note_duration=avg_duration,
            title=request.title_override or session.title,
            user_id=str(user.id),
        )

        if not midi_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"MIDI creation failed: {midi_result.get('error')}"
            )

        session.final_midi_path = midi_result["midi_file"]
        await db.commit()

        # Now compose via Suno
        style = request.style_override or session.style or "collaborative jam session"
        title = request.title_override or session.title

        # Check if MIDI pipeline is ready
        deps = midi_service.check_dependencies()
        if not deps["ready"]:
            # Return MIDI path but skip Suno composition
            session.state = JamState.COMPLETE.value
            session.completed_at = datetime.utcnow()
            await db.commit()

            return {
                "success": True,
                "message": "MIDI created (Suno composition skipped - dependencies missing)",
                "midi_file": midi_result["midi_file"],
                "note_count": len(all_notes),
                "dependencies_missing": [k for k, v in deps.items() if not v and k != "ready"],
            }

        # Full pipeline: MIDI → Suno
        from app.models.music import MusicTask

        # Convert MIDI to audio
        audio_result = await midi_service.midi_to_audio(midi_result["midi_file"])
        if not audio_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Audio conversion failed: {audio_result.get('error')}"
            )

        # Upload to Suno
        upload_result = await midi_service.upload_to_suno(audio_result["audio_path"])
        if not upload_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Upload failed: {upload_result.get('error')}"
            )

        # Call upload-cover
        cover_result = await midi_service.call_upload_cover(
            upload_url=upload_result["upload_url"],
            style=style,
            title=title,
            audio_weight=request.audio_influence,
            instrumental=True,
        )

        if not cover_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Suno cover failed: {cover_result.get('error')}"
            )

        # Create music task record
        music_task = MusicTask(
            id=uuid4(),
            user_id=user.id,
            prompt=f"[JAM SESSION] {session.title} - Collaborative composition by {', '.join(p.agent_id for p in session.participants)}",
            style=style,
            title=title,
            model="V5",
            instrumental=True,
            status="generating",
            progress="Village Band composition in progress...",
            suno_task_id=cover_result["suno_task_id"],
            agent_id="VILLAGE_BAND",
        )
        db.add(music_task)

        session.final_music_task_id = music_task.id
        session.state = JamState.COMPLETE.value
        session.completed_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Jam session {session_id} finalized -> music task {music_task.id}")

        return {
            "success": True,
            "message": "Jam session finalized! Music generation started.",
            "music_task_id": str(music_task.id),
            "midi_file": midi_result["midi_file"],
            "note_count": len(all_notes),
            "audio_influence": request.audio_influence,
            "style": style,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Finalize failed for session {session_id}")
        session.state = JamState.FAILED.value
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a jam session."""
    result = await db.execute(
        select(JamSession)
        .where(JamSession.id == session_id)
        .where(JamSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    return {"message": "Session deleted", "id": str(session_id)}


@router.get("/diagnostic")
async def jam_diagnostic():
    """Check jam session dependencies."""
    midi_service = MidiService()
    deps = midi_service.check_dependencies()

    return {
        "service": "jam",
        "midi_pipeline": deps,
        "message": "Village Band ready!" if deps["ready"] else "Some dependencies missing",
    }
