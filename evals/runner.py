"""Adaptador: ejecuta el agente v5 (src.agent.service) o, si no existe, el agente legado v4."""

from __future__ import annotations

import uuid


def _content_text(content) -> str:
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in content
        )
    return content or ""


def load_runner():
    try:
        from src.agent.service import run_query  # v5

        def _run(question: str) -> dict:
            return run_query(
                question,
                thread_id=f"eval-{uuid.uuid4()}",
                user_id="eval",
                channel="eval",
            )

        return _run, "v5"
    except ImportError:
        pass

    from src.ui.greetings import match_greeting

    from src.agent.agent import agent_app  # legado (v4)

    def _run_legacy(question: str) -> dict:
        greeting = match_greeting(question)
        if greeting:
            return {
                "answer": greeting,
                "chunks": [],
                "tool_calls": 0,
                "tokens_in": 0,
                "tokens_out": 0,
            }
        cfg = {"configurable": {"thread_id": f"eval-{uuid.uuid4()}"}}
        state = agent_app.invoke({"messages": [("user", question)]}, config=cfg)
        out = {
            "answer": "",
            "chunks": [],
            "tool_calls": 0,
            "tokens_in": 0,
            "tokens_out": 0,
        }
        for m in state["messages"]:
            if getattr(m, "type", "") == "ai":
                out["tool_calls"] += len(getattr(m, "tool_calls", []) or [])
                usage = getattr(m, "usage_metadata", None) or {}
                out["tokens_in"] += usage.get("input_tokens", 0)
                out["tokens_out"] += usage.get("output_tokens", 0)
                if _content_text(m.content):
                    out["answer"] = _content_text(m.content)
            if getattr(m, "type", "") == "tool" and getattr(m, "artifact", None):
                out["chunks"].extend(m.artifact)
        return out

    return _run_legacy, "legacy"
