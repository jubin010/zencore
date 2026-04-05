# 🔌 集成指南：如何构建你的智能体外壳

> **核心原则：AgentCore 是引擎，Driver 是传动轴，Main 是方向盘。**
> 你不需要我们的车壳（Main），你只需要把引擎装进你自己的载具里。

## 1. 架构分层

在集成之前，请理解 zencore 的三层架构：

| 层级 | 文件 | 职责 | 你的工作 |
| :--- | :--- | :--- | :--- |
| **核心 (Engine)** | `core/agent.py` | 思考、记忆、工具调度。**纯文本处理**。 | **不要改它**。直接引用。 |
| **驱动 (Adapter)** | `drivers/*.py` | 连接 LLM、处理输入输出。 | **编写你的 Driver**。 |
| **入口 (UI/Loop)** | `main.py` | 交互循环、UI 渲染。 | **编写你的 Main** 或集成到现有 App。 |

---

## 2. 如何编写你的 Driver

Driver 是智能体与外部世界（LLM、用户）的桥梁。你只需要实现 `DriverInterface` 接口。

### 步骤：

1.  创建一个新文件，例如 `my_driver.py`。
2.  继承 `DriverInterface`。
3.  实现 `call_llm` 方法（连接你的 LLM）。
4.  （可选）实现 `get_input` 和 `send_message`（如果你的 Main 需要）。

### 示例：一个简单的 Web Driver

```python
from core.agent import DriverInterface
from openai import OpenAI

class MyWebDriver(DriverInterface):
    def __init__(self, api_key, model):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def call_llm(self, messages: list) -> str:
        # 这里可以是任何 LLM，OpenAI, Ollama, 甚至本地模型
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content
    
    def send_message(self, content: str):
        # 在 Web 中，这里可能是推送到 WebSocket
        print(f"[Web Output]: {content}")
        
    def get_input(self, prompt: str = "") -> str:
        # 在 Web 中，这里可能是等待 HTTP POST 请求
        return input(prompt)
```

---

## 3. 如何集成到现有程序

你不需要 `main.py`。你只需要在你的业务逻辑中实例化 `AgentCore` 并调用它。

### 场景 A：集成到 Flask/FastAPI 网站

```python
from flask import Flask, request, jsonify
from core.agent import AgentCore
from my_driver import MyWebDriver # 你刚才写的驱动

app = Flask(__name__)

# 初始化驱动和智能体
driver = MyWebDriver(api_key="sk-...", model="gpt-4o")
agent = AgentCore(driver=driver)

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    
    # 核心调用：只有这一行
    response = agent.chat_with_tools(user_input)
    
    return jsonify({"reply": response})

if __name__ == '__main__':
    app.run()
```

### 场景 B：集成到微信/钉钉机器人

```python
# 假设这是微信机器人的消息回调
def on_wechat_message(msg):
    # 1. 获取用户消息
    user_input = msg.content
    
    # 2. 调用智能体 (复用同一个 agent 实例)
    reply = agent.chat_with_tools(user_input)
    
    # 3. 发送回复
    msg.reply(reply)
```

---

## 4. 常见问题

### Q: 我需要修改 `agent.py` 吗？
**A: 绝对不要。** `agent.py` 是纯粹的逻辑核心。如果你需要新功能，请通过**编写插件**来实现，而不是修改核心代码。

### Q: 我的程序是异步的 (Async)，怎么办？
**A:** 目前的 `AgentCore` 是同步的。你可以在异步函数中使用 `asyncio.to_thread` 或在后台线程中运行 `agent.chat_with_tools`。

### Q: 如何共享记忆？
**A:** `AgentCore` 实例保存了对话历史。如果你需要跨请求共享记忆，请保持同一个 `AgentCore` 实例存活，或者将 `conversation_history` 持久化到数据库并在初始化时恢复。

---

## 5. 现有文件说明

*   **`cli_driver.py`**: 终端环境下的驱动实现，负责连接 Ollama/OpenAI 并处理命令行输入。
*   **`main.py`**: 终端交互循环的实现，负责使用 Rich 库美化输出并处理用户指令（如 `quit`, `tools`）。

**它们是演示代码，不是核心。** 请根据你的需求自由替换。
