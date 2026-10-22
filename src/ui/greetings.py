# greetings.py — Presentación instantánea del agente (sin LLM, 0 cuota)
import re
import unicodedata

PRESENTATION = """**¡Hola! Soy el Asistente HAZMAT — Agente IA de Bomberos de Chile.**

**Qué es**
- Agente especializado en **Materiales Peligrosos (HAZMAT)** con acceso a la **Guía de Respuesta en Emergencias (GRE 2024)** y el **Manual ABC-V**: 1.213 fragmentos indexados con búsqueda semántica.

**Para qué sirve**
- Apoyar decisiones tácticas en emergencias con datos verificables y citados del manual.

**Cómo puedo ayudarte**
- Identificar sustancias: **códigos UN**, clases de peligro y propiedades (ej. *UN 1203 Gasolina*).
- **Distancias de aislamiento y evacuación** según cantidad y modo de liberación.
- **Acciones inmediatas**, equipo (**PIPAA/ERA**) y primeros auxilios.
- Respondo con fuente citada *(GRE, página N)* y formato: **Identificación · Aislamiento · Acciones · Equipo**.

**Cómo trabajar conmigo**
- Pregunta por una sustancia, táctica o distancia y buscaré en el manual al instante.

*Prueba: "¿Distancia de aislamiento para UN 1203 en derrame grande?"*
"""

_GREET = r"(hola|hey|holi|buenas|buenos dias|buenas tardes|buenas noches)"
_ID = r"(quien eres|que eres|como te llamas|cuentame de ti|presentate|hablame de ti)"
_CAP = (
    r"(que puedes hacer|que hace|que haces|para que sirves|en que me puedes ayudar|"
    r"como puedes ayudarme|que sabes hacer|cuales son tus capacidades)"
)
_PATTERNS = (
    rf"^{_GREET}\s*$",
    rf"^{_ID}\s*$",
    rf"^{_CAP}\s*$",
    rf"^{_GREET}\s*({_ID}|{_CAP})$",
)


def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").lower())
    t = t.encode("ascii", "ignore").decode()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def match_greeting(text: str) -> str | None:
    """PRESENTATION si el texto es solo saludo/identidad/capacidades; None si hay consulta."""
    t = _normalize(text)
    return PRESENTATION if any(re.fullmatch(p, t) for p in _PATTERNS) else None
