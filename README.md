<div align="center">

# Asistente Táctico HAZMAT

### Ingeniería de Soluciones con Inteligencia Artificial — Duoc UC

**Sistema de Consulta Inteligente basado en RAG para Emergencias con Materiales Peligrosos**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.63-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Google Gemini](https://img.shields.io/badge/Gemini-3.5%20Flash-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Duoc UC](https://img.shields.io/badge/Duoc%20UC-Puerto%20Montt-003DA5?style=flat&logo=education&logoColor=white)](#)
[![Version](https://img.shields.io/badge/Version-4.0.0-CE1004?style=flat)](#)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen?style=flat&logo=githubactions&logoColor=white)](#)

---

*Consulta instantánea y precisa de protocolos HAZMAT con trazabilidad de fuentes y cero alucinaciones.*

</div>

---

## Descripción General

El **Asistente Táctico HAZMAT** es un sistema de inteligencia artificial desarrollado como proyecto académico para la asignatura **Ingeniería de Soluciones con Inteligencia Artificial** en **Duoc UC Puerto Montt**. El sistema permite consultar de manera instantánea la **Guía de Respuesta en Emergencias (GRE 2024)** y el **Manual ABC-V** durante incidentes con materiales peligrosos.

El sistema implementa una arquitectura **RAG (Retrieval-Augmented Generation)** que combina búsqueda semántica vectorial con generación de texto controlada, garantizando respuestas verificadas, trazables y sin alucinaciones.

### Problema que Resuelve

| Dimensión | Desafío |
|-----------|---------|
| **Latencia** | Consulta manual de documentos extensos genera demoras inaceptables en escenarios donde cada minuto es crítico |
| **Error humano** | La presión operativa incrementa la probabilidad de seleccionar protocolos incorrectos |
| **Dispersión** | La información relevante está distribuida entre múltiples documentos y secciones |

### Solución

- **Respuesta en tiempo real** (< 5 segundos) para consultas tácticas
- **Cero alucinaciones** mediante anclaje estricto al contexto recuperado
- **Trazabilidad de fuentes** con citación de página y sección del manual
- **Formato táctico** con distancias de evacuación, riesgos y acciones inmediatas

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLUJO RAG COMPLETO                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │  PDFs    │───▶│ Chunking │───▶│Embeddings│───▶│ MongoDB  │     │
│  │  GRE/ABC │    │ 1000 chr │    │ 384 dim  │    │  Atlas   │     │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘     │
│                                                       │            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐        │            │
│  │Consulta  │───▶│ Embedding│───▶│  Vector  │◀───────┘            │
│  │ Usuario  │    │  Query   │    │  Search  │                     │
│  └──────────┘    └──────────┘    └────┬─────┘                     │
│                                       │                            │
│                                       ▼                            │
│                              ┌────────────────┐                    │
│                              │ System Prompt  │                    │
│                              │   + Contexto   │                    │
│                              │   + Historial  │                    │
│                              └───────┬────────┘                    │
│                                      │                             │
│                                      ▼                             │
│                              ┌────────────────┐                    │
│                              │  Gemini 3.5    │                    │
│                              │     Flash      │                    │
│                              └───────┬────────┘                    │
│                                      │                             │
│                                      ▼                             │
│                              ┌────────────────┐                    │
│                              │   Respuesta    │                    │
│                              │  Verificada    │                    │
│                              └────────────────┘                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

### Frontend
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework UI | Streamlit | 1.63.0 |
| Diseño CSS | Sistema institucional (23 archivos) | — |
| Iconografía | Material Symbols | — |

### Backend
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Lenguaje | Python | 3.12 |
| LLM | Google Gemini 3.5 Flash | — |
| Embeddings | all-MiniLM-L6-v2 (HuggingFace) | 384 dim |
| Vector Store | MongoDB Atlas Vector Search | — |
| Framework IA | LangChain | — |
| Observabilidad | LangSmith | — |

### Infraestructura
| Componente | Tecnología | Versión |
|------------|------------|---------|
| Containerización | Docker + Docker Compose | — |
| Base de datos | MongoDB Atlas (M10+) | — |
| CI/CD | GitHub Actions | v4 |
| Seguridad | Hadolint, Bandit, pip-audit | — |

### Documentos Fuente
| Documento | Descripción |
|-----------|-------------|
| GRE 2024 | Guía de Respuesta en Emergencias |
| Manual ABC-V | Clasificación de incendios y materiales peligrosos |

---

## Estructura del Proyecto

```
Asistente_HAZMAT/
├── app.py                          # Punto de entrada principal
├── Dockerfile                      # Containerización multi-etapa
├── docker-compose.yml              # Orquestación de servicios
├── requirements.txt                # Dependencias ligeras
├── requirements-heavy.txt          # Dependencias ML/NLP
│
├── src/
│   ├── config/
│   │   └── settings.py            # Configuración Singleton
│   │
│   ├── ingesta/
│   │   ├── loaders.py             # Carga de PDFs
│   │   ├── processor.py           # Chunking y embeddings
│   │   └── ingest.py              # Orquestador CLI
│   │
│   ├── retrieval/
│   │   └── retriever.py           # Vector Search MongoDB
│   │
│   ├── generate/
│   │   └── generator.py           # Integración Gemini
│   │
│   ├── session/
│   │   ├── manager.py             # Gestión de sesiones
│   │   ├── models.py              # Modelos Pydantic v2
│   │   ├── repository.py          # Capa de persistencia
│   │   ├── security.py            # Seguridad multicapa
│   │   └── export_manager.py      # Exportación JSON/MD
│   │
│   ├── ui/
│   │   ├── sidebar.py             # Panel lateral
│   │   ├── sidebar_history.py     # Historial de conversaciones
│   │   ├── sidebar_export.py      # Modal de exportación
│   │   ├── chat.py                # Lógica de chat
│   │   ├── styles.py              # Carga de estilos
│   │   ├── components/            # Componentes reutilizables
│   │   ├── layout/                # Layout y headers
│   │   └── renderers/             # Formateo de respuestas
│   │
│   └── utils/
│       ├── prompts.py             # System prompt HAZMAT
│       └── constants.py           # Constantes globales
│
├── styles/                        # Sistema de diseño CSS
│   ├── tokens/                    # Variables de diseño
│   ├── base/                      # Reset y reglas base
│   ├── components/                # Estilos de componentes
│   └── utilities/                 # Utilidades CSS
│
└── data/                          # Documentos PDF fuente
```

---

## Instalación y Configuración

### Requisitos Previos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose v2
- Cuenta en [Google AI Studio](https://aistudio.google.com/) (API Key gratuita)
- Cluster en [MongoDB Atlas](https://www.mongodb.com/atlas) con Vector Search habilitado
- (Opcional) Cuenta en [LangSmith](https://smith.langchain.com/) para observabilidad

### Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/DavNat13/Asistente_HAZMAT.git
   cd Asistente_HAZMAT
   ```

2. **Configurar variables de entorno:**
   ```bash
   cp .env.example .env
   ```
   Edita `.env` con tus credenciales:
   ```env
   GOOGLE_API_KEY=tu_api_key_de_google_ai_studio
   MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/?retryWrites=true&w=majority
   LANGCHAIN_API_KEY=tu_langsmith_key  # Opcional
   LANGCHAIN_TRACING_V2=true           # Opcional
   LANGCHAIN_PROJECT=Bomberos-HAZMAT-RAG
   ```

### Ejecución con Docker

1. **Fase de Ingesta** (primera vez):
   ```bash
   docker-compose run --rm hazmat-rag python src/ingesta/ingest.py --data
   ```

2. **Levantar la Interfaz:**
   ```bash
   docker-compose up --build -d
   ```
   Accede en: `http://localhost:8501`

3. **Detener el sistema:**
   ```bash
   docker-compose down
   ```

---

## Módulos Principales

### Pipeline RAG

| Fase | Componente | Descripción |
|------|------------|-------------|
| **Ingesta** | `src/ingesta/` | Carga PDFs, fragmenta texto (1000 chr, 150 overlap), genera embeddings |
| **Indexación** | MongoDB Atlas | Índice vectorial HNSW con similitud coseno |
| **Recuperación** | `src/retrieval/` | Vector Search con top_k=8, numCandidates=80, min_score=0.50 |
| **Generación** | `src/generate/` | Gemini 3.5 Flash con temperature=0.1, historial de 6 mensajes |

### Seguridad Multicapa

| Capa | Mecanismo |
|------|-----------|
| **Validación** | UUID v4, Pydantic models |
| **Anti-inyección** | Detección de patrones NoSQL (`$where`, `$regex`, `$ne`) |
| **Anti-XSS** | `html.escape()`, sanitización recursiva |
| **Persistencia** | TTL automático de 90 días para sesiones inactivas |

### Sistema de Diseño

- **23 archivos CSS** organizados en tokens, base, componentes y utilidades
- **Paleta institucional**: Rojo (#CE2029), Dorado (#FFB000), Texto (#F5F2E9), Fondo (#1A1A1A)
- **Responsive** con breakpoints para móvil, tablet y escritorio
- **Accesibilidad** con contraste WCAG 2.1 AA

---

## Integración Continua

El pipeline de CI/CD ejecuta automáticamente:

| Job | Descripción |
|-----|-------------|
| **Linting** | Ruff (linting + formato), MyPy (tipos), Bandit (seguridad) |
| **Pruebas** | pytest con cobertura (coverage.xml, htmlcov/) |
| **Seguridad** | pip-audit para vulnerabilidades de dependencias |
| **Docker** | Hadolint (linting Dockerfile), verificación de compose |

```bash
# Ejecutar localmente
ruff check .
ruff format --check .
pytest --cov=src -v
```

---

## Uso del Sistema

### Ejemplo de Consulta

```
Consulta: Emergencia química en curso. Volcadura de camión cisterna en carretera
con fuga activa de Amoníaco Anhidro (UN 1005). Indique de inmediato los riesgos
a la salud, las acciones iniciales de aislamiento y las distancias de evacuación
correspondientes.
```

**Respuesta del sistema:**
- Riesgos a la salud del amoníaco anhidro
- Distancias de evacuación por浓度
- Acciones iniciales de contención
- EPP requerido para el personal
- Fuente citada: GRE 2024, página 42

### Formato de Respuesta

Cada respuesta incluye:
- **Listas con viñetas** para distancias, riesgos y acciones
- **Citación de fuentes** con número de página del manual
- **Advertencias** cuando la información no está disponible en el contexto
- **Indicador de trazabilidad** para verificación en documento físico

---

## Rendimiento

| Métrica | Valor |
|---------|-------|
| Latencia promedio de respuesta | < 5 segundos |
| Tiempo de ingestión por PDF | ~30 segundos |
| Dimensionalidad de embeddings | 384 dimensiones |
| Tamaño del chunk | 1000 caracteres |
| Overlap entre chunks | 150 caracteres |
| Candidatos por consulta (HNSW) | 80 |
| Resultados retornados (top_k) | 8 |

---

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit con convención ([Conventional Commits](https://www.conventionalcommits.org/))
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Convención de Commits

```
feat(scope): descripción en español v3.4.0
fix(scope): corrección de bug
refactor(scope): reestructuración de código
docs(scope): documentación
```

---

## Licencia

Este proyecto es de carácter **académico** para la asignatura Ingeniería de Soluciones con Inteligencia Artificial en Duoc UC. El código fuente está disponible para fines de auditoría y colaboración técnica.

---

## Contacto

**David Nahuelcar Tecas**
- Proyecto: Asistente Táctico HAZMAT
- Institución: Duoc UC Puerto Montt
- Asignatura: Ingeniería de Soluciones con Inteligencia Artificial

---

<div align="center">

**Desarrollado con compromiso para la investigación y desarrollo de soluciones de IA**

*Duoc UC Puerto Montt — Septiembre 2026*

</div>
