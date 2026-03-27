# LangGraph Agent API Service

[mwaeckerlin/langgraph-agent] is a minimal FastAPI service that exposes [LangGraph] workflows as REST API — no commercial license key required.

Open-source and minimal: Just a stateless API server running as unprivileged user, with optional PostgreSQL checkpoint state storage for persistent graph execution.

Image size: ca. 9.87MB (depends on parent image sizes and changes)

This is the most lean and secure image for NGINX servers:
 - extremely small size, minimalistic dependencies
 - no shell, only the server command
 - small attack surface
 - starts as non root user

## Port

Exposes API on port `8000`.

## Configuration

- API endpoint: `http://localhost:8000`
- Health check: `GET /ok`
- Graph discovery from `/app/graphs` — place `.py` modules with `graph`, `name`, `description` exports
- Environment variables: `DATABASE_URI`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `GRAPHS_DIR`, `LLM_MODEL`
- Docker Secrets: `langgraph_api_key`, `litellm_master_key`, `langgraph_db_password`

### Docker Compose Sample

See `docker-compose.yml` for an example:

- `docker-compose build`
- `docker-compose up`
- browse to: `http://localhost:8000/docs` (interactive API docs)
- stop with `Ctrl+C`

### Command Line Example

    docker run -it --rm --name agent -p 8000:8000 mwaeckerlin/langgraph-agent

Browse to http://localhost:8000/ok. Returns 200 when healthy. Cleans up when you press `Ctrl+C`.

### Adding Graphs

Place `.py` files in `GRAPHS_DIR` (default `/app/graphs`). Each module must expose:

- `graph`: compiled LangGraph StateGraph
- `name`: str — unique graph identifier
- `description`: str — human-readable description

Example: see [`graphs/echo.py`](graphs/echo.py).

[LangGraph]: https://github.com/langchain-ai/langgraph
[mwaeckerlin/langgraph-agent]: https://hub.docker.com/r/mwaeckerlin/langgraph-agent
