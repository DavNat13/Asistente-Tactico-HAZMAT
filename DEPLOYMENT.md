<div align="center">

<img src="docs/assets/icons/rocket.svg" width="44" height="44" alt="">

# Guía de despliegue

**Asistente HAZMAT** · Del repositorio a un servidor con HTTPS

</div>

---

## Opción gratuita: Streamlit Community Cloud

Despliegue continuo sin costo ni tarjeta, con HTTPS. Streamlit Cloud instala un único `requirements.txt`,
así que el flujo `.github/workflows/deploy-streamlit.yml` genera la rama **`streamlit-cloud`** (= `main` +
dependencias unificadas, con PyTorch CPU por URL directa) cada vez que el CI pasa en `main`.

1. **Rama de despliegue.** En GitHub, **Actions → Despliegue en Streamlit Cloud → Run workflow** (solo la
   primera vez; después se actualiza sola). Debe aparecer la rama `streamlit-cloud`.
2. **Crear la app.** Entra a [share.streamlit.io](https://share.streamlit.io) con tu cuenta de GitHub →
   **Create app → Deploy a public app from GitHub**:
   - Repository: `DavNat13/Asistente-Tactico-HAZMAT` · Branch: **`streamlit-cloud`** · Main file: `app.py`
   - App URL: un subdominio, por ejemplo `asistente-hazmat` → `https://asistente-hazmat.streamlit.app`
3. **Advanced settings.** Python **3.12**. En **Secrets** pega la configuración en formato TOML (aquí las
   comillas **sí** van, porque es TOML; cada clave se expone como variable de entorno):

   ```toml
   GEMINI_API_KEYS = "clave1,clave2"
   MONGODB_URI = "mongodb+srv://..."
   MONGODB_DB_NAME = "hazmat_gre"
   MONGODB_COLLECTION_NAME = "gre_chunks_v5"
   OTP_SECRET = "..."
   TELEMETRY_SALT = "..."
   SMTP_USER = "tu.cuenta@dominio.cl"
   SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"
   MAIL_FROM = "tu.cuenta@dominio.cl"
   ADMIN_EMAILS = "admin@dominio.cl"
   APP_URL = "https://asistente-hazmat.streamlit.app"
   EMAIL_VERIFICATION_REQUIRED = "true"
   ESRI_API_KEY = "..."
   LANGCHAIN_TRACING_V2 = "false"
   ```
4. **Deploy.** La primera instalación tarda varios minutos. El modelo de embeddings se descarga al primer uso.
5. **Mapas.** Agrega la URL `https://asistente-hazmat.streamlit.app` en los *Referrers* de la clave Esri.

> [!WARNING]
> Streamlit Cloud documenta hasta ~2,7 GB de RAM por app; esta app usa ~0,8 GB en reposo y hasta ~1,4 GB
> en picos. Si aparece "This app has gone over its resource limits", reinicia la app desde **Manage app**.
> La app se duerme tras varias horas sin visitas y despierta al entrar.

## Opción gratuita: Hugging Face Spaces

> [!CAUTION]
> Las cuentas nuevas de Hugging Face tienen hoy **cuota gratuita 0** para `cpu-basic` (error
> `Quota exceeded for flavor cpu-basic ... limit=0`); en ese caso hace falta Hugging Face PRO. El flujo
> `.github/workflows/deploy-huggingface.yml` quedó **solo manual** para cuentas con cuota.

Docker, 2 vCPU, 16 GB de RAM y HTTPS incluido. El flujo publica una copia limpia en el Space.

1. **Cuenta y Space.** Crea una cuenta en [huggingface.co](https://huggingface.co) y luego
   **New Space**: nombre (por ejemplo `asistente-hazmat`), SDK **Docker** → plantilla **Blank**,
   hardware **CPU basic (free)** y visibilidad **Public**. Un Space privado exige iniciar sesión en
   Hugging Face para usar la app.
2. **Variables del Space.** En el Space, entra a **Settings → Variables and secrets** y agrega como
   *Secrets* `GEMINI_API_KEYS`, `MONGODB_URI`, `OTP_SECRET`, `TELEMETRY_SALT`, `SMTP_USER`,
   `SMTP_PASSWORD`, `MAIL_FROM`, `ADMIN_EMAILS`, `ESRI_API_KEY` y, si lo usas, `LANGCHAIN_API_KEY`.
   Agrega como *Variables* `APP_URL=https://usuario-asistente-hazmat.hf.space` y
   `EMAIL_VERIFICATION_REQUIRED=true`. Pega **solo el valor**, sin comillas.
3. **Token.** En **Settings → Access Tokens** de tu cuenta de Hugging Face, crea un token de tipo
   **Write** (o *fine-grained* con escritura solo sobre ese Space).
4. **GitHub.** En el repositorio, entra a **Settings → Secrets and variables → Actions** y crea el secret
   `HF_TOKEN` con ese token y la variable `HF_SPACE=usuario/asistente-hazmat`.
5. **Publicar.** Ejecuta **Actions → Despliegue en Hugging Face → Run workflow**. El Space construye la imagen (~10 minutos la primera vez).
6. **Mapas.** Agrega `https://usuario-asistente-hazmat.hf.space` en los *Referrers* de la clave Esri.
7. **Administrador.** Desde tu equipo, con el mismo `.env` (misma base de datos):
   `python -m src.security.create_user --username admin --role admin --email tu@correo.cl`.

> [!NOTE]
> Usa la dirección directa `https://usuario-asistente-hazmat.hf.space`. Dentro del marco de la página
> del Space el navegador puede bloquear la ubicación GPS y la subida de fotos. En el plan gratuito, el
> Space se suspende tras unas 48 horas sin visitas y despierta en alrededor de un minuto al entrar.

El resto de esta guía describe un despliegue en servidor propio con Docker Compose.

## Requisitos

| Componente | Requisito |
|---|---|
| Servidor | Linux con Docker y Docker Compose, **2 GB de RAM libres** para el contenedor y ~6 GB de disco |
| Dominio | Un dominio o subdominio apuntando al servidor, con **HTTPS** (obligatorio para la ubicación GPS) |
| Base de datos | MongoDB Atlas con **Vector Search**, y la IP del servidor permitida en *Network Access* |
| Modelo | Una o más claves de la API de Gemini |
| Correo | Cuenta de Gmail o Google Workspace con verificación en 2 pasos y **contraseña de aplicación** |
| Mapas (opcional) | Clave de Esri ArcGIS Location Platform; Google Map Tiles API si se quiere la capa de tráfico |

## 1. Base de datos

Indexa la GRE 2024 y el Manual ABC-V una sola vez, desde una máquina con los PDF en `data/`:

```bash
python -m src.ingesta.ingest --data --clear --create-index
```

El proceso crea las colecciones, el índice vectorial y el índice ONU. Los índices TTL de sesiones,
telemetría, códigos y cuentas pendientes se crean solos al iniciar la app.

## 2. Variables de entorno

Copia la plantilla y complétala en el servidor. **Nunca** subas `.env` al repositorio.

```bash
cp .env.example .env
```

| Variable | Obligatoria | Valor |
|---|:---:|---|
| `GEMINI_API_KEYS` | Sí | Claves separadas por coma |
| `MONGODB_URI` | Sí | Cadena `mongodb+srv://` de Atlas |
| `OTP_SECRET` | Sí | Aleatorio, 32+ caracteres (ver abajo) |
| `TELEMETRY_SALT` | Sí | Aleatorio, 32+ caracteres, distinto de `OTP_SECRET` |
| `SMTP_USER` | Sí | **Dirección de correo completa** que envía los mensajes |
| `SMTP_PASSWORD` | Sí | Contraseña de aplicación de 16 letras (no tu contraseña normal) |
| `MAIL_FROM` | Sí | Normalmente igual a `SMTP_USER` |
| `ADMIN_EMAILS` | Sí | Correos que reciben alertas y reportes, separados por coma |
| `APP_URL` | Sí | Dirección pública con HTTPS, por ejemplo `https://hazmat.tu-dominio.cl` |
| `EMAIL_VERIFICATION_REQUIRED` | Sí | `true` en producción |
| `ESRI_API_KEY` | No | Capas satelitales y mapas base |
| `GOOGLE_MAPS_API_KEY` | No | Capas de Google (requiere facturación) |
| `LANGCHAIN_API_KEY` | No | Trazas en LangSmith (`LANGCHAIN_TRACING_V2=true`) |

Genera cada secreto con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

> [!WARNING]
> Define `OTP_SECRET` y `TELEMETRY_SALT` **antes** de abrir la app a usuarios y no los cambies después:
> cambiar la sal desordena el historial de métricas y cambiar `OTP_SECRET` invalida los códigos ya enviados.

Comprueba el correo antes de seguir:

```bash
python -m src.notify.smtp_check --send-to tu@correo.cl
```

## 3. Construir y ejecutar

```bash
docker compose up -d --build
docker compose ps                       # debe mostrar "healthy" en menos de un minuto
docker compose logs -f hazmat-rag       # registro en vivo
```

La primera construcción tarda unos 10 minutos (PyTorch y el modelo de embeddings); las siguientes reutilizan
la caché y tardan segundos si solo cambia el código. La app queda en el puerto `8501` del servidor.

## 4. HTTPS con proxy inverso

Expón la app solo a través de un proxy con certificado. Ejemplo con [Caddy](https://caddyserver.com), que
obtiene y renueva el certificado automáticamente y admite WebSocket:

```caddy
hazmat.tu-dominio.cl {
    reverse_proxy localhost:8501
}
```

> [!NOTE]
> Detrás de un proxy, la IP que ve la app es la del proxy. Por eso los límites por IP son holgados, y los
> límites por cuenta y por correo siguen protegiendo el registro y la recuperación.

## 5. Claves de mapas

1. En el panel de Esri, agrega el dominio de producción (por ejemplo `https://hazmat.tu-dominio.cl`) en
   los **Referrers** de la clave, además de `http://localhost:8501` si pruebas en local.
2. Si usas Google, restringe la clave a **Map Tiles API** y a tu dominio en Google Cloud Console.

Sin claves, el mapa funciona igual con OpenStreetMap.

## 6. Cuenta de administración

```bash
docker compose exec hazmat-rag python -m src.security.create_user \
  --username admin --role admin --email admin@tu-dominio.cl
```

La contraseña se pide de forma interactiva. Las cuentas creadas así quedan con el correo verificado, de
modo que siempre existe una vía de entrada aunque el correo falle. El resto de los usuarios se registra
desde la app con rol `operador`.

Si hay cuentas creadas antes de la v5.3, pásalas a verificación de correo:

```bash
docker compose exec hazmat-rag python -m src.security.migrate_verification --dry-run
docker compose exec hazmat-rag python -m src.security.migrate_verification --apply
```

## 7. GitHub Actions

En **Settings → Secrets and variables → Actions** del repositorio:

| Tipo | Nombre | Usado por |
|---|---|---|
| Secret | `GEMINI_API_KEYS` | Evaluación nocturna, monitoreo |
| Secret | `MONGODB_URI` | Evaluación nocturna, monitoreo |
| Secret | `TELEMETRY_SALT` | Evaluación nocturna, monitoreo (debe ser **el mismo** que en el servidor) |
| Secret | `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` | Envío de alertas y reportes |
| Secret | `ADMIN_EMAILS` | Destinatarios de alertas y reportes |
| Variable | `APP_URL` | Enlace en los correos |

Si faltan los tres primeros, los flujos programados **se omiten con un aviso** en lugar de fallar. La
IP de los *runners* de GitHub cambia, así que Atlas debe permitir su acceso (por ejemplo `0.0.0.0/0` con
usuario de mínimos privilegios) o el monitoreo no podrá conectarse.

## 8. Lista de verificación antes de abrir

- [ ] `docker compose ps` muestra **healthy** y el pie de la pantalla de acceso, la versión esperada.
- [ ] HTTPS activo; "Usar mi ubicación" pide permiso en el navegador.
- [ ] Registro con un correo real: llega el código, se verifica y se entra.
- [ ] "¿Olvidaste tu contraseña?" envía el código y permite cambiarla.
- [ ] El mapa muestra las capas de Esri (si hay clave).
- [ ] El panel de Observabilidad (rol admin) muestra datos y el semáforo.
- [ ] Los flujos de GitHub Actions terminan sin avisos de secrets faltantes.
- [ ] El aviso de privacidad tiene sus marcadores `[[...]]` completados y revisión legal (uso real).

## 9. Actualizar y revertir

```bash
git pull
docker compose up -d --build            # reconstruye solo lo que cambió
```

Para revertir, vuelve al commit o *tag* anterior y reconstruye. Etiquetar cada versión desplegada
(`git tag v5.4.1`) facilita el retroceso.

## Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| El contenedor se reinicia o muere | Memoria insuficiente | Verifica `mem_limit: 2g` y la RAM libre del servidor |
| "El registro requiere el envío de correo…" | Correo mal configurado | `python -m src.notify.smtp_check` y revisa `SMTP_USER` |
| No llega el código | Spam o remitente distinto de la cuenta | Revisa spam y que `MAIL_FROM` coincida con `SMTP_USER` |
| "No se pudo crear la cuenta (ref. …)" | Error inesperado | Busca la referencia en `docker compose logs` o en `security_events` |
| Mapa satelital gris | Clave de Esri sin el dominio en Referrers, o vencida | Agrega el dominio o genera una clave nueva |
| "La ubicación requiere HTTPS" | La app se sirve por HTTP | Configura el proxy con certificado |
| Comportamiento extraño tras actualizar | Más de un servidor en ejecución | Deja un solo contenedor o proceso de Streamlit |
