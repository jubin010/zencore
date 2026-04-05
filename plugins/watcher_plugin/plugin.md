# watcher_plugin

插件目录监听 — 自动更新插件注册表

## 工具

### scan_plugins
扫描 plugins/ 目录，报告当前状态。
- 返回：插件目录数、每个插件的大小和修改时间

### update_plugins_md
更新 plugins.md 注册表。
- `force`（可选）：是否强制更新，默认 false（智能对比）
- 智能体添加新插件后自动调用此工具
- 人类开发者添加插件后也需调用此工具生效
