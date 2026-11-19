# Aviso de privacidad — Asistente HAZMAT

> **Borrador: revisión legal pendiente.** Este texto no ha sido aprobado por un abogado. Los
> marcadores `[[...]]` indican datos que el responsable debe completar o verificar antes de publicar.

**Versión:** 2026-12-01-v2 · **Vigente desde:** 1 de diciembre de 2026 · **Última revisión técnica:** 19 de noviembre de 2026

Este aviso explica qué datos personales trata el Asistente HAZMAT, para qué, con qué base legal,
con quién se comparten, cuánto tiempo se conservan, cómo se protegen y cómo puedes ejercer tus
derechos. Cada afirmación técnica fue contrastada con el código fuente del sistema en la fecha de
revisión indicada. Donde el código no permite confirmarla, se deja un marcador `[[VERIFICAR: ...]]`.

**En resumen:** el asistente usa tus datos de cuenta para darte acceso, tus consultas para
responderte (después de ocultar automáticamente RUT, teléfonos, correos, tarjetas y patentes) y
datos técnicos seudonimizados para medir y mejorar el servicio. No vendemos datos. La IA orienta,
pero no decide: el mando del incidente siempre tiene la última palabra.

## 0. Marco normativo y vigencia

Este tratamiento se rige por las siguientes normas chilenas:

- **Constitución Política de la República, artículo 19 número 4**, que asegura a todas las personas
  el respeto y la protección de su vida privada y la protección de sus datos personales.
- **Ley 19.628, sobre protección de la vida privada.** Es la ley general vigente hasta el 30 de
  noviembre de 2026.
- **Ley 21.719, que regula la protección y el tratamiento de los datos personales y crea la Agencia
  de Protección de Datos Personales.** Se publicó en el Diario Oficial el 13 de diciembre de 2024.
  Su entrada en vigencia está prevista para el **1 de diciembre de 2026**, fecha en que reemplaza el
  régimen anterior. Existe un proyecto de ley del Ejecutivo que propone postergar su entrada en
  vigencia al 1 de diciembre de 2027. A la fecha de esta revisión, la fecha vigente es el 1 de
  diciembre de 2026. `[[VERIFICAR antes de publicar si se aprobó la postergación y ajustar esta sección y las referencias a la Ley 21.719]]`
- **Ley 21.663, marco de ciberseguridad.** Impone deberes de reporte de incidentes a los prestadores
  de servicios esenciales y a los operadores de importancia vital (OIV).
  `[[VERIFICAR si el responsable es prestador de servicio esencial u OIV]]`
- **Ley 21.459, sobre delitos informáticos.** Se considera como referencia para la protección de los
  sistemas: el acceso indebido, la interceptación y el daño a datos o sistemas son delitos.

Mientras la Ley 19.628 siga vigente, este aviso cumple sus exigencias. Desde la entrada en vigencia
de la Ley 21.719, las referencias a principios, bases de licitud y derechos se entienden hechas a
esa ley.

## 1. Responsable y encargado

**Responsable del tratamiento** (quien decide para qué y cómo se tratan los datos):
`[[RESPONSABLE: nombre o razón social, RUT, domicilio, correo de contacto]]`

**Encargados del tratamiento** (proveedores que tratan datos por cuenta del responsable): se
detallan en la sección 7.

**Delegado de protección de datos:** `[[DPO: verificar si la Ley 21.719 lo exige en este caso o si se designará de forma voluntaria; indicar nombre y correo]]`

## 2. Datos que tratamos, por categoría

| Categoría | Datos | Origen | Dónde se guardan |
|---|---|---|---|
| Identificación de cuenta | Nombre, nombre de usuario, correo electrónico, rol (operador o admin), fecha de creación, fecha de último acceso, estado de verificación del correo | Tú, al registrarte | Base de datos MongoDB, colección `users` |
| Credenciales | Hash scrypt de la contraseña con sal única. **La contraseña nunca se guarda en texto plano** y no se puede recuperar a partir del hash | Tú | Colección `users` |
| Aceptación del aviso | Versión del aviso aceptada y fecha de aceptación | Tú | Colección `users` y registro de seguridad |
| Consultas y respuestas del chat | Texto de tus preguntas y las respuestas del asistente, después de la redacción automática (sección 6) | Tú y el sistema | Colección de sesiones (historial) |
| Feedback | Calificación 👍 o 👎 de una respuesta | Tú | Telemetría (`agent_runs`); si es 👎, la pregunta y la respuesta redactadas pasan a `eval_candidates` |
| Fotos de placas | Imagen de una placa, rombo o panel que subes para identificar el número ONU | Tú | **No se guardan.** Se validan, se re-codifican a JPEG en memoria y se envían al modelo de visión |
| Ubicación del dispositivo | Coordenadas y precisión del GPS, solo si pulsas «Usar mi ubicación» o «Seguir en vivo» y el navegador te da permiso | Tu dispositivo | **No se guarda** en la base de datos: vive en la sesión abierta del navegador y se pierde al cerrarla. Puedes detener el seguimiento en cualquier momento |
| Direcciones del mapa | Texto de la dirección que buscas para dibujar zonas de aislamiento | Tú | Se envía a OpenStreetMap/Nominatim y se guarda temporalmente en la memoria del proceso (caché de hasta 256 búsquedas). `[[VERIFICAR si la dirección queda en el historial o en la ficha del incidente]]` |
| Datos técnicos | Fecha, duración de cada etapa, errores tipificados, herramientas usadas, consumo de tokens, largo de la consulta (no su texto), modelo usado | El sistema | Colección `agent_runs`, con el usuario seudonimizado |
| Registros de seguridad | Intentos de inicio de sesión fallidos, bloqueos, límites alcanzados, códigos fallidos, reenvíos, cambios de contraseña y aceptación del aviso | El sistema | Colección `security_events`, con el usuario seudonimizado. Nunca se guarda el código ni la contraseña |
| Dirección IP | Se usa solo para limitar abusos (registro y recuperación de contraseña) | Tu conexión | Solo un seudónimo (hash con sal) en la colección `rate_limits`, que se borra sola en un máximo de 2 horas. No se guarda en los registros de seguridad. `[[VERIFICAR si el hosting o el proxy registran IP en sus propios logs]]` |
| Trazas de observabilidad | Pasos del agente, documentos recuperados y texto ya redactado de la consulta y la respuesta | El sistema | LangSmith (sección 7) |
| Códigos de verificación | Solo el HMAC-SHA256 del código de 6 dígitos, nunca el código | El sistema | Colección `email_tokens`, durante 10 a 15 minutos |
| Registro de correos enviados | Tipo de correo, destinatario seudonimizado, resultado del envío (sin contenido) | El sistema | Colección `email_log` |

## 3. Datos sensibles y de terceros

Una consulta de emergencia puede describir a **personas lesionadas o víctimas** e incluir datos de
salud (por ejemplo, síntomas de intoxicación o quemaduras). Los datos relativos a la salud son
**datos sensibles** y requieren una protección reforzada.

Cómo se tratan:

- El asistente **no necesita** saber quién es la persona afectada para orientar la respuesta. Basta
  con describir la situación ("una persona con irritación ocular"), sin nombres ni identificadores.
- Antes de llegar al modelo de IA y antes de guardarse en el historial, el texto pasa por la
  redacción automática de la sección 6. Ese filtro **no detecta nombres propios ni descripciones de
  salud**, por lo que no reemplaza tu cuidado al escribir.
- La telemetría no guarda el texto de las consultas, solo su largo.
- `[[VERIFICAR base de licitud aplicable al tratamiento incidental de datos de salud de terceros en emergencias]]`

**Te pedimos no ingresar datos personales de terceros** (nombres, RUT, teléfonos, domicilios,
diagnósticos) más allá de lo estrictamente necesario para atender la emergencia.

## 4. Finalidades

**Finalidades necesarias para prestar el servicio** (sin ellas el asistente no funciona):

1. Crear y administrar tu cuenta, verificar tu correo y permitirte iniciar sesión.
2. Responder tus consultas sobre materiales peligrosos con base en la GRE 2024 y el Manual ABC-V.
3. Generar planes de respuesta, listas de verificación, zonas de aislamiento en el mapa y la ficha
   PDF del incidente.
4. Enviarte correos operativos: código de verificación, bienvenida, aviso de bloqueo de cuenta,
   aviso de cambio de contraseña y, si lo pides, la ficha del incidente.
5. Seguridad y prevención de abuso: bloqueo tras intentos fallidos, límites de uso, auditoría y
   detección de intentos de manipulación del modelo.
6. Cumplir obligaciones legales, como atender el ejercicio de derechos y reportar incidentes de
   seguridad cuando corresponda.

**Finalidades de mejora del sistema** (no son indispensables para responderte):

7. Métricas de calidad y desempeño (latencia, errores, consumo), siempre seudonimizadas.
8. Alertas automáticas de salud del sistema y reporte semanal a los administradores, con datos
   agregados.
9. Mejora continua a partir de tu feedback: cuando marcas una respuesta con 👎, la pregunta y la
   respuesta **ya redactadas** se guardan como caso candidato. Un administrador puede revisarlo y
   convertirlo en un **caso de evaluación** que se ejecuta cada noche para detectar regresiones. Si
   no quieres que una respuesta se use así, no la califiques. `[[VERIFICAR si se ofrecerá un mecanismo de oposición específico y el plazo de conservación de eval_candidates y eval_cases]]`

## 5. Base de licitud

| Finalidad | Base de licitud propuesta | Referencia |
|---|---|---|
| 1 a 4. Cuenta, respuestas, planes, mapa, ficha y correos operativos | Ejecución del servicio que solicitas al registrarte | `[[VERIFICAR artículos de la Ley 21.719]]` |
| 5. Seguridad y prevención de abuso | Interés legítimo del responsable en proteger el sistema y a sus usuarios | `[[VERIFICAR artículos de la Ley 21.719]]` |
| 6. Cumplimiento legal | Obligación legal | `[[VERIFICAR artículos de la Ley 21.719]]` |
| 7 y 8. Métricas y alertas seudonimizadas | Interés legítimo en mantener un servicio de emergencia confiable | `[[VERIFICAR artículos de la Ley 21.719]]` |
| 9. Casos de evaluación a partir de 👎 | Consentimiento, expresado al calificar la respuesta | `[[VERIFICAR artículos de la Ley 21.719 y si basta la acción de calificar]]` |
| Datos de salud de terceros mencionados en una consulta | `[[VERIFICAR base aplicable a datos sensibles en situaciones de emergencia]]` | `[[VERIFICAR artículos]]` |

Mientras rija la Ley 19.628, el tratamiento se apoya en tu autorización expresa al aceptar este
aviso y en las excepciones que esa ley contempla. `[[VERIFICAR]]`

## 6. Redacción automática antes del modelo de IA

Antes de enviar tu consulta al modelo de lenguaje, y antes de guardarla en el historial, el sistema
reemplaza automáticamente los siguientes datos por una etiqueta (archivo `src/security/pii.py`):

| Dato | Se reemplaza por | Ejemplo |
|---|---|---|
| Correo electrónico | `[EMAIL]` | nombre@dominio.cl |
| RUT | `[RUT]` | 12.345.678-5 |
| Teléfono chileno (móvil y fijo, con o sin +56) | `[TELEFONO]` | +56 9 8765 4321 |
| Número de tarjeta (16 dígitos) | `[TARJETA]` | 1234 5678 9012 3456 |
| Patente de vehículo chilena (formatos LLLL-NN y LL-NNNN) | `[PATENTE]` | BB-1234 |

Los números ONU de materiales peligrosos (por ejemplo, "UN 1203") se excluyen a propósito para que
el asistente pueda responder. Además, el texto se limpia de código HTML o JavaScript
(`src/security/text.py`).

El mismo filtro se aplica a la pregunta y la respuesta que se guardan como caso candidato cuando
das 👎.

**Limitaciones:** es un filtro automático basado en patrones y **puede no detectar todo**. No
reconoce nombres propios, domicilios, descripciones de salud ni datos escritos en formatos poco
comunes. Las direcciones que buscas en el mapa se envían tal cual al servicio de geocodificación.
**No confíes en este filtro para proteger datos sensibles:** simplemente no los escribas.

## 7. Encargados y terceros

| Proveedor | Finalidad | Datos que recibe | País de tratamiento | Mecanismo de transferencia internacional |
|---|---|---|---|---|
| Google (API de Gemini) | Modelo de lenguaje que redacta las respuestas, clasificador de seguridad y análisis de fotos de placas | Consulta redactada, historial reciente redactado, fragmentos de los manuales y, si la subes, la foto re-codificada | `[[VERIFICAR región de procesamiento]]` | `[[VERIFICAR cláusulas contractuales o garantías del proveedor]]` |
| MongoDB Atlas | Base de datos (cuentas, historial, telemetría, registros de seguridad, códigos) | Todos los datos guardados descritos en la sección 2 | `[[región]]` | `[[VERIFICAR]]` |
| Google (Gmail SMTP) | Envío de correos | Tu correo, tu nombre y el contenido del mensaje (por ejemplo, el código) | `[[VERIFICAR]]` | `[[VERIFICAR]]` |
| Esri (ArcGIS Location Platform) | Imágenes satelitales y mapas base | La zona del mapa que se está viendo (coordenadas de las teselas) y la dirección IP del navegador; nunca tu nombre ni tu cuenta | `[[VERIFICAR región de los servidores de Esri]]` | `[[VERIFICAR]]` |
| Google (Map Tiles API, opcional) | Capas de mapa, satélite, relieve y tráfico, solo si el responsable configura la clave | La zona del mapa que se está viendo y la dirección IP del navegador | `[[VERIFICAR]]` | `[[VERIFICAR]]` |
| OpenStreetMap / Nominatim | Convertir una dirección en coordenadas para el mapa | Solo el texto de la dirección buscada, con un identificador genérico de la aplicación (sin datos tuyos) | `[[VERIFICAR país de los servidores de la Fundación OpenStreetMap]]` | `[[VERIFICAR]]` |
| LangSmith (LangChain) | Trazas técnicas para depurar y evaluar el agente | Consulta y respuesta ya redactadas, documentos recuperados, pasos del agente; metadatos de ejecución (identificador de ejecución y canal), no tu nombre de usuario | `[[VERIFICAR región]]` | `[[VERIFICAR]]` |
| Hosting de la aplicación (Streamlit / Docker) | Ejecutar la aplicación web | Tráfico de la sesión, incluida tu dirección IP | `[[dónde: proveedor y país]]` | `[[VERIFICAR]]` |
| GitHub Actions | Evaluaciones nocturnas, monitoreo de salud y limpieza de cuentas no verificadas | Accede a la base de datos para leer métricas seudonimizadas y casos de evaluación ya redactados | `[[VERIFICAR]]` | `[[VERIFICAR]]` |

Para Google (Gemini): `[[VERIFICAR retención del proveedor y configuración de no entrenamiento con los datos enviados]]`

Para LangSmith: `[[VERIFICAR qué contenido se envía exactamente y si está seudonimizado; plazo de retención de las trazas]]`. El envío de trazas se puede desactivar
con la variable `LANGCHAIN_TRACING_V2=false`.

La aplicación tiene desactivado el envío de estadísticas de uso de Streamlit
(`gatherUsageStats = false`).

## 8. Decisiones automatizadas

- La IA **genera orientaciones**: guía GRE aplicable, distancias de aislamiento, equipo de
  protección y tácticas, con la página del manual citada. **No toma decisiones** sobre ti ni
  reemplaza al mando del incidente, que evalúa la situación real y decide.
- Las únicas decisiones automáticas que te afectan son de seguridad de la cuenta: el bloqueo
  temporal tras 5 intentos fallidos (15 minutos), los límites de uso por minuto y por hora, y el
  rechazo de consultas que intentan manipular el sistema o causar daño. Puedes pedir revisión
  humana de cualquiera de ellas escribiendo al contacto de la sección 19.
- Tienes derecho a no ser objeto de decisiones basadas únicamente en tratamiento automatizado que
  produzcan efectos jurídicos o te afecten significativamente, según la Ley 21.719.
  `[[VERIFICAR artículo y alcance exacto]]`
- **Limitaciones:** el modelo puede equivocarse, omitir información o citar mal una página. El
  sistema verifica que las páginas citadas correspondan a los documentos recuperados y advierte
  cuando no coinciden, pero **debes verificar las citas con la guía impresa** antes de actuar.

## 9. Conservación y plazos

| Dato | Plazo | Cómo se elimina |
|---|---|---|
| Historial de conversaciones | 90 días desde la última actividad (`SESSION_TTL_DAYS`) | Índice TTL de la base de datos o botón "Eliminar mis datos" |
| Telemetría (`agent_runs`) | 180 días (`TELEMETRY_TTL_DAYS`) | Índice TTL |
| Registros de seguridad (`security_events`) | 180 días (`TELEMETRY_TTL_DAYS`) | Índice TTL |
| Registros de envío de correo (`email_log`) | `[[plazo: hoy no tiene borrado automático]]` | `[[VERIFICAR]]` |
| Códigos de verificación | 15 minutos (registro) o 10 minutos (contraseña); se invalidan al usarse | Índice TTL sobre `expires_at` |
| Contadores anti-abuso (`rate_limits`) | Hasta 2 horas | Índice TTL |
| Cuentas no verificadas | 30 minutos desde el registro | Índice TTL sobre `pending_expires_at` y tarea programada cada 30 minutos |
| Casos candidatos y casos de evaluación | `[[plazo: hoy no tienen borrado automático]]` | Revisión de un administrador |
| Fotos de placas | No se guardan | — |
| Cuenta verificada | Mientras la cuenta exista | `[[VERIFICAR procedimiento de eliminación de cuenta]]` |

**Qué se borra al eliminar tus datos:** el botón "Eliminar mis datos" borra físicamente todas tus
conversaciones. Las métricas y registros de seguridad ya están seudonimizados y no contienen tus
mensajes; se eliminan al cumplirse su plazo. Hoy la aplicación no ofrece un botón para eliminar la
cuenta completa; puedes pedirlo al contacto de la sección 19.
`[[VERIFICAR qué se conserva por obligación legal tras eliminar una cuenta y por cuánto tiempo]]`

## 10. Medidas de seguridad

- **Contraseñas:** hash scrypt (resistente a ataques con GPU) con sal única por contraseña y
  comparación en tiempo constante. Política mínima de 10 caracteres combinando letras con números
  o símbolos.
- **Códigos de verificación:** 6 dígitos generados con un generador criptográfico; se guarda solo su
  HMAC-SHA256 con una clave secreta; máximo 5 intentos por código, uso único y expiración corta.
- **Bloqueo y límites:** bloqueo temporal tras 5 intentos fallidos de inicio de sesión (con aviso
  por correo al titular), 12 consultas por minuto por usuario, límites de registros por hora (en
  total, por IP y por correo) y de solicitudes de recuperación de contraseña por correo y por IP.
- **Sin enumeración de cuentas:** los mensajes de error de inicio de sesión y de recuperación no
  revelan si un correo está registrado, y la recuperación responde en un tiempo uniforme.
- **Correo:** conexión TLS implícita (puerto 465) con verificación del certificado del servidor.
- **Seudonimización:** la telemetría y los registros de seguridad guardan un hash con sal del
  usuario, nunca su nombre ni el texto de las consultas.
- **Control de acceso por rol:** el rol operador solo ve sus propias conversaciones; el rol admin
  además ve el panel de observabilidad con datos seudonimizados. El historial se resuelve siempre
  desde la sesión autenticada en el servidor, nunca desde la URL.
- **Aplicación web:** protección CSRF en formularios, sin detalles de errores internos, salida del
  modelo sin HTML, validación y re-codificación de imágenes.
- **Desarrollo:** dependencias con versiones fijadas, análisis estático (Bandit), auditoría de
  vulnerabilidades (pip-audit) y detección de secretos en el repositorio (Gitleaks).

Ninguna medida es infalible. `[[VERIFICAR cifrado en reposo y respaldos en MongoDB Atlas]]`

## 11. Derechos del titular

Según la Ley 21.719, tienes derecho a:

- **Acceso:** saber si tratamos tus datos, cuáles y para qué.
- **Rectificación:** corregir datos inexactos, desactualizados o incompletos.
- **Supresión (cancelación):** pedir que se eliminen tus datos cuando corresponda.
- **Oposición:** oponerte a ciertos tratamientos, como el uso de tu feedback para casos de
  evaluación.
- **Bloqueo:** pedir la suspensión temporal de un tratamiento mientras se resuelve una solicitud.
- **Portabilidad:** recibir tus datos en un formato estructurado y de uso común.
- **No ser objeto de decisiones automatizadas** con efectos significativos (sección 8).

`[[VERIFICAR lista exacta y denominación de cada derecho en el texto de la ley]]`

**Cómo ejercerlos:**

- **Supresión del historial:** botón "Eliminar mis datos" en el menú de tu cuenta.
- **Descarga de tus conversaciones:** opción de exportar la conversación desde el menú de tu cuenta.
  `[[VERIFICAR si se implementará "Descargar mis datos" con todos los datos de la cuenta]]`
- **Cualquier otro derecho:** escribiendo a `[[contacto]]`, indicando tu nombre de usuario y el
  derecho que quieres ejercer. Podremos pedirte que confirmes tu identidad con un código enviado a
  tu correo verificado.

**Plazo de respuesta y gratuidad:** `[[VERIFICAR plazo legal de respuesta y condiciones de gratuidad]]`

## 12. Menores de edad

El asistente está destinado exclusivamente a **personal de emergencias mayor de 18 años**. No está
dirigido a menores de edad y no tratamos conscientemente sus datos. Si detectamos una cuenta de un
menor, la eliminaremos. `[[VERIFICAR si se admitirán cadetes o brigadistas juveniles y, en ese caso, las reglas aplicables]]`

## 13. Brechas de seguridad

**Procedimiento interno:**

1. **Detección:** monitoreo de registros de seguridad, alertas automáticas de salud del sistema y
   avisos de usuarios.
2. **Contención:** bloqueo de accesos comprometidos, rotación de credenciales (claves de API,
   contraseña de la base de datos, `OTP_SECRET`, `TELEMETRY_SALT`) y corrección de la causa.
3. **Evaluación:** datos y titulares afectados, gravedad y riesgos.
4. **Registro:** cada incidente se documenta con fecha, alcance, medidas y comunicaciones.
5. **Notificación** según corresponda (abajo).

**Notificación:** si la brecha genera un riesgo para los titulares, se informará a la Agencia de
Protección de Datos Personales y a los afectados por los medios más expeditos posibles y **sin
dilaciones indebidas**. `[[VERIFICAR plazo]]`

Si aplica la Ley 21.663, además se enviará una alerta temprana al CSIRT Nacional de la Agencia
Nacional de Ciberseguridad (ANCI) dentro de **3 horas**, un segundo informe dentro de **72 horas**
y un informe final dentro de **15 días**. `[[VERIFICAR aplicabilidad y plazos]]`

## 14. Transferencias internacionales

Varios proveedores de la sección 7 pueden tratar datos fuera de Chile. Las transferencias se
realizan solo para las finalidades de este aviso y con las garantías que exija la Ley 21.719
(por ejemplo, países con nivel adecuado de protección, cláusulas contractuales o garantías
equivalentes).

| Proveedor | País | Condiciones |
|---|---|---|
| Google (Gemini y Gmail) | `[[VERIFICAR]]` | `[[VERIFICAR]]` |
| MongoDB Atlas | `[[región]]` | `[[VERIFICAR]]` |
| LangSmith | `[[VERIFICAR]]` | `[[VERIFICAR]]` |
| Esri (mapas y satélite) | `[[VERIFICAR]]` | `[[VERIFICAR]]` |
| OpenStreetMap / Nominatim | `[[VERIFICAR]]` | `[[VERIFICAR]]` |
| Hosting y GitHub Actions | `[[VERIFICAR]]` | `[[VERIFICAR]]` |

## 15. Cookies y almacenamiento local

La aplicación usa Streamlit. La sesión de inicio de sesión se mantiene en el estado del servidor
asociado a la conexión de tu navegador: si cierras o recargas la pestaña, debes volver a iniciar
sesión. La aplicación no usa cookies de publicidad ni de seguimiento propias. Streamlit puede usar
una cookie técnica para la protección CSRF (activada en la configuración) y almacenamiento local
del navegador para preferencias de interfaz, como el tema claro u oscuro. Las fuentes tipográficas
se cargan desde Google Fonts, lo que expone tu dirección IP a ese servicio.
`[[VERIFICAR cookies y localStorage que crea la versión de Streamlit en uso y el hosting]]`

## 16. Autoridad de control y reclamos

Puedes presentar un reclamo ante la **Agencia de Protección de Datos Personales**, una vez
constituida conforme a la Ley 21.719. Mientras tanto: `[[ruta de reclamo]]`.

Te recomendamos escribirnos primero al contacto de la sección 19 para intentar resolver tu
solicitud.

## 17. Cambios al aviso

Cada versión de este aviso tiene un identificador (por ejemplo, `2026-12-01-v1`) y una fecha de
vigencia visibles al inicio del documento. Si cambiamos el aviso:

- Publicaremos la nueva versión en la aplicación, con su fecha de vigencia.
- La próxima vez que inicies sesión, te pediremos **leer y aceptar** la nueva versión antes de
  continuar.
- Registramos la versión que aceptaste y la fecha de aceptación.
- Puedes descargar el aviso completo en formato Markdown desde la ventana del aviso.

## 18. Uso responsable

- El Asistente HAZMAT es una **herramienta de apoyo**. No reemplaza al mando del incidente, a los
  protocolos de tu institución ni a la Guía de Respuesta en Emergencias impresa.
- Verifica siempre las citas con la guía impresa antes de actuar.
- **No ingreses datos personales de víctimas** ni de otras personas más allá de lo necesario.
- En una emergencia real, llama al **132 (Bomberos)** o al **131 (SAMU)**.

## 19. Contacto

Para consultas sobre este aviso o para ejercer tus derechos:

- **Correo:** `[[correo]]`
- **Dirección:** `[[dirección]]`
- **Delegado de protección de datos:** `[[DPO]]`
