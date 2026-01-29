"""
Nursery API - The Growth Chamber

Training data management endpoints.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.billing import Subscription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nursery", tags=["Nursery"])


# Request schemas
class GenerateDataRequest(BaseModel):
    tool_names: list[str]
    num_examples: int = 50
    variation_level: str = "medium"
    dataset_name: Optional[str] = None


class ExtractDataRequest(BaseModel):
    tools_filter: Optional[list[str]] = None
    min_examples: int = 10
    dataset_name: Optional[str] = None


async def _check_adept_tier(user: User, db: AsyncSession):
    """Check if user has Adept tier (required for Nursery).

    Reads tier from the Subscription model (same as chat.py),
    not user.settings which is never populated by Stripe/admin flows.
    """
    tier = "free"
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()
    if subscription:
        tier = subscription.tier
    if tier != "opus":
        raise HTTPException(
            status_code=403,
            detail="The Nursery requires Adept tier ($30/mo). Upgrade to access model training."
        )


@router.get("/datasets")
async def list_datasets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's training datasets."""
    await _check_adept_tier(user, db)

    from app.services.nursery import NurseryService
    datasets = await NurseryService.list_datasets(str(user.id))
    return {"datasets": datasets, "count": len(datasets)}


@router.post("/datasets/generate")
async def generate_data(
    request: GenerateDataRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate synthetic training data."""
    await _check_adept_tier(user, db)

    if not request.tool_names:
        raise HTTPException(status_code=400, detail="At least one tool name is required")

    if request.num_examples < 1 or request.num_examples > 500:
        raise HTTPException(status_code=400, detail="num_examples must be between 1 and 500")

    if request.variation_level not in ("low", "medium", "high"):
        raise HTTPException(status_code=400, detail="variation_level must be low, medium, or high")

    from app.services.nursery import NurseryService
    result = await NurseryService.generate_synthetic_data(
        tool_names=request.tool_names,
        num_examples=request.num_examples,
        variation_level=request.variation_level,
        user_id=str(user.id),
        dataset_name=request.dataset_name,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Generation failed"))

    return result


@router.post("/datasets/extract")
async def extract_data(
    request: ExtractDataRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extract training data from conversation history."""
    await _check_adept_tier(user, db)

    from app.services.nursery import NurseryService
    result = await NurseryService.extract_conversation_data(
        user_id=str(user.id),
        tools_filter=request.tools_filter,
        min_examples=request.min_examples,
        dataset_name=request.dataset_name,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Extraction failed"))

    return result


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a dataset and its file."""
    await _check_adept_tier(user, db)

    from app.services.nursery import NurseryService
    deleted = await NurseryService.delete_dataset(dataset_id, str(user.id))

    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return {"success": True, "message": "Dataset deleted"}


@router.get("/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get nursery statistics."""
    await _check_adept_tier(user, db)

    from app.services.nursery import NurseryService
    stats = await NurseryService.get_stats(str(user.id))
    return stats
