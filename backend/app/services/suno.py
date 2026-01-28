"""
Suno AI Music Generation Service

The Athanor's creative voice - transforms intent into vibrating eardrums.

API: https://api.sunoapi.org/api/v1
"""

import logging
import asyncio
import aiohttp
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.music import MusicTask

logger = logging.getLogger(__name__)
settings = get_settings()

# Suno API configuration
SUNO_API_BASE = "https://api.sunoapi.org/api/v1"

# Model character limits
MODEL_LIMITS = {
    "V3_5": {"prompt": 3000, "style": 200, "title": 80},
    "V4": {"prompt": 3000, "style": 200, "title": 80},
    "V4_5": {"prompt": 5000, "style": 1000, "title": 100},
    "V5": {"prompt": 5000, "style": 1000, "title": 100},
}


class SunoService:
    """
    Suno AI music generation service.

    Handles the full pipeline:
    1. Submit generation request
    2. Poll for completion
    3. Download audio to Vault
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = getattr(settings, 'suno_api_key', None)

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers."""
        if not self.api_key:
            raise ValueError("SUNO_API_KEY not configured")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def generate(
        self,
        task: MusicTask,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate music via Suno API.

        Args:
            task: MusicTask with prompt, style, model, etc.
            progress_callback: Optional async callback(status, progress_msg)

        Returns:
            Dict with success status and audio info or error.
        """
        try:
            # Update task status
            task.status = "generating"
            task.started_at = datetime.utcnow()
            task.progress = "Submitting to Suno API..."
            await self.db.commit()

            if progress_callback:
                await progress_callback("generating", task.progress)

            # Submit to Suno
            suno_task_id = await self._submit_generation(task)
            task.suno_task_id = suno_task_id
            task.progress = "Queued at Suno..."
            await self.db.commit()

            if progress_callback:
                await progress_callback("generating", task.progress)

            # Poll for completion
            result = await self._poll_completion(task, progress_callback)

            if not result.get("success"):
                raise Exception(result.get("error", "Generation failed"))

            # Download audio
            task.status = "downloading"
            task.progress = "Downloading audio..."
            await self.db.commit()

            if progress_callback:
                await progress_callback("downloading", task.progress)

            track_info = result["tracks"][0]  # Use first track
            file_path = await self._download_audio(task, track_info)

            # Update task with results
            task.status = "completed"
            task.file_path = file_path
            task.audio_url = track_info.get("audio_url")
            task.duration = track_info.get("duration", 0.0)
            task.clip_id = track_info.get("clip_id")
            task.title = track_info.get("title") or task.title or f"Track_{str(task.id)[:8]}"
            task.progress = "Complete"
            task.completed_at = datetime.utcnow()
            await self.db.commit()

            if progress_callback:
                await progress_callback("completed", f"Generated: {task.title}")

            logger.info(f"Music task {task.id} completed: {task.title}")

            # ═══════════════════════════════════════════════════════════════════
            # VILLAGE MEMORY INJECTION - Songs become cultural memories
            # ═══════════════════════════════════════════════════════════════════
            try:
                await self._inject_village_memory(task)
            except Exception as mem_error:
                logger.warning(f"Village memory injection failed (non-fatal): {mem_error}")

            return {
                "success": True,
                "file_path": file_path,
                "audio_url": task.audio_url,
                "duration": task.duration,
                "title": task.title,
            }

        except Exception as e:
            logger.error(f"Music generation failed: {e}")
            task.status = "failed"
            task.error = str(e)
            task.progress = f"Failed: {str(e)[:100]}"
            task.completed_at = datetime.utcnow()
            await self.db.commit()

            if progress_callback:
                await progress_callback("failed", task.error)

            return {"success": False, "error": str(e)}

    async def _submit_generation(self, task: MusicTask) -> str:
        """Submit generation request to Suno API."""
        headers = self._get_headers()

        payload = {
            "model": task.model,
            "instrumental": task.instrumental,
            "customMode": True,
            "prompt": task.prompt,
            "callBackUrl": "https://localhost/callback",  # Required but we poll
        }

        if task.title:
            payload["title"] = task.title[:100]
        if task.style:
            payload["style"] = task.style[:1000]

        logger.info(f"Submitting to Suno: model={task.model}, instrumental={task.instrumental}")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SUNO_API_BASE}/generate",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Suno API error: HTTP {response.status}: {text[:200]}")

                result = await response.json()

                if result.get("code") != 200:
                    raise Exception(f"Suno API error: {result.get('msg', 'Unknown error')}")

                suno_task_id = result.get("data", {}).get("taskId")
                if not suno_task_id:
                    raise Exception("No taskId in Suno response")

                logger.info(f"Suno task submitted: {suno_task_id}")
                return suno_task_id

    async def _poll_completion(
        self,
        task: MusicTask,
        progress_callback: Optional[callable] = None,
        max_wait: int = 600,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """Poll Suno API for completion."""
        headers = self._get_headers()
        start_time = asyncio.get_event_loop().time()

        async with aiohttp.ClientSession() as session:
            while asyncio.get_event_loop().time() - start_time < max_wait:
                try:
                    async with session.get(
                        f"{SUNO_API_BASE}/generate/record-info",
                        headers=headers,
                        params={"taskId": task.suno_task_id},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"Status check HTTP {response.status}")
                            await asyncio.sleep(poll_interval)
                            continue

                        result = await response.json()

                        if result.get("code") != 200:
                            logger.warning(f"Status API error: {result.get('msg')}")
                            await asyncio.sleep(poll_interval)
                            continue

                        data = result.get("data", {})
                        status = data.get("status", "UNKNOWN")

                        if status == "PENDING":
                            task.progress = "In queue..."
                            await self.db.commit()
                            if progress_callback:
                                await progress_callback("generating", task.progress)

                        elif status == "GENERATING":
                            task.progress = "Generating audio..."
                            await self.db.commit()
                            if progress_callback:
                                await progress_callback("generating", task.progress)

                        elif status == "SUCCESS":
                            suno_data = data.get("response", {}).get("sunoData", [])
                            if suno_data:
                                tracks = []
                                for track in suno_data:
                                    tracks.append({
                                        "audio_url": track.get("audioUrl"),
                                        "title": track.get("title"),
                                        "duration": track.get("duration", 0),
                                        "clip_id": track.get("id")
                                    })
                                return {
                                    "success": True,
                                    "tracks": tracks,
                                    "track_count": len(tracks)
                                }
                            else:
                                return {"success": False, "error": "No audio data in response"}

                        elif status == "ERROR":
                            return {
                                "success": False,
                                "error": data.get("error", "Generation failed")
                            }

                        await asyncio.sleep(poll_interval)

                except asyncio.TimeoutError:
                    logger.warning("Poll timeout, retrying...")
                    await asyncio.sleep(poll_interval)
                except Exception as e:
                    logger.warning(f"Poll error: {e}")
                    await asyncio.sleep(poll_interval)

        return {"success": False, "error": f"Timeout after {max_wait}s"}

    async def _download_audio(self, task: MusicTask, track_info: Dict[str, Any]) -> str:
        """Download audio file to Vault."""
        audio_url = track_info.get("audio_url")
        if not audio_url:
            raise Exception("No audio URL to download")

        # Sanitize filename
        title = track_info.get("title", task.title) or f"track_{str(task.id)[:8]}"
        safe_title = re.sub(r'[^a-zA-Z0-9\s\-_]', '', title)[:60].strip() or "untitled"
        clip_id = (track_info.get("clip_id") or str(task.id))[-8:]
        filename = f"{safe_title}_{clip_id}.mp3"

        # Use Vault path for user
        vault_path = Path(settings.vault_path) / "users" / str(task.user_id) / "music"
        vault_path.mkdir(parents=True, exist_ok=True)
        filepath = vault_path / filename

        logger.info(f"Downloading audio to: {filepath}")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                audio_url,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                response.raise_for_status()

                with open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        file_size = filepath.stat().st_size
        logger.info(f"Downloaded: {filepath} ({file_size} bytes)")

        return str(filepath)

    async def _inject_village_memory(self, task: MusicTask) -> None:
        """
        Inject completed music into Village memory.

        Creates a cultural memory that all agents can access.
        """
        from app.services.neural_memory import NeuralMemoryService

        memory_service = NeuralMemoryService(self.db)

        # Build content for the memory
        duration_str = f"{task.duration:.1f}s" if task.duration else "unknown"
        creator = task.agent_id or "User"
        prompt_preview = (task.prompt[:200] + "...") if len(task.prompt) > 200 else task.prompt

        content = f"""🎵 MUSIC CREATED: "{task.title}"
Style: {task.style or 'None specified'}
Duration: {duration_str}
Creator: {creator}
Model: {task.model}
Prompt: {prompt_preview}"""

        # Store as village-visible cultural memory
        memory_id = await memory_service.store_message(
            user_id=task.user_id,
            content=content,
            agent_id=task.agent_id or "AZOTH",
            role="assistant",  # Treat as agent observation
            visibility="village",  # Shared with all agents
            collection="music",  # Music-specific collection
        )

        if memory_id:
            logger.info(f"Injected music memory to Village: {memory_id}")
        else:
            logger.warning("Village memory injection returned None")

    async def get_task(self, task_id: UUID, user_id: UUID) -> Optional[MusicTask]:
        """Get a task by ID for user."""
        result = await self.db.execute(
            select(MusicTask)
            .where(MusicTask.id == task_id)
            .where(MusicTask.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def generate_music_stream(
    db: AsyncSession,
    task: MusicTask
) -> AsyncGenerator[str, None]:
    """
    Generate music with SSE progress streaming.

    Yields SSE events:
    - {"type": "status", "status": "...", "progress": "..."}
    - {"type": "completed", "file_path": "...", "duration": ...}
    - {"type": "error", "error": "..."}
    """
    import json

    async def progress_callback(status: str, message: str):
        event = {"type": "status", "status": status, "progress": message}
        yield f"data: {json.dumps(event)}\n\n"

    service = SunoService(db)

    # We can't use the callback directly in an async generator
    # So we'll poll the task status ourselves

    # Start generation in background
    generation_task = asyncio.create_task(service.generate(task))

    last_progress = None
    while not generation_task.done():
        # Refresh task from DB
        await db.refresh(task)

        if task.progress != last_progress:
            last_progress = task.progress
            event = {
                "type": "status",
                "status": task.status,
                "progress": task.progress or ""
            }
            yield f"data: {json.dumps(event)}\n\n"

        await asyncio.sleep(1)

    # Get final result
    result = await generation_task

    if result.get("success"):
        event = {
            "type": "completed",
            "file_path": result["file_path"],
            "audio_url": result.get("audio_url"),
            "duration": result.get("duration"),
            "title": result.get("title"),
        }
    else:
        event = {
            "type": "error",
            "error": result.get("error", "Unknown error")
        }

    yield f"data: {json.dumps(event)}\n\n"
