"""
The Vault - File Storage API

User file management with hierarchical folders, quota enforcement,
and secure file upload/download.

"Every alchemist needs a sanctum"
"""

import hashlib
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.file import (
    File, Folder,
    ALLOWED_EXTENSIONS, BLOCKED_EXTENSIONS,
    get_file_type, is_allowed_extension,
)
from app.auth.deps import get_current_user
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[UUID] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[UUID] = None  # For moving folders
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_archived: Optional[bool] = None


class FolderResponse(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID]
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    is_archived: bool
    file_count: int
    folder_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class FileUpdate(BaseModel):
    name: Optional[str] = None
    folder_id: Optional[UUID] = None  # For moving files
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class FileResponse(BaseModel):
    id: UUID
    name: str
    original_filename: str
    mime_type: Optional[str]
    file_type: str
    size_bytes: int
    folder_id: Optional[UUID]
    description: Optional[str]
    tags: list[str]
    favorite: bool
    is_archived: bool
    access_count: int
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BreadcrumbItem(BaseModel):
    id: UUID
    name: str


class DirectoryListing(BaseModel):
    current_folder: Optional[FolderResponse]
    path: list[BreadcrumbItem]  # Breadcrumb trail
    folders: list[FolderResponse]
    files: list[FileResponse]
    storage_used: int
    storage_quota: int


class StorageStats(BaseModel):
    used_bytes: int
    quota_bytes: int
    file_count: int
    folder_count: int
    by_type: dict[str, int]  # bytes per file type


class BulkMoveRequest(BaseModel):
    file_ids: list[UUID] = []
    folder_ids: list[UUID] = []
    target_folder_id: Optional[UUID] = None  # None = root


class BulkDeleteRequest(BaseModel):
    file_ids: list[UUID] = []
    folder_ids: list[UUID] = []


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_vault_path(user_id: UUID) -> Path:
    """Get the vault storage path for a user."""
    settings = get_settings()
    return Path(settings.vault_path) / "users" / str(user_id) / "files"


async def get_storage_used(user_id: UUID, db: AsyncSession) -> int:
    """Calculate total storage used by a user."""
    result = await db.execute(
        select(func.coalesce(func.sum(File.size_bytes), 0))
        .where(File.user_id == user_id)
    )
    return result.scalar() or 0


async def check_quota(user_id: UUID, additional_bytes: int, db: AsyncSession) -> bool:
    """Check if user has enough quota for additional bytes."""
    settings = get_settings()
    used = await get_storage_used(user_id, db)
    return (used + additional_bytes) <= settings.default_quota_bytes


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_extension(filename: str) -> str:
    """Extract extension from filename."""
    if '.' in filename:
        return filename.rsplit('.', 1)[-1].lower()
    return ''


async def get_folder_path(folder_id: UUID, user_id: UUID, db: AsyncSession) -> list[BreadcrumbItem]:
    """Build breadcrumb path from root to folder."""
    path = []
    current_id = folder_id

    while current_id:
        result = await db.execute(
            select(Folder)
            .where(Folder.id == current_id)
            .where(Folder.user_id == user_id)
        )
        folder = result.scalar_one_or_none()
        if not folder:
            break
        path.insert(0, BreadcrumbItem(id=folder.id, name=folder.name))
        current_id = folder.parent_id

    return path


async def folder_to_response(folder: Folder, db: AsyncSession) -> FolderResponse:
    """Convert Folder model to response with counts."""
    # Count child folders
    folder_result = await db.execute(
        select(func.count(Folder.id))
        .where(Folder.parent_id == folder.id)
    )
    folder_count = folder_result.scalar() or 0

    # Count files in this folder
    file_result = await db.execute(
        select(func.count(File.id))
        .where(File.folder_id == folder.id)
    )
    file_count = file_result.scalar() or 0

    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        description=folder.description,
        color=folder.color,
        icon=folder.icon,
        is_archived=folder.is_archived,
        file_count=file_count,
        folder_count=folder_count,
        created_at=folder.created_at.isoformat(),
        updated_at=folder.updated_at.isoformat(),
    )


def file_to_response(file: File) -> FileResponse:
    """Convert File model to response."""
    return FileResponse(
        id=file.id,
        name=file.name,
        original_filename=file.original_filename,
        mime_type=file.mime_type,
        file_type=file.file_type,
        size_bytes=file.size_bytes,
        folder_id=file.folder_id,
        description=file.description,
        tags=file.tags or [],
        favorite=file.favorite,
        is_archived=file.is_archived,
        access_count=file.access_count,
        status=file.status,
        created_at=file.created_at.isoformat(),
        updated_at=file.updated_at.isoformat(),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTORY LISTING
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=DirectoryListing)
async def list_root_directory(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List contents of root directory."""
    return await list_directory_contents(None, user, db)


@router.get("/folder/{folder_id}", response_model=DirectoryListing)
async def list_folder_contents(
    folder_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List contents of a specific folder."""
    # Verify folder exists and belongs to user
    result = await db.execute(
        select(Folder)
        .where(Folder.id == folder_id)
        .where(Folder.user_id == user.id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    return await list_directory_contents(folder_id, user, db)


async def list_directory_contents(
    folder_id: Optional[UUID],
    user: User,
    db: AsyncSession
) -> DirectoryListing:
    """Internal helper to list directory contents."""
    settings = get_settings()

    # Get current folder info (if not root)
    current_folder = None
    path = []
    if folder_id:
        result = await db.execute(
            select(Folder)
            .where(Folder.id == folder_id)
            .where(Folder.user_id == user.id)
        )
        folder = result.scalar_one_or_none()
        if folder:
            current_folder = await folder_to_response(folder, db)
            path = await get_folder_path(folder_id, user.id, db)

    # Get child folders
    folders_result = await db.execute(
        select(Folder)
        .where(Folder.user_id == user.id)
        .where(Folder.parent_id == folder_id)
        .where(Folder.is_archived == False)
        .order_by(Folder.name)
    )
    folders = folders_result.scalars().all()
    folder_responses = [await folder_to_response(f, db) for f in folders]

    # Get files in this folder
    files_result = await db.execute(
        select(File)
        .where(File.user_id == user.id)
        .where(File.folder_id == folder_id)
        .where(File.is_archived == False)
        .order_by(File.name)
    )
    files = files_result.scalars().all()
    file_responses = [file_to_response(f) for f in files]

    # Get storage stats
    storage_used = await get_storage_used(user.id, db)

    return DirectoryListing(
        current_folder=current_folder,
        path=path,
        folders=folder_responses,
        files=file_responses,
        storage_used=storage_used,
        storage_quota=settings.default_quota_bytes,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FOLDER CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/folder", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    request: FolderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new folder."""
    # Validate parent folder if specified
    if request.parent_id:
        result = await db.execute(
            select(Folder)
            .where(Folder.id == request.parent_id)
            .where(Folder.user_id == user.id)
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )

    # Check for duplicate name in same parent
    result = await db.execute(
        select(Folder)
        .where(Folder.user_id == user.id)
        .where(Folder.parent_id == request.parent_id)
        .where(Folder.name == request.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A folder with this name already exists"
        )

    folder = Folder(
        id=uuid4(),
        user_id=user.id,
        parent_id=request.parent_id,
        name=request.name,
        description=request.description,
        color=request.color,
        icon=request.icon,
    )
    db.add(folder)
    await db.commit()

    logger.info(f"Created folder {folder.id} for user {user.id}")
    return await folder_to_response(folder, db)


@router.patch("/folder/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    request: FolderUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update folder properties or move to new parent."""
    result = await db.execute(
        select(Folder)
        .where(Folder.id == folder_id)
        .where(Folder.user_id == user.id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    # Validate parent if moving
    if request.parent_id is not None and request.parent_id != folder.parent_id:
        # Can't move folder into itself
        if request.parent_id == folder.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move folder into itself"
            )
        # Validate new parent exists
        if request.parent_id:
            parent_result = await db.execute(
                select(Folder)
                .where(Folder.id == request.parent_id)
                .where(Folder.user_id == user.id)
            )
            if not parent_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target folder not found"
                )

    # Update fields
    if request.name is not None:
        folder.name = request.name
    if request.parent_id is not None:
        folder.parent_id = request.parent_id
    if request.description is not None:
        folder.description = request.description
    if request.color is not None:
        folder.color = request.color
    if request.icon is not None:
        folder.icon = request.icon
    if request.is_archived is not None:
        folder.is_archived = request.is_archived

    folder.updated_at = datetime.utcnow()
    await db.commit()

    return await folder_to_response(folder, db)


@router.delete("/folder/{folder_id}")
async def delete_folder(
    folder_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a folder and all its contents (cascades to files and subfolders)."""
    result = await db.execute(
        select(Folder)
        .where(Folder.id == folder_id)
        .where(Folder.user_id == user.id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    # Get all files in this folder tree for disk cleanup
    # We need to recursively collect all files
    async def collect_files_recursive(folder_id: UUID) -> list[File]:
        files = []

        # Get files in this folder
        files_result = await db.execute(
            select(File).where(File.folder_id == folder_id)
        )
        files.extend(files_result.scalars().all())

        # Get subfolders
        subfolders_result = await db.execute(
            select(Folder).where(Folder.parent_id == folder_id)
        )
        for subfolder in subfolders_result.scalars().all():
            files.extend(await collect_files_recursive(subfolder.id))

        return files

    files_to_delete = await collect_files_recursive(folder_id)

    # Delete from disk
    for file in files_to_delete:
        try:
            file_path = Path(file.storage_path)
            if file_path.exists():
                file_path.unlink()
                # Clean up parent directory if empty
                parent_dir = file_path.parent
                if parent_dir.exists() and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
        except Exception as e:
            logger.warning(f"Failed to delete file from disk: {file.storage_path} - {e}")

    # Delete folder (cascades to files and subfolders in DB)
    await db.delete(folder)
    await db.commit()

    logger.info(f"Deleted folder {folder_id} with {len(files_to_delete)} files")
    return {"message": f"Folder deleted with {len(files_to_delete)} files"}


# ═══════════════════════════════════════════════════════════════════════════════
# FILE UPLOAD / DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    folder_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file to The Vault.

    - Validates file type against allowed extensions
    - Enforces user storage quota
    - Calculates checksum for integrity
    - Stores file on Railway volume
    """
    settings = get_settings()

    # Validate file extension
    extension = get_extension(file.filename or "")
    if not extension or not is_allowed_extension(extension):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Blocked extensions: {BLOCKED_EXTENSIONS}"
        )

    # Read file content to check size and calculate checksum
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size_bytes / 1024 / 1024:.0f}MB"
        )

    # Check quota
    if not await check_quota(user.id, file_size, db):
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Storage quota exceeded. Delete some files to free up space."
        )

    # Validate folder if specified
    if folder_id:
        result = await db.execute(
            select(Folder)
            .where(Folder.id == folder_id)
            .where(Folder.user_id == user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )

    # Generate unique file ID and storage path
    file_id = uuid4()
    vault_path = get_vault_path(user.id)
    file_dir = vault_path / str(file_id)
    file_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_filename = (file.filename or f"file.{extension}").replace("/", "_").replace("\\", "_")
    storage_path = file_dir / safe_filename

    # Write file to disk
    try:
        with open(storage_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to write file to disk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )

    # Calculate checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Determine file type category
    file_type = get_file_type(extension)

    # Create database record
    file_record = File(
        id=file_id,
        user_id=user.id,
        folder_id=folder_id,
        name=safe_filename,
        original_filename=file.filename or safe_filename,
        mime_type=file.content_type,
        file_type=file_type,
        size_bytes=file_size,
        storage_path=str(storage_path),
        checksum=checksum,
        status="ready",
    )
    db.add(file_record)
    await db.commit()

    logger.info(f"Uploaded file {file_id} ({file_size} bytes) for user {user.id}")
    return file_to_response(file_record)


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_metadata(
    file_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get file metadata without downloading."""
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return file_to_response(file)


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download a file."""
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = Path(file.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    # Update access stats
    file.access_count += 1
    file.last_accessed_at = datetime.utcnow()
    await db.commit()

    return FileResponse(
        path=str(file_path),
        filename=file.original_filename,
        media_type=file.mime_type or "application/octet-stream",
    )


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: UUID,
    lines: int = 100,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a preview of file contents.

    For text files, returns first N lines.
    For images, returns the file itself.
    For other types, returns metadata only.
    """
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = Path(file.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    # Update access stats
    file.access_count += 1
    file.last_accessed_at = datetime.utcnow()
    await db.commit()

    # Image preview - return the file
    if file.file_type == "image":
        return FileResponse(
            path=str(file_path),
            filename=file.name,
            media_type=file.mime_type or "image/png",
        )

    # Text/code preview - return first N lines
    if file.file_type in ("document", "code", "data"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content_lines = []
                for i, line in enumerate(f):
                    if i >= lines:
                        break
                    content_lines.append(line)
                content = "".join(content_lines)
                truncated = i >= lines
        except Exception:
            content = "[Unable to read file content]"
            truncated = False

        return {
            "id": file.id,
            "name": file.name,
            "file_type": file.file_type,
            "mime_type": file.mime_type,
            "size_bytes": file.size_bytes,
            "content": content,
            "truncated": truncated,
            "lines_shown": min(lines, len(content_lines)) if 'content_lines' in dir() else 0,
        }

    # Other types - metadata only
    return {
        "id": file.id,
        "name": file.name,
        "file_type": file.file_type,
        "mime_type": file.mime_type,
        "size_bytes": file.size_bytes,
        "preview_available": False,
        "message": "Preview not available for this file type",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CORTEX DIVER - FILE CONTENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

class FileContentRequest(BaseModel):
    content: str


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full file content for editing.

    Returns the complete file content (no truncation) for text-based files.
    Used by Cortex Diver IDE.
    """
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_path = Path(file.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    # Only allow text-based files
    if file.file_type not in ("document", "code", "data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit binary files"
        )

    # Read full content
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )

    # Update access stats
    file.access_count += 1
    file.last_accessed_at = datetime.utcnow()
    await db.commit()

    return {
        "id": file.id,
        "name": file.name,
        "file_type": file.file_type,
        "mime_type": file.mime_type,
        "size_bytes": file.size_bytes,
        "content": content,
        "language": get_monaco_language(file.name),
    }


@router.put("/{file_id}/content")
async def save_file_content(
    file_id: UUID,
    request: FileContentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save file content from editor.

    Overwrites the file with new content and updates metadata.
    Used by Cortex Diver IDE.
    """
    settings = get_settings()

    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Only allow text-based files
    if file.file_type not in ("document", "code", "data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit binary files"
        )

    file_path = Path(file.storage_path)

    # Calculate new size and check quota
    new_content = request.content.encode("utf-8")
    new_size = len(new_content)
    size_delta = new_size - file.size_bytes

    # Check quota if size is increasing
    if size_delta > 0:
        user_settings = user.settings or {}
        used = user_settings.get("storage_used_bytes", 0)
        quota = user_settings.get("storage_quota_bytes", settings.default_quota_bytes)

        if used + size_delta > quota:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Storage quota exceeded. Available: {quota - used} bytes"
            )

    # Write content
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Update file metadata
    old_size = file.size_bytes
    file.size_bytes = new_size
    file.checksum = hashlib.sha256(new_content).hexdigest()
    file.updated_at = datetime.utcnow()

    # Update user storage stats
    if size_delta != 0:
        user_settings = user.settings or {}
        user_settings["storage_used_bytes"] = user_settings.get("storage_used_bytes", 0) + size_delta
        user.settings = user_settings

    await db.commit()
    await db.refresh(file)

    return {
        "id": file.id,
        "name": file.name,
        "size_bytes": file.size_bytes,
        "saved": True,
        "size_delta": size_delta,
    }


def get_monaco_language(filename: str) -> str:
    """Map file extension to Monaco editor language."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    language_map = {
        # Web
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "html": "html",
        "htm": "html",
        "css": "css",
        "scss": "scss",
        "less": "less",
        "vue": "html",
        "svelte": "html",
        # Python
        "py": "python",
        "pyw": "python",
        "pyi": "python",
        # Systems
        "c": "c",
        "h": "c",
        "cpp": "cpp",
        "hpp": "cpp",
        "cc": "cpp",
        "rs": "rust",
        "go": "go",
        "java": "java",
        "kt": "kotlin",
        "swift": "swift",
        # Data/Config
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "toml": "toml",
        "xml": "xml",
        "sql": "sql",
        "graphql": "graphql",
        # Shell
        "sh": "shell",
        "bash": "shell",
        "zsh": "shell",
        "fish": "shell",
        "ps1": "powershell",
        # Markup
        "md": "markdown",
        "mdx": "markdown",
        "rst": "restructuredtext",
        "tex": "latex",
        # Other
        "rb": "ruby",
        "php": "php",
        "lua": "lua",
        "r": "r",
        "dockerfile": "dockerfile",
        "makefile": "makefile",
        "env": "ini",
        "ini": "ini",
        "conf": "ini",
        "txt": "plaintext",
        "log": "plaintext",
    }

    # Handle special filenames
    special_files = {
        "dockerfile": "dockerfile",
        "makefile": "makefile",
        ".gitignore": "ignore",
        ".dockerignore": "ignore",
        ".env": "ini",
        ".editorconfig": "ini",
    }

    lower_name = filename.lower()
    if lower_name in special_files:
        return special_files[lower_name]

    return language_map.get(ext, "plaintext")


@router.patch("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: UUID,
    request: FileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update file properties or move to new folder."""
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Validate folder if moving
    if request.folder_id is not None and request.folder_id != file.folder_id:
        if request.folder_id:  # Not moving to root
            folder_result = await db.execute(
                select(Folder)
                .where(Folder.id == request.folder_id)
                .where(Folder.user_id == user.id)
            )
            if not folder_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target folder not found"
                )

    # Update fields
    if request.name is not None:
        file.name = request.name
    if request.folder_id is not None:
        file.folder_id = request.folder_id if request.folder_id else None
    if request.description is not None:
        file.description = request.description
    if request.tags is not None:
        file.tags = request.tags
    if request.favorite is not None:
        file.favorite = request.favorite
    if request.is_archived is not None:
        file.is_archived = request.is_archived

    file.updated_at = datetime.utcnow()
    await db.commit()

    return file_to_response(file)


@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a file from The Vault."""
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
        .where(File.user_id == user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Delete from disk
    try:
        file_path = Path(file.storage_path)
        if file_path.exists():
            file_path.unlink()
            # Clean up parent directory if empty
            parent_dir = file_path.parent
            if parent_dir.exists() and not any(parent_dir.iterdir()):
                parent_dir.rmdir()
    except Exception as e:
        logger.warning(f"Failed to delete file from disk: {file.storage_path} - {e}")

    # Delete from database
    await db.delete(file)
    await db.commit()

    logger.info(f"Deleted file {file_id} for user {user.id}")
    return {"message": "File deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
# BULK OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/move")
async def bulk_move(
    request: BulkMoveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Move multiple files and/or folders to a target folder."""
    # Validate target folder
    if request.target_folder_id:
        result = await db.execute(
            select(Folder)
            .where(Folder.id == request.target_folder_id)
            .where(Folder.user_id == user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target folder not found"
            )

    moved_files = 0
    moved_folders = 0

    # Move files
    for file_id in request.file_ids:
        result = await db.execute(
            select(File)
            .where(File.id == file_id)
            .where(File.user_id == user.id)
        )
        file = result.scalar_one_or_none()
        if file:
            file.folder_id = request.target_folder_id
            file.updated_at = datetime.utcnow()
            moved_files += 1

    # Move folders (can't move folder into its own child)
    for folder_id in request.folder_ids:
        if folder_id == request.target_folder_id:
            continue  # Skip moving folder to itself

        result = await db.execute(
            select(Folder)
            .where(Folder.id == folder_id)
            .where(Folder.user_id == user.id)
        )
        folder = result.scalar_one_or_none()
        if folder:
            folder.parent_id = request.target_folder_id
            folder.updated_at = datetime.utcnow()
            moved_folders += 1

    await db.commit()

    return {
        "message": f"Moved {moved_files} files and {moved_folders} folders",
        "moved_files": moved_files,
        "moved_folders": moved_folders,
    }


@router.post("/delete")
async def bulk_delete(
    request: BulkDeleteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple files and/or folders."""
    deleted_files = 0
    deleted_folders = 0

    # Delete files
    for file_id in request.file_ids:
        result = await db.execute(
            select(File)
            .where(File.id == file_id)
            .where(File.user_id == user.id)
        )
        file = result.scalar_one_or_none()
        if file:
            # Delete from disk
            try:
                file_path = Path(file.storage_path)
                if file_path.exists():
                    file_path.unlink()
                    parent_dir = file_path.parent
                    if parent_dir.exists() and not any(parent_dir.iterdir()):
                        parent_dir.rmdir()
            except Exception as e:
                logger.warning(f"Failed to delete file from disk: {e}")

            await db.delete(file)
            deleted_files += 1

    # Delete folders (cascades in DB, need disk cleanup)
    for folder_id in request.folder_ids:
        result = await db.execute(
            select(Folder)
            .where(Folder.id == folder_id)
            .where(Folder.user_id == user.id)
        )
        folder = result.scalar_one_or_none()
        if folder:
            # Collect all files recursively for disk cleanup
            async def collect_files(fid: UUID) -> list[str]:
                paths = []
                files_result = await db.execute(
                    select(File.storage_path).where(File.folder_id == fid)
                )
                paths.extend([r[0] for r in files_result.fetchall()])

                subfolders_result = await db.execute(
                    select(Folder.id).where(Folder.parent_id == fid)
                )
                for (subfolder_id,) in subfolders_result.fetchall():
                    paths.extend(await collect_files(subfolder_id))
                return paths

            file_paths = await collect_files(folder_id)

            # Delete files from disk
            for path in file_paths:
                try:
                    file_path = Path(path)
                    if file_path.exists():
                        file_path.unlink()
                        parent_dir = file_path.parent
                        if parent_dir.exists() and not any(parent_dir.iterdir()):
                            parent_dir.rmdir()
                except Exception as e:
                    logger.warning(f"Failed to delete file from disk: {e}")

            await db.delete(folder)
            deleted_folders += 1

    await db.commit()

    return {
        "message": f"Deleted {deleted_files} files and {deleted_folders} folders",
        "deleted_files": deleted_files,
        "deleted_folders": deleted_folders,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH & SPECIAL LISTINGS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/search/files", response_model=list[FileResponse])
async def search_files(
    q: str,
    file_type: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search files by name, with optional type filter."""
    query = (
        select(File)
        .where(File.user_id == user.id)
        .where(File.name.ilike(f"%{q}%"))
    )

    if file_type:
        query = query.where(File.file_type == file_type)

    query = query.order_by(File.updated_at.desc()).limit(limit)

    result = await db.execute(query)
    files = result.scalars().all()

    return [file_to_response(f) for f in files]


@router.get("/recent", response_model=list[FileResponse])
async def get_recent_files(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recently accessed files."""
    result = await db.execute(
        select(File)
        .where(File.user_id == user.id)
        .where(File.last_accessed_at.is_not(None))
        .order_by(File.last_accessed_at.desc())
        .limit(limit)
    )
    files = result.scalars().all()
    return [file_to_response(f) for f in files]


@router.get("/favorites", response_model=list[FileResponse])
async def get_favorite_files(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get favorite files."""
    result = await db.execute(
        select(File)
        .where(File.user_id == user.id)
        .where(File.favorite == True)
        .order_by(File.updated_at.desc())
        .limit(limit)
    )
    files = result.scalars().all()
    return [file_to_response(f) for f in files]


@router.get("/stats", response_model=StorageStats)
async def get_storage_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user storage statistics."""
    settings = get_settings()

    # Total used
    used = await get_storage_used(user.id, db)

    # File count
    file_count_result = await db.execute(
        select(func.count(File.id)).where(File.user_id == user.id)
    )
    file_count = file_count_result.scalar() or 0

    # Folder count
    folder_count_result = await db.execute(
        select(func.count(Folder.id)).where(Folder.user_id == user.id)
    )
    folder_count = folder_count_result.scalar() or 0

    # By type
    by_type_result = await db.execute(
        select(File.file_type, func.sum(File.size_bytes))
        .where(File.user_id == user.id)
        .group_by(File.file_type)
    )
    by_type = {row[0]: row[1] or 0 for row in by_type_result.fetchall()}

    return StorageStats(
        used_bytes=used,
        quota_bytes=settings.default_quota_bytes,
        file_count=file_count,
        folder_count=folder_count,
        by_type=by_type,
    )
