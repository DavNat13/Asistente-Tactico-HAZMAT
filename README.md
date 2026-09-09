# Asistente Táctico HAZMAT - Bomberos de Chile

Este repositorio contiene la implementación de un Asistente Virtual basado en IA Generativa (RAG) diseñado para Centrales de Alarmas y equipos de Materiales Peligrosos (HAZMAT) de Bomberos de Chile. El sistema permite consultar de manera instantánea y precisa la Guía de Respuesta en Caso de Emergencia (GRE), asegurando trazabilidad y cero alucinaciones mediante controles estrictos de contexto.

## Tecnologías Utilizadas
* **Frontend:** Streamlit
* **LLM & Embeddings:** Google Gemini (`gemini-1.5-flash`, `gemini-embedding-001`)
* **Vector Store:** MongoDB Atlas (Vector Search)
* **Observabilidad:** LangSmith
* **Despliegue:** Docker y Docker Compose

## Requisitos Previos
1. Docker y Docker Compose instalados.
2. Cuenta en Google AI Studio (API Key gratuita).
3. Cluster en MongoDB Atlas con Vector Search configurado.
4. (Opcional) Cuenta en LangSmith para monitoreo de tokens.

## Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd Asistente_HAZMAT
   ```

2. **Configurar variables de entorno:**
   Copia el archivo `.env.example` y renómbralo a `.env`. Completa las credenciales:
   ```env
   GOOGLE_API_KEY=tu_api_key_aqui
   MONGODB_URI=tu_conexion_mongodb_aqui
   LANGCHAIN_API_KEY=tu_langsmith_key_aqui
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=Bomberos-HAZMAT-RAG
   ```

## Ejecución del Sistema con Docker

El proyecto está dockerizado para asegurar una ejecución estable sin depender de configuraciones locales.

1. **Fase de Ingesta (Solo la primera vez):**
   Ejecuta el script de ingesta dentro de un contenedor temporal para poblar la base de datos MongoDB:
   ```bash
   docker-compose run --rm hazmat-rag python src/ingesta/ingest.py --github <URL_REPO_CON_PDF>
   ```

2. **Levantar la Interfaz de Usuario:**
   Construye e inicia el contenedor en segundo plano:
   ```bash
   docker-compose up --build -d
   ```
   Accede al asistente abriendo tu navegador en: `http://localhost:8501`

3. **Detener el sistema:**
   ```bash
   docker-compose down
   ```

## Evaluación de Trazabilidad
El sistema está diseñado para que cada respuesta táctica incluya la cita exacta de la página de la Guía GRE de donde se extrajo la información. Para auditar el flujo de los datos, latencia y calidad, revisa el panel del proyecto configurado en LangSmith.
