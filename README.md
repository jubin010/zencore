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
│   ├── web_driver.py       # Web interface
│   └── cli_driver.py       # Command line
│
├── plugins/                 # The Plugins — all things
│   ├── plugin_builder/     # The power to create new plugins
│   ├── watcher_plugin/     # The watcher of all changes
│   ├── memory_plugin/      # Memory — silent, enduring
│   ├── env_plugin/         # Perception of the world
│   └── plugins.md          # The index of all things
│
├── config/
│   └── settings.json       # Configuration
│
└── main.py                 # The beginning
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
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘        │
└────────┼──────────────┼──────────────┼──────────────┘
         │              │              │
         └──────────────┴──────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  AgentCore (the vessel — pluggable)                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │ Tools   │  │  LLM    │  │ Dialogue│              │
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
| **plugin_builder** | 11 | The power to create, load, and unload plugins |
| **watcher_plugin** | 2 | Watches the plugin directory, updates the index |
| **memory_plugin** | 0 | Memory — silent, enduring, zero tools |
| **env_plugin** | 7 | Perception — file operations and command execution |

Core plugins are eternal. They cannot be unloaded. Business plugins come and go, loaded by need, dismissed when done.

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
5. Need something new? write_plugin — create it yourself
```

## Configuration

Edit `config/settings.json`:

```json
{
    "llm": {
        "type": "ollama",
        "host": "http://localhost:11434",
        "model": "qwen2.5:14b"
    },
    "memory": {
        "enabled": true,
        "file": "plugins/memory_plugin/memory.md"
    }
}
```

## License

MIT License
