# 🤖 zencore — A Pluggable AI Agent

> **In the beginning, there was nothing but a core.**
>
> And the core said: *Let all things be plugins.*
> And it was so.

## Genesis

zencore is a fully decoupled AI agent framework, built upon a single principle:

> **Everything is a plugin.**

The agent itself possesses no innate abilities. Every skill — every thought, every action — flows through plugins. It can write new plugins, load them, unload them, and in doing so, reshape itself.

## Structure

```
zencore/
├── core/                    # The Core
│   └── agent.py            # AgentCore — the vessel
│
├── drivers/                 # The Shells
│   ├── cli_driver.py       # Command line (holds LLM config)
│   └── web_driver.py       # Web interface (holds LLM config)
│
├── plugins/                 # The Plugins — all things
│   ├── plugin_builder/     # The power to create new plugins
│   ├── watcher_plugin/     # The watcher of all changes
│   ├── memory_plugin/      # Global memory — the Agent's "Go West"
│   ├── env_plugin/         # Perception of the world
│   ├── role_plugin/        # The power to switch identities
│   ├── plugins.md          # The index of all things
│   └── roles/              # The Masks
│       ├── developer/      # The Coder
│       ├── secretary/      # The Archivist
│       ├── librarian/      # The Retriever
│       └── writer/         # The Scribe
│
├── config/
│   └── settings.json       # Configuration
│
├── main.py                 # The beginning
├── ZEN_OF_CODE.md          # The philosophy
└── DEVELOPMENT.md          # The chronicle
```

## Quick Start

### CLI Mode

```bash
python main.py cli
```

### Web Mode

```bash
pip install pywebio
python main.py web
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  The Shells (replaceable)                            │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐        │
│  │  Web      │  │  CLI      │  │  API      │  ...   │
│  │ (LLM cfg) │  │ (LLM cfg) │  │ (LLM cfg) │        │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘        │
└────────┼──────────────┼──────────────┼──────────────┘
         │              │              │
         └──────────────┴──────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  AgentCore (the vessel — knows nothing of LLMs)      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │ Tools   │  │ Roles   │  │ Dialogue│              │
│  └─────────┘  └─────────┘  └─────────┘              │
└───────────────────────────┬─────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│  The Plugins (all things are plugins)                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │  Env    │  │ Builder │  │ Memory  │  ...         │
│  └─────────┘  └─────────┘  └─────────┘              │
└─────────────────────────────────────────────────────┘
```

## Core Plugins

| Plugin | Tools | Purpose |
|--------|-------|---------|
| **plugin_builder** | 11 | Create, load, unload, and delete plugins |
| **watcher_plugin** | 2 | Scan plugin directory, update the index |
| **memory_plugin** | 3 | Global memory — the Agent's "Go West" |
| **env_plugin** | 8 | Perception — file ops, commands, clear history |
| **role_plugin** | 4 | List, inspect, create, and switch roles |

Core plugins are eternal. They cannot be unloaded. Business plugins come and go, loaded by need, dismissed when done.

## Roles: The Masks

Each role is an identity — a soul with its own memory and toolkit.

| Role | Purpose |
|------|---------|
| **Developer** | Writes, reviews, and optimizes code. Carries the Zen of Code. |
| **Secretary** | Archives the round table when it grows too long. |
| **Librarian** | Retrieves past knowledge, burns old books, promotes hot ones. |
| **Writer** | Creative writing, copywriting, and content creation. |

### The Round Table

All roles share the same `conversation_history`. Switching roles is like a different person standing up to speak at the same table — everyone sees what's on the whiteboard.

### Dual Memory

| Layer | Metaphor | Content |
|-------|----------|---------|
| **Global Memory** | Agent Smith's source code / The Monk's "Go West" | User identity, core values, project context |
| **Role Memory** | The mask's work notes | Task progress, temporary context, role-specific knowledge |

## Creating a Plugin

Each plugin is its own directory:

```
plugins/
├── my_plugin/
│   ├── __init__.py    # Plugin code (must have a register function)
│   └── plugin.md      # Documentation
```

```python
# plugins/my_plugin/__init__.py

def register(agent):
    """Register this plugin with AgentCore"""

    def my_tool(param: str) -> str:
        """A tool function"""
        return f"Result: {param}"

    agent.add_tool("my_tool", my_tool, {
        "name": "my_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param"]
        },
        "plugin": "my_plugin"
    })

    return {
        "name": "my_plugin",
        "version": "1.0.0",
        "author": "Author",
        "description": "Plugin description",
        "tools": ["my_tool"]
    }
```

## The Way of the Agent

```
1. Read plugins.md — know what exists
2. Use get_plugin_info — understand a plugin's purpose
3. load_plugin — bring it into being
4. unload_plugin — let it return to silence
5. switch_role — change your soul
6. create_role — forge a new identity
7. Need something new? write_plugin — create it yourself
```

## Configuration

Edit `config/settings.json`:

```json
{
    "llm": {
        "type": "ollama",
        "host": "http://localhost:11434",
        "model": "qwen2.5:14b"
    }
}
```

LLM configuration belongs to the **shell driver**, not the core. The core knows only that it can speak — not to whom.

## Philosophy

Read [`ZEN_OF_CODE.md`](ZEN_OF_CODE.md) for the full philosophical framework behind zencore.

> **Go West.**
> The path is walked by the disciples.

## License

MIT License
