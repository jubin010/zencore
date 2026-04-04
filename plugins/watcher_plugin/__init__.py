"""
watcher_plugin - 插件目录监听
功能：扫描 plugins/ 下的子目录，自动更新 plugins.md
"""

import re
import time
from pathlib import Path

PLUGINS_DIR = Path(__file__).parent.parent


def extract_plugin_info(plugin_dir: Path) -> dict:
    """从插件目录提取信息"""
    init_file = plugin_dir / "__init__.py"

    info = {
        "name": plugin_dir.name,
        "dir": plugin_dir.name,
        "path": str(plugin_dir),
        "description": "",
        "author": "未知",
        "version": "1.0.0",
        "tools": {},
    }

    if not init_file.exists():
        return info

    content = init_file.read_text(encoding="utf-8")

    # 提取多行文档字符串的第一行有效内容
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if match:
        docstring = match.group(1).strip()
        for line in docstring.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                line = re.sub(rf"^{plugin_dir.name}\s*[-—]\s*", "", line)
                info["description"] = line[:60]
                break

    return info


def generate_plugins_md(plugins_info: list) -> str:
    """生成 plugins.md 内容 — 纯索引格式"""
    lines = [
        "# 插件索引",
        "",
        "> AI 自主决策工作流：",
        "> 1. 查看本索引了解可用插件",
        "> 2. 用 `get_plugin_info` 读取目标插件的 plugin.md 详情",
        "> 3. 按需 `load_plugin` 加载",
        "",
        "## 插件列表",
        "",
        "| 插件目录 | 一句话描述 |",
        "|----------|------------|",
    ]

    for p in plugins_info:
        desc = p.get("description", "")[:60]
        lines.append(f"| `{p['name']}/` | {desc} |")

    lines.extend(
        [
            "",
            "---\n",
            f"*最后更新: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n",
        ]
    )

    return "\n".join(lines)


def update_plugins_md(agent=None, force=False) -> str:
    """更新 plugins.md 注册表 — 纯索引格式"""
    if not PLUGINS_DIR.exists():
        return "❌ plugins/ 目录不存在"

    plugins_info = []

    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir():
            continue
        if plugin_dir.name in ("__pycache__",):
            continue
        if not (plugin_dir / "__init__.py").exists():
            continue

        info = extract_plugin_info(plugin_dir)
        plugins_info.append(info)

    plugins_md_path = PLUGINS_DIR / "plugins.md"
    new_content = generate_plugins_md(plugins_info)

    should_update = force
    if plugins_md_path.exists():
        old_content = plugins_md_path.read_text(encoding="utf-8")
        should_update = should_update or (old_content != new_content)

    if should_update:
        plugins_md_path.write_text(new_content, encoding="utf-8")
        return f"✅ plugins.md 已更新 ({len(plugins_info)} 个插件)"

    return "✅ plugins.md 已是最新，无需更新"


def scan_plugins() -> str:
    """扫描并报告插件目录状态"""
    if not PLUGINS_DIR.exists():
        return "❌ plugins/ 目录不存在"

    plugin_dirs = []
    for d in sorted(PLUGINS_DIR.iterdir()):
        if d.is_dir() and (d / "__init__.py").exists():
            plugin_dirs.append(d)

    md_exists = (PLUGINS_DIR / "plugins.md").exists()

    report = [
        "📁 插件目录扫描报告",
        "=" * 40,
        f"目录: {PLUGINS_DIR.absolute()}",
        f"插件目录数: {len(plugin_dirs)}",
        f"plugins.md 存在: {'✅' if md_exists else '❌'}",
        "",
        "插件列表:",
    ]

    for d in plugin_dirs:
        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(d.stat().st_mtime))
        report.append(f"  - {d.name}/ ({size} bytes, {mtime})")

    return "\n".join(report)


def register(agent):
    """注册文件监听插件到 AgentCore"""

    def update_wrapper(force=False):
        return update_plugins_md(agent=agent, force=force)

    agent.add_tool("update_plugins_md", update_wrapper, {
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
        },
        "plugin": "watcher_plugin"
    })

    agent.add_tool("scan_plugins", scan_plugins, {
        "name": "scan_plugins",
        "description": "扫描 plugins/ 目录，报告当前状态（目录模式）",
        "parameters": {"type": "object", "properties": {}},
        "plugin": "watcher_plugin"
    })

    return {
        "name": "watcher_plugin",
        "version": "2.0.0",
        "author": "AgentCore",
        "description": "插件目录监听 - 自动更新插件注册表",
        "tools": ["update_plugins_md", "scan_plugins"]
    }
