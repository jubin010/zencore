"""
watcher_plugin - 插件目录监听
功能：扫描 plugins/ 下的子目录，自动更新 plugins.md

使用方式：
1. 手动调用：update_plugins_md()
2. 自动监听：install_watcher(agent)
"""

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
    # 格式: """\n模块名 - 描述\n...
    import re

    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if match:
        docstring = match.group(1).strip()
        # 取第一行非空内容
        for line in docstring.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                # 清理模块名前缀
                line = re.sub(rf"^{plugin_dir.name}\s*[-—]\s*", "", line)
                info["description"] = line[:60]
                break

    return info

    content = init_file.read_text(encoding="utf-8")

    # 从文档字符串提取描述 — 只取第一行有效内容
    lines = content.split("\n")
    in_docstring = False

    for line in lines[:50]:
        stripped = line.strip()

        if '"""' in stripped or "'''" in stripped:
            if not in_docstring:
                in_docstring = True
                # 提取引号内的内容
                for q in ['"""', "'''"]:
                    if q in stripped:
                        parts = stripped.split(q)
                        if len(parts) >= 2:
                            first_line = parts[1].strip()
                            if first_line:
                                # 清理模块名前缀
                                import re

                                first_line = re.sub(
                                    rf"^{plugin_dir.name}\s*[-—]\s*", "", first_line
                                )
                                info["description"] = first_line[:60]
                                break
                if info["description"]:
                    break
            else:
                # 多行文档字符串的第一行
                first_line = stripped
                if first_line:
                    import re

                    first_line = re.sub(
                        rf"^{plugin_dir.name}\s*[-—]\s*", "", first_line
                    )
                    info["description"] = first_line[:60]
                break

    return info

    content = init_file.read_text(encoding="utf-8")

    # 从文档字符串提取描述
    lines = content.split("\n")
    in_docstring = False
    docstring_content = []

    for line in lines[:50]:
        stripped = line.strip()

        if '"""' in stripped or "'''" in stripped:
            if not in_docstring:
                in_docstring = True
                docstring_content.append(stripped.strip('"""\'\'"'))
            else:
                in_docstring = False
                break
        elif in_docstring and stripped:
            docstring_content.append(stripped)

    if docstring_content:
        full_text = " ".join(docstring_content)
        # 清理：去掉 "模块名 - " 前缀
        import re

        full_text = re.sub(rf"^{plugin_dir.name}\s*[-—]\s*", "", full_text)
        # 取第一个句号前的内容
        desc = full_text.split("。")[0].strip()
        info["description"] = desc[:60]

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


def auto_watch(agent, interval=5):
    """
    启动文件监听（后台守护进程）
    """
    import threading

    def watch_loop():
        last_mtimes = {}

        while True:
            try:
                current_mtimes = {}
                for plugin_dir in PLUGINS_DIR.iterdir():
                    if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                        init_file = plugin_dir / "__init__.py"
                        current_mtimes[str(init_file)] = init_file.stat().st_mtime

                for path, mtime in current_mtimes.items():
                    if path not in last_mtimes or last_mtimes[path] != mtime:
                        print(f"📝 检测到变化: {Path(path).parent.name}/")
                        update_plugins_md(agent=agent, force=True)
                        agent.reload_plugins()
                        break

                last_mtimes = current_mtimes

            except Exception as e:
                print(f"⚠️ 监听错误: {e}")

            time.sleep(interval)

    thread = threading.Thread(target=watch_loop, daemon=True)
    thread.start()
    return "🔄 文件监听已启动"


def register(agent):
    """注册文件监听插件到 AgentCore"""

    def update_wrapper(force=False):
        return update_plugins_md(agent=agent, force=force)

    agent.add_tool(
        "update_plugins_md",
        update_wrapper,
        {
            "name": "update_plugins_md",
            "description": "更新 plugins.md 注册表。智能体添加新插件后自动调用，或人类开发者添加插件后自动生效。",
            "parameters": {
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "是否强制更新（忽略内容对比）",
                    }
                },
            },
            "plugin": "watcher_plugin",
        },
    )

    agent.add_tool(
        "scan_plugins",
        scan_plugins,
        {
            "name": "scan_plugins",
            "description": "扫描 plugins/ 目录，报告当前状态（目录模式）",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "watcher_plugin",
        },
    )

    return {
        "name": "watcher_plugin",
        "version": "2.0.0",
        "author": "AgentCore",
        "description": "插件目录监听 - 自动更新插件注册表",
        "tools": ["update_plugins_md", "scan_plugins"],
    }
