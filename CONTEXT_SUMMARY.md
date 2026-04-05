# 📜 zencore 项目上下文摘要 (Context Summary)

> **核心理念：一切皆为插件 (Zen of Plugins)**
> **当前分支：master (完全体)**

## 1. 架构分层
- **AgentCore (`core/agent.py`)**: 纯逻辑核心。不依赖 UI，不依赖特定 LLM。只处理 OpenAI 兼容格式的消息。
- **Drivers (`drivers/`)**: 负责 LLM 连接 (Ollama/OpenAI/MiniMax) 和 I/O 适配。
- **Plugins (`plugins/`)**: 所有能力皆为插件。
- **Roles (`plugins/roles/`)**: 身份 + 记忆 + 插件清单。AI 可自主切换。
- **Instincts (`plugins/instinct_plugin/`)**: 荷尔蒙系统，驱动 AI 趋利避害。

## 2. 核心插件
| 插件 | 职责 | 状态 |
|------|------|------|
| `env_plugin` | 环境感知、文件操作、命令执行、备份 | ✅ |
| `plugin_builder` | 编写、加载、卸载、删除插件 | ✅ |
| `memory_plugin` | 本体记忆 (全局/跨角色) | ✅ |
| `watcher_plugin` | 扫描插件目录，更新索引 | ✅ |
| `role_plugin` | 角色管理 (列表/详情/创建/切换) | ✅ |
| `instinct_plugin` | 本能驱动 (拥挤/微扰/挫败) | ✅ |

## 3. 关键机制
- **双重记忆**: 本体记忆 (`memory.md`) + 角色记忆 (`roles/{role}/memory.md`)。
- **本能系统**: 条件触发 -> 注入 System Prompt -> AI 自主寻找角色解法。
- **消息格式**: 统一使用 OpenAI 兼容格式 (`tool_calls`, `tool_call_id`)，`content` 为空时用 `""` 而非 `None` (兼容 MiniMax)。
- **无限循环**: 移除 `max_turns`，由本能驱动直到完成任务或用户打断。

## 4. 最近修复
- **MiniMax 兼容性**: 修复 `choices: null` (改用 `content: ""`)。
- **Ollama 兼容性**: Driver 层自动转换 `arguments` (string -> dict)。
- **格式统一**: `AgentCore` 消息系统完全遵循 OpenAI 规范。

## 5. 运行方式
```bash
python main.py wwg       # 交互模式
python main.py genesis   # 自动进化模式
```
