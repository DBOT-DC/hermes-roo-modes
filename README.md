# Hermes Roo Modes

Roo-Code style mode system for Hermes Agent — tool gating, role-based personas, and multi-agent task orchestration.

## Overview

Hermes Roo Modes brings Roo Code's powerful mode system to Hermes Agent. Modes control which tools the agent can use, what persona it adopts, and provide file path constraints for specialized workflows.

## Built-in Modes

| Mode | Description | Tool Groups |
|------|-------------|-------------|
| `code` | General coding assistant | read, edit, command, mcp |
| `architect` | Design, planning, specifications | read, edit, mcp (markdown/config only) |
| `ask` | Answer questions only | read, mcp |
| `debug` | Debugging specialist | read, edit, command, mcp |
| `orchestrator` | Multi-agent task coordination | delegate_task only |

## Bundled Modes

Seven specialized YAML-based modes are included:

- **`devops`** — Infrastructure, CI/CD, Docker, Kubernetes
- **`docs-extractor`** — Extract documentation from source code
- **`documentation-writer`** — Write READMEs, API docs, guides
- **`merge-resolver`** — Git merge conflict resolution
- **`project-research`** — Technology research and comparison
- **`security-reviewer`** — Security vulnerability auditing
- **`skills-writer`** — Create Hermes Agent skills

## Tool Groups

Tools are organized into groups that modes can enable/disable:

- **`read`** — read_file, search_files, browser_*, web_search, web_extract, vision_analyze
- **`edit`** — write_file, patch, execute_code
- **`command`** — terminal, process
- **`mcp`** — All MCP tools (dynamic)

## Always Available Tools

These tools are available in ALL modes regardless of configuration:

- `switch_mode` — Change the current mode
- `delegate_task` — Spawn subagents
- `todo` — Task tracking
- `memory` — Memory operations
- `clarify` — Ask clarifying questions
- `session_search` — Search conversation history
- `skills_list`, `skill_view`, `skill_manage` — Skills management
- `cronjob` — Scheduled tasks
- `orchestrate` — Task planning in orchestrator mode

## Usage

### Switch Modes

```
You: /mode architect
Hermes: Switched to Architect mode. Tool groups: read, edit, mcp
```

### List Available Modes

```
You: /mode list
Hermes: Available Modes:
- code: Code ← active
- architect: Architect
- ask: Ask
- debug: Debug
- orchestrator: Orchestrator
...
```

### Use switch_mode Tool

```
You: Use architect mode to plan a new feature
Hermes: [uses architect mode automatically based on context]
```

## Custom Modes

Add custom modes by creating YAML files in `~/.hermes/modes/`:

```yaml
slug: my-custom-mode
name: My Custom Mode
role_definition: |
  You are a specialized assistant focused on...
when_to_use: |
  Use this mode when...
tool_groups: ['read', 'edit', 'mcp']
constraints:
  file_regex: '\.(py|js)$'
```

## Architecture

```
hermes_roo_modes/
├── modes.py              # Mode dataclass, built-in modes, YAML loading
├── task_hierarchy.py      # Task tree for orchestrator mode
├── orchestrator.py        # Task decomposition engine
├── hermesignore.py        # Gitignore-style file filtering
├── mode_tool.py           # switch_mode + orchestrate tools
└── bundled_modes/         # 7 YAML mode definitions
```

## Tool Gating

Mode-based tool gating works by:

1. `get_tool_definitions()` in `model_tools.py` filters tools based on active mode
2. `_refresh_tools_for_mode()` in `run_agent.py` refreshes tool list after mode switch
3. `pre_tool_call` hook blocks tool execution if mode doesn't allow it
4. Always-available tools bypass all gating

## Commands

| Command | Description |
|---------|-------------|
| `/mode [name]` | Switch to named mode |
| `/mode list` | List all available modes |
| `/mode info [name]` | Show details about a mode |

## Requirements

- Hermes Agent 0.10.0+
- PyYAML (for custom mode loading)
