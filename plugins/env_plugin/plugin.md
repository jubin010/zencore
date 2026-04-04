# env_plugin

## 描述
环境感知 — 让 AI 感知运行环境，支持文件操作和命令执行

## 触发词
当前目录、文件、命令、环境变量、执行

## 工具
| 工具 | 参数 | 描述 |
|------|------|------|
| get_cwd | 无 | 获取当前工作目录 |
| list_files | path: str | 列出目录内容 |
| get_env | key: str | 获取环境变量 |
| run_command | command: str, timeout: int | 执行 shell 命令 |
| read_file | path: str, max_lines: int | 读取文件内容 |
| write_file | path: str, content: str | 写入文件（覆盖） |
| append_file | path: str, content: str | 追加内容到文件 |

## 使用示例
```
get_cwd() → "/home/user/project"
list_files(path=".") → 列出当前目录
run_command(command="ls -la") → 执行命令
read_file(path="config.json") → 读取文件
```
