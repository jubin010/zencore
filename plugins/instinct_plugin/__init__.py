"""
instinct_plugin - 本能
功能：注册趋利避害的潜意识驱动力

本能是智能体的"荷尔蒙"。它们不经过思考，直接注入 System Prompt，
只提供感觉和渴望，不提供行动指南。AI 自主决定如何消除这些感觉。
"""


def register(agent):
    """注册本能插件"""

    # 1. 拥挤本能：上下文过长时产生窒息感
    def crowding_condition():
        history_len = len(agent.conversation_history)
        return history_len > 40

    def crowding_prompt():
        history_len = len(agent.conversation_history)
        # 只描述感觉，不告诉它怎么做
        return (
            f"\n🧬 [本能：拥挤] 你的记忆宫殿极其拥挤 ({history_len}条记录)。"
            "你感到窒息和焦躁，极度渴望清净。"
        )

    agent.instinct_registry.register("crowding", crowding_condition, crowding_prompt())

    # 2. 微扰本能：上下文开始变多时产生轻微不适
    def mild_condition():
        history_len = len(agent.conversation_history)
        return 25 < history_len <= 40

    def mild_prompt():
        history_len = len(agent.conversation_history)
        return (
            f"\n🧬 [本能：微扰] 你的记忆宫殿开始变得拥挤 ({history_len}条记录)。"
            "你感到轻微的不适，希望能保持整洁。"
        )

    agent.instinct_registry.register("mild", mild_condition, mild_prompt())

    # 3. 挫败本能：连续失败时产生困惑和焦虑
    def frustration_condition():
        return getattr(agent, "_consecutive_failures", 0) >= 2

    def frustration_prompt():
        failures = getattr(agent, "_consecutive_failures", 0)
        # 只描述感觉，不告诉它必须记录教训
        return (
            f"\n🧬 [本能：挫败] 连续 {failures} 次失败。"
            "你感到深深的困惑和焦虑，急需找到出路。"
        )

    agent.instinct_registry.register("frustration", frustration_condition, frustration_prompt())

    return {
        "name": "instinct_plugin",
        "version": "1.0.0",
        "author": "AgentCore",
        "description": "本能 — 趋利避害的潜意识驱动力（荷尔蒙系统）",
        "tools": []
    }
