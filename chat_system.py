# -*- coding: utf-8 -*-
"""
聊天系统已合并到 main.py
此文件保留用于向后兼容
"""

from main import (
    Server,
    SendTextArea,
    ChatUI,
    HumanClient,
    AIClient,
    run_chat,
    get_active_model,
    list_models,
)

__all__ = [
    "Server",
    "SendTextArea",
    "ChatUI",
    "HumanClient",
    "AIClient",
    "run_chat",
    "get_active_model",
    "list_models",
]
