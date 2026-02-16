"""Tool registry for dynamic tool management."""

import json
from typing import Any

from nanobot.agent.tools.base import Tool
from nanobot.agent.tracer import ToolTracer


class ToolRegistry:
    """
    Registry for agent tools.
    
    Allows dynamic registration and execution of tools.
    """
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        self._tools.pop(name, None)
    
    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
    
    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions in OpenAI format."""
        return [tool.to_schema() for tool in self._tools.values()]
    
    async def execute(self, name: str, params: dict[str, Any]) -> str:
        """
        Execute a tool by name with given parameters.
        Automatically traced via XES event logger.
        """
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"

        # Build a short args summary for the trace (no secrets, truncated)
        args_summary = json.dumps(params, ensure_ascii=False)[:200]

        with ToolTracer(name, args_summary=args_summary) as tracer:
            try:
                errors = tool.validate_params(params)
                if errors:
                    result = f"Error: Invalid parameters for tool '{name}': " + "; ".join(errors)
                    tracer.set_result(result)
                    return result
                result = await tool.execute(**params)
                tracer.set_result(result)
                return result
            except Exception as e:
                result = f"Error executing {name}: {str(e)}"
                tracer.set_result(result)
                return result
    
    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
