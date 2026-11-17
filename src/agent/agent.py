"""Grafo LangGraph del Asistente HAZMAT v5 (agente por niveles de complejidad).

    START → guard_in ─┬─ bloqueado ─────────────────────────────→ direct → END
                      └─ classify ─┬─ low ──────────────────────→ direct → END
                                   └─ medium/high → prefetch → agent ⇄ tools
                                                                  └→ guard_out → END

El presupuesto de herramientas (settings.TOOL_BUDGET) lo impone el código, no el prompt:
al agotarse, el modelo se invoca SIN herramientas y debe responder con lo recuperado.
"""

from __future__ import annotations

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.context import format_docs
from src.agent.llm_factory import LLMRouter
from src.agent.nodes import (
    classify_node,
    direct,
    guard_in,
    guard_out,
    prefetch_node,
    timed,
)
from src.agent.prompts import (
    CONTEXT_TEMPLATE,
    HIGH_ADDENDUM,
    MEDIUM_ADDENDUM,
    SYSTEM_PROMPT,
)
from src.agent.states import AgentState
from src.agent.tools import TOOLS
from src.config.settings import settings

_router: LLMRouter | None = None
_tool_node = ToolNode(TOOLS)


def get_router() -> LLMRouter:
    global _router
    if (
        _router is None
    ):  # perezoso: importar el grafo no crea clientes ni consume llaves
        _router = LLMRouter(TOOLS)
    return _router


def _window(messages: list) -> list:
    """Historial previo (solo texto) recortado + turno actual completo (pares tool intactos)."""
    last_h = max((i for i, m in enumerate(messages) if m.type == "human"), default=0)
    prior = [m for m in messages[:last_h] if m.type in ("human", "ai") and m.content]
    prior = prior[-settings.AGENT_HISTORY_MESSAGES :]
    while (
        prior and prior[0].type != "human"
    ):  # Gemini exige iniciar con un turno de usuario
        prior = prior[1:]
    return prior + messages[last_h:]


@timed("agent")
def agent_node(state: AgentState) -> dict:
    level = state.get("complexity", "medium")
    addendum = HIGH_ADDENDUM if level == "high" else MEDIUM_ADDENDUM
    system = (
        SYSTEM_PROMPT
        + addendum
        + CONTEXT_TEMPLATE.format(documents=format_docs(state.get("context", [])))
    )
    budget = settings.TOOL_BUDGET.get(level, 2)
    with_tools = state.get("tool_calls", 0) < budget
    response = get_router().invoke(
        [SystemMessage(content=system), *_window(state["messages"])],
        with_tools=with_tools,
    )
    return {"messages": [response]}


@timed("tools")
def tools_node(state: AgentState) -> dict:
    result = _tool_node.invoke(state)
    messages = result["messages"]
    docs = [d for m in messages for d in (getattr(m, "artifact", None) or [])]
    return {
        "messages": messages,
        "docs": docs,
        "tool_calls": state.get("tool_calls", 0) + len(messages),
    }


def _after_guard(state: AgentState) -> str:
    return "direct" if state.get("blocked") else "classify"


def _after_classify(state: AgentState) -> str:
    return "direct" if state.get("complexity") == "low" else "prefetch"


def _after_agent(state: AgentState) -> str:
    return (
        "tools" if getattr(state["messages"][-1], "tool_calls", None) else "guard_out"
    )


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("guard_in", guard_in)
    g.add_node("classify", classify_node)
    g.add_node("direct", direct)
    g.add_node("prefetch", prefetch_node)
    g.add_node("agent", agent_node)
    g.add_node("tools", tools_node)
    g.add_node("guard_out", guard_out)

    g.add_edge(START, "guard_in")
    g.add_conditional_edges(
        "guard_in", _after_guard, {"direct": "direct", "classify": "classify"}
    )
    g.add_conditional_edges(
        "classify", _after_classify, {"direct": "direct", "prefetch": "prefetch"}
    )
    g.add_edge("prefetch", "agent")
    g.add_conditional_edges(
        "agent", _after_agent, {"tools": "tools", "guard_out": "guard_out"}
    )
    g.add_edge("tools", "agent")
    g.add_edge("guard_out", END)
    g.add_edge("direct", END)
    return g.compile()


agent_app = build_graph()
