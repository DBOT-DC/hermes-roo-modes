#!/usr/bin/env python3
"""
Hermes Roo Modes Plugin — Roo-Code style mode system for Hermes Agent.

This plugin provides:
- 5 built-in modes: code, architect, ask, debug, orchestrator
- 7 bundled YAML modes: devops, docs-extractor, documentation-writer,
  merge-resolver, project-research, security-reviewer, skills-writer
- switch_mode tool for in-conversation mode switching
- orchestrate tool for task planning in orchestrator mode
- /mode slash command for CLI/gateway use
- Mode-based tool gating via monkey-patching of core modules

Monkey-patching strategy:
- Add ALWAYS_AVAILABLE_TOOLS and TOOL_GROUPS to toolsets.py
- Patch model_tools.get_tool_definitions() to add mode gating
- Patch run_agent._invoke_tool() to handle switch_mode + orchestrate
- Patch run_agent._refresh_tools_for_mode() to use plugin's mode system
- Register /mode command in hermes_cli/commands.py
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Plugin directory and module injection
# ---------------------------------------------------------------------------

_PLUGIN_DIR = Path(__file__).parent
_HERMES_AGENT_ROOT = Path(os.environ.get(
    "HERMES_AGENT_ROOT",
    str(Path.home() / ".hermes" / "hermes-agent")
))


def _inject_plugin_modules():
    """Inject hermes_roo_modes into sys.modules so hermes-agent can import it."""
    plugin_package = "hermes_roo_modes"
    plugin_path = _PLUGIN_DIR / "hermes_roo_modes"

    # Add plugin directory to sys.path for hermes_roo_modes import
    if str(_PLUGIN_DIR) not in sys.path:
        sys.path.insert(0, str(_PLUGIN_DIR))

    # Create package entries in sys.modules
    if plugin_package not in sys.modules:
        import types
        pkg = types.ModuleType(plugin_package)
        pkg.__path__ = [str(plugin_path)]
        pkg.__file__ = str(plugin_path / "__init__.py")
        sys.modules[plugin_package] = pkg

    # Register submodules
    submodules = [
        "modes",
        "task_hierarchy",
        "orchestrator",
        "hermesignore",
        "mode_tool",
    ]
    for submod in submodules:
        full_name = f"{plugin_package}.{submod}"
        if full_name not in sys.modules:
            mod_path = plugin_path / f"{submod}.py"
            if mod_path.exists():
                spec = importlib.util.spec_from_file_location(full_name, mod_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[full_name] = mod
                    spec.loader.exec_module(mod)


# ---------------------------------------------------------------------------
# Robust patch helper
# ---------------------------------------------------------------------------

def _apply_patch(name: str, target_obj: Any, attr: str, new_attr: Any,
                 fallback: Optional[Any] = None) -> bool:
    """Apply a monkey-patch robustly, logging errors but never crashing."""
    try:
        original = getattr(target_obj, attr, None)
        if original is None and fallback is not None:
            setattr(target_obj, attr, new_attr)
            logger.info("Patched %s.%s (was None, set to fallback)", name, attr)
            return True

        # Store original for reference
        setattr(target_obj, f"_orig_{attr}", original)
        setattr(target_obj, attr, new_attr)
        logger.info("Patched %s.%s", name, attr)
        return True
    except Exception as e:
        logger.warning("Failed to patch %s.%s: %s", name, attr, e)
        return False


# ---------------------------------------------------------------------------
# Tool registration helpers
# ---------------------------------------------------------------------------

def _register_switch_mode_tool(ctx) -> bool:
    """Register switch_mode tool with the context."""
    try:
        tool_schema = {
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

        def switch_mode_handler(args: dict) -> str:
            import json
            mode_slug = args.get("mode", "")
            if not mode_slug:
                return json.dumps({"success": False, "error": "No mode specified"})

            try:
                from hermes_roo_modes.modes import set_active_mode, list_modes
                mode = set_active_mode(mode_slug)
                if mode is None:
                    return json.dumps({"success": True, "message": "Mode cleared"})
                all_modes = list_modes()
                return json.dumps({
                    "success": True,
                    "mode": mode.name,
                    "slug": mode.slug,
                    "tool_groups": mode.tool_groups,
                    "available_tools": len(mode.get_allowed_tools()),
                    "all_modes": list(all_modes.keys()),
                })
            except ValueError as e:
                return json.dumps({"success": False, "error": str(e)})
            except Exception as e:
                return json.dumps({"success": False, "error": f"Failed to switch mode: {e}"})

        ctx.register_tool(
            name="switch_mode",
            handler=switch_mode_handler,
            schema=tool_schema,
            description="Switch the agent's operating mode",
            toolset="agent",
        )
        logger.info("Registered switch_mode tool")
        return True
    except Exception as e:
        logger.warning("Failed to register switch_mode tool: %s", e)
        return False


def _register_orchestrate_tool(ctx) -> bool:
    """Register orchestrate tool with the context."""
    try:
        tool_schema = {
            "type": "function",
            "function": {
                "name": "orchestrate",
                "description": (
                    "Plan a complex task by breaking it into subtasks. "
                    "Used in orchestrator mode for multi-agent coordination."
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

        def orchestrate_handler(args: dict) -> str:
            import json
            task_description = args.get("task", "")
            if not task_description:
                return json.dumps({"success": False, "error": "No task description"})

            try:
                from hermes_roo_modes.orchestrator import OrchestratorEngine
                engine = OrchestratorEngine()
                plan = engine.plan_task(task_description)
                return json.dumps({
                    "success": True,
                    "planned_tasks": len(plan),
                    "tasks": [{"description": p.description, "mode": p.mode} for p in plan],
                })
            except Exception as e:
                return json.dumps({"success": False, "error": f"Failed to orchestrate: {e}"})

        ctx.register_tool(
            name="orchestrate",
            handler=orchestrate_handler,
            schema=tool_schema,
            description="Plan a complex task by breaking it into subtasks",
            toolset="agent",
        )
        logger.info("Registered orchestrate tool")
        return True
    except Exception as e:
        logger.warning("Failed to register orchestrate tool: %s", e)
        return False


# ---------------------------------------------------------------------------
# Mode command handler
# ---------------------------------------------------------------------------

def _handle_mode_command(ctx, args: str) -> str:
    """Handle /mode slash command."""
    try:
        from hermes_roo_modes.modes import (
            get_active_mode, set_active_mode, list_modes, get_all_modes
        )

        args = args.strip()
        if not args or args == "list":
            active = get_active_mode()
            modes = get_all_modes()
            lines = ["**Available Modes:**"]
            for m in modes:
                marker = " ← active" if active and m.slug == active.slug else ""
                lines.append(f"- **{m.slug}**: {m.name}{marker}")
            lines.append("")
            lines.append(f"Current mode: **{(active.name if active else 'none')}**")
            return "\n".join(lines)

        # Check for specific mode info
        if args.startswith("info "):
            mode_slug = args[5:].strip()
            from hermes_roo_modes.modes import get_mode
            mode = get_mode(mode_slug)
            if not mode:
                return f"Unknown mode: {mode_slug}"
            return (
                f"**{mode.name}** (`{mode.slug}`)\n"
                f"{mode.role_definition}\n\n"
                f"**When to use:** {mode.when_to_use}\n"
                f"**Tool groups:** {', '.join(mode.tool_groups)}\n"
                f"**Source:** {mode.source}"
            )

        # Set mode
        try:
            mode = set_active_mode(args)
            return f"Switched to **{mode.name}** mode. Tool groups: {', '.join(mode.tool_groups)}"
        except ValueError as e:
            return f"Error: {e}"
    except Exception as e:
        logger.error("Error handling /mode command: %s", e)
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Monkey-patch: toolsets.py — add ALWAYS_AVAILABLE_TOOLS and TOOL_GROUPS
# ---------------------------------------------------------------------------

def _patch_toolsets():
    """Add mode-based tool groups to toolsets.py."""
    try:
        import toolsets
        if hasattr(toolsets, 'ALWAYS_AVAILABLE_TOOLS'):
            logger.debug("toolsets already has ALWAYS_AVAILABLE_TOOLS, skipping patch")
            return

        toolsets.ALWAYS_AVAILABLE_TOOLS: set = {
            "switch_mode", "delegate_task", "todo", "memory", "clarify",
            "session_search", "cronjob", "send_message",
            "skills_list", "skill_view", "skill_manage",
            "orchestrate",
        }

        toolsets.TOOL_GROUPS: dict = {
            "read": {
                "read_file", "search_files",
                "browser_navigate", "browser_snapshot", "browser_click",
                "browser_type", "browser_scroll", "browser_back",
                "browser_press", "browser_get_images", "browser_vision", "browser_console",
                "web_search", "web_extract",
                "vision_analyze",
            },
            "edit": {
                "write_file", "patch", "execute_code",
            },
            "command": {
                "terminal", "process",
            },
            "mcp": set(),
        }

        # Also update _HERMES_CORE_TOOLS to include switch_mode and orchestrate
        _orig_core = getattr(toolsets, '_HERMES_CORE_TOOLS', [])
        if "switch_mode" not in _orig_core:
            toolsets._HERMES_CORE_TOOLS = _orig_core + ["switch_mode", "orchestrate"]

        logger.info("Patched toolsets.py: added ALWAYS_AVAILABLE_TOOLS, TOOL_GROUPS")
    except Exception as e:
        logger.warning("Failed to patch toolsets.py: %s", e)


# ---------------------------------------------------------------------------
# Monkey-patch: model_tools.get_tool_definitions() — add mode gating
# ---------------------------------------------------------------------------

def _patch_model_tools():
    """Patch get_tool_definitions to support active_mode parameter."""
    try:
        import model_tools

        # Check if already patched
        if hasattr(model_tools, '_roo_modes_patched'):
            logger.debug("model_tools already patched, skipping")
            return

        orig_func = model_tools.get_tool_definitions

        def patched_get_tool_definitions(
            enabled_toolsets=None,
            disabled_toolsets=None,
            quiet_mode=False,
            active_mode=None,
        ):
            """Patched get_tool_definitions with mode-based tool gating."""
            # If active_mode is provided by the plugin's modes module, use it
            if active_mode is None:
                try:
                    from hermes_roo_modes.modes import get_active_mode
                    active_mode = get_active_mode()
                except Exception:
                    pass  # Not yet initialized, proceed without mode gating

            return orig_func(
                enabled_toolsets=enabled_toolsets,
                disabled_toolsets=disabled_toolsets,
                quiet_mode=quiet_mode,
                active_mode=active_mode,
            )

        patched_get_tool_definitions._orig = orig_func
        patched_get_tool_definitions._roo_modes_patched = True
        model_tools.get_tool_definitions = patched_get_tool_definitions

        # Also patch _AGENT_LOOP_TOOLS to include switch_mode and orchestrate
        if hasattr(model_tools, '_AGENT_LOOP_TOOLS'):
            agent_tools = set(model_tools._AGENT_LOOP_TOOLS)
            agent_tools.add("switch_mode")
            agent_tools.add("orchestrate")
            model_tools._AGENT_LOOP_TOOLS = frozenset(agent_tools)

        logger.info("Patched model_tools.get_tool_definitions for mode gating")
    except Exception as e:
        logger.warning("Failed to patch model_tools: %s", e)


# ---------------------------------------------------------------------------
# Monkey-patch: run_agent — handle switch_mode in _invoke_tool
# ---------------------------------------------------------------------------

def _patch_run_agent():
    """Patch run_agent._invoke_tool() to handle switch_mode and orchestrate."""
    try:
        import run_agent

        if hasattr(run_agent, '_roo_modes_patched'):
            logger.debug("run_agent already patched, skipping")
            return

        orig_invoke = getattr(run_agent.AIAgent, '_invoke_tool', None)
        if orig_invoke is None:
            logger.debug("_invoke_tool not found in run_agent.AIAgent, skipping patch")
            return

        def patched_invoke_tool(
            self,
            function_name: str,
            function_args: dict,
            effective_task_id: str,
            tool_call_id=None,
        ):
            """Patched _invoke_tool that handles switch_mode and orchestrate."""
            if function_name == "switch_mode":
                import json
                try:
                    from hermes_roo_modes.modes import set_active_mode, get_active_mode
                    mode_slug = function_args.get("mode", "")
                    if mode_slug:
                        mode = set_active_mode(mode_slug)
                    else:
                        mode = get_active_mode()

                    result = json.dumps({
                        "success": True,
                        "mode": mode.name if mode else "none",
                        "slug": mode.slug if mode else "",
                        "tool_groups": mode.tool_groups if mode else [],
                    })
                except Exception as e:
                    result = json.dumps({"success": False, "error": str(e)})

                # Refresh tool list after mode switch
                try:
                    self._refresh_tools_for_mode()
                except Exception:
                    pass
                return result

            elif function_name == "orchestrate":
                import json
                try:
                    from hermes_roo_modes.orchestrator import OrchestratorEngine
                    engine = OrchestratorEngine()
                    engine.set_agent(self)
                    task = function_args.get("task", function_args.get("description", ""))
                    if task:
                        plan = engine.plan_task(task)
                        result = json.dumps({
                            "success": True,
                            "planned_tasks": len(plan),
                            "tasks": [
                                {"description": p.description, "mode": p.mode}
                                for p in plan
                            ],
                        })
                    else:
                        result = json.dumps({"success": False, "error": "No task provided"})
                except Exception as e:
                    result = json.dumps({"success": False, "error": str(e)})
                return result

            # Call original for all other tools
            return orig_invoke(
                self, function_name, function_args,
                effective_task_id, tool_call_id=tool_call_id
            )

        # Store original
        patched_invoke_tool._orig = orig_invoke
        patched_invoke_tool._roo_modes_patched = True
        run_agent.AIAgent._invoke_tool = patched_invoke_tool

        # Patch _refresh_tools_for_mode to use plugin's modes
        orig_refresh = getattr(run_agent.AIAgent, '_refresh_tools_for_mode', None)
        if orig_refresh:
            def patched_refresh(self):
                try:
                    from hermes_roo_modes.modes import get_active_mode
                    from model_tools import get_tool_definitions
                    active = get_active_mode()
                    self.tools = get_tool_definitions(
                        enabled_toolsets=self._enabled_toolsets,
                        disabled_toolsets=self._disabled_toolsets,
                        quiet_mode=self.quiet_mode,
                        active_mode=active,
                    )
                    self.valid_tool_names = {t["function"]["name"] for t in (self.tools or [])}
                except Exception as e:
                    logger.warning("Failed to refresh tools for mode: %s", e)
                    # Fallback to original
                    return orig_refresh(self)

            patched_refresh._orig = orig_refresh
            run_agent.AIAgent._refresh_tools_for_mode = patched_refresh

        logger.info("Patched run_agent.AIAgent._invoke_tool for switch_mode/orchestrate")
    except Exception as e:
        logger.warning("Failed to patch run_agent: %s", e)


# ---------------------------------------------------------------------------
# Monkey-patch: run_agent sequential/concurrent execution paths
# ---------------------------------------------------------------------------

def _patch_run_agent_tool_execution():
    """Patch tool execution paths in run_agent for switch_mode display."""
    try:
        import run_agent

        if hasattr(run_agent, '_roo_modes_execution_patched'):
            return

        # The sequential execution path calls _invoke_tool which we already patched
        # For the concurrent path, we need to ensure switch_mode results are handled

        # Find and patch _execute_tool_calls_sequential if it references switch_mode
        orig_seq = getattr(run_agent.AIAgent, '_execute_tool_calls_sequential', None)
        if orig_seq and 'switch_mode' not in str(orig_seq):
            # The original already handles switch_mode via _invoke_tool
            pass

        # Find and patch _execute_tool_calls_concurrent
        orig_conc = getattr(run_agent.AIAgent, '_execute_tool_calls_concurrent', None)
        if orig_conc:
            # The concurrent path uses _invoke_tool for each tool call,
            # so our patch above should cover it
            pass

        run_agent._roo_modes_execution_patched = True
        logger.info("Patched run_agent tool execution paths")
    except Exception as e:
        logger.warning("Failed to patch run_agent execution: %s", e)


# ---------------------------------------------------------------------------
# Register /mode command
# ---------------------------------------------------------------------------

def _register_mode_command(ctx) -> bool:
    """Register /mode slash command with the context."""
    try:
        ctx.register_command(
            name="mode",
            handler=_handle_mode_command,
            description="Switch or list agent modes (code, architect, ask, debug, orchestrator)",
        )
        logger.info("Registered /mode command")
        return True
    except Exception as e:
        logger.warning("Failed to register /mode command: %s", e)
        return False


# ---------------------------------------------------------------------------
# Patch: hermes_cli/commands.py — ensure /mode command is registered
# ---------------------------------------------------------------------------

def _patch_commands():
    """Ensure /mode command is in COMMAND_REGISTRY."""
    try:
        from hermes_cli import commands

        # Check if /mode is already registered
        already_registered = any(
            cmd.name == "mode" for cmd in commands.COMMAND_REGISTRY
        )
        if already_registered:
            logger.debug("/mode command already in COMMAND_REGISTRY")
            return

        # Add /mode command definition
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class CommandDef:
            name: str
            description: str
            category: str
            aliases: tuple = ()
            args_hint: str = ""
            subcommands: tuple = ()
            cli_only: bool = False
            gateway_only: bool = False
            gateway_config_gate = None

        new_cmd = CommandDef(
            name="mode",
            description="Switch or list agent modes (code, architect, ask, debug, orchestrator)",
            category="Configuration",
            args_hint="[mode-name|list]",
        )
        commands.COMMAND_REGISTRY.append(new_cmd)

        # Rebuild the lookup if the function exists
        if hasattr(commands, "_build_command_lookup"):
            try:
                commands._COMMAND_LOOKUP = commands._build_command_lookup()
            except Exception:
                pass

        logger.info("Added /mode command to COMMAND_REGISTRY")
    except Exception as e:
        logger.warning("Failed to patch hermes_cli/commands.py: %s", e)


# ---------------------------------------------------------------------------
# Patch: context_compressor.py — inject mode role_definition into system prompt
# ---------------------------------------------------------------------------

def _patch_context_compressor():
    """Patch context_compressor to include mode role_definition."""
    try:
        from agent import context_compressor

        if hasattr(context_compressor, '_roo_modes_patched'):
            return

        orig_build = getattr(context_compressor.ContextCompressor, 'build_system_prompt', None)
        if orig_build is None:
            orig_build = getattr(context_compressor.ContextCompressor, 'compress', None)

        def patched_build(self, *args, **kwargs):
            result = orig_build(self, *args, **kwargs) if orig_build else ""

            # Try to add mode role definition to system prompt
            try:
                from hermes_roo_modes.modes import get_active_mode
                mode = get_active_mode()
                if mode and mode.role_definition:
                    # Prepend role definition to system prompt
                    role_block = f"\n\n## Mode: {mode.name}\n{mode.role_definition}\n"
                    if isinstance(result, str):
                        result = role_block + result
                    elif isinstance(result, list):
                        result = [role_block] + result
            except Exception:
                pass  # Mode system not available

            return result

        if orig_build:
            patched_build._orig = orig_build
            patched_build._roo_modes_patched = True
            context_compressor.ContextCompressor.build_system_prompt = patched_build

        logger.info("Patched context_compressor for mode role_definition injection")
    except Exception as e:
        logger.warning("Failed to patch context_compressor: %s", e)


# ---------------------------------------------------------------------------
# Register hook handlers for tool gating at runtime
# ---------------------------------------------------------------------------

def _register_mode_tool_hooks():
    """Register on_tool_call hook for mode-based tool gating."""
    try:
        from hermes_cli import plugins

        def mode_tool_gate(tool_name: str, args: dict = None, task_id: str = "",
                          session_id: str = "", tool_call_id: str = "") -> Optional[dict]:
            """Hook that gates tools based on active mode.

            Returns {"action": "block", "message": "..."} to block, or None to allow.
            """
            try:
                from hermes_roo_modes.modes import get_active_mode
                mode = get_active_mode()
                if mode is None:
                    return None  # No mode active, allow all

                # Always allow switch_mode
                if tool_name == "switch_mode":
                    return None

                # Check if tool is allowed in current mode
                if not mode.is_tool_allowed(tool_name):
                    allowed = ', '.join(sorted(mode.tool_groups))
                    return {
                        "action": "block",
                        "message": (
                            f"Tool '{tool_name}' is not available in {mode.name} mode. "
                            f"Available tool groups: {allowed}. "
                            f"Use switch_mode to change modes."
                        ),
                    }
            except Exception:
                pass  # Fail open — allow tool
            return None

        pm = plugins.get_plugin_manager()
        pm._hooks.setdefault("pre_tool_call", []).append(mode_tool_gate)
        logger.info("Registered mode_tool_gate hook")
    except Exception as e:
        logger.warning("Failed to register mode tool hooks: %s", e)


# ---------------------------------------------------------------------------
# Main register() function — called by Hermes plugin system
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Register the hermes-roo-modes plugin with the Hermes Agent.

    This function is called by the Hermes plugin system when the plugin
    is loaded. It:
    1. Injects hermes_roo_modes modules into sys.modules
    2. Registers switch_mode and orchestrate tools
    3. Registers /mode slash command
    4. Applies monkey-patches to core modules for mode gating
    """
    logger.info("Registering hermes-roo-modes plugin v1.0.0")

    # Step 1: Inject plugin modules so hermes-agent can import them
    _inject_plugin_modules()

    # Step 2: Initialize modes (load bundled + user modes)
    try:
        from hermes_roo_modes.modes import reload_modes
        reload_modes()
        logger.info("Loaded %d modes", len(importlib.import_module("hermes_roo_modes.modes")._ALL_MODES))
    except Exception as e:
        logger.warning("Failed to reload modes: %s", e)

    # Step 3: Register tools
    _register_switch_mode_tool(ctx)
    _register_orchestrate_tool(ctx)

    # Step 4: Register /mode command
    _register_mode_command(ctx)

    # Step 5: Apply monkey-patches to core modules
    _patch_toolsets()
    _patch_model_tools()
    _patch_run_agent()
    _patch_run_agent_tool_execution()
    _patch_commands()
    _patch_context_compressor()

    # Step 6: Register tool gating hooks
    _register_mode_tool_hooks()

    logger.info("hermes-roo-modes plugin registered successfully")
