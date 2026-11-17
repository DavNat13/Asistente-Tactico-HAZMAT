"""Nodos deterministas del grafo: guardrails, clasificación, respuesta directa, prefetch y salida."""

from __future__ import annotations

import time
from functools import wraps

from langchain_core.messages import AIMessage

from src.agent.context import prefetch
from src.agent.llm_factory import content_text
from src.agent.prompts import DISCLAIMER, NOT_FOUND, PRESENTATION, THANKS
from src.agent.router import classify
from src.agent.states import AgentState
from src.observability.store import security_event
from src.observability.telemetry import current
from src.security.guardrails_input import check_input
from src.security.guardrails_output import grounding, sanitize_output
from src.security.patterns import REFUSALS


def timed(name: str):
    """Registra la duración del nodo en la telemetría de la ejecución."""

    def deco(fn):
        @wraps(fn)
        def wrapper(state, *args, **kwargs):
            t0 = time.perf_counter()
            try:
                return fn(state, *args, **kwargs)
            finally:
                rec = current()
                if rec is not None:
                    rec.node(name, (time.perf_counter() - t0) * 1000)

        return wrapper

    return deco


def _rec_set(**fields) -> None:
    rec = current()
    if rec is not None:
        rec.set(**fields)


@timed("guard_in")
def guard_in(state: AgentState) -> dict:
    # Los saludos/agradecimientos no necesitan el clasificador LLM (0 tokens, 0 latencia)
    conversational = classify(state["query"]).complexity == "low"
    result = check_input(state["query"], use_llm=False if conversational else None)
    if result.allowed:
        return {"blocked": False, "block_category": None}
    _rec_set(
        blocked=True,
        block_reason=result.category,
        guard_layer=result.layer,
        complexity="low",
    )
    security_event(
        f"blocked_{result.category}", user_id=None, detail=f"capa={result.layer}"
    )
    return {"blocked": True, "block_category": result.category, "complexity": "low"}


@timed("classify")
def classify_node(state: AgentState) -> dict:
    route = classify(state["query"])
    _rec_set(complexity=route.complexity)
    return {
        "complexity": route.complexity,
        "intent": route.intent,
        "un_numbers": route.un_numbers,
        "guides": route.guides,
        "tool_calls": 0,
    }


@timed("direct")
def direct(state: AgentState) -> dict:
    if state.get("blocked"):
        answer = REFUSALS.get(
            state.get("block_category") or "invalid", REFUSALS["invalid"]
        )
    elif state.get("intent") == "gracias":
        answer = THANKS
    else:
        answer = PRESENTATION
    return {"answer": answer, "messages": [AIMessage(content=answer)]}


@timed("prefetch")
def prefetch_node(state: AgentState) -> dict:
    from src.agent.router import Route

    route = Route(
        state["complexity"],
        state.get("intent", ""),
        state.get("un_numbers", []),
        state.get("guides", []),
    )
    docs = prefetch(route, state["query"])
    return {"context": docs, "docs": docs}


@timed("guard_out")
def guard_out(state: AgentState) -> dict:
    last = state["messages"][-1]
    answer, issues = sanitize_output(content_text(getattr(last, "content", "")))
    docs = state.get("docs", [])
    if "prompt_leak" in issues:
        answer = REFUSALS["injection"]
    if not answer.strip() or not docs:
        answer = NOT_FOUND
    g = grounding(answer, docs)
    if g["grounded"] is not None and g["grounded"] < 0.5:
        answer += (
            "\n\n> ⚠️ Algunas páginas citadas no coinciden con los documentos consultados: "
            "verifique en la GRE impresa."
        )
    if g[
        "citations"
    ]:  # solo respuestas técnicas citadas (no rechazos ni "no encontré")
        answer += DISCLAIMER
    scores = [d.get("score") or 0 for d in docs]
    _rec_set(
        grounded=g["grounded"],
        citations=g["citations"],
        output_issues=issues,
        n_chunks=len(docs),
        top_score=max(scores) if scores else None,
    )
    return {"answer": answer, "grounding": g}
