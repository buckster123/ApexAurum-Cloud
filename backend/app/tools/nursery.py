"""
Tier 15: Nursery Tools - The Data Garden

Training data generation and dataset management.
"From data, new minds are born."
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from . import registry
from .base import BaseTool, ToolSchema, ToolResult, ToolContext, ToolCategory
from app.config import get_settings

logger = logging.getLogger(__name__)


class NurseryGenerateDataTool(BaseTool):
    """Generate synthetic training data for specified tools."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="nursery_generate_data",
            description="""Generate synthetic training data for model fine-tuning.

Creates ChatML-format JSONL training examples by analyzing tool schemas
and generating varied user queries paired with correct tool calls.

Use to:
- Create training data for specific tools
- Build datasets for model fine-tuning
- Prepare data for the Training Forge

Variation levels: low (simple), medium (natural), high (diverse).
Returns dataset ID and metadata.""",
            category=ToolCategory.NURSERY,
            input_schema={
                "type": "object",
                "properties": {
                    "tool_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tool names to generate data for (e.g., ['calculator', 'web_search'])",
                    },
                    "num_examples": {
                        "type": "integer",
                        "description": "Number of examples to generate (default: 50)",
                        "default": 50,
                    },
                    "variation_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Query variation level",
                        "default": "medium",
                    },
                    "dataset_name": {
                        "type": "string",
                        "description": "Custom name for the dataset (optional)",
                    },
                },
                "required": ["tool_names"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        tool_names = params.get("tool_names", [])
        if not tool_names:
            return ToolResult(success=False, error="At least one tool name is required")

        num_examples = min(params.get("num_examples", 50), 500)  # Cap at 500
        variation_level = params.get("variation_level", "medium")
        dataset_name = params.get("dataset_name")

        try:
            from app.services.nursery import NurseryService

            result = await NurseryService.generate_synthetic_data(
                tool_names=tool_names,
                num_examples=num_examples,
                variation_level=variation_level,
                user_id=str(context.user_id),
                agent_id=context.agent_id,
                dataset_name=dataset_name,
            )

            if not result.get("success"):
                return ToolResult(success=False, error=result.get("error", "Generation failed"))

            return ToolResult(
                success=True,
                result={
                    "dataset_id": result["dataset_id"],
                    "name": result["name"],
                    "num_examples": result["num_examples"],
                    "size_kb": round(result["size_bytes"] / 1024, 1),
                    "tools": result["tools"],
                    "message": f"Generated {result['num_examples']} training examples for {', '.join(tool_names)}",
                },
            )

        except Exception as e:
            logger.exception("Nursery generate data error")
            return ToolResult(success=False, error=f"Failed to generate data: {str(e)}")


class NurseryExtractDataTool(BaseTool):
    """Extract training data from conversation history."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="nursery_extract_data",
            description="""Extract training data from your conversation history.

Mines real tool usage from past chats - finds messages where tools
were called and pairs them with the user query that triggered them.

Use to:
- Mine real-world tool usage patterns
- Create datasets from actual conversations
- Build training data from authentic interactions

Returns dataset with deduplicated examples in ChatML JSONL format.""",
            category=ToolCategory.NURSERY,
            input_schema={
                "type": "object",
                "properties": {
                    "tools_filter": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Only extract calls to these tools (optional, extracts all if omitted)",
                    },
                    "min_examples": {
                        "type": "integer",
                        "description": "Minimum examples required (default: 10)",
                        "default": 10,
                    },
                    "dataset_name": {
                        "type": "string",
                        "description": "Custom name for the dataset (optional)",
                    },
                },
                "required": [],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        tools_filter = params.get("tools_filter")
        min_examples = params.get("min_examples", 10)
        dataset_name = params.get("dataset_name")

        try:
            from app.services.nursery import NurseryService

            result = await NurseryService.extract_conversation_data(
                user_id=str(context.user_id),
                tools_filter=tools_filter,
                min_examples=min_examples,
                agent_id=context.agent_id,
                dataset_name=dataset_name,
            )

            if not result.get("success"):
                return ToolResult(success=False, error=result.get("error", "Extraction failed"))

            return ToolResult(
                success=True,
                result={
                    "dataset_id": result["dataset_id"],
                    "name": result["name"],
                    "num_examples": result["num_examples"],
                    "size_kb": round(result["size_bytes"] / 1024, 1),
                    "tools_extracted": result.get("tools_extracted", {}),
                    "message": f"Extracted {result['num_examples']} examples from conversation history",
                },
            )

        except Exception as e:
            logger.exception("Nursery extract data error")
            return ToolResult(success=False, error=f"Failed to extract data: {str(e)}")


class NurseryListDatasetsTool(BaseTool):
    """List available training datasets."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="nursery_list_datasets",
            description="""List your training datasets in the Nursery.

Shows all datasets with name, source (synthetic/extracted),
tool coverage, example count, and size.

Use to:
- See available training data
- Check dataset sizes before training
- Find datasets for specific tools""",
            category=ToolCategory.NURSERY,
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default: 20)",
                        "default": 20,
                    },
                },
                "required": [],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        try:
            from app.services.nursery import NurseryService

            datasets = await NurseryService.list_datasets(str(context.user_id))

            limit = min(params.get("limit", 20), 50)
            datasets = datasets[:limit]

            return ToolResult(
                success=True,
                result={
                    "count": len(datasets),
                    "datasets": datasets,
                },
            )

        except Exception as e:
            logger.exception("Nursery list datasets error")
            return ToolResult(success=False, error=f"Failed to list datasets: {str(e)}")


class NurseryEstimateCostTool(BaseTool):
    """Estimate the cost of fine-tuning a model on a dataset."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="nursery_estimate_cost",
            description="""Estimate the cost of fine-tuning a model on a Nursery dataset.

Returns estimated cost, training time, and resource breakdown based on
dataset size, model, and training configuration.

Use to:
- Check cost before starting a training job
- Compare costs across different models or configs
- Plan training budget""",
            category=ToolCategory.NURSERY,
            input_schema={
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "ID of the dataset to train on",
                    },
                    "base_model": {
                        "type": "string",
                        "description": "Base model for fine-tuning (default: meta-llama/Llama-3.2-3B-Instruct)",
                        "default": "meta-llama/Llama-3.2-3B-Instruct",
                    },
                    "n_epochs": {
                        "type": "integer",
                        "description": "Number of training epochs (default: 3)",
                        "default": 3,
                    },
                    "lora": {
                        "type": "boolean",
                        "description": "Use LoRA (parameter-efficient) training (default: true)",
                        "default": True,
                    },
                },
                "required": ["dataset_id"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        dataset_id = params.get("dataset_id")
        base_model = params.get("base_model", "meta-llama/Llama-3.2-3B-Instruct")
        n_epochs = params.get("n_epochs", 3)
        lora = params.get("lora", True)

        try:
            from app.services.nursery import NurseryService
            from app.services.cloud_trainer import CloudTrainerService

            dataset = await NurseryService.get_dataset(dataset_id, str(context.user_id))
            if not dataset:
                return ToolResult(success=False, error="Dataset not found")

            num_examples = dataset.get("num_examples", 0)
            estimate = CloudTrainerService.estimate_cost(
                num_examples=num_examples,
                base_model=base_model,
                n_epochs=n_epochs,
                lora=lora,
            )

            return ToolResult(success=True, result=estimate)

        except Exception as e:
            logger.exception("Nursery estimate cost error")
            return ToolResult(success=False, error=f"Failed to estimate cost: {str(e)}")


class NurseryTrainTool(BaseTool):
    """Start a cloud fine-tuning job on a Nursery dataset."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="nursery_train",
            description="""Start a cloud fine-tuning job via Together.ai.

Uploads the dataset, creates a training job, and begins fine-tuning.
Progress is tracked automatically in the background.

Requires a Together.ai API key configured in Settings > API Keys.

Use to:
- Fine-tune a model on your training data
- Create custom tool-calling models
- Train apprentice models for agents""",
            category=ToolCategory.NURSERY,
            input_schema={
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "ID of the dataset to train on",
                    },
                    "base_model": {
                        "type": "string",
                        "description": "Base model for fine-tuning (default: meta-llama/Llama-3.2-3B-Instruct)",
                        "default": "meta-llama/Llama-3.2-3B-Instruct",
                    },
                    "n_epochs": {
                        "type": "integer",
                        "description": "Number of training epochs (default: 3)",
                        "default": 3,
                    },
                    "learning_rate": {
                        "type": "number",
                        "description": "Learning rate (default: 0.00001)",
                        "default": 0.00001,
                    },
                    "lora": {
                        "type": "boolean",
                        "description": "Use LoRA training (default: true)",
                        "default": True,
                    },
                    "suffix": {
                        "type": "string",
                        "description": "Custom suffix for the output model name (optional)",
                    },
                },
                "required": ["dataset_id"],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        dataset_id = params.get("dataset_id")
        base_model = params.get("base_model", "meta-llama/Llama-3.2-3B-Instruct")
        n_epochs = params.get("n_epochs", 3)
        learning_rate = params.get("learning_rate", 1e-5)
        lora = params.get("lora", True)
        suffix = params.get("suffix")

        try:
            from app.services.nursery import NurseryService
            from app.services.cloud_trainer import CloudTrainerService, auto_complete_training_job
            from app.models.nursery import NurseryTrainingJob
            from app.models.user import User
            from app.api.v1.user import get_user_api_key
            from app.database import get_db_context
            from sqlalchemy import select

            # 1. Validate dataset
            dataset = await NurseryService.get_dataset(dataset_id, str(context.user_id))
            if not dataset:
                return ToolResult(success=False, error="Dataset not found")

            # 2. Get Together API key from user settings
            async with get_db_context() as db:
                result = await db.execute(
                    select(User).where(User.id == UUID(str(context.user_id)))
                )
                user = result.scalar_one_or_none()

            if not user:
                return ToolResult(success=False, error="User not found")

            api_key = get_user_api_key(user, "together")
            if not api_key:
                return ToolResult(
                    success=False,
                    error="Together.ai API key required. Configure in Settings > API Keys.",
                )

            # 3. Get cost estimate
            num_examples = dataset.get("num_examples", 0)
            estimate = CloudTrainerService.estimate_cost(
                num_examples=num_examples,
                base_model=base_model,
                n_epochs=n_epochs,
                lora=lora,
            )

            # 4. Upload dataset to Together
            storage_path = dataset.get("storage_path", "")
            file_id = await CloudTrainerService.upload_dataset(storage_path, api_key)

            # 5. Create training job on Together
            job_info = await CloudTrainerService.create_training_job(
                file_id=file_id,
                base_model=base_model,
                api_key=api_key,
                n_epochs=n_epochs,
                learning_rate=learning_rate,
                lora=lora,
                suffix=suffix,
            )

            # 6. Save job to DB
            from uuid import uuid4

            job_id = uuid4()
            async with get_db_context() as db:
                job = NurseryTrainingJob(
                    id=job_id,
                    user_id=UUID(str(context.user_id)),
                    dataset_id=UUID(dataset_id),
                    provider="together",
                    provider_job_id=job_info.get("job_id"),
                    base_model=base_model,
                    output_name=job_info.get("output_name"),
                    status="running",
                    progress=0.0,
                    config={
                        "n_epochs": n_epochs,
                        "learning_rate": learning_rate,
                        "lora": lora,
                        "suffix": suffix,
                        "file_id": file_id,
                    },
                    cost_estimate=estimate.get("estimated_cost_usd"),
                    agent_id=context.agent_id,
                    started_at=datetime.utcnow(),
                )
                db.add(job)
                await db.commit()

            # 7. Fire background polling task
            asyncio.create_task(
                auto_complete_training_job(str(job_id), str(context.user_id))
            )

            return ToolResult(
                success=True,
                result={
                    "job_id": str(job_id),
                    "status": "running",
                    "estimated_cost": estimate.get("estimated_cost_usd"),
                    "base_model": base_model,
                    "message": f"Training job started on Together.ai. Fine-tuning {base_model} with {num_examples} examples for {n_epochs} epochs.",
                },
            )

        except Exception as e:
            logger.exception("Nursery train error")
            return ToolResult(success=False, error=f"Failed to start training: {str(e)}")


class NurseryJobStatusTool(BaseTool):
    """Check the status of a training job."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="nursery_job_status",
            description="""Check the status of a Training Forge job.

Returns job status, progress, cost, and output model info.
If no job_id is given, returns the latest job.

Use to:
- Monitor training progress
- Check if a job completed or failed
- Get the output model name after training""",
            category=ToolCategory.NURSERY,
            input_schema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Training job ID (optional - returns latest if omitted)",
                    },
                },
                "required": [],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        job_id = params.get("job_id")

        try:
            from app.models.nursery import NurseryTrainingJob
            from app.database import get_db_context
            from sqlalchemy import select

            async with get_db_context() as db:
                if job_id:
                    result = await db.execute(
                        select(NurseryTrainingJob).where(
                            NurseryTrainingJob.id == UUID(job_id),
                            NurseryTrainingJob.user_id == UUID(str(context.user_id)),
                        )
                    )
                else:
                    result = await db.execute(
                        select(NurseryTrainingJob)
                        .where(NurseryTrainingJob.user_id == UUID(str(context.user_id)))
                        .order_by(NurseryTrainingJob.created_at.desc())
                        .limit(1)
                    )

                job = result.scalar_one_or_none()

            if not job:
                return ToolResult(
                    success=False,
                    error="No training job found" if job_id else "No training jobs yet",
                )

            return ToolResult(
                success=True,
                result={
                    "id": str(job.id),
                    "status": job.status,
                    "progress": job.progress,
                    "base_model": job.base_model,
                    "provider": job.provider,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "cost_estimate": job.cost_estimate,
                    "error_message": job.error_message,
                    "output_name": job.output_name,
                },
            )

        except Exception as e:
            logger.exception("Nursery job status error")
            return ToolResult(success=False, error=f"Failed to get job status: {str(e)}")


class NurseryListJobsTool(BaseTool):
    """List training jobs."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="nursery_list_jobs",
            description="""List your Training Forge jobs.

Shows all training jobs with status, model, progress, and timestamps.
Optionally filter by status (pending, running, completed, failed).

Use to:
- See all training history
- Find completed models
- Check for running or failed jobs""",
            category=ToolCategory.NURSERY,
            input_schema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "description": "Filter by status: pending, running, completed, failed (optional)",
                        "enum": ["pending", "running", "completed", "failed"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default: 10)",
                        "default": 10,
                    },
                },
                "required": [],
            },
            requires_auth=True,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        if not context.user_id:
            return ToolResult(success=False, error="Authentication required")

        status_filter = params.get("status_filter")
        limit = min(params.get("limit", 10), 50)

        try:
            from app.models.nursery import NurseryTrainingJob, NurseryDataset
            from app.database import get_db_context
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            async with get_db_context() as db:
                query = (
                    select(NurseryTrainingJob)
                    .options(selectinload(NurseryTrainingJob.dataset))
                    .where(NurseryTrainingJob.user_id == UUID(str(context.user_id)))
                )

                if status_filter:
                    query = query.where(NurseryTrainingJob.status == status_filter)

                query = query.order_by(NurseryTrainingJob.created_at.desc()).limit(limit)

                result = await db.execute(query)
                jobs = result.scalars().all()

            return ToolResult(
                success=True,
                result={
                    "count": len(jobs),
                    "jobs": [
                        {
                            "id": str(j.id),
                            "dataset_name": j.dataset.name if j.dataset else "unknown",
                            "base_model": j.base_model,
                            "status": j.status,
                            "progress": j.progress,
                            "created_at": j.created_at.isoformat() if j.created_at else None,
                        }
                        for j in jobs
                    ],
                },
            )

        except Exception as e:
            logger.exception("Nursery list jobs error")
            return ToolResult(success=False, error=f"Failed to list jobs: {str(e)}")


# Register tools
registry.register(NurseryGenerateDataTool())
registry.register(NurseryExtractDataTool())
registry.register(NurseryListDatasetsTool())
registry.register(NurseryEstimateCostTool())
registry.register(NurseryTrainTool())
registry.register(NurseryJobStatusTool())
registry.register(NurseryListJobsTool())
