# memory_plugin

本体记忆 — 全局、跨角色、长期有效的记忆操作

## 工具

### read_global_memory
读取全局记忆。无参数。
- 返回：完整的记忆内容（Markdown 格式）
- 如果记忆为空，返回"（全局记忆为空）"

### write_global_memory
覆盖写入全局记忆。
- `content`（必填）：完整的全局记忆内容（Markdown 格式）
- 注意：这是**覆盖写入**，会替换全部内容
- 适用场景：更新用户画像、项目全局配置等需要整体更新的场景

### append_global_memory
追加一行到全局记忆。
- `line`（必填）：要追加的内容
- 注意：只追加一行，不会替换已有内容
- 适用场景：记录跨角色的长期经验、补充信息

## 记忆方法论

- **write_global_memory** = 重写整本笔记
- **append_global_memory** = 在笔记末尾加一行
- 不确定用哪个时：如果只是补充信息，用 append；如果要重新整理，用 write
