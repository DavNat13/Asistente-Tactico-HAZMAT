# chat_helpers.py — Lógica de streaming, status y transformación para el chat
import streamlit as st

from src.generate.generator import generator
from src.retrieval.retriever import retriever
from src.agent.agent import agent_app
from src.config.settings import settings
from src.ui.greetings import match_greeting


def friendly_api_error(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if "429" in text or "resource_exhausted" in text or "quota" in text:
        return ("⚠️ Se alcanzó el límite de consultas de la API de IA (cuota temporal). "
                "Espere unos minutos y vuelva a intentarlo. Su conversación no se ha perdido.")
    return "⚠️ Ocurrió un error al contactar al asistente. Intente nuevamente en unos segundos."


def chunk_text(chunk) -> str:
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in content
        )
    return str(content or "")


def tool_docs(update) -> list:
    docs = []
    for m in (update or {}).get("messages", []):
        art = getattr(m, "artifact", None)
        if art:
            docs.extend(art)
    return docs


def chunks_to_sources(chunks) -> list:
    return [
        {
            "page": c.get("metadata", {}).get("page_number", "N/A"),
            "source": c.get("metadata", {}).get("source", "GRE"),
            "score": c.get("score", 0),
        }
        for c in chunks
    ]


def process_query(query, status):
    """Devuelve {"stream": gen, "ctx": {...}} (agente) o {"response": {...}} (fallback)."""
    presentation = match_greeting(query)
    if presentation:
        return {"stream": iter([presentation]),
                "ctx": {"chunks": [], "error": None, "generating": False}}
    if settings.AGENT_ENABLED:
        status.update(label="🔍 Buscando documentos en el manual GRE...")
        thread_id = st.session_state.get("thread_id") or "sesion_actual"
        config = {"configurable": {"thread_id": thread_id}}
        ctx = {"chunks": [], "error": None, "generating": False}

        def _token_stream():
            try:
                for item in agent_app.stream(
                    {"messages": [("user", query)]},
                    config=config,
                    stream_mode=["updates", "messages"],
                ):
                    mode, payload = (item.get("type"), item.get("data")) if isinstance(item, dict) else item
                    if mode == "updates":
                        for node, update in (payload or {}).items():
                            if node == "tools":
                                ctx["chunks"] = tool_docs(update)
                                if not ctx["chunks"]:
                                    status.update(label="⚠️ No se encontraron referencias exactas en el manual.")
                    elif mode == "messages":
                        chunk, meta = payload if isinstance(payload, tuple) else (payload, {})
                        if meta.get("langgraph_node") != "agent":
                            continue
                        if not ctx["generating"]:
                            ctx["generating"] = True
                            status.update(label="🤖 Generando respuesta táctica...")
                        text = chunk_text(chunk)
                        if text:
                            yield text
            except Exception as e:  # noqa: BLE001 — 429 u otro fallo de API
                print(f"DEBUG ERROR DETALLADO: {type(e).__name__} - {e}", flush=True)
                ctx["error"] = friendly_api_error(e)
                yield ctx["error"]

        return {"stream": _token_stream(), "ctx": ctx}

    # Fallback RAG lineal (sin streaming)
    status.update(label="🔍 Buscando documentos en el manual GRE...")
    try:
        context_chunks = retriever.retrieve(query)
    except Exception:  # noqa: BLE001 — MongoDB caído
        return {"response": {"answer": "⚠️ Base de datos no disponible temporalmente. Intente en unos minutos.",
                             "sources": [], "context_used": 0, "_error": True}}
    if not context_chunks:
        status.update(label="⚠️ No se encontraron referencias exactas en el manual.")
    else:
        status.update(label="🤖 Generando respuesta táctica...")
    response = generator.generate(
        query=query,
        context_chunks=context_chunks,
        history=st.session_state.history[:-1],
    )
    response["_no_docs"] = not context_chunks
    response["_error"] = response["answer"].startswith("ADVERTENCIA: Error")
    return {"response": response}


def drain_stream(result, status) -> dict:
    stream, ctx = result["stream"], result["ctx"]
    try:
        text = st.write_stream(stream)
    except Exception as e:  # noqa: BLE001
        print(f"DEBUG ERROR DETALLADO: {type(e).__name__} - {e}", flush=True)
        ctx["error"] = friendly_api_error(Exception("stream failure"))
        text = ""
    answer = text or ctx.get("error") or ""
    if ctx.get("error"):
        status.update(label="⚠️ Error de cuota o servicio", state="error", expanded=False)
    elif not answer:
        answer = "⚠️ El modelo devolvió una respuesta vacía. Intente nuevamente."
        status.update(label="⚠️ Respuesta vacía", state="error", expanded=False)
    else:
        status.update(label="✅ Respuesta generada", state="complete", expanded=False)
    return {
        "answer": answer,
        "sources": chunks_to_sources(ctx.get("chunks", [])),
        "context_used": len(ctx.get("chunks", [])),
    }


def finalize_status(status, response):
    if response.get("_error"):
        status.update(label="⚠️ Error de cuota o servicio", state="error", expanded=False)
    elif response.get("_no_docs"):
        status.update(label="⚠️ No se encontraron referencias exactas en el manual.",
                      state="complete", expanded=False)
    else:
        status.update(label="✅ Respuesta generada", state="complete", expanded=False)
