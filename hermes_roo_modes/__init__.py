"""Hermes Roo Modes — Roo-Code style mode system for Hermes Agent."""

from hermes_roo_modes.modes import (
    Mode,
    get_active_mode,
    set_active_mode,
    get_mode,
    list_modes,
    get_all_modes,
    reload_modes,
)

from hermes_roo_modes.task_hierarchy import (
    TaskNode,
    TaskHierarchyManager,
    get_manager,
    reset_manager,
)

from hermes_roo_modes.orchestrator import (
    OrchestratorEngine,
    SubtaskPlan,
)

__all__ = [
    # modes
    "Mode",
    "get_active_mode",
    "set_active_mode",
    "get_mode",
    "list_modes",
    "get_all_modes",
    "reload_modes",
    # task_hierarchy
    "TaskNode",
    "TaskHierarchyManager",
    "get_manager",
    "reset_manager",
    # orchestrator
    "OrchestratorEngine",
    "SubtaskPlan",
]
