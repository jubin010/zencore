# -*- coding: utf-8 -*-
"""
AgentCore - AI智能体核心
完全插件化架构，AI可插拔到任意外壳驱动
"""

import os
import sys
import json
import re
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# 路径配置
AGENT_CORE_DIR = Path(__file__).parent.parent
PLUGINS_DIR = AGENT_CORE_DIR / "plugins"
PLUGINS_MD = PLUGINS_DIR / "plugins.md"


class DriverInterface:
    """外壳驱动接口 - 所有外壳必须实现此接口"""
    
    def send_message(self, content: str):
        """发送消息"""
        raise NotImplementedError
    
    def send_image(self, path: str):
        """发送图片"""
        raise NotImplementedError
    
    def send_file(self, path: str):
        """发送文件"""
        raise NotImplementedError
    
    def get_input(self, prompt: str = "") -> str:
        """获取输入"""
        raise NotImplementedError
    
    def show_loading(self, message: str):
        """显示加载提示"""
        raise NotImplementedError
    
    def toast(self, message: str):
        """显示提示"""
        raise NotImplementedError


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
    
    def register(self, name: str, func: Callable, description: str = "", 
                 parameters: Dict = None, **kwargs):
        """注册工具"""
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {},
            **kwargs
        }
    
    def unregister(self, name: str):
        """注销工具"""
        self._tools.pop(name, None)
    
    def get(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        tool = self._tools.get(name)
        return tool["func"] if tool else None
    
    def list_all(self) -> Dict[str, Dict]:
        """列出所有工具"""
        return self._tools.copy()
    
    def has(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools


class Memory:
    """长期记忆 - 管理AI的持久化记忆"""
    
    def __init__(self, memory_file: str = None):
        if memory_file is None:
            memory_file = AGENT_CORE_DIR / "memory.json"
        self.memory_file = Path(memory_file)
        self._memory = self._load()
    
    def _load(self) -> Dict:
        """加载记忆"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"history": [], "knowledge": [], "config": {}}
    
    def save(self):
        """保存记忆"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self._memory, f, ensure_ascii=False, indent=2)
    
    def add(self, key: str, value: Any):
        """添加记忆"""
        self._memory[key] = value
        self.save()
    
    def get(self, key: str, default=None):
        """获取记忆"""
        return self._memory.get(key, default)
    
    def update(self, updates: Dict):
        """批量更新记忆"""
        self._memory.update(updates)
        self.save()


class AgentCore:
    """
    AI智能体核心类
    
    设计原则:
    1. 一切皆为插件 - 所有能力通过插件扩展
    2. AI可插拔 - 核心与外壳完全解耦
    3. 懒加载 - 按需加载插件，不一次性加载所有功能
    """
    
    _global_instance = None  # 全局实例引用
    
    def __init__(self, driver: DriverInterface = None, config: Dict = None):
        """
        初始化AI智能体核心
        
        Args:
            driver: 外壳驱动实例
            config: 配置字典
        """
        self.driver = driver
        self.config = config or {}
        self.tool_registry = ToolRegistry()
        self.memory = Memory()
        
        # LLM配置
        self.llm_provider = self.config.get("llm_provider", "ollama")
        self.llm_model = self.config.get("llm_model", "qwen2.5:7b")
        self.llm_base_url = self.config.get("llm_base_url", "http://localhost:11434")
        
        # 上下文
        self.conversation_history = []
        self.max_history = self.config.get("max_history", 50)
        
        # 加载核心插件
        self._load_core_plugins()
        
        # 设置全局引用
        AgentCore._global_instance = self
    
    def _load_core_plugins(self):
        """加载核心插件"""
        # 加载插件构建器（让AI能自我编写插件）
        try:
            sys.path.insert(0, str(AGENT_CORE_DIR))
            from plugins import plugin_builder
            
            # 注册插件构建器的工具
            tools_info = plugin_builder.tool_info()
            for tool_name in tools_info.get('tools', []):
                def make_wrapper(tn):
                    def wrapper(**kwargs):
                        return plugin_builder.execute(tn, **kwargs)
                    return wrapper
                self.tool_registry.register(
                    name=tool_name,
                    func=make_wrapper(tool_name),
                    description=f"[插件构建器] {tool_name}"
                )
            
            print(f"✅ 核心插件已加载: {len(tools_info.get('tools', []))} 个工具")
        except Exception as e:
            print(f"⚠️ 核心插件加载失败: {e}")
    
    # ==================== 工具管理 ====================
    
    def add_tool(self, name: str, func: Callable, description: str = "", 
                 parameters: Dict = None):
        """注册工具"""
        self.tool_registry.register(name, func, description, parameters)
    
    def remove_tool(self, name: str):
        """移除工具"""
        self.tool_registry.unregister(name)
    
    def list_tools(self) -> Dict[str, Dict]:
        """列出所有工具"""
        return self.tool_registry.list_all()
    
    def execute_tool(self, name: str, **kwargs) -> str:
        """执行工具"""
        func = self.tool_registry.get(name)
        if func:
            try:
                return func(**kwargs)
            except Exception as e:
                return f"❌ 工具执行失败: {str(e)}\n{traceback.format_exc()}"
        else:
            return f"❌ 未知工具: {name}"
    
    # ==================== 对话管理 ====================
    
    def add_message(self, role: str, content: str):
        """添加对话消息"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # 限制历史长度
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    # ==================== LLM交互 ====================
    
    def _build_prompt(self, user_message: str) -> str:
        """构建发送给LLM的提示词"""
        
        # 获取可用工具描述
        tools_desc = self._get_tools_description()
        
        # 读取插件注册表作为AI的自我认知
        plugins_info = self._get_plugins_info()
        
        system_prompt = f"""你是一个AI智能体，你的核心能力由插件提供。

## 你的插件系统

当前已加载的插件工具:
{tools_desc}

## 插件注册表 (plugins.md)
{plugins_info}

## 工作原则

1. **按需加载**: 需要什么功能，就先用 `load_plugin` 加载对应插件
2. **自我进化**: 遇到没有的工具，用 `write_plugin` 编写新插件
3. **更新认知**: 添加新插件后，更新 `plugins.md` 注册表
4. **工具优先**: 优先使用工具解决问题，不要凭空编造

## 响应格式

当需要执行工具时，返回JSON格式:
{{"tool": "工具名", "params": {{"参数名": "参数值"}}}}

当直接回答时，直接返回文字内容。

## 当前时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history,
            {"role": "user", "content": user_message}
        ]
        
        return json.dumps(messages, ensure_ascii=False)
    
    def _get_tools_description(self) -> str:
        """获取工具描述"""
        tools = self.tool_registry.list_all()
        if not tools:
            return "(暂无已加载工具)"
        
        lines = []
        for name, info in tools.items():
            desc = info.get("description", "无描述")
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)
    
    def _get_plugins_info(self) -> str:
        """读取插件注册表"""
        if PLUGINS_MD.exists():
            try:
                with open(PLUGINS_MD, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                pass
        return "(插件注册表不存在)"
    
    def chat(self, message: str) -> str:
        """同步对话 - 完整的对话处理"""
        self.add_message("user", message)
        
        # 构建提示词
        prompt = self._build_prompt(message)
        
        # 调用LLM
        response = self._call_llm(prompt)
        
        self.add_message("assistant", response)
        
        return response
    
    def chat_with_tools(self, message: str) -> str:
        """
        带工具调用的对话
        支持多轮工具调用直到LLM返回最终答案
        """
        self.add_message("user", message)
        
        # 构建初始提示词
        prompt = self._build_prompt(message)
        
        # 多轮对话循环
        max_turns = 10
        turns = 0
        
        while turns < max_turns:
            turns += 1
            
            # 调用LLM
            llm_response = self._call_llm(prompt)
            
            # 检查是否需要工具调用
            tool_call = self._extract_tool_call(llm_response)
            
            if tool_call is None:
                # 没有工具调用，返回结果
                self.add_message("assistant", llm_response)
                return llm_response
            
            # 执行工具
            tool_name = tool_call.get("tool")
            tool_params = tool_call.get("params", {})
            
            # 执行并获取结果
            tool_result = self.execute_tool(tool_name, **tool_params)
            
            # 将工具调用和结果添加到上下文
            tool_message = json.dumps({
                "tool": tool_name,
                "params": tool_params,
                "result": tool_result
            }, ensure_ascii=False)
            
            self.add_message("assistant", f"[工具调用]\n{tool_message}")
            self.add_message("tool", tool_result)
            
            # 更新提示词继续对话
            prompt = self._build_prompt("")
        
        return "❌ 对话超时，已达到最大轮次限制"
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM服务"""
        if self.llm_provider == "ollama":
            return self._call_ollama(prompt)
        elif self.llm_provider == "openai":
            return self._call_openai(prompt)
        else:
            return f"❌ 不支持的LLM提供商: {self.llm_provider}"
    
    def _call_ollama(self, prompt: str) -> str:
        """调用Ollama LLM"""
        try:
            import urllib.request
            import urllib.error
            
            url = f"{self.llm_base_url}/api/chat"
            data = json.loads(prompt)  # prompt本身是JSON格式的消息列表
            
            payload = {
                "model": self.llm_model,
                "messages": data,
                "stream": False
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("message", {}).get("content", "")
                
        except Exception as e:
            return f"❌ LLM调用失败: {str(e)}\n{traceback.format_exc()}"
    
    def _call_openai(self, prompt: str) -> str:
        """调用OpenAI兼容LLM"""
        try:
            import urllib.request
            import urllib.error
            
            url = f"{self.llm_base_url}/v1/chat/completions"
            data = json.loads(prompt)
            
            payload = {
                "model": self.llm_model,
                "messages": data
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {self.config.get('api_key', '')}"
                }
            )
            
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
        except Exception as e:
            return f"❌ LLM调用失败: {str(e)}"
    
    def _extract_tool_call(self, response: str) -> Optional[Dict]:
        """从LLM响应中提取工具调用"""
        # 尝试解析JSON
        try:
            # 查找JSON块
            match = re.search(r'\{[^{}]*"tool"[^{}]*\}', response)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return None
    
    # ==================== 便捷方法 ====================
    
    def send(self, content: str):
        """发送消息"""
        if self.driver:
            self.driver.send_message(content)
        else:
            print(content)
    
    def run_cli(self):
        """运行CLI交互模式"""
        print("=" * 50)
        print("🤖 AgentCore CLI 模式")
        print("=" * 50)
        print("输入消息与AI对话，输入 'quit' 退出")
        print("输入 'tools' 查看可用工具")
        print("输入 'clear' 清空对话历史")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n👤 你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ('quit', 'exit', '退出'):
                    print("👋 再见!")
                    break
                
                if user_input.lower() == 'tools':
                    tools = self.list_tools()
                    print(f"\n🛠️ 可用工具 ({len(tools)}个):")
                    for name, info in sorted(tools.items()):
                        print(f"   • {name}")
                    continue
                
                if user_input.lower() == 'clear':
                    self.clear_history()
                    print("✅ 对话历史已清空")
                    continue
                
                # 对话
                print("\n🤖 AI: ", end="", flush=True)
                response = self.chat_with_tools(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"\n❌ 错误: {str(e)}")
    
    def run_web(self, host: str = "0.0.0.0", port: int = 8080):
        """运行Web交互模式"""
        from drivers.web_driver import WebDriver
        
        driver = WebDriver(self)
        driver.run(host, port)


# ==================== 插件基类 ====================

class PluginBase:
    """插件基类（推荐使用）"""
    
    name = "BasePlugin"
    description = "基础插件"
    
    @classmethod
    def tool_info(cls):
        return {
            "name": cls.name,
            "description": cls.description,
            "tools": []
        }
    
    @classmethod
    def execute(cls, tool_name: str, **kwargs):
        raise NotImplementedError
