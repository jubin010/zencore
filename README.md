# 🤖 AgentCore - 可插拔AI智能体

> **核心理念：一切皆为插件**
> 
> AgentCore 是一个完全解耦的AI智能体核心，可以插入到任何符合DriverInterface的外壳驱动中。

## 📁 项目结构

```
agent_core/
├── core/                  # AI智能体核心
│   ├── __init__.py
│   ├── agent.py          # AgentCore主类
│   └── llm.py            # LLM模块
│
├── drivers/              # 外壳驱动层
│   ├── __init__.py
│   ├── web_driver.py     # PyWebIO Web驱动
│   └── cli_driver.py     # 命令行驱动
│
├── tools/                # 内置工具
│   ├── __init__.py
│   ├── file_tools.py     # 文件工具
│   └── bash_tools.py     # 执行工具
│
├── plugins/              # 业务插件层
│   ├── __init__.py
│   ├── hello_plugin.py   # 示例插件
│   └── calc_plugin.py    # 计算插件
│
├── config/
│   └── settings.json     # 配置文件
│
└── main.py               # 主入口
```

## 🚀 快速开始

### CLI模式

```bash
cd /CODE/agent_core
python main.py cli
```

### Web模式

```bash
cd /CODE/agent_core
pip install pywebio
python main.py web
```

## 🛠️ 内置工具

### 文件工具 (file_tools)

| 工具 | 功能 |
|------|------|
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件内容 |
| `glob_search` | 搜索匹配的文件 |
| `grep_search` | 在文件中搜索内容 |
| `get_cwd` | 获取当前工作目录 |

### 执行工具 (bash_tools)

| 工具 | 功能 |
|------|------|
| `bash` | 执行命令行命令 |
| `python_exec` | 执行Python代码 |
| `list_files` | 列出目录文件 |
| `get_env` | 获取环境变量 |

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│  外壳驱动层（可替换）                                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐        │
│  │ Web驱动   │  │ CLI驱动   │  │ API驱动   │  ...   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘        │
└────────┼──────────────┼──────────────┼──────────────┘
         │              │              │
         └──────────────┴──────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│  AgentCore（AI智能体核心 - 可插拔）                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │ 记忆模块 │  │ 工具调度 │  │ LLM交互 │              │
│  └─────────┘  └─────────┘  └─────────┘              │
└───────────────────────────┬─────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────┐
│  工具层                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │文件工具 │  │执行工具 │  │业务插件 │  ...          │
│  └─────────┘  └─────────┘  └─────────┘              │
└─────────────────────────────────────────────────────┘
```

## 🔌 创建新的外壳驱动

```python
from core.agent import DriverInterface, AgentCore

class MyDriver(DriverInterface):
    def send_message(self, content: str):
        print(content)
    
    def send_image(self, path: str):
        print(f"[图片: {path}]")
    
    def send_file(self, path: str):
        print(f"[文件: {path}]")
    
    def get_input(self, prompt: str = ""):
        return input(prompt)
    
    def show_loading(self, message: str = "处理中..."):
        print(f"⏳ {message}")
    
    def toast(self, message: str, duration: int = 3):
        print(f"📢 {message}")
    
    def set_title(self, title: str):
        pass

# 使用
driver = MyDriver()
agent = AgentCore(driver)
response = agent.chat("你好")
```

## 📝 创建新的插件

```python
# plugins/my_plugin.py

def register(agent):
    """注册工具到智能体"""
    agent.register_tool("my_tool", my_tool, {
        "name": "my_tool",
        "description": "我的工具",
        "version": "1.0.0"
    })


def my_tool(param: str) -> str:
    """工具函数"""
    return f"结果: {param}"
```

## ⚙️ 配置

编辑 `config/settings.json`:

```json
{
    "max_history": 50,
    "memory_file": "memory.json",
    "plugins_dir": "plugins",
    "llm": {
        "provider": "ollama",
        "model": "llama3.2",
        "base_url": "http://localhost:11434"
    }
}
```

## 📜 许可证

MIT License
