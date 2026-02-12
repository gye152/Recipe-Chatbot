"""Tool router — dispatches OpenAI tool calls to service functions."""

from __future__ import annotations

import json
import logging

from app.services import recipe_provider

logger = logging.getLogger(__name__)

# Registry of available tools and the functions they map to
_TOOL_REGISTRY: dict[str, callable] = {
    "search_recipes": recipe_provider.search_recipes,
}


async def execute_tool_call(name: str, arguments: str) -> str:
    """
    Execute a tool call by name with the given JSON-encoded arguments.
    Returns the result as a JSON string to feed back to the model.
    """
    handler = _TOOL_REGISTRY.get(name)
    if handler is None:
        logger.error("Unknown tool requested: %s", name)
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        args = json.loads(arguments)
        logger.info("Executing tool '%s' with args: %s", name, args)
        result = await handler(**args)

        # Convert pydantic models to dicts
        if isinstance(result, list):
            serialized = [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in result
            ]
        elif hasattr(result, "model_dump"):
            serialized = result.model_dump()
        else:
            serialized = result

        return json.dumps(serialized, ensure_ascii=False)

    except Exception as exc:
        logger.exception("Tool execution failed for '%s'", name)
        return json.dumps({"error": str(exc)})
