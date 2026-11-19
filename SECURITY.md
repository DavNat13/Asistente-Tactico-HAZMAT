<div align="center">

<img src="docs/assets/icons/shield.svg" width="44" height="44" alt="">

# Política de seguridad

**Asistente HAZMAT** · Cómo reportar una vulnerabilidad y qué protege el sistema

</div>

---

## Versiones con soporte

| Versión | Soporte de seguridad |
|---|:---:|
| 5.4.x | Sí |
| 5.0 a 5.3 | No (actualizar a 5.4) |
| Menor a 5.0 | No |

## <img src="docs/assets/icons/bug.svg" width="22" height="22" align="top"> Reportar una vulnerabilidad

> [!CAUTION]
> **No abras un *issue* público** para reportar una vulnerabilidad: expondría el problema antes de que
> exista una corrección.

1. Ve a la pestaña **Security** de este repositorio y elige **Report a vulnerability** (reporte privado
   de GitHub). Si la opción no aparece, contacta al autor por los medios indicados en
   [`LICENSE.MD`](LICENSE.MD) sin incluir detalles técnicos y solicita un canal privado.
2. Incluye:
   - Descripción del problema y su impacto.
   - Pasos para reproducirlo, versión afectada (visible en el pie de la pantalla de acceso) y entorno.
   - Si es posible, una prueba de concepto mínima.
3. **No incluyas datos personales reales**, credenciales ni contenido de conversaciones de terceros.

**Plazos objetivo**

| Etapa | Plazo |
|---|---|
| Acuse de recibo | 5 días hábiles |
| Evaluación inicial y severidad | 10 días hábiles |
| Corrección de severidad alta o crítica | Lo antes posible; se informará el avance |
| Divulgación coordinada | Después de publicar la corrección, de común acuerdo con quien reporta |

## Alcance

**Dentro del alcance**

- Inyección de *prompts* que logre revelar instrucciones internas, secretos o datos de otros usuarios.
- Evasión de los *guardrails* que produzca contenido dañino o fuera del dominio.
- Fallos de autenticación, verificación de correo, recuperación de contraseña o control de acceso por rol.
- Acceso al historial o a la telemetría de otro usuario.
- XSS o ejecución de código a través de mensajes, imágenes o archivos.
- Exposición de secretos (`.env`, claves de API, cadenas de conexión) en el código, los registros o la salida.
- Vulnerabilidades en la imagen Docker o en los flujos de GitHub Actions.

**Fuera del alcance**

- Denegación de servicio por volumen o pruebas de carga.
- Ingeniería social, phishing o ataques físicos.
- Vulnerabilidades en servicios de terceros (Google, MongoDB Atlas, Esri, OpenStreetMap, GitHub): repórtalas
  directamente a cada proveedor.
- Respuestas técnicamente incorrectas del modelo sin implicancia de seguridad: repórtalas como error funcional.

## Buenas prácticas para quien investiga

- Usa una instalación **local** con tus propias credenciales; no pruebes contra despliegues de terceros.
- No accedas, modifiques ni elimines datos que no sean tuyos.
- Detén la prueba y repórtala apenas confirmes la vulnerabilidad.

Las investigaciones de buena fe que respeten esta política no serán objeto de acciones por parte del autor.

## <img src="docs/assets/icons/lock.svg" width="22" height="22" align="top"> Controles implementados

| Área | Control | Referencia |
|---|---|---|
| Entrada al modelo | Heurísticas contra inyección, uso dañino y pedido de secretos; clasificador LLM como segunda capa | `src/security/guardrails_input.py` |
| Datos personales | Ocultamiento de RUT, teléfonos, correos, tarjetas y patentes antes del modelo y antes de guardar | `src/security/pii.py` |
| Salida | Sin HTML ni JavaScript, redacción de secretos y verificación de páginas citadas | `src/security/guardrails_output.py` |
| Contraseñas | scrypt con sal única, comparación en tiempo constante, bloqueo tras 5 intentos | `src/security/passwords.py`, `auth.py` |
| Correo | Código de 6 dígitos con HMAC-SHA256 (`OTP_SECRET`), 5 intentos, uso único y expiración corta | `src/security/otp.py` |
| Enumeración | Mensajes y tiempos idénticos en inicio de sesión y recuperación, exista o no la cuenta | `src/security/recovery.py` |
| Abuso | Límites por usuario, IP y correo con contadores seudonimizados | `src/security/throttle.py`, `rate_limit.py` |
| Auditoría | Eventos en `security_events` con usuario seudonimizado y retención limitada | `src/observability/store.py` |
| Aplicación web | Protección CSRF y sin detalle de errores internos | `.streamlit/config.toml` |
| Contenedor | Usuario sin privilegios, dependencias fijadas y *healthcheck* | `Dockerfile` |
| Cadena de suministro | Bandit, pip-audit, Gitleaks, hadolint y Dependabot | `.github/` |

El modelo de amenazas completo (OWASP Top 10 for LLM Applications) está en
[`docs/SEGURIDAD_ETICA.md`](docs/SEGURIDAD_ETICA.md), y el tratamiento de datos personales, en
[`docs/AVISO_PRIVACIDAD.md`](docs/AVISO_PRIVACIDAD.md).

## Gestión de secretos

- Las credenciales se cargan solo desde variables de entorno; `.env` está excluido de Git y de la imagen Docker.
- `OTP_SECRET` y `TELEMETRY_SALT` deben ser valores aleatorios de al menos 32 caracteres, distintos entre sí.
- Las claves de mapas viajan en las URL de las teselas: **restríngelas por dominio** (Esri: *referrers*;
  Google: restricción de API y de sitio web).
- Si un secreto se expone: revócalo en el proveedor, genera uno nuevo y reemplázalo en el servidor y en
  los secrets de GitHub Actions.

---

<div align="center"><sub>Última actualización: noviembre de 2026</sub></div>
