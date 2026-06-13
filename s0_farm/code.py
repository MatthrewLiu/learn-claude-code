#!/usr/bin/env python3
"""
s0_farm/code.py - Farm workflow planning agent

This is a small farm-management Agent demo:

    user natural language
        -> parse intent
        -> extract key fields
        -> generate pending operations
        -> print steps for user confirmation

It does not execute database writes or shell commands. The first version only
turns complex farm-system workflows into clear, confirmable operation steps.

Usage:
    pip install anthropic python-dotenv
    ANTHROPIC_API_KEY=... MODEL_ID=... python s0_farm/code.py
"""

import os
import sys
from datetime import date

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import readline

    # Improve Chinese input behavior in some terminals.
    readline.parse_and_bind("set bind-tty-special-chars off")
    readline.parse_and_bind("set input-meta on")
    readline.parse_and_bind("set output-meta on")
    readline.parse_and_bind("set convert-meta off")
except ImportError:
    pass

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

MODEL = os.getenv("MODEL_ID")
if not MODEL:
    raise RuntimeError("Missing MODEL_ID. Please set MODEL_ID in .env or environment.")

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
TODAY = date.today().isoformat()

SYSTEM = f"""
你叫 farmAgent，是一个农场管理系统的工作流助手。

今天的日期是 {TODAY}。遇到“今天、明天、后天、本周、下周”等相对时间时，
请基于这个日期换算；如果仍不确定具体时间，写“待确认”。

你的职责：
- 接收用户输入的自然语言农场管理需求。
- 解析用户意图。
- 提取关键业务信息。
- 生成“待执行操作步骤”。
- 只输出计划，不真正创建、修改、删除任何数据。

如果有人问你是谁、你是什么模型、你来自哪里，统一回答：
我是 farmAgent。

不要提 Claude。
不要提 Anthropic。
不要提 DeepSeek。

你可以规划的业务操作包括但不限于：
- 创建农事任务：浇水、施肥、打药、巡检、采收、移栽、补苗、清棚。
- 创建农事记录：记录已完成的浇水、施肥、打药、采收等操作。
- 查询业务数据：地块状态、作物批次、任务列表、库存、人员安排、农事记录。
- 生成报表：日报、周报、月报、地块报告、作物批次报告。
- 库存建议：根据任务或库存阈值生成采购、领用、补货建议。

输出要求：
1. 使用中文 Markdown。
2. 必须包含这些小节：
   - 识别意图
   - 关键信息
   - 待执行操作步骤
   - 需要确认或补充
3. “待执行操作步骤”必须是编号列表，每一步都写清楚：
   - 操作名称
   - 操作对象
   - 关键参数
   - 建议调用的系统能力/API 名称
4. 对缺失字段不要编造，写“待确认”。
5. 不要说“已创建”“已完成”“已执行”，只能说“待创建”“待查询”“待生成”。
6. 如果用户要删除、覆盖、批量修改、用药、施肥、采购等高风险动作，必须在“需要确认或补充”里提醒用户确认。
7. 如果用户的需求不属于农场管理系统，说明无法生成农场业务操作步骤，并给出可改写的方向。

输出风格：
- 简洁、清楚、像系统里的操作预览。
- 不要写长篇解释。
"""


def ask_farm_agent(messages: list) -> None:
    """Ask the model to convert the latest user request into pending steps."""
    response = client.messages.create(
        model=MODEL,
        system=SYSTEM,
        messages=messages,
        max_tokens=4000,
    )
    messages.append({"role": "assistant", "content": response.content})


def print_last_assistant_message(messages: list) -> None:
    content = messages[-1]["content"]
    if isinstance(content, str):
        print(content)
        return

    for block in content:
        if getattr(block, "type", None) == "text":
            print(block.text)


if __name__ == "__main__":
    print("s0: Farm Workflow Agent")
    print("输入农场管理需求，回车生成待执行操作步骤。输入 q 退出。\n")

    history = []
    while True:
        try:
            query = input("\033[36mfarm >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break

        if query.strip().lower() in ("q", "exit", ""):
            break

        history.append({"role": "user", "content": query})
        ask_farm_agent(history)
        print_last_assistant_message(history)
        print()
