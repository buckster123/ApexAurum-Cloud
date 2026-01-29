"""
Nursery API - The Growth Chamber

Training data management and Training Forge endpoints.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from sqlalchemy.orm import selectinload

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


class EstimateRequest(BaseModel):
    dataset_id: str
    base_model: str = "meta-llama/Llama-3.2-3B-Instruct"
    n_epochs: int = 3
    lora: bool = True


class StartTrainingRequest(BaseModel):
    dataset_id: str
    base_model: str = "meta-llama/Llama-3.2-3B-Instruct"
    n_epochs: int = 3
    learning_rate: float = 1e-5
    lora: bool = True
    batch_size: Optional[int] = None
    suffix: Optional[str] = None


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


# ═══════════════════════════════════════════════════════════════════════════════
# TRAINING FORGE - Cloud fine-tuning endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/training/models")
async def list_trainable_models():
    """List available base models for fine-tuning."""
    from app.services.cloud_trainer import TRAINABLE_MODELS

    return {"models": [
        {"id": model_id, **info}
        for model_id, info in TRAINABLE_MODELS.items()
    ]}


@router.post("/training/estimate")
async def estimate_training_cost(
    request: EstimateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estimate the cost of a fine-tuning job."""
    await _check_adept_tier(user, db)

    from app.services.nursery import NurseryService
    from app.services.cloud_trainer import CloudTrainerService

    dataset = await NurseryService.get_dataset(request.dataset_id, str(user.id))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    num_examples = dataset.get("num_examples", 0)
    estimate = CloudTrainerService.estimate_cost(
        num_examples=num_examples,
        base_model=request.base_model,
        n_epochs=request.n_epochs,
        lora=request.lora,
    )

    return estimate


@router.post("/training/start")
async def start_training(
    request: StartTrainingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a cloud fine-tuning job via Together.ai."""
    await _check_adept_tier(user, db)

    from app.services.nursery import NurseryService
    from app.services.cloud_trainer import CloudTrainerService, auto_complete_training_job
    from app.api.v1.user import get_user_api_key
    from app.models.nursery import NurseryTrainingJob

    # Get Together API key
    api_key = get_user_api_key(user, "together")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Together.ai API key required. Configure in Settings > API Keys.",
        )

    # Validate dataset
    dataset = await NurseryService.get_dataset(request.dataset_id, str(user.id))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    num_examples = dataset.get("num_examples", 0)

    # Get cost estimate
    estimate = CloudTrainerService.estimate_cost(
        num_examples=num_examples,
        base_model=request.base_model,
        n_epochs=request.n_epochs,
        lora=request.lora,
    )

    # Upload dataset to Together
    storage_path = dataset.get("storage_path", "")
    file_id = await CloudTrainerService.upload_dataset(storage_path, api_key)

    # Create training job on Together
    job_info = await CloudTrainerService.create_training_job(
        file_id=file_id,
        base_model=request.base_model,
        api_key=api_key,
        n_epochs=request.n_epochs,
        learning_rate=request.learning_rate,
        lora=request.lora,
        suffix=request.suffix,
    )

    # Save job to DB
    job = NurseryTrainingJob(
        id=uuid4(),
        user_id=user.id,
        dataset_id=UUID(request.dataset_id),
        provider="together",
        provider_job_id=job_info.get("job_id"),
        base_model=request.base_model,
        output_name=job_info.get("output_name"),
        status="running",
        progress=0.0,
        config={
            "n_epochs": request.n_epochs,
            "learning_rate": request.learning_rate,
            "lora": request.lora,
            "batch_size": request.batch_size,
            "suffix": request.suffix,
            "file_id": file_id,
        },
        cost_estimate=estimate.get("estimated_cost_usd"),
        started_at=datetime.utcnow(),
    )
    db.add(job)
    await db.flush()

    # Fire background polling task
    asyncio.create_task(
        auto_complete_training_job(str(job.id), str(user.id))
    )

    return {
        "job_id": str(job.id),
        "provider_job_id": job_info.get("job_id"),
        "status": "running",
        "base_model": request.base_model,
        "output_name": job_info.get("output_name"),
        "estimated_cost": estimate.get("estimated_cost_usd"),
        "num_examples": num_examples,
        "n_epochs": request.n_epochs,
        "message": f"Training job started. Fine-tuning {request.base_model} with {num_examples} examples.",
    }


@router.get("/training/jobs")
async def list_training_jobs(
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List training jobs for the current user."""
    await _check_adept_tier(user, db)

    from app.models.nursery import NurseryTrainingJob

    query = (
        select(NurseryTrainingJob)
        .options(selectinload(NurseryTrainingJob.dataset))
        .where(NurseryTrainingJob.user_id == user.id)
    )

    if status:
        query = query.where(NurseryTrainingJob.status == status)

    query = query.order_by(NurseryTrainingJob.created_at.desc()).limit(50)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return {
        "count": len(jobs),
        "jobs": [
            {
                "id": str(j.id),
                "dataset_id": str(j.dataset_id),
                "dataset_name": j.dataset.name if j.dataset else "unknown",
                "provider": j.provider,
                "provider_job_id": j.provider_job_id,
                "base_model": j.base_model,
                "output_name": j.output_name,
                "status": j.status,
                "progress": j.progress,
                "cost_estimate": j.cost_estimate,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ],
    }


@router.get("/training/jobs/{job_id}")
async def get_training_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info for a specific training job."""
    await _check_adept_tier(user, db)

    from app.models.nursery import NurseryTrainingJob

    result = await db.execute(
        select(NurseryTrainingJob)
        .options(selectinload(NurseryTrainingJob.dataset))
        .where(
            NurseryTrainingJob.id == UUID(job_id),
            NurseryTrainingJob.user_id == user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")

    return {
        "id": str(job.id),
        "dataset_id": str(job.dataset_id),
        "dataset_name": job.dataset.name if job.dataset else "unknown",
        "provider": job.provider,
        "provider_job_id": job.provider_job_id,
        "base_model": job.base_model,
        "output_name": job.output_name,
        "status": job.status,
        "progress": job.progress,
        "config": job.config,
        "cost_estimate": job.cost_estimate,
        "cost_actual": job.cost_actual,
        "error_message": job.error_message,
        "agent_id": job.agent_id,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.post("/training/jobs/{job_id}/cancel")
async def cancel_training_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running training job."""
    await _check_adept_tier(user, db)

    from app.models.nursery import NurseryTrainingJob
    from app.services.cloud_trainer import CloudTrainerService
    from app.api.v1.user import get_user_api_key

    result = await db.execute(
        select(NurseryTrainingJob).where(
            NurseryTrainingJob.id == UUID(job_id),
            NurseryTrainingJob.user_id == user.id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")

    if job.status not in ("pending", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status '{job.status}'. Only pending or running jobs can be cancelled.",
        )

    # Cancel on Together if we have the provider job ID
    if job.provider_job_id:
        api_key = get_user_api_key(user, "together")
        if api_key:
            try:
                await CloudTrainerService.cancel_job(job.provider_job_id, api_key)
            except Exception as e:
                logger.warning(f"Failed to cancel job on provider: {e}")

    job.status = "failed"
    job.error_message = "Cancelled by user"
    job.completed_at = datetime.utcnow()

    return {
        "success": True,
        "job_id": str(job.id),
        "status": "failed",
        "message": "Training job cancelled.",
    }
