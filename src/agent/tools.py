from langchain_core.tools import tool
from src.retrieval.retriever import retriever

@tool(response_format="content_and_artifact")
def buscar_normas_hazmat(query: str) -> tuple[str, list]:
    """Consulta la base HAZMAT/GRE de Bomberos de Chile. 
    Contiene normas de transporte, símbolos, clases de riesgo, distancias y tácticas.
    Úsala para responder preguntas técnicas sobre emergencias con materiales peligrosos.
    NO la uses para saludos o conversación general."""
    chunks = retriever.retrieve(query)
    segments = []
    for chunk in chunks:
        if isinstance(chunk, dict):
            text = chunk.get("text", "")
            page = chunk.get("metadata", {}).get("page_number", "N")
        else:
            text, page = getattr(chunk, 'page_content', str(chunk)), "N"
        segments.append(f"[GRE p. {page}]\n{text}")
    content = "\n\n---\n\n".join(segments) or "Sin resultados en el manual GRE para esta consulta."
    return content, chunks
