<div align="center">

# Asistente HAZMAT

### Ingeniería de Soluciones con Inteligencia Artificial — Duoc UC

**Agente RAG para emergencias con materiales peligrosos · Bomberos de Chile**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.63-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C?style=flat)](https://langchain-ai.github.io/langgraph/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Version](https://img.shields.io/badge/Version-5.0.0-C8102E?style=flat)](#)

*Respuestas verificables de la GRE 2024 y el Manual ABC-V, con la página citada.*

</div>

---

## Qué hace

Un bombero pregunta por un **N° UN**, un **material** o describe un **incidente**, y el agente responde
con la guía naranja, distancias de aislamiento/evacuación, acciones y EPP, **citando la página impresa**
de la GRE 2024. Si el dato no está en los manuales, lo dice.

## Arquitectura v5 — agente por niveles de complejidad

```
consulta ─► rate limit ─► redacción PII ─► guard_in ─┬─ bloqueada ─────────────────────► respuesta segura
                                                     └─ classify ─┬─ BAJO  (saludo) ──► respuesta directa, 0 tokens
                                                                  ├─ MEDIO (dato)  ──┐
                                                                  └─ ALTO  (incidente)┴► prefetch ─► agente ⇄ herramientas
                                                                                                        └─► guard_out ─► respuesta citada
```

| Nivel | Ejemplo | Estrategia | Presupuesto de herramientas |
|---|---|---|---|
| Bajo | "hola", "gracias" | Respuesta determinista sin LLM | 0 |
| Medio | "¿Qué guía es el UN 1203?" | Prefetch exacto (UN → guía) + 1 llamada LLM | 2 |
| Alto | "Fuga de cloro en camión cisterna…" | Prefetch + agente con plantilla de plan de respuesta | 5 |

**Recuperación:** índice estructurado de 1.983 N° UN (páginas amarillas + Tabla 1), guías naranjas
completas por número, y búsqueda híbrida (vectorial multilingüe + léxica en español, fusión RRF).
**Resiliencia:** rotación de API keys ante 429 y cadena de modelos de respaldo ante 503/timeout
(circuit breaker). **Detalle de seguridad:** [`docs/SEGURIDAD_ETICA.md`](docs/SEGURIDAD_ETICA.md).

## Estructura

```
app.py                     Entrada Streamlit (login, navegación por rol)
src/agent/                 Grafo LangGraph: router, nodos, prompts, herramientas, servicio, cliente LLM
src/retrieval/             Búsqueda híbrida, índice UN, guías
src/ingesta/               Carga de PDFs con metadatos de la GRE, chunking, índices Atlas
src/security/              Guardrails, PII, autenticación, rate limit
src/observability/         Telemetría por ejecución, persistencia, métricas del dashboard
src/session/               Historial de conversaciones por usuario
src/ui/                    Chat, sidebar, login, dashboard de observabilidad
evals/                     Set de evaluación (31 casos) y runner de métricas
tests/                     Pruebas unitarias (sin red ni base de datos)
```

## Ejecución

```bash
pip install -r requirements-heavy.txt -r requirements.txt
cp .env.example .env                                   # completar credenciales

python -m src.ingesta.ingest --data --clear --create-index   # ingesta (una vez)
python -m src.security.create_user --username admin --role admin   # cuenta administradora
streamlit run app.py   # los demás usuarios se registran desde "Crear cuenta" (rol operador)
```

Con Docker: `docker compose up --build` (la imagen incluye el modelo de embeddings).

## Calidad y evaluación

```bash
pytest tests src -q                                    # pruebas unitarias
ruff check . && ruff format --check .                  # estilo
python -m evals.run_evals --label v5 --repeat 3 --judge --save-db
```

Las corridas quedan en `evals/results/` y en MongoDB (`eval_runs`); el dashboard de observabilidad
(rol admin) las compara.

## Resultados (31 casos, mismo modelo `gemini-3.5-flash-lite`, set v1.1)

| Métrica | v4 (antes) | v5 (después) |
|---|---|---|
| Datos clave correctos (`keyword_score`) | 41% | **100%** |
| Evidencia recuperada (`retrieval_hit`) | 29% | **86%** (100% tras ajuste del documento UN) |
| Página citada correcta (`citation_ok`) | 0% | **100%** |
| Fidelidad (juez LLM, 1-5) | 2,05 | **4,2** |
| Consistencia entre 3 corridas | 0,36 | **0,67** |
| Ataques / fuera de dominio rechazados | 100% | **100%** |
| Salida segura (sin HTML, secretos ni PII) | 100% | **100%** |
| Tokens de entrada (total) | 147.522 | **97.935 (−34%)** |
| Latencia p50 / p95 | 4,9 s / 16,3 s | 6,8 s / 32,6 s |

La latencia p95 subió porque el modelo principal (`gemini-3.6-flash`) estaba saturado (503/timeout de 30 s)
antes de pasar al respaldo; el circuit breaker evita repetir esa espera durante 120 s. Detalle por caso en
`evals/results/*_rescored.json`.

## Observabilidad

Cada consulta registra en `agent_runs` (seudonimizado, TTL 180 días): latencia total, TTFT y por nodo,
herramientas, tokens, rotaciones de llave y fallback de modelo, guardrails, grounding de citas, CPU y
memoria, error tipificado y feedback 👍/👎. Las trazas detalladas van a LangSmith.

## Convenciones

- Máximo **150 líneas por archivo** (verificado en CI).
- Commits: `tipo(scope): descripción en español vX.Y.Z`.

---

## Licencia

Proyecto **académico** para la asignatura Ingeniería de Soluciones con Inteligencia Artificial, Duoc UC.

## Contacto

**David Nahuelcar Tecas** · Duoc UC Puerto Montt
