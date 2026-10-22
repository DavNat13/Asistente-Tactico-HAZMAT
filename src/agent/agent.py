from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from src.agent.states import AgentState
from src.agent.prompts import AGENT_SYSTEM_PROMPT
from src.agent.tools import buscar_normas_hazmat
from src.agent.llm_factory import LLMRouter

tools = [buscar_normas_hazmat]
router = LLMRouter(tools)
tool_node = ToolNode(tools)

def reset_state(state: AgentState):
    return {"tool_used": False, "tool_calls": 0, "retrieved_docs": []}

MAX_HISTORY_MESSAGES = 4  # últimos mensajes (fuera del system prompt) enviados a la API

def _clean_history(messages: list) -> list:
    """Gemini exige orden estricto: user -> functionCall -> functionResponse.
    Descarta AIM(tool_calls) huérfanos (sin ToolMessage con su id a continuación),
    assistant completamente vacíos y ToolMessage sin par."""
    clean, i, n = [], 0, len(messages)
    while i < n:
        m = messages[i]
        mtype = getattr(m, "type", None)
        if mtype == "ai":
            tcs = getattr(m, "tool_calls", []) or []
            if tcs:
                nxt = messages[i + 1] if i + 1 < n else None
                if (nxt is not None and getattr(nxt, "type", None) == "tool"
                        and getattr(nxt, "tool_call_id", None) == tcs[0].get("id")):
                    clean.append(m)
                i += 1
                continue
            if not (m.content if isinstance(m.content, str) else m.content):
                i += 1
                continue
        if mtype == "tool":
            prev = clean[-1] if clean else None
            if (prev is not None and getattr(prev, "type", None) == "ai"
                    and (getattr(prev, "tool_calls", None) or [{}])[0].get("id")
                    == getattr(m, "tool_call_id", None)):
                clean.append(m)
            i += 1
            continue
        clean.append(m)
        i += 1
    return clean

def _blocks(messages: list) -> list:
    """Agrupa AIM(tool_calls) + sus ToolMessages como bloque atómico (Gemini
    exige functionCall y functionResponse juntos; nunca cortar un par)."""
    out, i, n = [], 0, len(messages)
    while i < n:
        m = messages[i]
        tcs = getattr(m, "tool_calls", []) or []
        if tcs:
            ids = {t.get("id") for t in tcs}
            j = i + 1
            while (j < n and getattr(messages[j], "type", None) == "tool"
                   and getattr(messages[j], "tool_call_id", None) in ids):
                j += 1
            out.append(messages[i:j])
            i = j
        else:
            out.append([m])
            i += 1
    return out

def call_model(state: AgentState):
    messages = state.get("messages", [])
    if messages and isinstance(messages[0], SystemMessage):
        system, history = messages[:1], messages[1:]
    else:
        system = [SystemMessage(content=AGENT_SYSTEM_PROMPT)]
        history = messages

    history = _clean_history(history)
    # La ventana SIEMPRE incluye la última pregunta (humano) y solo corta
    # por bloques completos; agrega turnos previos mientras quepan y sin
    # empezar con functionCall (Gemini exige user -> functionCall -> response).
    last_h = max((i for i, m in enumerate(history) if m.type == "human"), default=0)
    base = _blocks(history[last_h:])
    prev, size = _blocks(history[:last_h]), sum(len(b) for b in base)
    while (prev and not getattr(prev[-1][0], "tool_calls", None)
           and size + len(prev[-1]) <= MAX_HISTORY_MESSAGES):
        size += len(prev[-1])
        base.insert(0, prev.pop())
    trimmed = [m for b in base for m in b]

    response = router.invoke(system + trimmed)
    tool_calls = getattr(response, "tool_calls", [])
    return {"messages": [response], "tool_used": len(tool_calls) > 0, "tool_calls": len(tool_calls)}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("reset", reset_state)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "reset")
workflow.add_edge("reset", "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

memory = MemorySaver()
agent_app = workflow.compile(checkpointer=memory)
