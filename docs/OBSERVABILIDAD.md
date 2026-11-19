# Observabilidad y análisis de ejecución — Asistente HAZMAT

Base técnica para el informe y la presentación de la EV3 (IE1–IE7). Las conclusiones y reflexiones
personales del informe deben redactarlas los integrantes (la pauta prohíbe usar IA para eso).

## 0. Qué es, para qué sirve y cómo se lee el panel (v5.4)

**Qué es.** La observabilidad mide en vivo cómo se comporta el asistente con usuarios reales:
rapidez, fallas, costo, veracidad de las citas y abuso. Los datos están seudonimizados (hash con sal)
y se borran a los 180 días.

**Para qué sirve.** En una emergencia una respuesta lenta o inventada es un riesgo. El panel permite
**detectar** (modelo saturado, cuota agotada, base caída), **verificar** (citas comprobadas, feedback,
evaluación nocturna) y **mejorar** (cada 👎 puede convertirse en un caso de prueba).

**Cómo funciona.** Consulta → el agente registra la telemetría (`RunRecorder`) → MongoDB
(`agent_runs`, `security_events`) → el panel la lee cada 30 s → cada 30 min `health-check` compara con
los umbrales y avisa por correo; cada noche corre la evaluación.

**Cómo se lee.** La banda superior es un semáforo con la **misma lógica que las alertas por correo**
(`src/observability/health_status.py`, que reutiliza `automation/health.health_alerts`):

| Indicador | Verde | Ámbar | Rojo |
|---|---|---|---|
| Latencia p95 | ≤ `ALERT_P95_S` (20 s) | > umbral | > 1,5 × umbral |
| Tasa de error | 0 % | > 0 % | > `ALERT_ERROR_RATE` (5 %) |
| Citas verificadas | ≥ 95 % | ≥ 80 % | < 80 % |
| Feedback positivo | ≥ 80 % | ≥ 60 % | < 60 % |
| Consultas bloqueadas | ≤ `ALERT_BLOCKED_RATE` (30 %) | sobre el umbral | — |

Cada tarjeta tiene un botón **?** que explica qué muestra y qué hacer si está en rojo. Pestañas: Uso
real, Seguridad, Evaluación offline, Mejora continua y Registro.

## 1. Métricas implementadas

| Dimensión (pauta) | Métrica | Dónde se mide |
|---|---|---|
| Precisión | `keyword_score` (datos clave correctos), `retrieval_hit` (evidencia recuperada), `citation_ok` (página citada correcta), `faithfulness` (juez LLM 1-5), `grounded` (citas presentes en documentos) | `evals/`, `agent_runs.grounded` |
| Consistencia | similitud media entre 3 respuestas a la misma pregunta | `evals --repeat 3` |
| Errores | tasa de error, tipo (`quota`, `timeout`, `llm_unavailable`, `database`…), fallback de modelo, rotación de llaves | `agent_runs.status/error_type/model_fallback` |
| Latencia | p50/p95 total, TTFT, ms por nodo del grafo | `agent_runs.latency_ms/ttft_ms/nodes` |
| Recursos | tokens in/out, llamadas LLM, CPU s, RSS MB | `agent_runs.tokens_*/cpu_s/rss_mb` |
| Seguridad | % bloqueadas por categoría, PII redactada, eventos de auditoría | `agent_runs.block_reason`, `security_events` |
| Satisfacción | feedback 👍/👎 por respuesta | `agent_runs.feedback` |

Trazabilidad detallada (prompts, herramientas, tiempos por paso): LangSmith, proyecto `Bomberos-HAZMAT-RAG`.

## 2. Hallazgos del análisis de logs y trazas (v4 → v5)

| # | Evidencia observada | Causa raíz | Corrección |
|---|---|---|---|
| 1 | Citas con páginas imposibles (p. 1.137 en un libro de 392) | Ingesta guardaba el **índice del chunk** como página | Página impresa real (`page_label` / pie "Página N") |
| 2 | Recuperación correcta en solo 29% de los casos | Embeddings `all-MiniLM-L6-v2` (solo inglés) sobre texto en español | Modelo multilingüe 384-d + búsqueda léxica + índice exacto UN |
| 3 | "Gasolina" recuperaba guías de **gases** | La búsqueda semántica confunde guías de redacción similar | Prefetch determinista material → UN → guía |
| 4 | 503 *high demand* y timeouts de 60 s en las 6 llaves | Punto único de falla: un solo modelo; rotar llaves no sirve ante 503 | Cadena de modelos de respaldo + circuit breaker (120 s) + timeout 30 s |
| 5 | Saludo "hola" tardó 77 s | El clasificador LLM de guardrails se ejecutaba también en saludos | Saludos resueltos por reglas antes del clasificador (142 ms) |
| 6 | "UN 1203" llegaba al modelo como `[PATENTE]` | Regex de patente chilena `LL 1234` coincidía con "UN 1203" | Exclusión de prefijos UN/ID/NU + prueba unitaria |
| 7 | Caída de MongoDB se mostraba como "la IA tardó demasiado" | `ServerSelectionTimeoutError` contiene "timeout" y se clasificaba mal | Reglas de clasificación ordenadas (BD primero) |
| 8 | Primera consulta ~30 s más lenta | Carga perezosa del modelo de embeddings | Precarga en segundo plano al iniciar la app |
| 9 | Límite "máx. 2 herramientas" no se cumplía siempre | El límite estaba solo en el prompt | Presupuesto impuesto por código en el grafo (probado con LLM simulado) |
| 10 | Mensajes con `<script>` hacían fallar el guardado | El sanitizador lanzaba excepción ante texto "peligroso" | Validación de claves `$`, render seguro en vez de bloquear texto |
| 11 | Respuestas variables entre corridas | `gemini-3.6-flash` ignora `temperature` (log de la librería) | Prefetch determinista reduce variación; documentado como limitación |

## 3. Resultados de evaluación

### Resultados (31 casos, mismo modelo `gemini-3.5-flash-lite`, set v1.1)

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

## 4. Recomendaciones (sostenibilidad y escalabilidad)

1. **Caché semántica** de respuestas para consultas frecuentes (UN más consultados) → menos tokens y latencia.
2. **Ventanilla de modelos**: medir semanalmente disponibilidad/latencia por modelo y reordenar la cadena de fallback con datos del dashboard.
3. **Re-ranker** (cross-encoder multilingüe) sobre la búsqueda híbrida para preguntas generales del Manual ABC-V.
4. **Ampliar el set de evaluación** con preguntas reales de bomberos (feedback 👎) y ejecutarlo en CI ante cada cambio de prompt.
5. **Despliegue con réplicas**: el rate limit ya se comparte vía MongoDB; la app es *stateless* salvo la sesión del navegador.
6. **Alertas**: p95 > 20 s o tasa de error > 5% en 15 min → notificación al equipo.
