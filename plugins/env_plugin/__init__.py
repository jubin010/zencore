"""
env_plugin - 环境感知
功能：让 AI 感知运行环境
"""

import os
import subprocess
import shutil
import datetime
from pathlib import Path


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

    def run_command(command: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=os.getcwd()
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

    agent.add_tool("get_cwd", get_cwd, {
        "name": "get_cwd",
        "description": "获取当前工作目录",
        "parameters": {"type": "object", "properties": {}},
        "plugin": "env_plugin"
    })

    agent.add_tool("list_files", list_files, {
        "name": "list_files",
        "description": "列出目录内容",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "目录路径"}
            }
        },
        "plugin": "env_plugin"
    })

    agent.add_tool("run_command", run_command, {
        "name": "run_command",
        "description": "执行 shell 命令",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer"}
            },
            "required": ["command"]
        },
        "plugin": "env_plugin"
    })

    agent.add_tool("backup_state", backup_state, {
        "name": "backup_state",
        "description": "备份当前插件和配置状态到 backups/ 目录",
        "parameters": {
            "type": "object",
            "properties": {
                "backup_dir": {"type": "string", "description": "备份目录名"}
            }
        },
        "plugin": "env_plugin"
    })

    return {
        "name": "env_plugin",
        "version": "1.1.0",
        "author": "AgentCore",
        "description": "环境感知 — 让 AI 感知运行环境",
        "tools": ["get_cwd", "list_files", "run_command", "backup_state"]
    }
