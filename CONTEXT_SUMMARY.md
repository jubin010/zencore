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
| 插件 | 职责 |
|------|------|
| `env_plugin` | 环境感知、文件操作、命令执行、备份 |
| `plugin_builder` | 编写、加载、卸载、删除插件 |
| `memory_plugin` | 本体记忆 — L2缓存区(本能管理) + 持久区(Librarian管理) |
| `watcher_plugin` | 扫描插件目录，更新索引 |
| `role_plugin` | 角色管理 (列表/详情/创建/切换) |
| `instinct_plugin` | 本能驱动 — 三层本能模型(感觉/反射/驱动) |

## 3. 记忆层次架构
**核心原则：用最宝贵的上下文窗口处理当前最需要的需求**

| 层级 | 位置 | 管理器 | 说明 |
|------|------|--------|------|
| **L1** | conversation_history | 本能自动 | 当前上下文 |
| **L2** | memory.md 的 L2 缓存区 | 本能遗忘(自动) | hits 追踪访问频率 |
| **Disk** | memory.md 的持久区 | Librarian(手动) | 永久重要记忆 |

## 4. 关键机制
- **本能系统**: 三层模型（感觉层/反射层/驱动层），反射自动处理 L2 Cache 管理
- **消息格式**: 统一使用 OpenAI 兼容格式 (`tool_calls`, `tool_call_id`)，`content` 为空时用 `""` 而非 `None` (兼容 MiniMax)
- **无限循环**: 移除 `max_turns`，由本能驱动直到完成任务或用户打断

## 5. 运行方式
```bash
python main.py wwg       # 交互模式
python main.py genesis   # 自动进化模式
```

## 6. Librarian 职责（L2 ↔ Disk 管理）
- `list_l2_cache`: 列出 L2 缓存条目及 hits
- `heat_memory`: 检索记忆时 hits +1（升温）
- `promote_memory`: 将高 hits 记忆晋升到持久区
- `delete_from_l2 / delete_from_persistent`: 删除记忆
