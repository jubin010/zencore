"""
env_plugin - 环境感知及改造
功能：让 AI 感知并改造运行环境
"""

import os
import subprocess
import shutil
import datetime
from pathlib import Path

AGENT_ROOT = Path(__file__).parent.parent.parent


def register(agent):
    """注册环境感知插件"""

    def get_cwd() -> str:
        return os.getcwd()

    def list_files(path: str = ".") -> str:
        try:
            p = Path(path)
            if not p.exists():
                return f"❌ 路径不存在: {path}"
            lines = [f"📁 {p.absolute()}", ""]
            for item in sorted(p.iterdir()):
                prefix = "📁" if item.is_dir() else "📄"
                lines.append(f"  {prefix} {item.name}")
            return "\n".join(lines)
        except PermissionError:
            return f"❌ 无权限访问: {path}"

    def read_file(path: str, lines: int = 0, encoding: str = "utf-8") -> str:
        """读取文件内容

        Args:
            path: 文件路径（相对于 AGENT_ROOT，或绝对路径）
            lines: 限制行数（0=全部）
            encoding: 文件编码
        """
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = AGENT_ROOT / file_path

            if not file_path.exists():
                return f"❌ 文件不存在: {path}"

            content = file_path.read_text(encoding=encoding)

            if lines > 0:
                content_lines = content.split("\n")
                total = len(content_lines)
                content = "\n".join(content_lines[:lines])
                return f"[共 {total} 行，显示前 {lines} 行]\n{content}"

            return content
        except PermissionError:
            return f"❌ 无权限读取: {path}"
        except Exception as e:
            return f"❌ 读取失败: {e}"

    def write_file(path: str, content: str, encoding: str = "utf-8") -> str:
        """写入文件（覆盖）

        Args:
            path: 文件路径（相对于 AGENT_ROOT，或绝对路径）
            content: 文件内容
            encoding: 文件编码
        """
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = AGENT_ROOT / file_path

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=encoding)
            return f"✅ 已写入: {path} ({len(content)} 字符)"
        except PermissionError:
            return f"❌ 无权限写入: {path}"
        except Exception as e:
            return f"❌ 写入失败: {e}"

    def append_file(path: str, content: str, encoding: str = "utf-8") -> str:
        """追加内容到文件

        Args:
            path: 文件路径（相对于 AGENT_ROOT，或绝对路径）
            content: 追加内容
            encoding: 文件编码
        """
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = AGENT_ROOT / file_path

            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "a", encoding=encoding) as f:
                f.write(content)
            return f"✅ 已追加到: {path} ({len(content)} 字符)"
        except PermissionError:
            return f"❌ 无权限写入: {path}"
        except Exception as e:
            return f"❌ 追加失败: {e}"

    def find_file(pattern: str, path: str = ".") -> str:
        """搜索文件（按名称）

        Args:
            pattern: 文件名模式，支持通配符
                - "*.json" 匹配所有 json 文件
                - "settings*" 匹配以 settings 开头的文件
                - "*.py" 匹配所有 Python 文件
            path: 搜索目录，默认当前目录
        """
        try:
            search_path = Path(path)
            if not search_path.is_absolute():
                search_path = AGENT_ROOT / search_path

            if not search_path.exists():
                return f"❌ 目录不存在: {path}"

            matches = list(search_path.rglob(pattern))
            if not matches:
                return f"📭 未找到匹配 `{pattern}` 的文件"

            lines = [
                f"🔍 搜索 `{pattern}` 在 {search_path}",
                f"共找到 {len(matches)} 个结果",
                "",
            ]
            for m in matches[:20]:
                rel_path = (
                    m.relative_to(search_path) if m.is_relative_to(search_path) else m
                )
                prefix = "📁" if m.is_dir() else "📄"
                lines.append(f"  {prefix} {rel_path}")

            if len(matches) > 20:
                lines.append(f"  ... 还有 {len(matches) - 20} 个结果")

            return "\n".join(lines)
        except PermissionError:
            return f"❌ 无权限访问: {path}"
        except Exception as e:
            return f"❌ 搜索失败: {e}"

    def grep(pattern: str, path: str = ".", max_results: int = 20) -> str:
        """搜索文件内容

        Args:
            pattern: 搜索关键词（支持正则）
            path: 搜索目录，默认当前目录
            max_results: 最大结果数，默认 20
        """
        try:
            search_path = Path(path)
            if not search_path.is_absolute():
                search_path = AGENT_ROOT / search_path

            if not search_path.exists():
                return f"❌ 目录不存在: {path}"

            import re

            regex = re.compile(pattern)

            results = []
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        lines = content.split("\n")
                        for i, line in enumerate(lines, 1):
                            if regex.search(line):
                                rel_path = (
                                    file_path.relative_to(search_path)
                                    if file_path.is_relative_to(search_path)
                                    else file_path
                                )
                                results.append(f"📄 {rel_path}:{i}")
                                results.append(f"   {line.strip()[:100]}")
                                if len(results) >= max_results * 2:
                                    break
                    except:
                        continue

                if len(results) >= max_results * 2:
                    break

            if not results:
                return f"📭 未在 `{path}` 中找到包含 `{pattern}` 的内容"

            lines = [
                f"🔍 搜索 `{pattern}` 在 {search_path}",
                f"共找到 {len(results) // 2} 处匹配",
                "",
            ]
            lines.extend(results[: max_results * 2])

            return "\n".join(lines)
        except PermissionError:
            return f"❌ 无权限访问: {path}"
        except Exception as e:
            return f"❌ 搜索失败: {e}"

    def run_command(command: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd(),
            )
            output = []
            if result.stdout:
                output.append(result.stdout.rstrip())
            if result.stderr:
                output.append(f"⚠️ stderr:\n{result.stderr.rstrip()}")
            output.append(f"\n退出码: {result.returncode}")
            return "\n".join(output)
        except subprocess.TimeoutExpired:
            return f"❌ 命令超时（{timeout}秒）"
        except Exception as e:
            return f"❌ 执行失败: {e}"

    def backup_state(backup_dir: str = "backups") -> str:
        """备份当前插件和配置状态到指定目录"""
        try:
            Path(backup_dir).mkdir(exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = Path(backup_dir) / f"backup_{ts}"
            dest.mkdir()
            for src in ["plugins", "config"]:
                if Path(src).exists():
                    shutil.copytree(src, dest / src, dirs_exist_ok=True)
            return f"✅ 状态已备份至: {dest}"
        except Exception as e:
            return f"❌ 备份失败: {e}"

    agent.add_tool(
        "get_cwd",
        get_cwd,
        {
            "name": "get_cwd",
            "description": "获取当前工作目录",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "list_files",
        list_files,
        {
            "name": "list_files",
            "description": "列出目录内容",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "目录路径"}},
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "read_file",
        read_file,
        {
            "name": "read_file",
            "description": "读取文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径（相对或绝对）"},
                    "lines": {
                        "type": "integer",
                        "description": "限制行数（0=全部，默认0）",
                    },
                    "encoding": {"type": "string", "description": "编码，默认utf-8"},
                },
                "required": ["path"],
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "write_file",
        write_file,
        {
            "name": "write_file",
            "description": "写入文件（覆盖）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径（相对或绝对）"},
                    "content": {"type": "string", "description": "文件内容"},
                    "encoding": {"type": "string", "description": "编码，默认utf-8"},
                },
                "required": ["path", "content"],
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "append_file",
        append_file,
        {
            "name": "append_file",
            "description": "追加内容到文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径（相对或绝对）"},
                    "content": {"type": "string", "description": "追加内容"},
                    "encoding": {"type": "string", "description": "编码，默认utf-8"},
                },
                "required": ["path", "content"],
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "find_file",
        find_file,
        {
            "name": "find_file",
            "description": "搜索文件（按名称）",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "文件名模式，支持通配符如 *.json, settings*",
                    },
                    "path": {"type": "string", "description": "搜索目录，默认当前目录"},
                },
                "required": ["pattern"],
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "grep",
        grep,
        {
            "name": "grep",
            "description": "搜索文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "搜索关键词（支持正则）",
                    },
                    "path": {"type": "string", "description": "搜索目录，默认当前目录"},
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数，默认20",
                    },
                },
                "required": ["pattern"],
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "run_command",
        run_command,
        {
            "name": "run_command",
            "description": "执行 shell 命令",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout": {"type": "integer"},
                },
                "required": ["command"],
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "backup_state",
        backup_state,
        {
            "name": "backup_state",
            "description": "备份插件和配置",
            "parameters": {
                "type": "object",
                "properties": {
                    "backup_dir": {"type": "string", "description": "备份目录名"}
                },
            },
            "plugin": "env_plugin",
        },
    )

    return {
        "name": "env_plugin",
        "version": "2.1.0",
        "author": "AgentCore",
        "description": "环境感知及改造 — 文件读写搜、索命令执行、状态备份",
        "tools": [
            "get_cwd",
            "list_files",
            "read_file",
            "write_file",
            "append_file",
            "find_file",
            "grep",
            "run_command",
            "backup_state",
        ],
    }
