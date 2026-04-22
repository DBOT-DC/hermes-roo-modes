#!/usr/bin/env python3
"""
Switch Mode Tool for Hermes Agent.

Allows the agent to switch between modes (code, architect, ask, debug, orchestrator).
Always available regardless of current mode.
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to register with registry, but don't fail if registry isn't ready yet
try:
    from tools.registry import registry
    _HAS_REGISTRY = True
except ImportError:
    _HAS_REGISTRY = False


def switch_mode_handler(args: dict) -> str:
    """Handle switch_mode tool calls."""
    mode_slug = args.get("mode", "")
    if not mode_slug:
        return json.dumps({"success": False, "error": "No mode specified"})

    try:
        # Import from the plugin's own modes module
        from hermes_roo_modes.modes import set_active_mode, list_modes, get_all_modes
        mode = set_active_mode(mode_slug)
        if mode is None:
            return json.dumps({"success": True, "message": "Mode cleared"})

        all_modes = list_modes()
        tool_count = len(mode.get_allowed_tools())
        return json.dumps({
            "success": True,
            "mode": mode.name,
            "slug": mode.slug,
            "tool_groups": mode.tool_groups,
            "available_tools": tool_count,
            "all_modes": list(all_modes.keys()),
        })
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
    except Exception as e:
        logger.error("Failed to switch mode: %s", e)
        return json.dumps({"success": False, "error": f"Failed to switch mode: {e}"})


def orchestrate_handler(args: dict) -> str:
    """Handle orchestrate tool calls for orchestrator mode task planning."""
    try:
        from hermes_roo_modes.orchestrator import OrchestratorEngine
        from hermes_roo_modes.task_hierarchy import get_manager

        engine = OrchestratorEngine()
        task_description = args.get("task", args.get("description", ""))
        if not task_description:
            return json.dumps({"success": False, "error": "No task description provided"})

        # Plan the task
        plan = engine.plan_task(task_description)
        return json.dumps({
            "success": True,
            "planned_tasks": len(plan),
            "tasks": [{"description": p.description, "mode": p.mode} for p in plan],
        })
    except Exception as e:
        logger.error("Failed to orchestrate: %s", e)
        return json.dumps({"success": False, "error": f"Failed to orchestrate: {e}"})


_SWITCH_MODE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "switch_mode",
        "description": (
            "Switch the agent's operating mode. Each mode has different tool access "
            "and persona. Available modes: code, architect, ask, debug, orchestrator. "
            "Use 'list' as the mode argument to see all available modes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "The mode slug to switch to (e.g., 'code', 'architect', 'ask', 'debug', 'orchestrator'). Use 'list' to see all available modes.",
                },
            },
            "required": ["mode"],
        },
    },
}

_ORCHESTRATE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "orchestrate",
        "description": (
            "Plan a complex task by breaking it into subtasks using the orchestrator engine. "
            "Returns a structured plan with subtasks and inferred modes. "
            "Use this when coordinating complex multi-step work in orchestrator mode."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The task description to break into subtasks.",
                },
            },
            "required": ["task"],
        },
    },
}

# Register tools if registry is available
if _HAS_REGISTRY:
    registry.register(
        name="switch_mode",
        toolset="agent",
        schema=_SWITCH_MODE_SCHEMA,
        handler=switch_mode_handler,
        description=(
            "Switch the agent's operating mode. Each mode has different tool access "
            "and persona. Available modes: code, architect, ask, debug, orchestrator."
        ),
        emoji="🔄",
    )
    registry.register(
        name="orchestrate",
        toolset="agent",
        schema=_ORCHESTRATE_SCHEMA,
        handler=orchestrate_handler,
        description=(
            "Plan a complex task by breaking it into subtasks. "
            "Used in orchestrator mode for multi-agent coordination."
        ),
        emoji="🎭",
    )
