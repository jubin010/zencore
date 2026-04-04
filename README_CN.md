# 🤖 zencore — 可插拔 AI 智能体

> **核心理念：一切皆为插件**
>
> zencore 是一个完全解耦的 AI 智能体核心，所有能力通过插件提供，AI 可自我编写、加载、卸载插件。

## 📁 项目结构

```
zencore/
├── core/                    # AI 智能体核心
│   └── agent.py            # AgentCore 主类
│
├── drivers/                 # 外壳驱动层
│   ├── web_driver.py       # PyWebIO Web 驱动
│   └── cli_driver.py       # 命令行驱动
│
├── plugins/                 # 插件层
│   ├── plugin_builder/     # 插件构建器 — AI 编写插件的能力
│   ├── watcher_plugin/     # 监听插件 — 自动更新插件索引
│   ├── memory_plugin/      # 记忆 — AI 的持久化记忆
│   ├── env_plugin/         # 环境感知 — 文件操作与命令执行
│   └── plugins.md          # 插件索引（自动生成）
│
├── config/
│   └── settings.json       # 配置文件
│
└── main.py                 # 主入口
```

## 🚀 快速开始

### CLI 模式

```bash
python main.py cli
```

### Web 模式

```bash
pip install pywebio
python main.py web
```

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│  外壳驱动层（可替换）                                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐        │
│  │ Web 驱动  │  │ CLI 驱动  │  │ API 驱动  │  ...   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘        │
└────────┼──────────────┼──────────────┼──────────────┘
         │              │              │
         └──────────────┴──────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  AgentCore（AI 智能体核心 — 可插拔）                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │ 工具调度 │  │ LLM 交互│  │ 对话管理 │              │
│  └─────────┘  └─────────┘  └─────────┘              │
└───────────────────────────┬─────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│  插件层（一切皆为插件）                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │环境感知 │  │插件构建 │  │   记忆   │  ...         │
│  └─────────┘  └─────────┘  └─────────┘              │
└─────────────────────────────────────────────────────┘
```

## 🔌 核心插件

| 插件 | 工具数 | 作用 |
|------|--------|------|
| **plugin_builder** | 11 | 编写、加载、卸载、删除插件 |
| **watcher_plugin** | 2 | 扫描插件目录，自动更新索引 |
| **memory_plugin** | 0 | 记忆的存在（纯存在，零工具） |
| **env_plugin** | 7 | 环境感知、文件操作、命令执行 |

核心插件永久保留，不可卸载。业务插件按需加载，用完即走。

## 📝 创建插件

每个插件是一个独立目录：

```
plugins/
├── my_plugin/
│   ├── __init__.py    # 插件代码（必须有 register 函数）
│   └── plugin.md      # 工具说明文档
```

```python
# plugins/my_plugin/__init__.py

def register(agent):
    """注册插件到 AgentCore"""

    def my_tool(param: str) -> str:
        """工具函数"""
        return f"结果: {param}"

    agent.add_tool("my_tool", my_tool, {
        "name": "my_tool",
        "description": "工具描述",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "参数描述"}
            },
            "required": ["param"]
        },
        "plugin": "my_plugin"
    })

    return {
        "name": "my_plugin",
        "version": "1.0.0",
        "author": "作者名",
        "description": "插件描述",
        "tools": ["my_tool"]
    }
```

## 🧠 AI 工作流

```
1. 查看 plugins.md 索引 → 了解可用插件
2. 用 get_plugin_info 读取 plugin.md 详情
3. 按需 load_plugin 加载
4. 用完 unload_plugin 卸载
5. 遇到没有的工具 → write_plugin 自主编写
```

## ⚙️ 配置

编辑 `config/settings.json`:

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

## 📜 许可证

MIT License
