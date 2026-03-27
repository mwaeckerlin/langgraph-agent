# langgraph-agent — Open-Source LangGraph API Service

Minimal FastAPI service that exposes [LangGraph] as a REST API — no commercial license required.
Docker image available on [mwaeckerlin/langgraph-agent].

## Features

- 🆓 Open-source — no `langchain/langgraph-api` license key needed
- ⚡ Minimal FastAPI service built on [LangGraph] OSS library
- 🐘 PostgreSQL checkpoint support via `langgraph-checkpoint-postgres`
- 🔌 Dynamic graph loading from a configurable directory
- 🔒 Docker Secrets for sensitive values (no shell required in runtime image)

## Port

| Port | Description   |
|------|---------------|
| 8000 | HTTP API      |

## Environment Variables

| Variable          | Description                                      | Default            |
|-------------------|--------------------------------------------------|--------------------|
| `DATABASE_URI`    | PostgreSQL connection URI                        |                    |
| `OPENAI_BASE_URL` | Base URL for OpenAI-compatible API (e.g. LiteLLM) |                  |
| `OPENAI_API_KEY`  | OpenAI API key (prefer Docker Secret)            |                    |
| `GRAPHS_DIR`      | Directory to scan for graph modules              | `/app/graphs`      |
| `LLM_MODEL`       | LLM model name                                   | `gpt-4o-mini`      |

## Docker Secrets

Secrets are read from `/run/secrets/<name>` at runtime (no shell workaround needed).

| Secret                 | Description                          |
|------------------------|--------------------------------------|
| `langgraph_api_key`    | Bearer token for API authentication  |
| `litellm_master_key`   | LiteLLM master key                   |
| `langgraph_db_password`| PostgreSQL password (preferred)      |

## Adding Graphs

Place `.py` files in `GRAPHS_DIR`. Each file must expose:

```python
graph        # compiled LangGraph StateGraph
name         # str — unique graph identifier
description  # str — human-readable description
```

See [`graphs/echo.py`](graphs/echo.py) for a starter example.

## Docker Compose Example

```yaml
services:
  langgraph-agent:
    image: mwaeckerlin/langgraph-agent
    ports:
      - "8000:8000"
    environment:
      DATABASE_URI: postgresql://langgraph:${LANGGRAPH_DB_PASSWORD}@db/langgraph
      OPENAI_BASE_URL: http://litellm:4000
      LLM_MODEL: gpt-4o-mini
      GRAPHS_DIR: /app/graphs
    secrets:
      - langgraph_api_key
      - litellm_master_key
      - langgraph_db_password
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: langgraph
      POSTGRES_DB: langgraph
      POSTGRES_PASSWORD_FILE: /run/secrets/langgraph_db_password
    secrets:
      - langgraph_db_password
    volumes:
      - pg_data:/var/lib/postgresql/data

secrets:
  langgraph_api_key:
    external: true
  litellm_master_key:
    external: true
  langgraph_db_password:
    external: true

volumes:
  pg_data:
```

## API Endpoints

| Method | Path                          | Auth | Description                   |
|--------|-------------------------------|------|-------------------------------|
| GET    | `/ok`                         | No   | Health check                  |
| GET    | `/graphs`                     | Yes  | List loaded graphs            |
| POST   | `/runs`                       | Yes  | Stateless graph execution     |
| POST   | `/threads`                    | Yes  | Create a new thread           |
| POST   | `/threads/{thread_id}/runs`   | Yes  | Run graph with checkpoint     |
| GET    | `/threads/{thread_id}/state`  | Yes  | Get thread state              |

Authentication uses `Authorization: Bearer <langgraph_api_key>`.

[LangGraph]: https://github.com/langchain-ai/langgraph
[mwaeckerlin/langgraph-agent]: https://hub.docker.com/r/mwaeckerlin/langgraph-agent
