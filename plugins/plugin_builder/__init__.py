"""
plugin_builder - 插件构建器
功能：让 AI 和人类都能编写插件
"""

import ast
from pathlib import Path

PLUGINS_DIR = Path(__file__).parent.parent


def register(agent):
    """注册插件构建器到 AgentCore"""

    def write_plugin(plugin_name: str, code: str) -> str:
        """
        编写并加载新插件
        
        Args:
            plugin_name: 插件目录名
            code: 插件代码（写入 __init__.py）
        """
        try:
            if plugin_name.endswith(".py"):
                plugin_name = plugin_name.replace(".py", "")
            if "/" in plugin_name or "\\" in plugin_name:
                plugin_name = plugin_name.split("/")[-1].split("\\")[-1]

            plugin_dir = PLUGINS_DIR / plugin_name
            plugin_dir.mkdir(exist_ok=True)

            init_file = plugin_dir / "__init__.py"
            init_file.write_text(code, encoding="utf-8")

            try:
                agent.load_plugin(plugin_name)
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

    def validate_code(code: str) -> str:
        """验证 Python 代码语法"""
        try:
            ast.parse(code)
            return "✅ 语法正确"
        except SyntaxError as e:
            return f"❌ 语法错误: 第{e.lineno}行 - {e.msg}"

    agent.add_tool("write_plugin", write_plugin, {
        "name": "write_plugin",
        "description": "编写新插件。创建插件目录和 __init__.py，写入后自动加载。",
        "parameters": {
            "type": "object",
            "properties": {
                "plugin_name": {"type": "string", "description": "插件目录名"},
                "code": {"type": "string", "description": "插件代码"}
            },
            "required": ["plugin_name", "code"]
        },
        "plugin": "plugin_builder"
    })

    agent.add_tool("load_plugin", load_plugin, {
        "name": "load_plugin",
        "description": "加载指定插件目录",
        "parameters": {
            "type": "object",
            "properties": {
                "plugin_name": {"type": "string", "description": "插件目录名"}
            },
            "required": ["plugin_name"]
        },
        "plugin": "plugin_builder"
    })

    agent.add_tool("validate_code", validate_code, {
        "name": "validate_code",
        "description": "验证Python代码语法是否正确",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "待验证的代码"}
            },
            "required": ["code"]
        },
        "plugin": "plugin_builder"
    })

    return {
        "name": "plugin_builder",
        "version": "1.0.0",
        "author": "AgentCore",
        "description": "插件构建器 - 让AI能编写插件",
        "tools": ["write_plugin", "load_plugin", "validate_code"]
    }
