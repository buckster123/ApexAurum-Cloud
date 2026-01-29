"""
Tier 15: Nursery Tools - The Data Garden

Training data generation and dataset management.
"From data, new minds are born."
"""

import logging
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


# Register tools
registry.register(NurseryGenerateDataTool())
registry.register(NurseryExtractDataTool())
registry.register(NurseryListDatasetsTool())
