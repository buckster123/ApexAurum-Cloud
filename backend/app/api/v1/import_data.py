"""
Import Endpoints

Import data from local ApexAurum app (conversations, memory).
"""

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.auth.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


@router.post("/conversations", response_model=ImportResult)
async def import_conversations(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import conversations from local ApexAurum app.

    Accepts the sandbox/conversations.json format:
    {
      "conv_id": {
        "title": "...",
        "created_at": "ISO_8601",
        "messages": [{"role": "user|assistant", "content": "...", "timestamp": "..."}]
      }
    }

    Or the export format (array of conversations):
    [
      {"title": "...", "created_at": "...", "messages": [...]}
    ]
    """
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}"
        )

    imported = 0
    skipped = 0
    errors = []

    # Handle both dict format (local app) and array format (export)
    if isinstance(data, dict):
        conversations = list(data.values())
    elif isinstance(data, list):
        conversations = data
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Expected object or array of conversations."
        )

    for i, conv_data in enumerate(conversations):
        try:
            # Parse timestamps
            created_at = conv_data.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_at = datetime.utcnow()

            # Create conversation
            conv = Conversation(
                id=uuid4(),
                user_id=user.id,
                title=conv_data.get('title', f'Imported Conversation {i+1}')[:200],
                created_at=created_at,
                favorite=conv_data.get('favorite', False),
                tags=conv_data.get('tags', []),
            )
            db.add(conv)
            await db.flush()

            # Import messages
            messages = conv_data.get('messages', [])
            for msg_data in messages:
                content = msg_data.get('content', '')

                # Handle local app structured content (array of text blocks)
                if isinstance(content, list):
                    content = ' '.join(
                        c.get('text', '') for c in content
                        if isinstance(c, dict) and c.get('type') == 'text'
                    )

                if not content:
                    continue

                # Parse message timestamp
                msg_time = msg_data.get('timestamp') or msg_data.get('created_at')
                if msg_time and isinstance(msg_time, str):
                    try:
                        msg_time = datetime.fromisoformat(msg_time.replace('Z', '+00:00'))
                    except:
                        msg_time = datetime.utcnow()
                else:
                    msg_time = datetime.utcnow()

                message = Message(
                    id=uuid4(),
                    conversation_id=conv.id,
                    role=msg_data.get('role', 'user'),
                    content=content,
                    created_at=msg_time,
                )
                db.add(message)

            imported += 1

        except Exception as e:
            logger.warning(f"Failed to import conversation {i}: {e}")
            errors.append(f"Conversation {i}: {str(e)}")
            skipped += 1

    await db.commit()

    return ImportResult(imported=imported, skipped=skipped, errors=errors[:10])


@router.post("/memory", response_model=ImportResult)
async def import_memory(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import memory from local ApexAurum app.

    Accepts the sandbox/memory.json format:
    {
      "key": {
        "value": any,
        "stored_at": "ISO_8601",
        "metadata": {}
      }
    }

    Memory is stored in the user's settings JSON field.
    """
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}"
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Expected object with key-value entries."
        )

    # Initialize user settings if needed
    if not user.settings:
        user.settings = {}

    if 'imported_memory' not in user.settings:
        user.settings['imported_memory'] = {}

    imported = 0
    skipped = 0
    errors = []

    for key, entry in data.items():
        try:
            # Store in user settings
            user.settings['imported_memory'][key] = {
                'value': entry.get('value'),
                'stored_at': entry.get('stored_at', datetime.utcnow().isoformat()),
                'metadata': entry.get('metadata', {}),
                'imported_at': datetime.utcnow().isoformat(),
            }
            imported += 1
        except Exception as e:
            logger.warning(f"Failed to import memory key {key}: {e}")
            errors.append(f"Key {key}: {str(e)}")
            skipped += 1

    # Mark settings as modified for SQLAlchemy
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(user, 'settings')

    await db.commit()

    return ImportResult(imported=imported, skipped=skipped, errors=errors[:10])


@router.get("/memory")
async def get_imported_memory(
    user: User = Depends(get_current_user),
):
    """Get user's imported memory."""
    if not user.settings:
        return {"memory": {}}

    return {"memory": user.settings.get('imported_memory', {})}
