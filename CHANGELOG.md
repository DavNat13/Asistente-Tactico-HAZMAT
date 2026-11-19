<div align="center">

<img src="docs/assets/icons/clock.svg" width="44" height="44" alt="">

# Registro de cambios

**Asistente HAZMAT** · Formato [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) ·
[Versionado semántico](https://semver.org/lang/es/)

</div>

---

Las versiones previas a 5.0 se agrupan por línea mayor. El detalle de cada versión está en los commits,
que siguen el formato `tipo(scope): descripción vX.Y.Z`.

## [5.4.2] · 2026-11-19

### Agregado
- Despliegue continuo gratuito en Hugging Face Spaces: cuando el CI pasa en `main`, se publica una copia
  limpia (sin binarios ni historial) con el README propio del Space. Guía en `DEPLOYMENT.md`.

## [5.4.1] · 2026-11-19

### Corregido
- La imagen Docker no incluía `docs/AVISO_PRIVACIDAD.md` y `.dockerignore` excluía los `*.md`: el modal
  de privacidad fallaba dentro del contenedor.
- `mem_limit` del contenedor sube de 1 GB a 2 GB, porque el uso real llega a ~1,4 GB.
- Los flujos de monitoreo y evaluación nocturna fallaban cuando faltaban los secrets del repositorio.
  Ahora se omiten con un aviso, y el monitoreo instala `pydantic`, que necesita la tarea `purge-unverified`.

### Agregado
- Prueba que impide volver a dejar el aviso de privacidad fuera de la imagen.
- `SECURITY.md`, `CHANGELOG.md`, `DEPLOYMENT.md` y documentación renovada con íconos propios.

## [5.4.0] · 2026-11-19

### Agregado
- Sistema de diseño "Centro de mando": tokens de color, forma y movimiento para tema claro y oscuro, y kit
  de componentes (encabezados, tarjetas, indicadores con semáforo, banda de estado).
- Mapa de zonas con capas de Esri (satélite con calles y nombres, calles, noche, topográfico), Google Map
  Tiles API opcional y OpenStreetMap como respaldo.
- Ubicación del dispositivo en tiempo real ("Usar mi ubicación" y "Seguir en vivo"), con círculo de precisión.
- Pantalla completa y medición de distancias en el mapa.
- Observabilidad: semáforo con los mismos umbrales que las alertas por correo, explicación del panel y de
  cada gráfico, y nombres legibles para los eventos de auditoría.

### Cambiado
- Barra superior fija con fondo sólido: el contenido ya no pasa por debajo.
- Respuestas del chat en tarjetas y acciones como píldoras.
- Aviso de privacidad v2 (`2026-12-01-v2`): incorpora la ubicación del dispositivo y los proveedores de
  mapas. Todas las cuentas deben volver a aceptarlo.

### Corregido
- Los gráficos de barras superponían sus etiquetas; ahora usan un alto fijo por fila.
- Los estilos por rol del chat no se aplicaban con avatares personalizados en Streamlit 1.67.

## [5.3.2] · 2026-11-19

### Agregado
- `EMAIL_VERIFICATION_REQUIRED`: permite desactivar la verificación solo en desarrollo.
- `python -m src.notify.smtp_check` para diagnosticar el correo real.
- `create_user --email`, que crea cuentas con el correo ya verificado.

### Corregido
- Los errores inesperados del registro se perdían sin registro. Ahora dejan traceback, el evento
  `signup_failed` y una referencia visible para el usuario.
- La configuración de correo inválida, como `SMTP_USER` sin dirección, se detecta y explica.

## [5.3.1] · 2026-11-19

### Agregado
- Validación en vivo de nombre, usuario, correo y contraseña en el registro. Las mismas reglas se aplican
  en el servidor.

## [5.3.0] · 2026-11-19

### Agregado
- Verificación de correo con código de 6 dígitos: se guarda solo su HMAC, vence pronto, admite 5 intentos
  y es de uso único. El registro es transaccional.
- Recuperación de contraseña sin enumeración de correos.
- Límites anti-abuso por IP y por correo.
- Aviso de privacidad completo y versionado (Ley 19.628 y Ley 21.719) en un modal con índice y descarga.
- Migración de cuentas existentes (`migrate_verification`) y limpieza de cuentas no verificadas.

## [5.2.0] · 2026-11-17

### Agregado
- Zonas de aislamiento sobre el mapa, identificación del N° ONU por foto, lista de verificación por fases y
  ficha de incidente en PDF.
- Correos operativos, evaluación nocturna, alertas de salud, reporte semanal y ciclo de mejora continua a
  partir de las valoraciones negativas.
- Cuentas con correo único e inicio de sesión por usuario o correo.

## [5.1.0] · 2026-11-17

### Agregado
- Registro de cuentas sin sobrescritura e interfaz al estilo de asistentes de IA con historial agrupado.
- Observabilidad en vivo que separa el uso real de las pruebas automáticas.

### Seguridad
- Eliminación de código HTML/JS de los mensajes antes de mostrarlos, guardarlos o enviarlos al modelo.

## [5.0.0] · 2026-11-17

### Agregado
- Agente por niveles (bajo, medio, alto) con presupuesto de herramientas.
- Página impresa real, índice ONU, embeddings multilingües y búsqueda híbrida con RRF.
- Telemetría por ejecución, guardrails, ocultamiento de datos personales, autenticación y aislamiento de
  sesiones.
- Set de evaluación de 31 casos y CI con seguridad bloqueante.

## [4.x] · 2026-09-14 a 2026-10-22

- Agente autónomo con LangGraph y *tool calling*, rotación automática de claves de API, *streaming* de
  respuestas y endurecimiento de Docker y CI.

## [1.x – 3.x] · 2026-09-09 a 2026-09-14

- Configuración inicial, ingesta multi-documento, recuperación y generación, interfaz en Streamlit,
  embeddings locales, módulo de sesiones y primeros ajustes de seguridad y Docker.

