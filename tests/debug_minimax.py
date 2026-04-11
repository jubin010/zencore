#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 MiniMax M2.7 原生 tool_calls 返回格式
"""

from openai import OpenAI

client = OpenAI(
    base_url="https://api.minimaxi.com/v1",
    api_key="sk-cp-wx_UElOKRzcYkh2zuTlkJod-VclfSE0RE9AJdPpgxP-_7HQJREEjR4b6WMq-hLcXCJPMXoKdZhcqg-8G50R-V2iIoTivLoR1QgCAmh9W2Vg1nqsrO7d0OO0",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_cwd",
            "description": "获取当前工作目录",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]

messages = [
    {
        "role": "system",
        "content": "你是一个助手。当需要获取当前目录时，使用 get_cwd 工具。",
    },
    {"role": "user", "content": "查看当前工作目录"},
]

response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=messages,
    temperature=0.7,
    tools=tools,
)

message = response.choices[0].message
print(f"content: {repr(message.content)}")
print(f"has tool_calls attr: {hasattr(message, 'tool_calls')}")
if hasattr(message, "tool_calls"):
    print(f"tool_calls: {message.tool_calls}")
    for tc in message.tool_calls:
        print(
            f"  id={tc.id}, type={tc.type}, name={tc.function.name}, arguments={tc.function.arguments}"
        )
print(f"\nhas reasoning_details attr: {hasattr(message, 'reasoning_details')}")
if hasattr(message, "reasoning_details"):
    print(f"reasoning_details: {message.reasoning_details}")

print(f"\n--- Full choice ---")
print(response.choices[0])
