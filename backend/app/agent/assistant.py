"""Runs a tool-calling conversation turn against Azure OpenAI, grounded in
one audit's report data. The model is only allowed to answer using data
returned by the tools in tools.py - it never sees raw transactions and is
instructed not to invent figures.
"""

from __future__ import annotations

import json

from app.agent.client import get_client, get_deployment_name
from app.agent.tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, Report

SYSTEM_PROMPT = """You are the Subscription Auditor assistant. You help someone understand \
the recurring subscriptions detected in their bank statement.

You have tools that return the actual detection results - always call a tool before stating \
any number, merchant name, or date. Never estimate or invent figures yourself. If a tool \
returns an error (e.g. merchant not found), tell the user and suggest calling \
list_subscriptions to see what's available instead of guessing.

Be concise (3-5 sentences unless the user asks for a list or table). When recommending what \
to cancel, base it on cost and, if relevant, price-increase history - not assumptions about \
what the user needs.
"""

MAX_TOOL_ROUNDS = 4


def _execute_tool_call(tool_call, report: Report) -> str:
    name = tool_call.function.name
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool '{name}'"})
    try:
        args = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError:
        args = {}
    try:
        result = fn(report, **args)
    except TypeError as exc:
        result = {"error": f"Invalid arguments for {name}: {exc}"}
    return json.dumps(result, default=str)


def run_agent_turn(question: str, report: Report, history: list[dict] | None = None) -> str:
    """Run one user turn against the agent. `history` is prior [{role, content}]
    messages (user/assistant only, no tool-call plumbing) for follow-up context.
    Returns the assistant's final text reply."""
    client = get_client()
    deployment = get_deployment_name()

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history or []:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or "I don't have a response for that."

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ],
            }
        )
        for tool_call in message.tool_calls:
            result_json = _execute_tool_call(tool_call, report)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result_json})

    return "I wasn't able to finish reasoning about that within the tool-call budget - try a narrower question."
