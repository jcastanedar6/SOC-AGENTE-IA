# Despliegue — Agente SOC

## Requisitos Mínimos

- **CPU**: 4 vCPU
- **RAM**: 8 GB
- **Disco**: 50 GB SSD
- **SO**: Linux (Ubuntu 22.04+), macOS, o Windows con WSL2

## Software Requerido

| Software | Versión | Instalación |
|----------|---------|-------------|
| Docker & Docker Compose | Última estable | [docker.com](https://docs.docker.com/get-docker/) |
| Ollama | Última | [ollama.com](https://ollama.com/) |
| Modelo Open Code | opencode | `ollama pull opencode` |

---

## Despliegue con Docker (recomendado)

### 1. Clonar y configurar

```bash
git clone <repo-url> agente-soc
cd agente-soc
cp .env.example .env
# Editar .env si es necesario (Telegram tokens, etc.)
```

### 2. Iniciar el stack

```bash
docker compose up -d
```

Esto levanta:
- `soc-postgres`: PostgreSQL 16 en puerto 5432
- `soc-backend`: FastAPI en puerto 8002
- `soc-frontend`: Nginx + React build en puerto 5175

### 3. Verificar

```bash
curl http://localhost:8002/health
# {"status":"online","agent":"Agente SOC","version":"1.0.0"}

# Abrir en navegador: http://localhost:5175
```

### 4. Asegurar que Ollama esté corriendo

```bash
ollama pull opencode
ollama serve
```

El backend se conecta a Ollama via `host.docker.internal:11434`.

### 5. Ejecutar el simulador (opcional)

```bash
cd simulator
python event_generator.py --scenario combined
```

### 6. Ejecutar el agente

Desde el frontend, click en "Analizar" o vía API:

```bash
curl -X POST http://localhost:8002/api/v1/agent/run
```

---

## Despliegue Manual (sin Docker)

### Backend

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Configurar DATABASE_URL, OPENCODE_API_URL, etc.
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Servidor de desarrollo en http://localhost:5175
# Para producción: npm run build && npm run preview
```

---

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./agente_soc.db` | Conexión a base de datos |
| `OPENCODE_API_URL` | `http://localhost:11434` | URL del servidor Ollama |
| `OPENCODE_MODEL` | `opencode` | Modelo LLM a usar |
| `OPENCODE_TIMEOUT` | `30` | Timeout en segundos para LLM |
| `TELEGRAM_BOT_TOKEN` | (vacío) | Token del bot de Telegram |
| `TELEGRAM_CHAT_IDS` | (vacío) | IDs de chat separados por coma |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | Directorio de persistencia de ChromaDB |
| `EMBEDDER_MODEL` | `all-MiniLM-L6-v2` | Modelo de embeddings |
| `RAG_TOP_K` | `5` | Número de documentos a recuperar |
| `CORRELATION_WINDOW_SECONDS` | `60` | Ventana de correlación en segundos |
| `BRUTE_FORCE_THRESHOLD` | `5` | Intentos fallidos para detectar brute force |

---

## Comandos Útiles

```bash
# Ver logs del backend
docker compose logs -f backend

# Ejecutar tests
docker compose exec backend python -m pytest tests/unit/ -v

# Restaurar base de datos
docker compose down -v  # Elimina volúmenes (PELIGRO: borra datos)

# Reconstruir un servicio
docker compose build --no-cache backend

# Acceder a la base de datos
docker compose exec postgres psql -U soc_user -d soc_agent
```

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| Backend no conecta a PostgreSQL | Verificar que `postgres` esté healthy: `docker compose ps` |
| LLM no responde | Verificar Ollama: `curl http://localhost:11434/api/tags` |
| Embedding falla | Verificar que el modelo se descargó: revisar `huggingface_cache` volume |
| Frontend muestra pantalla en blanco | Revisar la consola del navegador; verificar que el proxy `/api` funcione |
| Puerto 5175 ocupado | Cambiar en `docker-compose.yml` el mapeo de puertos del frontend |
