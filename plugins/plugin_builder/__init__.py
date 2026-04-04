"""
plugin_builder - 插件构建器
功能：让 AI 和人类都能编写插件

遵循"一切皆为插件"原则：
- 每个插件拥有独立目录
- 编写完成后自动更新 plugins.md
"""

import ast
from pathlib import Path

# 路径常量
PLUGINS_DIR = Path(__file__).parent.parent


def register(agent):
    """注册插件构建器到 AgentCore"""

    def write_plugin(plugin_name: str, code: str, plugin_md: str = "") -> str:
        """
        编写并加载新插件（目录模式）

        Args:
            plugin_name: 插件目录名（如: weather_plugin）
            code: 插件代码（写入 __init__.py）
            plugin_md: 可选的 plugin.md 内容（工具说明文档）

        Returns:
            执行结果
        """
        try:
            # 规范化名称
            if plugin_name.endswith(".py"):
                plugin_name = plugin_name.replace(".py", "")
            if "/" in plugin_name or "\\" in plugin_name:
                plugin_name = plugin_name.split("/")[-1].split("\\")[-1]

            plugin_dir = PLUGINS_DIR / plugin_name
            plugin_dir.mkdir(exist_ok=True)

            # 写入 __init__.py
            init_file = plugin_dir / "__init__.py"
            init_file.write_text(code, encoding="utf-8")

            # 可选写入 plugin.md
            if plugin_md:
                md_file = plugin_dir / "plugin.md"
                md_file.write_text(plugin_md, encoding="utf-8")

            # 尝试加载插件
            try:
                agent.load_plugin(plugin_name)
            except Exception:
                pass

            # 自动更新 plugins.md
            try:
                if agent.tool_registry.has("update_plugins_md"):
                    agent.execute_tool("update_plugins_md", force=True)
            except Exception:
                pass

            return f"✅ 插件 {plugin_name}/ 已创建并注册"

        except Exception as e:
            return f"❌ 创建失败: {str(e)}"

    def load_plugin(plugin_name: str) -> str:
        """加载指定插件"""
        try:
            success = agent.load_plugin(plugin_name)
            if success:
                return f"✅ 插件 {plugin_name} 加载成功"
            return f"❌ 插件 {plugin_name} 加载失败"
        except Exception as e:
            return f"❌ 加载失败: {str(e)}"

    def reload_plugins() -> str:
        """重新加载所有插件"""
        try:
            agent.reload_plugins()
            return "✅ 插件重载完成"
        except Exception as e:
            return f"❌ 重载失败: {str(e)}"

    def list_plugins() -> str:
        """列出所有已加载的插件"""
        tools = agent.tool_registry.list_all()
        if not tools:
            return "📭 暂无已加载的工具"

        # 按插件分组
        plugin_tools = {}
        for name, info in tools.items():
            plugin = info.get("plugin", "unknown")
            if plugin not in plugin_tools:
                plugin_tools[plugin] = []
            plugin_tools[plugin].append(name)

        lines = ["📦 已加载插件列表", "=" * 40]
        for pname, tnames in sorted(plugin_tools.items()):
            tools_str = ", ".join([f"`{t}`" for t in tnames[:5]])
            if len(tnames) > 5:
                tools_str += f" ... (+{len(tnames) - 5})"
            lines.append(f"\n### `{pname}`")
            lines.append(f"工具: {tools_str}")

        return "\n".join(lines)

    def get_plugin_template(plugin_name: str = "my_plugin") -> str:
        """获取插件开发模板（返回 __init__.py + plugin.md 的代码）"""
        return f'''# __init__.py
"""
{plugin_name} - 插件描述
"""

from pathlib import Path

PLUGINS_DIR = Path(__file__).parent.parent


def register(agent):
    """注册插件到 AgentCore"""
    
    def my_tool(param: str) -> str:
        """我的工具函数"""
        return f"结果: {{param}}"
    
    # 注册工具
    agent.add_tool("my_tool", my_tool, {{
        "name": "my_tool",
        "description": "工具描述",
        "parameters": {{
            "type": "object",
            "properties": {{
                "param": {{
                    "type": "string",
                    "description": "参数描述"
                }}
            }},
            "required": ["param"]
        }},
        "plugin": "{plugin_name}"
    }})
    
    # 返回插件信息
    return {{
        "name": "{plugin_name}",
        "version": "1.0.0",
        "author": "作者名",
        "description": "插件描述",
        "tools": ["my_tool"]
    }}


---SEPARATOR---


# plugin.md
# {plugin_name}

## 描述
简要描述这个插件做什么

## 触发词
关键词1、关键词2、关键词3

## 工具
| 工具名 | 参数 | 描述 |
|--------|------|------|
| my_tool | param: str | 工具描述 |

## 使用示例
```
my_tool(param="test") → "结果: test"
```

## 注意事项
- 注意事项1
- 注意事项2
'''

    def get_plugin_info(plugin_name: str) -> str:
        """读取指定插件的 plugin.md 详情"""
        plugin_dir = PLUGINS_DIR / plugin_name
        md_file = plugin_dir / "plugin.md"

        if not plugin_dir.is_dir():
            return f"❌ 插件 {plugin_name}/ 不存在"

        if not md_file.exists():
            return f"⚠️ 插件 {plugin_name}/ 没有 plugin.md，可尝试 load_plugin 后查看工具列表"

        content = md_file.read_text(encoding="utf-8")
        return content

    def get_plugin_readme() -> str:
        """获取插件编写指南"""
        guide_path = PLUGINS_DIR / "插件编写指南.md"
        if guide_path.exists():
            return guide_path.read_text(encoding="utf-8")
        return "❌ 插件编写指南.md 不存在"

    def get_available_tools() -> str:
        """获取所有可用工具"""
        tools = agent.tool_registry.list_all()

        lines = ["🔧 可用工具列表", "=" * 50, "", f"**已加载: {len(tools)} 个**", ""]

        for tool in sorted(tools.keys()):
            desc = tools[tool].get("description", "")
            lines.append(f"  - `{tool}`: {desc}")

        lines.extend(
            [
                "",
                "💡 提示: 需要更多工具？AI可以自己编写！",
                "",
                "示例:",
                "```python",
                'code = get_plugin_template("my_tool")',
                "# 修改 code",
                'write_plugin("my_tool", code)',
                "```",
            ]
        )

        return "\n".join(lines)

    def validate_code(code: str) -> str:
        """验证 Python 代码语法"""
        try:
            ast.parse(code)
            return "✅ 语法正确"
        except SyntaxError as e:
            return f"❌ 语法错误: 第{e.lineno}行 - {e.msg}"

    def unload_plugin(plugin_name: str) -> str:
        """卸载指定插件"""
        try:
            return agent.unload_plugin(plugin_name)
        except Exception as e:
            return f"❌ 卸载失败: {str(e)}"

    def delete_plugin(plugin_name: str) -> str:
        """删除插件（整个目录）"""
        try:
            if plugin_name.endswith(".py"):
                plugin_name = plugin_name.replace(".py", "")

            plugin_dir = PLUGINS_DIR / plugin_name

            if not plugin_dir.is_dir():
                return f"❌ 插件目录 {plugin_name}/ 不存在"

            import shutil

            shutil.rmtree(plugin_dir)

            # 自动更新 plugins.md
            try:
                if agent.tool_registry.has("update_plugins_md"):
                    agent.execute_tool("update_plugins_md", force=True)
            except Exception:
                pass

            return f"✅ 插件 {plugin_name}/ 已删除"

        except Exception as e:
            return f"❌ 删除失败: {str(e)}"

    # 注册所有工具
    agent.add_tool(
        "write_plugin",
        write_plugin,
        {
            "name": "write_plugin",
            "description": "编写新插件（目录模式）。创建插件目录、__init__.py 和可选 plugin.md，写入后自动加载并更新注册表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "plugin_name": {
                        "type": "string",
                        "description": "插件目录名（如: weather_plugin）",
                    },
                    "code": {
                        "type": "string",
                        "description": "插件代码（__init__.py 内容）",
                    },
                    "plugin_md": {
                        "type": "string",
                        "description": "可选的 plugin.md 内容（工具说明文档）",
                    },
                },
                "required": ["plugin_name", "code"],
            },
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "load_plugin",
        load_plugin,
        {
            "name": "load_plugin",
            "description": "加载指定插件目录",
            "parameters": {
                "type": "object",
                "properties": {
                    "plugin_name": {"type": "string", "description": "插件目录名"}
                },
                "required": ["plugin_name"],
            },
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "reload_plugins",
        reload_plugins,
        {
            "name": "reload_plugins",
            "description": "重新加载所有插件目录",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "list_plugins",
        list_plugins,
        {
            "name": "list_plugins",
            "description": "列出所有已加载的插件及其工具",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "get_plugin_template",
        get_plugin_template,
        {
            "name": "get_plugin_template",
            "description": "获取插件开发模板代码（目录模式）",
            "parameters": {
                "type": "object",
                "properties": {
                    "plugin_name": {"type": "string", "description": "插件目录名"}
                },
            },
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "get_plugin_info",
        get_plugin_info,
        {
            "name": "get_plugin_info",
            "description": "读取指定插件的 plugin.md 详情。在 load_plugin 之前调用，了解工具参数、使用示例和注意事项。",
            "parameters": {
                "type": "object",
                "properties": {
                    "plugin_name": {"type": "string", "description": "插件目录名"}
                },
                "required": ["plugin_name"],
            },
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "get_plugin_readme",
        get_plugin_readme,
        {
            "name": "get_plugin_readme",
            "description": "读取插件编写指南",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "get_available_tools",
        get_available_tools,
        {
            "name": "get_available_tools",
            "description": "获取所有可用工具列表",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "validate_code",
        validate_code,
        {
            "name": "validate_code",
            "description": "验证Python代码语法是否正确",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "待验证的代码"}
                },
                "required": ["code"],
            },
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "unload_plugin",
        unload_plugin,
        {
            "name": "unload_plugin",
            "description": "卸载指定插件的所有工具。核心插件不可卸载。用于释放不需要的工具，保持注册表精简。",
            "parameters": {
                "type": "object",
                "properties": {
                    "plugin_name": {"type": "string", "description": "插件目录名"}
                },
                "required": ["plugin_name"],
            },
            "plugin": "plugin_builder",
        },
    )

    agent.add_tool(
        "delete_plugin",
        delete_plugin,
        {
            "name": "delete_plugin",
            "description": "删除指定插件目录",
            "parameters": {
                "type": "object",
                "properties": {
                    "plugin_name": {"type": "string", "description": "插件目录名"}
                },
                "required": ["plugin_name"],
            },
            "plugin": "plugin_builder",
        },
    )

    return {
        "name": "plugin_builder",
        "version": "2.0.0",
        "author": "AgentCore",
        "description": "插件构建器 - 让AI和人类都能编写插件（目录模式）",
        "tools": [
            "write_plugin",
            "load_plugin",
            "unload_plugin",
            "reload_plugins",
            "list_plugins",
            "get_plugin_template",
            "get_plugin_info",
            "get_plugin_readme",
            "get_available_tools",
            "validate_code",
            "delete_plugin",
        ],
    }
