"""
watcher_plugin.py - 文件监听插件
功能：监控 plugins/ 目录，自动更新 plugins.md

使用方式：
1. 手动调用：agent.tools['update_plugins_md']()
2. 自动监听：install_watcher(agent) - 每次处理消息前检查更新
"""

import os
import time
import json
from pathlib import Path


def extract_plugin_info(py_file: Path) -> dict:
    """从插件文件提取信息"""
    content = py_file.read_text(encoding="utf-8")
    
    info = {
        "name": py_file.stem,
        "file": py_file.name,
        "path": str(py_file),
        "description": "",
        "author": "未知",
        "version": "1.0.0",
        "tools": {}
    }
    
    # 尝试从文件头部提取信息
    lines = content.split("\n")
    in_docstring = False
    docstring_content = []
    
    for line in lines[:50]:  # 只检查前50行
        stripped = line.strip()
        
        # 检测文档字符串
        if '"""' in stripped or "'''" in stripped:
            if not in_docstring:
                in_docstring = True
                docstring_content.append(stripped.strip('"""\'\'\"'))
            else:
                in_docstring = False
                break
        elif in_docstring and stripped:
            docstring_content.append(stripped)
    
    if docstring_content:
        info["description"] = " ".join(docstring_content[:3])
    
    # 尝试提取 register 函数中的工具定义
    if "def register" in content:
        info["tools"]["动态加载"] = {
            "description": "此插件提供动态加载能力",
            "params": []
        }
    
    return info


def generate_plugins_md(plugins_info: list, tool_registry: dict) -> str:
    """生成 plugins.md 内容"""
    lines = [
        "# AgentCore 插件注册表",
        "",
        "> **智能体的自我认知档案** - 告诉AI自己有什么能力、如何使用",
        "",
        "## 📋 插件列表",
        "",
        "| 插件 | 描述 | 工具数 |",
        "|------|------|--------|",
    ]
    
    for p in plugins_info:
        tool_count = len(p.get("tools", {}))
        desc = p.get("description", "")[:40]
        lines.append(f"| `{p['name']}` | {desc}... | {tool_count} |")
    
    lines.extend([
        "",
        "## 🔧 工具注册表",
        "",
        "| 工具 | 所属插件 | 描述 |",
        "|------|----------|------|",
    ])
    
    for tool_name, tool_info in sorted(tool_registry.items()):
        desc = tool_info.get("description", "")[:50]
        lines.append(f"| `{tool_name}` | {tool_info['plugin']} | {desc} |")
    
    lines.extend([
        "",
        "## 📦 插件开发指南",
        "",
        "### 人类开发",
        "```bash",
        "# 1. 创建插件文件",
        "touch plugins/my_plugin.py",
        "",
        "# 2. 编写插件代码（参考 插件编写指南.md）",
        "",
        "# 3. 此插件会自动更新本注册表 ✓",
        "```",
        "",
        "### AI 自动进化",
        "```",
        "AI 发现需要某个工具 → 调用 write_plugin() → 自动更新本注册表 ✓",
        "```",
        "",
        "---\n",
        f"*最后更新: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n",
    ])
    
    return "\n".join(lines)


def update_plugins_md(force=False) -> str:
    """
    更新 plugins.md 注册表
    
    Args:
        force: 是否强制更新（忽略时间戳检查）
    
    Returns:
        更新结果
    """
    plugins_dir = Path("plugins")
    plugins_md_path = Path("plugins/plugins.md")
    
    # 插件目录不存在
    if not plugins_dir.exists():
        return "❌ plugins/ 目录不存在"
    
    # 获取插件列表
    plugins_info = []
    tool_registry = {}
    
    for py_file in sorted(plugins_dir.glob("*.py")):
        # 跳过自己
        if py_file.name == "watcher_plugin.py":
            # 特殊处理 watcher_plugin
            info = {
                "name": "watcher_plugin",
                "file": "watcher_plugin.py",
                "path": str(py_file),
                "description": "文件监听插件 - 自动更新插件注册表",
                "tools": {
                    "update_plugins_md": {"description": "更新 plugins.md 注册表", "params": []},
                    "scan_plugins": {"description": "扫描插件目录", "params": []}
                }
            }
        else:
            info = extract_plugin_info(py_file)
        
        plugins_info.append(info)
        
        # 构建工具注册表
        for tool_name, tool_info in info.get("tools", {}).items():
            tool_registry[tool_name] = {
                "plugin": py_file.stem,
                "description": tool_info.get("description", ""),
                "params": tool_info.get("params", [])
            }
    
    # 生成新的 plugins.md
    new_content = generate_plugins_md(plugins_info, tool_registry)
    
    # 检查是否需要更新
    should_update = force
    if plugins_md_path.exists():
        old_content = plugins_md_path.read_text(encoding="utf-8")
        should_update = should_update or (old_content != new_content)
    
    if should_update:
        plugins_md_path.write_text(new_content, encoding="utf-8")
        return f"✅ plugins.md 已更新 ({len(plugins_info)} 个插件, {len(tool_registry)} 个工具)"
    
    return "✅ plugins.md 已是最新，无需更新"


def scan_plugins() -> str:
    """扫描并报告插件目录状态"""
    plugins_dir = Path("plugins")
    
    if not plugins_dir.exists():
        return "❌ plugins/ 目录不存在"
    
    files = list(plugins_dir.glob("*.py"))
    md_exists = (plugins_dir / "plugins.md").exists()
    
    report = [
        "📁 插件目录扫描报告",
        "=" * 40,
        f"目录: {plugins_dir.absolute()}",
        f"Python文件数: {len(files)}",
        f"plugins.md 存在: {'✅' if md_exists else '❌'}",
        "",
        "文件列表:",
    ]
    
    for f in sorted(files):
        size = f.stat().st_size
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))
        report.append(f"  - {f.name} ({size} bytes, {mtime})")
    
    return "\n".join(report)


def auto_watch(agent, interval=5):
    """
    启动文件监听（后台守护进程）
    
    Args:
        agent: AgentCore 实例
        interval: 检查间隔（秒）
    
    注意：此函数需要单独线程运行
    """
    import threading
    
    def watch_loop():
        last_mtimes = {}
        plugins_dir = Path("plugins")
        
        while True:
            try:
                # 记录当前文件修改时间
                current_mtimes = {}
                for py_file in plugins_dir.glob("*.py"):
                    if py_file.name != "watcher_plugin.py":
                        current_mtimes[str(py_file)] = py_file.stat().st_mtime
                
                # 检测变化
                for path, mtime in current_mtimes.items():
                    if path not in last_mtimes or last_mtimes[path] != mtime:
                        print(f"📝 检测到变化: {Path(path).name}")
                        update_plugins_md(force=True)
                        agent.reload_plugins()
                        break
                
                last_mtimes = current_mtimes
                
            except Exception as e:
                print(f"⚠️ 监听错误: {e}")
            
            time.sleep(interval)
    
    thread = threading.Thread(target=watch_loop, daemon=True)
    thread.start()
    return "🔄 文件监听已启动"


def install_watcher(agent):
    """
    安装文件监听器到 AgentCore
    让 AgentCore 每次响应前自动检查插件更新
    """
    original_process = agent.process_message
    
    def process_with_watch(message):
        # 每次处理消息前检查
        update_plugins_md()
        return original_process(message)
    
    agent.process_message = process_with_watch
    return "✅ 文件监听已安装到 AgentCore"


# ============= 注册函数（给 AgentCore 调用） =============

def register(agent):
    """注册文件监听插件到 AgentCore"""
    
    # 注册工具
    agent.add_tool("update_plugins_md", update_plugins_md, {
        "name": "update_plugins_md",
        "description": "更新 plugins.md 注册表。智能体添加新插件后自动调用，或人类开发者添加插件后自动生效。",
        "parameters": {
            "type": "object",
            "properties": {
                "force": {
                    "type": "boolean",
                    "description": "是否强制更新（忽略内容对比）"
                }
            }
        }
    })
    
    agent.add_tool("scan_plugins", scan_plugins, {
        "name": "scan_plugins",
        "description": "扫描 plugins/ 目录，报告当前状态",
        "parameters": {"type": "object", "properties": {}}
    })
    
    # 返回插件信息
    return {
        "name": "watcher_plugin",
        "version": "1.0.0",
        "author": "AgentCore",
        "description": "文件监听插件 - 自动更新插件注册表",
        "tools": ["update_plugins_md", "scan_plugins"]
    }
