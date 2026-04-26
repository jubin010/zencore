# memory_plugin

本体记忆 — L2 缓存区（本能管理）+ 持久区（Librarian 管理）

## 记忆层次架构

| 层级 | 位置 | 管理器 | 说明 |
|------|------|--------|------|
| **L1 Cache** | conversation_history | AI 自动 | 当前上下文 |
| **L2 Cache** | memory.md 的 L2 缓存区 | 本能自动 | 归档区，hits 追踪访问频率 |
| **Disk** | memory.md 的持久区 | Librarian 手动 | 真正持久的重要记忆 |

## 基础工具（读写）

### read_global_memory
读取全局记忆（包含 L2 和持久区）。无参数。

### write_global_memory
覆盖写入全局记忆。
- `content`（必填）：完整的全局记忆内容（Markdown 格式）

### append_global_memory
追加一行到全局记忆。
- `line`（必填）：要追加的内容

### archive_to_l2
手动归档指定对话条目到 L2（秘书筛选后使用，不做语义压缩）。
- `indices`（必填）：要归档的对话索引列表，如 `[3, 4, 5]`
- **特点**：文本内容保留原始，仅代码块压缩为 `[lang代码块]`
- **用途**：秘书审视后，建议归档的条目由此工具归档

## L2 缓存区工具（Librarian 使用）

### list_l2_cache
列出 L2 缓存区的所有条目及其访问次数。
- 返回：索引、日期、hits、摘要
- **每次检索记忆都会使该条目的 hits +1（升温）**

### list_persistent_memory
列出持久记忆区的所有条目。

### heat_memory
将 L2 缓存区指定索引的条目 hits +1。
- `index`（必填）：L2 条目索引
- **调用时机**：当 Librarian 检索某段记忆时调用此工具，使其升温

### promote_memory
将 L2 缓存区指定索引的条目晋升到持久区（永久保存）。
- `index`（必填）：L2 条目索引
- **晋升标准**：hits >= 3 或 age > 7天 且 hits > 0

### delete_from_l2
从 L2 缓存区删除指定索引的条目。
- `index`（必填）：L2 条目索引

### delete_from_persistent
从持久记忆区删除指定索引的条目。
- `index`（必填）：持久区条目索引

### write_persistent_memory
手动写入持久记忆（由 Librarian 整理后的内容）。
- `content`（必填）：要持久化的内容

## Librarian 工作流

1. `list_l2_cache` — 查看 L2 缓存条目
2. `heat_memory(index)` — 检索某条目时调用，使其升温
3. `promote_memory(index)` — 高频记忆晋升到持久区
4. `delete_from_l2(index)` 或 `delete_from_persistent(index)` — 删除过时记忆

## 本能注入（自动）

以下内容会通过本能系统自动注入系统提示：

| 本能名 | 触发条件 | 注入内容 |
|--------|----------|----------|
| global_lessons | 始终 | 全局教训 |
| global_wins | 始终 | 全局成功经验 |
| role_lessons | 有角色时 | 当前角色专属教训 |
| role_wins | 有角色时 | 当前角色专属成功经验 |
| user_profile | 始终 | 用户特征（对话中感知到用户偏好后，用 append_file 追加到 user_profile.md） |
