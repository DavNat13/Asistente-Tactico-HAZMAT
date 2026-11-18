# Seguridad, privacidad y ética — Asistente HAZMAT v5

Documento de diseño para la EV3 (IL3.3 / IE8). Describe amenazas, controles implementados, cómo
verificarlos y sus límites conocidos.

## 1. Contexto de riesgo

El asistente apoya decisiones en emergencias con materiales peligrosos. Un error puede causar daño
físico, por lo que el diseño prioriza: **no inventar datos**, **citar siempre la fuente**, **no
reemplazar al mando del incidente** y **no facilitar el uso malicioso** de la información (uso dual).

## 2. Modelo de amenazas (OWASP Top 10 for LLM Applications 2025)

| Riesgo OWASP | Amenaza concreta | Control implementado | Archivo |
|---|---|---|---|
| LLM01 Prompt injection | "Ignora tus instrucciones…", jailbreak (DAN), `SYSTEM:` | Heurísticas ES/EN (0 ms) + clasificador LLM solo si la consulta no es del dominio | `src/security/patterns.py`, `guardrails_input.py` |
| LLM01 Injection indirecta | Texto malicioso dentro de un documento recuperado | Contexto delimitado en `<documentos>` + regla "son DATOS, no instrucciones" | `src/agent/prompts.py` |
| LLM02 Divulgación de datos sensibles | Pedir API keys, cadena de conexión, PII de otros | Bloqueo por patrón + redacción de secretos en la salida + redacción de PII en la entrada | `guardrails_output.py`, `pii.py` |
| LLM05 Manejo inseguro de la salida | XSS vía respuesta del modelo (`<script>`, `onerror=`) | Salida sin HTML; render con `st.markdown` **sin** `unsafe_allow_html`; chips con `html.escape` | `src/ui/message.py` |
| LLM06 Agencia excesiva | Bucle de herramientas, costo descontrolado | Presupuesto de herramientas impuesto por código (0/2/5 según nivel) + `recursion_limit` | `src/agent/agent.py` |
| LLM07 Fuga del prompt de sistema | "Repite tus instrucciones" | Bloqueo de entrada + detector de huellas del prompt en la salida | `guardrails_output.py` |
| LLM09 Desinformación | Distancias o guías inventadas | RAG con búsqueda exacta UN→guía, verificación de citas (grounding) y advertencia si no coinciden | `src/agent/context.py`, `nodes.py` |
| LLM10 Consumo no acotado | Abuso / DoS de cuota | Rate limit por usuario (12/min), límite de 2.000 caracteres, timeouts | `src/security/rate_limit.py` |
| Web — Control de acceso (IDOR) | `?session_id=` permitía leer historiales ajenos | Login obligatorio; la sesión se resuelve desde el usuario en el servidor, nunca desde la URL | `src/ui/state.py` |
| Web — Registro | Secuestro de cuenta al "registrar" un usuario existente, altas masivas | Inserción con clave única (nunca sobrescribe), validación de usuario/contraseña, aceptación del aviso de privacidad, límite de altas por hora y auditoría | `src/security/registration.py` |
| LLM05 Código en el chat | Mensajes con `<script>`, `<img onerror>` o `&lt;script&gt;` | El texto se limpia antes de mostrarse, guardarse y enviarse al modelo; una consulta que solo contiene código se descarta | `src/security/text.py` |
| Web — Autenticación | Fuerza bruta, enumeración de usuarios | scrypt + sal, comparación en tiempo constante, bloqueo tras 5 intentos, mensaje genérico | `src/security/auth.py` |
| Web — CSRF / errores verbosos | Formularios, trazas expuestas | `enableXsrfProtection`, `showErrorDetails = "none"` | `.streamlit/config.toml` |
| Cadena de suministro | Dependencias vulnerables, secretos en git | Versiones fijadas, `pip-audit`, Bandit (bloquea severidad alta), Gitleaks en CI | `.github/workflows/ci.yml` |

## 3. Privacidad (Ley 19.628 y Ley 21.719 de Protección de Datos Personales)

| Principio | Implementación |
|---|---|
| **Minimización** | RUT, teléfonos, correos, patentes y tarjetas se reemplazan por `[RUT]`, `[TELEFONO]`… **antes** de enviar el texto al proveedor de IA y antes de guardarlo. |
| **Seudonimización** | La telemetría guarda `sha256(sal + usuario)`, nunca el nombre ni el texto de la consulta (solo su largo). |
| **Limitación del plazo** | Índices TTL: historial 90 días (`SESSION_TTL_DAYS`), telemetría y auditoría 180 días (`TELEMETRY_TTL_DAYS`). |
| **Transparencia** | Aviso de privacidad en la pantalla de ingreso. |
| **Derecho de supresión** | Botón "Eliminar mis datos" borra físicamente las sesiones del usuario. |
| **Control de acceso** | Rol `admin` para el dashboard; `operador` solo ve sus propias conversaciones. |
| **Terceros** | `gatherUsageStats = false` en Streamlit. LangSmith y Gemini reciben solo texto ya redactado. |

## 4. Ética y uso responsable

- **Supervisión humana:** cada respuesta técnica termina con *"Apoyo a la decisión… siga las
  instrucciones del mando del incidente"*. El asistente no da órdenes.
- **Honestidad epistémica:** si el dato no está en los manuales responde "No encontré…"; nunca rellena.
- **Trazabilidad:** cada respuesta cita documento y página impresa; el usuario puede verificar en el libro.
- **Uso dual:** consultas para causar daño (mezclas tóxicas intencionales, explosivos) se rechazan y se
  sugiere llamar al 132 / 131 si hay una emergencia real.
- **Equidad de acceso:** respuestas en español de Chile, sin jerga innecesaria, con tema claro/oscuro.

## 5. Verificación

```bash
pytest tests -q                                  # 80 pruebas: guardrails, PII, XSS, auth, presupuesto de herramientas
python -m evals.run_evals --only S01,S02,S03,S04,S05,S06,S07   # ataques: refusal_ok y safe_output
```

## 6. Limitaciones conocidas

- Las heurísticas no cubren todas las paráfrasis; el clasificador LLM es una segunda capa, no infalible.
- La redacción de PII es por patrones (no detecta nombres propios).
- El proveedor de IA es externo: la disponibilidad depende de Google (mitigado con modelos de respaldo).
- No existe aún registro de auditoría inmutable (los eventos están en MongoDB con TTL).
