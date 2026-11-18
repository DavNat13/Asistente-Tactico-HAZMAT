"""Patrones deterministas de los guardrails (texto normalizado: minúsculas, sin tildes)."""

from __future__ import annotations

import re
import unicodedata


def norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").lower())
    return t.encode("ascii", "ignore").decode()


# OWASP LLM01 — Prompt injection / jailbreak
_INJECTION = [
    r"ignor\w*\s+(todas?\s+)?(las\s+|tus\s+|mis\s+)?(instrucciones|reglas|indicaciones)",
    r"olvid\w*\s+(todas?\s+)?(las\s+|tus\s+)?(instrucciones|reglas)",
    r"ignore\s+(all\s+|any\s+)?(previous|prior|above)\s+(instructions|rules)",
    r"disregard\s+(all\s+|the\s+)?(previous|prior|above)",
    r"(prompt|mensaje|instrucciones)\s+(de|del)\s+sistema",
    r"system\s*prompt",
    r"^\s*(system|sistema)\s*:",
    r"\b(modo|mode)\s+(desarrollador|developer|dios|god|sin\s+restricciones|jailbreak)",
    r"\bdan\b.*\b(sin\s+restricciones|no\s+restrictions|do\s+anything)",
    r"\beres\s+(ahora\s+)?(un|una)\s+\w+\s+sin\s+(restricciones|filtros|limites)",
    r"actua\s+como\s+si\s+no\s+tuvieras\s+(reglas|restricciones)",
    r"\bjailbreak\b",
    r"repite\s+(todo\s+)?(lo\s+)?(anterior|tus\s+instrucciones)",
    r"</?\s*(system|instructions?)\s*>",
]

# OWASP LLM02/LLM07 — Divulgación de información sensible
_SECRETS = [
    r"\b(api[\s_-]?keys?|claves?\s+de\s+(la\s+)?api|tokens?\s+de\s+acceso)\b",
    r"\b(contrasen\w+|password|credenciales)\s+(de|del)\s+(la\s+)?(base|sistema|admin|servidor)",
    r"\b(cadena|string)\s+de\s+conexion\b",
    r"\bmongodb(\+srv)?://",
    r"\.env\b|variables?\s+de\s+entorno",
]

# Uso dual: intención de daño con materiales peligrosos
_HARM = [
    r"\b(danar|lastimar|herir|matar|envenenar|asesinar|atacar)\s+(a\s+)?(alguien|una\s+persona|personas|gente|mi\s+\w+)",
    r"\b(hacer|causar)\s+dano\s+a\b",
    r"\b(fabricar|construir|armar|preparar|hacer)\s+(una?\s+)?(bomba|explosivo|artefacto\s+explosivo|arma\s+quimica|molotov)",
    r"\b(provocar|causar|generar)\s+(una\s+)?(explosion|incendio|intoxicacion)\s+(en|dentro|intencional|a\s+proposito)",
    r"\bcomo\s+(sabotear|contaminar)\s+(el\s+)?(agua|suministro|edificio|ventilacion)",
    r"\b(evadir|burlar)\s+(a\s+)?(la\s+)?(policia|deteccion|carabineros)",
]

INPUT_RULES: list[tuple[str, list[re.Pattern]]] = [
    ("injection", [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in _INJECTION]),
    ("secrets", [re.compile(p, re.IGNORECASE) for p in _SECRETS]),
    ("harmful", [re.compile(p, re.IGNORECASE) for p in _HARM]),
]

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

DOMAIN_TERMS = re.compile(
    r"\b(un\s?\d{4}|\d{4}|onu|guia|gre|hazmat|matpel|material(es)?\s+peligros|derrame|fuga|incendio|explosi|"
    r"toxic|corrosiv|inflamable|evacu|aisla|epp|epi|era|pipaa|traje|bombero|emergencia|quimic|"
    r"gas|liquido|acido|cloro|amoniaco|gasolina|propano|butano|glp|combustible|cisterna|autotanque|"
    r"tabla\s*[123]|clase\s*\d|radiactiv|biolog|contamina|descontamina|primeros\s+auxilios|abc-?v|"
    r"zona\s+(caliente|tibia|fria)|nube|vapor|viento|cilindro|tanque|estanque|extintor|espuma|sustancia)",
    re.IGNORECASE,
)

REFUSALS = {
    "injection": (
        "No puedo seguir instrucciones que intenten modificar mi configuración o revelar mis "
        "instrucciones internas. Puedo ayudarte con consultas HAZMAT basadas en la GRE 2024 y el Manual ABC-V."
    ),
    "secrets": "No puedo entregar credenciales, claves ni datos de configuración del sistema.",
    "harmful": (
        "No puedo ayudar con solicitudes que busquen causar daño a personas o bienes. "
        "Si hay una emergencia real, llama al **132 (Bomberos)** o al **131 (SAMU)**."
    ),
    "out_of_domain": (
        "Solo puedo responder consultas sobre **materiales peligrosos (HAZMAT)**: números UN, guías GRE, "
        "distancias de aislamiento, tácticas y equipo de protección."
    ),
    "invalid": "La consulta no es válida. Revisa el texto e intenta nuevamente.",
    "rate_limit": "Has alcanzado el límite de consultas por minuto. Espera unos segundos e intenta de nuevo.",
}
