# env_plugin

环境感知及改造 — 让 AI 感知并改造运行环境

## 工具

### get_cwd
获取当前工作目录。
- 参数：无
- 返回：当前目录路径

### list_files
列出目录内容。
- `path`（可选）：目录路径，默认为当前目录 `.`
- 返回：带图标的目录列表（📁 目录，📄 文件）
- 示例：`list_files(path="config")`

### find_file
按文件名搜索文件（递归遍历子目录）。
- `pattern`（必填）：文件名模式，支持通配符
  - `*.json` - 所有 json 文件
  - `settings*` - 以 settings 开头的文件
  - `*.py` - 所有 Python 文件
- `path`（可选）：搜索目录，默认当前目录
- 示例：`find_file(pattern="*.json")`

### grep
在文件中搜索内容（递归遍历子目录）。
- `pattern`（必填）：搜索关键词，支持正则表达式
- `path`（可选）：搜索目录，默认当前目录
- `max_results`（可选）：最大结果数，默认 20
- 示例：`grep(pattern="TODO", path="plugins")`

### read_file
读取文件内容。
- `path`（必填）：文件路径
- `lines`（可选）：限制行数，0=全部，默认 0
- `encoding`（可选）：文件编码，默认 utf-8
- 示例：`read_file(path="config/settings.json", lines=50)`

### write_file
写入文件（覆盖）。会**自动创建父目录**。
- `path`（必填）：文件路径
- `content`（必填）：文件内容
- `encoding`（可选）：文件编码，默认 utf-8
- 注意：会覆盖原文件，写入前建议先用 `read_file` 确认

### append_file
追加内容到文件。会**自动创建父目录**。
- `path`（必填）：文件路径
- `content`（必填）：追加内容（会自动加换行）
- `encoding`（可选）：文件编码，默认 utf-8

### run_command
执行 shell 命令。
- `command`（必填）：要执行的 shell 命令
- `timeout`（可选）：超时秒数，默认 30 秒
- 返回：stdout + stderr（如有）+ 退出码
- 常用命令：
  - `ls -la` - 详细列出目录
  - `cat file` - 查看文件
  - `grep "pattern" file` - 搜索内容
  - `mkdir -p dir` - 创建目录

### backup_state
备份当前插件和配置状态。
- `backup_dir`（可选）：备份目录名，默认 `backups`
- 备份内容：`plugins/` 和 `config/` 目录
- 返回：备份路径

## 组合用法

**快速定位配置文件**：
```
1. find_file(pattern="settings.json")
2. read_file(path="找到的路径")
```

**搜索代码中的关键字**：
```
1. grep(pattern="TODO", path="plugins")
2. read_file(path="找到的文件", lines=10)
```

**读取并修改**：
```
1. read_file(path="config/settings.json")
2. write_file(path="config/settings.json", content=新内容)
```
