# hermes-roo-modes

Roo Code modes for [Hermes Agent](https://github.com/nousresearch/hermes-agent) — 15 specialized modes with tool gating, orchestration, and HermesIgnore support.

Ported from [Roo Code for VS Code](https://github.com/RooVetGit/Roo-Code) and enhanced with Hermes-native features.

## Installation

```bash
hermes plugins install DBOT-DC/hermes-roo-modes --enable
```

After install, restart Hermes. Verify with:

```bash
hermes plugins list
```

## Modes

### Built-in (5)

| Mode | Description | Tool Groups |
|------|-------------|-------------|
| 🏗️ Architect | Plan and design before implementation | read, edit (.md only), mcp |
| 💻 Code | Write, modify, and refactor code | read, edit, command, mcp |
| ❓ Ask | Get answers and explanations | read, mcp |
| 🪲 Debug | Diagnose and fix software issues | read, edit, command, mcp |
| 🪃 Orchestrator | Coordinate tasks across multiple modes | read (delegates work) |

### Bundled (10)

| Mode | Description | Tool Groups |
|------|-------------|-------------|
| ⚙️ DevOps Engineer | Docker, CI/CD, infrastructure | read, edit, command, mcp |
| 📚 Docs Extractor | Extract facts from codebase for docs teams | read, edit (restricted), command, mcp |
| 📝 Documentation Writer | Write polished documentation | read, edit, command, mcp |
| 🔀 Merge Resolver | Resolve merge conflicts using git history | read, edit, command, mcp |
| 🔬 Project Research | Technology evaluation and comparison | read, command, mcp |
| 🔒 Security Reviewer | Vulnerability detection and security audit | read, edit, command, mcp |
| 🛠️ Skills Writer | Create and maintain Hermes skills | read, edit, command, mcp |
| 🧪 Jest Test Engineer | JavaScript/TypeScript testing with Jest | read, edit, command, mcp |
| 🎭 Mode Writer | Design and create new Hermes modes | read, edit, command, mcp |
| 📋 User Story Creator | Agile user stories and acceptance criteria | read, edit, command, mcp |

## Usage

### Switch Modes

In any Hermes session:

```
/mode code
/mode architect
/mode debug
/mode ask
/mode orchestrator
```

Or use the `switch_mode` tool directly:

```
switch_mode("code")
switch_mode("architect")
```

### Check Current Mode

```
/mode
```

### List All Modes

```
/mode list
```

### Clear Mode (return to unrestricted)

```
/mode clear
```

## How Tool Gating Works

Each mode restricts which tools the agent can use:

- **read** — file reading, searching, web search
- **edit** — file writing, patching, terminal commands
- **command** — shell execution, process management
- **mcp** — MCP server tools (GitHub, Context7, etc.)

Example: In **Architect** mode, the agent can read files and edit only `.md` files — perfect for planning without accidentally modifying source code.

## Orchestrator Mode

The orchestrator plans complex tasks and delegates to other modes:

1. `/mode orchestrator` — enter orchestration mode
2. Describe your task
3. The orchestrator breaks it into subtasks, each assigned to the best mode
4. Subtasks execute in parallel where possible
5. Results are synthesized into a final deliverable

## Custom Modes

Create your own modes by adding YAML files to `~/.hermes/modes/`:

```yaml
slug: my-mode
name: "🚀 My Custom Mode"
role_definition: |
  You are a specialist in...
when_to_use: |
  Use this mode when...
tool_groups:
  - read
  - edit
custom_instructions: |
  Additional guidance...
source: custom
```

## HermesIgnore

Create a `.hermesignore` file in your project to exclude files from agent access:

```
# Ignore patterns
*.log
.env
dist/
```

## Requirements

- Hermes Agent v0.20+ with plugin support
- Python 3.10+

## License

MIT
