# hermes-roo-modes

Roo Code modes for [Hermes Agent](https://github.com/nousresearch/hermes-agent) — 15 specialized modes with tool gating, orchestration, and HermesIgnore support.

Ported from [Roo Code](https://github.com/RooVetGit/Roo-Code) for VS Code.

## Features

- **15 modes** — All official Roo Code modes (5 built-in + 10 bundled YAML)
- **Tool gating** — Each mode restricts which tools are available (read/edit/mcp/command)
- **Orchestrator** — Auto-delegates subtasks to appropriate modes
- **HermesIgnore** — `.hermesignore` file support (like `.gitignore` for agent access)
- **Custom modes** — Add your own via `~/.hermes/modes/*.yaml` or project `.roomodes`
- **Context compression** — Sliding window context management

## Installation

```bash
hermes plugins install DBOT-DC/hermes-roo-modes --enable
```

## Modes

### Built-in (Python)

| Mode | Description | Tool Groups |
|------|-------------|-------------|
| `code` | Full coding with file edit, terminal, search | `read`, `edit`, `mcp`, `command` |
| `architect` | System design, architecture planning | `read`, `edit`, `mcp` |
| `ask` | Q&A only — no file modification | `read`, `mcp` |
| `debug` | Bug investigation and fixing | `read`, `edit`, `mcp`, `command` |
| `orchestrator` | Delegates subtasks to other modes | (managed — delegates to others) |

### Bundled (YAML)

| Mode | Source | Description |
|------|--------|-------------|
| `devops` | Roo Code | DevOps and deployment tasks |
| `docs-extractor` | Roo Code | Extract and organize documentation |
| `documentation-writer` | Roo Code | Write and update project docs |
| `merge-resolver` | Roo Code | Resolve merge conflicts |
| `project-research` | Roo Code | Research projects and technologies |
| `security-reviewer` | Roo Code | Security audit and review |
| `skills-writer` | Roo Code | Write Hermes skills |
| `jest-test-engineer` | Roo Code | Jest test writing and debugging |
| `mode-writer` | Roo Code | Create custom modes |
| `user-story-creator` | Roo Code | Write user stories |

## Usage

### Switch Modes

```
/mode code        # Switch to code mode
/mode architect   # Switch to architect mode
/mode ask         # Switch to ask mode
/mode list        # List all available modes
```

### Tool Gating

Each mode gates tools based on its `tool_groups`:

- **`read`** — `read_file`, `search_files`, `browser_snapshot`, `list_directory`
- **`edit`** — `write_file`, `patch`, `execute_code`, `terminal`
- **`mcp`** — All MCP tools
- **`command`** — `browser_navigate`, `browser_click`, `browser_type`, `browser_press`

### Orchestrator Workflow

```
/mode orchestrator
Plan a React dashboard with authentication →
  ├─ architect: Design system architecture
  ├─ code: Implement components
  ├─ code: Write tests
  └─ debug: Fix integration issues
```

### Custom Modes

Create `~/.hermes/modes/my-mode.yaml`:

```yaml
slug: my-mode
name: My Custom Mode
role_definition: |
  You are a specialist in...
tool_groups:
  - read
  - edit
  - mcp
```

Or add a `.roomodes` file in your project root (same format as Roo Code).

### HermesIgnore

Create `.hermesignore` in your project root:

```
# Ignore node_modules
node_modules/
# Ignore build artifacts
dist/
build/
# Ignore specific files
secrets.json
```

## MCP Integration

This plugin works alongside these recommended MCP servers:

### MiniMax Token Plan MCP
```bash
hermes mcp add minimax --command uvx --args "minimax-coding-plan-mcp" --args "-y" \
  --env MINIMAX_API_KEY=your_key --env MINIMAX_API_HOST=https://api.minimax.io
```
Tools: `web_search`, `understand_image`

### MiniMax Full MCP
```bash
hermes mcp add minimax-full --command uvx --args "minimax-mcp" \
  --env MINIMAX_API_KEY=your_key --env MINIMAX_API_HOST=https://api.minimax.io \
  --env MINIMAX_MCP_BASE_PATH=/path/to/output
```
Tools: `text_to_audio`, `list_voices`, `voice_clone`, `play_audio`, `voice_design`, `text_to_image`, `generate_video`, `query_video_generation`, `music_generation`

### Z.AI Vision MCP
```bash
hermes mcp add glm-vision --command node --args "/path/to/@z_ai/mcp-server/build/index.js" \
  --env Z_AI_API_KEY=your_key --env Z_AI_MODE=ZAI
```
Tools: `ui_to_artifact`, `extract_text_from_screenshot`, `diagnose_error_screenshot`, `understand_technical_diagram`, `analyze_data_visualization`, `ui_diff_check`, `analyze_image`, `analyze_video`

### Z.AI Web Search (HTTP)
```bash
hermes mcp add zai-web-search --url "https://api.z.ai/api/mcp/web_search_prime/mcp" \
  --header "Authorization: Bearer your_key"
```
Tools: `web_search_prime`

### Z.AI Web Reader (HTTP)
```bash
hermes mcp add zai-web-reader --url "https://api.z.ai/api/mcp/web_reader/mcp" \
  --header "Authorization: Bearer your_key"
```
Tools: `webReader`

### Z.AI Zread (HTTP)
```bash
hermes mcp add zai-zread --url "https://api.z.ai/api/mcp/zread/mcp" \
  --header "Authorization: Bearer your_key"
```
Tools: `search_doc`, `read_file`, `get_repo_structure`

## Provider Configuration

### MiniMax M2.7 (Primary)
```bash
hermes model  # Select "MiniMax (global endpoint)" → enter Token Plan API key
```
- API: `https://api.minimax.io/anthropic` (Anthropic-compatible)
- Model: `MiniMax-M2.7`

### GLM-5-Turbo (Fallback)
- API: `https://api.z.ai/api/coding/paas/v4`
- Model: `GLM-5-Turbo`
- Set as `fallback_model` in `config.yaml`

## Development

```bash
cd /tmp/hermes-roo-modes
git clone https://github.com/DBOT-DC/hermes-roo-modes.git
# Edit modes in hermes_roo_modes/bundled_modes/
# Test: python3 -c "from hermes_roo_modes.modes import list_modes; print(list_modes())"
```

## License

MIT
