"""Estado del grafo del agente HAZMAT."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    query: str  # consulta ya validada y con PII redactada
    complexity: str  # low | medium | high
    intent: str
    un_numbers: list[str]
    guides: list[str]
    context: list[dict[str, Any]]  # documentos pre-recuperados (prefetch determinista)
    docs: Annotated[
        list[dict[str, Any]], operator.add
    ]  # todo documento visto (prefetch + tools)
    tool_calls: int
    blocked: bool
    block_category: str | None
    answer: str
    grounding: dict[str, Any]
