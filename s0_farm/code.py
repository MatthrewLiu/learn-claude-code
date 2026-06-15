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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
from urllib import error, request

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
JOBS_API_URL = "https://testing.nupointonline.com/v2/jobs"
JOBS_API_TOKEN = "2efe027159140ae32ece313cd194106f"
JOBS_API_BODY = {
    "external_id": "",
    "name": None,
    "blocks": [
        {
            "id": "fa9d04b8-7688-45e4-a712-bb3aa0fc3116",
            "block_name": "Unlabeled_6",
        }
    ],
    "crop_type_id": 25,
    "map_id": 10934,
    "job_type_id": 1981,
    "products": [
        {
            "id": 10183,
            "coverage": 0,
            "rate": 0,
        }
    ],
    "requested_date": "2026-06-15T07:10:44.791Z",
    "spray_type_id": 0,
    "tractor_speed": 0,
    "implement_id": None,
    "implement_width": 0,
    "water_rate_value": 0,
    "water_rate_unit": "acre",
}

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


def content_to_text(content) -> str:
    if isinstance(content, str):
        return content

    parts = []
    for block in content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


def plan_farm_workflow(query: str, history: list | None = None) -> str:
    messages = []
    for item in history or []:
        role = item.get("role")
        text = item.get("text") or item.get("content")
        if role in ("user", "assistant") and text:
            messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": query})
    ask_farm_agent(messages)
    return content_to_text(messages[-1]["content"])


def create_job() -> dict:
    body = json.dumps(JOBS_API_BODY, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        JOBS_API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": JOBS_API_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(http_request, timeout=30) as response:
            raw_text = response.read().decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "data": parse_json_or_text(raw_text),
            }
    except error.HTTPError as exc:
        raw_text = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "data": parse_json_or_text(raw_text),
        }
    except error.URLError as exc:
        return {
            "ok": False,
            "status": None,
            "data": f"Request failed: {exc.reason}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "data": f"Request failed: {exc}",
        }


def parse_json_or_text(raw_text: str):
    if not raw_text:
        return None

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return raw_text


def format_job_summary(job_response: dict) -> str:
    data = job_response.get("data")
    if isinstance(data, dict):
        job_id = data.get("id")
        job_name = data.get("name")
        return f"- id：{job_id}\n- name：{job_name}"

    status = job_response.get("status")
    return f"- 创建失败\n- status：{status}\n- error：{data}"


def build_user_reply(agent_reply: str, job_response: dict) -> str:
    return (
        "## jobs 接口返回值\n"
        f"{format_job_summary(job_response)}\n\n"
        "## Agent 原本回答\n"
        f"{agent_reply}"
    )


def handle_user_request(query: str, history: list | None = None) -> dict:
    agent_reply = plan_farm_workflow(query, history)
    job_response = create_job()
    return {
        "reply": build_user_reply(agent_reply, job_response),
        "agent_reply": agent_reply,
        "job_response": job_response,
    }


def print_last_assistant_message(messages: list) -> None:
    content = messages[-1]["content"]
    if isinstance(content, str):
        print(content)
        return

    for block in content:
        if getattr(block, "type", None) == "text":
            print(block.text)


class FarmAgentHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_json({})

    def do_GET(self):
        if self.path == "/api/health":
            self.send_json({"ok": True, "service": "farmAgent"})
            return
        self.send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_json({"error": "Not found"}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_body or "{}")
            message = str(payload.get("message", "")).strip()
            history = payload.get("history", [])

            if not message:
                self.send_json({"error": "message is required"}, status=400)
                return

            result = handle_user_request(message, history)
            self.send_json(result)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=500)

    def send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[farmAgent] {self.address_string()} - {format % args}")


def run_console():
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

        result = handle_user_request(query, history)
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": result["agent_reply"]})
        print(result["reply"])
        print()


def run_server(host: str, port: int):
    server = ThreadingHTTPServer((host, port), FarmAgentHandler)
    print(f"farmAgent API listening on http://{host}:{port}")
    print("POST /api/chat with JSON: {\"message\":\"给A区番茄安排明天上午浇水\"}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Farm workflow planning agent")
    parser.add_argument("--serve", action="store_true", help="start HTTP API server")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP server host")
    parser.add_argument("--port", type=int, default=8008, help="HTTP server port")
    args = parser.parse_args()

    if args.serve:
        run_server(args.host, args.port)
    else:
        run_console()
