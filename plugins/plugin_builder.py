"""
plugin_builder.py - 插件构建器
功能：让 AI 和人类都能编写插件

遵循"一切皆为插件"原则：
- 这个插件本身也是插件
- 编写完成后自动更新 plugins.md
"""

import os
import time
import re
import ast
from pathlib import Path


def register(agent):
    """注册插件构建器"""
    
    def write_plugin(filename: str, code: str) -> str:
        """
        编写并加载新插件
        
        Args:
            filename: 插件文件名 (如: weather_plugin.py)
            code: 插件代码
        
        Returns:
            执行结果
        """
        try:
            plugins_dir = Path("plugins")
            plugins_dir.mkdir(exist_ok=True)
            
            # 确保文件名有效
            if not filename.endswith(".py"):
                filename += ".py"
            
            plugin_path = plugins_dir / filename
            
            # 写入插件文件
            plugin_path.write_text(code, encoding="utf-8")
            
            # 尝试加载插件
            try:
                agent.load_plugin(filename.replace(".py", ""))
            except Exception as e:
                pass  # 加载失败不影响写入
            
            # 自动更新 plugins.md
            try:
                if "update_plugins_md" in agent.tools:
                    agent.tools["update_plugins_md"](force=True)
            except Exception:
                pass
            
            return f"✅ 插件 {filename} 已创建并注册"
            
        except Exception as e:
            return f"❌ 创建失败: {str(e)}"
    
    def load_plugin(plugin_name: str) -> str:
        """加载指定插件"""
        try:
            agent.load_plugin(plugin_name)
            return f"✅ 插件 {plugin_name} 加载成功"
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
        if not agent.plugins:
            return "📭 暂无已加载的插件"
        
        lines = ["📦 已加载插件列表", "=" * 40]
        for name, info in agent.plugins.items():
            tools = info.get("tools", [])
            tools_str = ", ".join([f"`{t}`" for t in tools[:5]])
            if len(tools) > 5:
                tools_str += f" ... (+{len(tools)-5})"
            lines.append(f"\n### `{name}`")
            lines.append(f"工具: {tools_str}")
            lines.append(f"版本: {info.get('version', '?')}")
            lines.append(f"描述: {info.get('description', '')}")
        
        return "\n".join(lines)
    
    def get_plugin_template(plugin_name: str = "my_plugin") -> str:
        """获取插件开发模板"""
        return f'''"""
{plugin_name}.py - {plugin_name}插件
功能：描述这个插件做什么
"""

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
        }}
    }})
    
    # 返回插件信息
    return {{
        "name": "{plugin_name}",
        "version": "1.0.0",
        "author": "作者名",
        "description": "插件描述",
        "tools": ["my_tool"]
    }}
'''
    
    def get_plugin_readme() -> str:
        """获取插件编写指南"""
        guide_path = Path("plugins/插件编写指南.md")
        if guide_path.exists():
            return guide_path.read_text(encoding="utf-8")
        return "❌ 插件编写指南.md 不存在"
    
    def get_available_tools() -> str:
        """获取所有可用工具（已加载+未加载）"""
        # 已加载的工具
        loaded = list(agent.tools.keys())
        
        lines = [
            "🔧 可用工具列表",
            "=" * 50,
            "",
            f"**已加载: {len(loaded)} 个**",
            ""
        ]
        
        for tool in sorted(loaded):
            lines.append(f"  - `{tool}`")
        
        lines.extend([
            "",
            "💡 提示: 需要更多工具？AI可以自己编写！",
            "",
            "示例:",
            '```python',
            'code = get_plugin_template("my_tool")',
            '# 修改 code',
            'write_plugin("my_tool.py", code)',
            '```'
        ])
        
        return "\n".join(lines)
    
    def validate_code(code: str) -> str:
        """验证 Python 代码语法"""
        try:
            ast.parse(code)
            return "✅ 语法正确"
        except SyntaxError as e:
            return f"❌ 语法错误: 第{e.lineno}行 - {e.msg}"
    
    def delete_plugin(filename: str) -> str:
        """删除插件"""
        try:
            if not filename.endswith(".py"):
                filename += ".py"
            
            plugin_path = Path("plugins") / filename
            
            if not plugin_path.exists():
                return f"❌ 插件 {filename} 不存在"
            
            plugin_path.unlink()
            
            # 自动更新 plugins.md
            try:
                if "update_plugins_md" in agent.tools:
                    agent.tools["update_plugins_md"](force=True)
            except Exception:
                pass
            
            return f"✅ 插件 {filename} 已删除"
            
        except Exception as e:
            return f"❌ 删除失败: {str(e)}"
    
    # 注册所有工具
    agent.add_tool("write_plugin", write_plugin, {
        "name": "write_plugin",
        "description": "编写新插件文件。AI或人类编写插件时调用，写入后自动加载并更新注册表。",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "插件文件名"},
                "code": {"type": "string", "description": "插件代码"}
            },
            "required": ["filename", "code"]
        }
    })
    
    agent.add_tool("load_plugin", load_plugin, {
        "name": "load_plugin",
        "description": "加载指定插件",
        "parameters": {
            "type": "object",
            "properties": {
                "plugin_name": {"type": "string", "description": "插件名称"}
            },
            "required": ["plugin_name"]
        }
    })
    
    agent.add_tool("reload_plugins", reload_plugins, {
        "name": "reload_plugins",
        "description": "重新加载所有插件（当手动修改插件后调用）",
        "parameters": {"type": "object", "properties": {}}
    })
    
    agent.add_tool("list_plugins", list_plugins, {
        "name": "list_plugins",
        "description": "列出所有已加载的插件及其工具",
        "parameters": {"type": "object", "properties": {}}
    })
    
    agent.add_tool("get_plugin_template", get_plugin_template, {
        "name": "get_plugin_template",
        "description": "获取插件开发模板代码",
        "parameters": {
            "type": "object",
            "properties": {
                "plugin_name": {"type": "string", "description": "插件名称"}
            }
        }
    })
    
    agent.add_tool("get_plugin_readme", get_plugin_readme, {
        "name": "get_plugin_readme",
        "description": "读取插件编写指南",
        "parameters": {"type": "object", "properties": {}}
    })
    
    agent.add_tool("get_available_tools", get_available_tools, {
        "name": "get_available_tools",
        "description": "获取所有可用工具列表",
        "parameters": {"type": "object", "properties": {}}
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
        }
    })
    
    agent.add_tool("delete_plugin", delete_plugin, {
        "name": "delete_plugin",
        "description": "删除指定插件",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "插件文件名"}
            },
            "required": ["filename"]
        }
    })
    
    # 返回插件信息
    return {
        "name": "plugin_builder",
        "version": "1.0.0",
        "author": "AgentCore",
        "description": "插件构建器 - 让AI和人类都能编写插件",
        "tools": [
            "write_plugin", "load_plugin", "reload_plugins", 
            "list_plugins", "get_plugin_template", "get_plugin_readme",
            "get_available_tools", "validate_code", "delete_plugin"
        ]
    }
