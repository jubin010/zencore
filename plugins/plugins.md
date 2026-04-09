# 插件索引

> AI 自主决策工作流：
> 1. 查看本索引了解可用插件和工具
> 2. 用 `get_plugin_info` 读取目标插件的 plugin.md 详情
> 3. 按需 `load_plugin` 加载后直接使用工具

## `env_plugin/` — 环境感知及改造
**工具**: `get_cwd`, `list_files`, `read_file`, `write_file`, `append_file`, `find_file`, `grep`, `run_command`, `backup_state`

## `instinct_plugin/` — 本能
**工具**: （本能插件，无直接工具）

## `memory_plugin/` — 本体记忆
**工具**: `read_global_memory`, `write_global_memory`, `append_global_memory`, `list_l2_cache`, `list_persistent_memory`, `heat_memory`, `promote_memory`, `delete_from_l2`, `delete_from_persistent`, `write_persistent_memory`

## `plugin_builder/` — 插件构建器
**工具**: `write_plugin`, `load_plugin`, `unload_plugin`, `reload_plugins`, `list_plugins`, `get_plugin_template`, `get_plugin_info`, `get_plugin_readme`, `get_available_tools`, `validate_code`, `delete_plugin`

## `role_plugin/` — 角色
**工具**: `list_roles`, `get_role_info`, `create_role`, `switch_role`

## `watcher_plugin/` — 插件目录监听
**工具**: `update_plugins_md`, `scan_plugins`

---
*最后更新: 2026-04-09 20:40:20*
