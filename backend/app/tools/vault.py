"""
Tier 3: Vault Tools - The Crafting Hands

File operations mapped to the existing Vault API.
User-scoped, quota-enforced file management.
"Shape and mold the user's files"

NOTE: These tools require database access with user context.
They use SQLAlchemy models directly rather than HTTP endpoints.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from . import registry
from .base import BaseTool, ToolSchema, ToolResult, ToolContext, ToolCategory


logger = logging.getLogger(__name__)


async def get_db_session():
    """Get a database session for tool operations."""
    from app.database import async_session
    async with async_session() as session:
        yield session


# =============================================================================
# VAULT LIST
# =============================================================================

class VaultListTool(BaseTool):
    """List files and folders in the user's vault."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="vault_list",
            description="""List files and folders in the user's vault.

Use to:
- Browse the user's file storage
- Find specific files by name
- Navigate folder hierarchy

Returns file names, sizes, and types. Root folder is used if no folder_id specified.""",
            category=ToolCategory.FILES,
            input_schema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "Folder UUID to list (omit for root folder)",
                    },
                },
                "required": [],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required to access vault")

        folder_id = params.get("folder_id")

        try:
            from app.models.file import File, Folder
            from app.database import async_session

            async with async_session() as db:
                user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

                # Get folder (root if not specified)
                if folder_id:
                    folder_uuid = UUID(folder_id)
                    folder_result = await db.execute(
                        select(Folder).where(
                            Folder.id == folder_uuid,
                            Folder.user_id == user_uuid
                        )
                    )
                    folder = folder_result.scalar_one_or_none()
                    if not folder:
                        return ToolResult(success=False, error=f"Folder not found: {folder_id}")
                else:
                    # Get root folder
                    folder_result = await db.execute(
                        select(Folder).where(
                            Folder.user_id == user_uuid,
                            Folder.parent_id == None  # noqa: E711
                        )
                    )
                    folder = folder_result.scalar_one_or_none()
                    if not folder:
                        return ToolResult(
                            success=True,
                            result={"folder_id": "root", "folders": [], "files": [], "total_items": 0}
                        )

                # Get subfolders
                subfolders_result = await db.execute(
                    select(Folder).where(
                        Folder.parent_id == folder.id,
                        Folder.user_id == user_uuid
                    )
                )
                subfolders = subfolders_result.scalars().all()

                # Get files in folder
                files_result = await db.execute(
                    select(File).where(
                        File.folder_id == folder.id,
                        File.user_id == user_uuid
                    )
                )
                files = files_result.scalars().all()

                folders_list = [
                    {"id": str(f.id), "name": f.name}
                    for f in subfolders
                ]

                files_list = [
                    {
                        "id": str(f.id),
                        "name": f.name,
                        "size": f.size_bytes,
                        "mime_type": f.mime_type,
                    }
                    for f in files
                ]

                return ToolResult(
                    success=True,
                    result={
                        "folder_id": str(folder.id),
                        "folder_name": folder.name,
                        "folders": folders_list,
                        "files": files_list,
                        "total_items": len(folders_list) + len(files_list),
                    },
                )

        except Exception as e:
            logger.exception("Vault list error")
            return ToolResult(success=False, error=f"Failed to list vault: {str(e)}")


# =============================================================================
# VAULT READ
# =============================================================================

class VaultReadTool(BaseTool):
    """Read content from a file in the vault."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="vault_read",
            description="""Read the content of a text file from the user's vault.

Use to:
- Read code files (Python, JavaScript, etc.)
- Read markdown or text documents
- Get configuration files

Note: Only text files are supported. Binary files will return metadata only.""",
            category=ToolCategory.FILES,
            input_schema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "File UUID to read",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Max content length to return (default: 50000)",
                        "default": 50000,
                    },
                },
                "required": ["file_id"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required to access vault")

        file_id = params.get("file_id")
        max_length = min(params.get("max_length", 50000), 100000)

        if not file_id:
            return ToolResult(success=False, error="file_id is required")

        try:
            from app.models.file import File
            from app.database import async_session
            from pathlib import Path

            async with async_session() as db:
                user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id
                file_uuid = UUID(file_id)

                # Get file record
                file_result = await db.execute(
                    select(File).where(
                        File.id == file_uuid,
                        File.user_id == user_uuid
                    )
                )
                file = file_result.scalar_one_or_none()

                if not file:
                    return ToolResult(success=False, error=f"File not found: {file_id}")

                # Check if text file
                is_text = file.mime_type and (
                    file.mime_type.startswith("text/") or
                    file.mime_type in [
                        "application/json",
                        "application/javascript",
                        "application/xml",
                        "application/x-python",
                    ] or
                    file.name.endswith(('.py', '.js', '.ts', '.md', '.txt', '.json', '.yaml', '.yml', '.html', '.css'))
                )

                result = {
                    "id": str(file.id),
                    "name": file.name,
                    "size": file.size_bytes,
                    "mime_type": file.mime_type,
                    "is_text": is_text,
                }

                if is_text and file.storage_path:
                    # Read from filesystem - storage_path is the full path
                    file_path = Path(file.storage_path)

                    if file_path.exists():
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                        if len(content) > max_length:
                            content = content[:max_length] + "\n\n[Truncated...]"
                            result["truncated"] = True
                        result["content"] = content
                    else:
                        result["error"] = "File content not found on disk"

                return ToolResult(success=True, result=result)

        except Exception as e:
            logger.exception("Vault read error")
            return ToolResult(success=False, error=f"Failed to read file: {str(e)}")


# =============================================================================
# VAULT INFO
# =============================================================================

class VaultInfoTool(BaseTool):
    """Get storage usage and quota information."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="vault_info",
            description="""Get the user's vault storage statistics.

Returns:
- Total storage used
- Storage quota/limit
- File count
- Folder count

Use to check available space before creating files.""",
            category=ToolCategory.FILES,
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required to access vault")

        try:
            from app.models.file import File, Folder
            from app.database import async_session

            async with async_session() as db:
                user_uuid = UUID(context.user_id) if isinstance(context.user_id, str) else context.user_id

                # Count files and total size
                files_result = await db.execute(
                    select(
                        func.count(File.id).label("count"),
                        func.coalesce(func.sum(File.size_bytes), 0).label("total_size")
                    ).where(File.user_id == user_uuid)
                )
                file_stats = files_result.one()

                # Count folders
                folders_result = await db.execute(
                    select(func.count(Folder.id)).where(Folder.user_id == user_uuid)
                )
                folder_count = folders_result.scalar() or 0

                used_bytes = file_stats.total_size or 0
                quota_bytes = 100 * 1024 * 1024  # 100MB default

                return ToolResult(
                    success=True,
                    result={
                        "used_bytes": used_bytes,
                        "used_human": _format_size(used_bytes),
                        "quota_bytes": quota_bytes,
                        "quota_human": _format_size(quota_bytes),
                        "percent_used": round(used_bytes / quota_bytes * 100, 1),
                        "file_count": file_stats.count or 0,
                        "folder_count": folder_count,
                    },
                )

        except Exception as e:
            logger.exception("Vault info error")
            return ToolResult(success=False, error=f"Failed to get vault info: {str(e)}")


def _format_size(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# =============================================================================
# REGISTER TOOLS
# =============================================================================

# Register available vault tools
# Note: vault_write and vault_search need more work - skipping for now
registry.register(VaultListTool())
registry.register(VaultReadTool())
registry.register(VaultInfoTool())
