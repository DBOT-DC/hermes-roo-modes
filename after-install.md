# After Installation — Hermes Roo Modes

## Verification

After installing the plugin, verify it's working:

```bash
hermes plugins list
# You should see: hermes-roo-modes v1.0.0

hermes /mode list
# Lists all available modes
```

## Quick Start

1. **Try switching modes:**
   ```
   /mode architect
   /mode debug
   /mode code
   ```

2. **Use mode-aware commands:**
   ```
   /mode architect
   Plan a new microservices architecture for my project

   /mode debug
   Investigate why my login is failing

   /mode orchestrator
   Coordinate building a full-stack app with frontend, backend, and tests
   ```

3. **Create custom modes:**
   ```bash
   mkdir -p ~/.hermes/modes
   # Create my-mode.yaml in ~/.hermes/modes/
   ```

## Configuration

### Custom Mode Location

Custom modes are loaded from `~/.hermes/modes/`. Each mode is a YAML file:

```yaml
slug: my-mode
name: My Custom Mode
role_definition: |
  You are a specialized developer focused on...
when_to_use: |
  Use when working on specific tasks...
tool_groups: ['read', 'edit', 'command', 'mcp']
constraints:
  file_regex: '\.(py|js|ts)$'
```

### Mode Constraints

The `architect` mode includes a file constraint that limits edits to documentation and config files:

```python
constraints: {"file_regex": r"\.(md|yaml|yml|json|toml|txt)$"}
```

This prevents accidental code edits during architecture planning.

## Troubleshooting

### Plugin not loading

Check the plugin is in the right location:
```bash
ls ~/.hermes/hermes-agent/plugins/hermes-roo-modes/
```

### Modes not switching

Check the mode system initialized:
```python
from hermes_roo_modes.modes import list_modes
print(list_modes().keys())
```

### Tool gating not working

Verify tool groups are loaded:
```python
from toolsets import ALWAYS_AVAILABLE_TOOLS, TOOL_GROUPS
print("Always:", ALWAYS_AVAILABLE_TOOLS)
print("Groups:", list(TOOL_GROUPS.keys()))
```

## Integration with Existing Tools

The mode system integrates with:

- **delegate_task** — Subagents inherit parent mode unless overridden
- **context_compressor** — Mode role_definition injected into system prompt
- **hermesignore** — .hermesignore files for path-based restrictions
- **Skills** — Skills work within mode constraints

## Removing the Plugin

To disable temporarily:
```bash
mv ~/.hermes/hermes-agent/plugins/hermes-roo-modes ~/.hermes/hermes-agent/plugins/hermes-roo-modes.disabled
```

To remove completely:
```bash
rm -rf ~/.hermes/hermes-agent/plugins/hermes-roo-modes
```
