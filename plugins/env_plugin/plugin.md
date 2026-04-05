# env_plugin

环境感知 — 让 AI 感知运行环境

## 工具

### get_cwd
获取当前工作目录。无参数。

### list_files
列出指定目录下的文件和子目录。
- `path`（可选）：目录路径，默认为当前目录 `.`
- 返回：带图标的目录列表（📁 目录，📄 文件）

### run_command
执行 shell 命令。
- `command`（必填）：要执行的 shell 命令
- `timeout`（可选）：超时秒数，默认 30 秒
- 返回：stdout + stderr（如有）+ 退出码
- 注意：命令在当前工作目录下执行

### backup_state
备份当前插件和配置状态。
- `backup_dir`（可选）：备份目录名，默认 `backups`
- 备份内容：`plugins/` 和 `config/` 目录
- 返回：备份路径
