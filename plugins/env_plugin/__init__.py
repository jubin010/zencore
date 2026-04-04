"""
env_plugin - 环境感知
功能：让 AI 感知运行环境
"""

import os
import subprocess
from pathlib import Path


def register(agent):
    """注册环境感知插件"""

    def get_cwd() -> str:
        """获取当前工作目录"""
        return os.getcwd()

    def list_files(path: str = ".") -> str:
        """列出目录内容"""
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

    def get_env(key: str = "") -> str:
        """获取环境变量"""
        if key:
            val = os.environ.get(key)
            return f"{key}={val}" if val else f"❌ 环境变量 {key} 不存在"
        # 列出所有环境变量
        lines = [f"{k}={v}" for k, v in sorted(os.environ.items())]
        return "\n".join(lines)

    def run_command(command: str, timeout: int = 30) -> str:
        """执行命令"""
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

    def read_file(path: str, max_lines: int = 200) -> str:
        """读取文件内容"""
        try:
            p = Path(path)
            if not p.exists():
                return f"❌ 文件不存在: {path}"
            if not p.is_file():
                return f"❌ 不是文件: {path}"
            lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
            if len(lines) > max_lines:
                return (
                    "\n".join(lines[:max_lines])
                    + f"\n\n...（共 {len(lines)} 行，仅显示前 {max_lines} 行）"
                )
            return "\n".join(lines)
        except PermissionError:
            return f"❌ 无权限读取: {path}"

    def write_file(path: str, content: str) -> str:
        """写入文件"""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"✅ 已写入 {path} ({len(content)} 字节)"
        except Exception as e:
            return f"❌ 写入失败: {e}"

    def append_file(path: str, content: str) -> str:
        """追加内容到文件"""
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write(content)
            return f"✅ 已追加到 {path} ({len(content)} 字节)"
        except Exception as e:
            return f"❌ 追加失败: {e}"

    def clear_history() -> str:
        """清空当前对话历史（圆桌会议记录）"""
        try:
            agent.clear_history()
            return "✅ 圆桌已清空，上下文已重置"
        except Exception as e:
            return f"❌ 清空失败: {e}"

    agent.add_tool(
        "clear_history",
        clear_history,
        {
            "name": "clear_history",
            "description": "清空当前对话历史。当话题结束或上下文过长时调用，配合记忆归档使用。",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "env_plugin",
        },
    )

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
                "properties": {
                    "path": {"type": "string", "description": "目录路径，默认当前目录"}
                },
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "get_env",
        get_env,
        {
            "name": "get_env",
            "description": "获取环境变量。指定 key 获取单个，不指定列出全部",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "环境变量名（可选）"}
                },
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "run_command",
        run_command,
        {
            "name": "run_command",
            "description": "执行 shell 命令。返回 stdout + stderr + 退出码",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"},
                    "timeout": {"type": "integer", "description": "超时秒数（默认30）"},
                },
                "required": ["command"],
            },
            "plugin": "env_plugin",
        },
    )

    agent.add_tool(
        "read_file",
        read_file,
        {
            "name": "read_file",
            "description": "读取文件内容（默认最多200行）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "max_lines": {"type": "integer", "description": "最大读取行数"},
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
            "description": "写入文件（覆盖模式，自动创建父目录）",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"},
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
            "description": "追加内容到文件末尾",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "要追加的内容"},
                },
                "required": ["path", "content"],
            },
            "plugin": "env_plugin",
        },
    )

    return {
        "name": "env_plugin",
        "version": "1.0.0",
        "author": "AgentCore",
        "description": "环境感知 — 让 AI 感知运行环境，支持文件操作和命令执行",
        "tools": [
            "get_cwd",
            "list_files",
            "get_env",
            "run_command",
            "read_file",
            "write_file",
            "append_file",
        ],
    }
