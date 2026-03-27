# Minimalistic Secure LangGraph Agent API Docker Image

[mwaeckerlin/langgraph-agent] is a minimalistic, highly optimized and secure image to run [LangGraph] agent workflows as a REST API.

Built on top of [mwaeckerlin/python], using [mwaeckerlin/python-build] for multi-stage builds. No commercial license required — uses LangGraph as an open-source Python library.

This image is intended as a self-hosted alternative to `langchain/langgraph-api` for local and on-prem deployments, without requiring platform registration or commercial runtime licensing.

 - extremely small size, minimalistic dependencies
 - no shell, only the Python runtime
 - small attack surface
 - starts as non-root user
 - dynamic graph loading from volume-mounted Python modules
 - PostgreSQL-backed checkpoint persistence for stateful agents (fail fast if DB is missing)

## Port

Exposes API on port `8000`.

## Configuration

 - Graphs are loaded from `GRAPHS_DIR` (default `/app/graphs`) — mount `.py` modules with `graph`, `name`, `description` exports
 - Authentication via Docker secret `langgraph_api_key` or environment variable `LANGGRAPH_API_KEY`
 - LLM access via OpenAI-compatible endpoint (e.g. [LiteLLM])

### Environment Variables

 - `DATABASE_URI` — PostgreSQL connection string for checkpoint persistence (**required**, startup fails if missing)
 - `OPENAI_BASE_URL` — OpenAI-compatible API base URL (e.g. `http://litellm:4000/v1`)
 - `OPENAI_API_KEY` — API key for the LLM endpoint (can also be read from secret `litellm_master_key`)
 - `GRAPHS_DIR` — directory to scan for graph modules (default `/app/graphs`)
 - `LLM_MODEL` — default model name (default `gpt-4o-mini`)

### Docker Secrets (optional)

Secrets are read from `/run/secrets/` and take precedence over environment variables:

 - `langgraph_api_key` — Bearer token for API authentication
 - `litellm_master_key` — LLM endpoint API key (sets `OPENAI_API_KEY`)
 - `langgraph_db_password` — fallback to construct `DATABASE_URI` when `DATABASE_URI` is not set

### API Endpoints

 - `GET /ok` — health check (no auth required)
 - `GET /graphs` — list loaded graphs
 - `POST /runs` — execute a graph statelessly
 - `POST /threads` — create a conversation thread
 - `POST /threads/{thread_id}/runs` — execute a graph with checkpoint persistence
 - `GET /threads/{thread_id}/state` — retrieve thread state

## Compared to langchain/langgraph-api

This project focuses on a lightweight self-hosted runtime and intentionally keeps a smaller operational surface.

What this image provides:

- Local/on-prem deployment without platform registration.
- No commercial runtime license requirement for this container.
- Minimal API for graph execution and thread persistence.
- Simple integration path for n8n and custom HTTP clients.

What is intentionally out of scope compared to full platform runtimes:

- Control-plane/admin APIs and platform tenancy features.
- Managed orchestration features (advanced queueing/backpressure policies).
- Full platform observability stack and hosted operations.
- Managed deployment/version governance as a service.

### Docker Compose Sample

See `docker-compose.yml` for a local example stack with:

 - `db` (PostgreSQL)
 - `n8n`
 - `langgraph-agent`
 - environment-variable based local configuration

Start:

 - `npm run start`
 - health check: `http://localhost:8583/ok`
 - n8n UI: `http://localhost:5678`

Notes:

 - The stack reads variables from `.env` (Docker Compose standard).
 - `.env` is ignored by git; commit only `.env.example`.
 - `POST /runs` needs a real LLM endpoint/key (`OPENAI_BASE_URL`, `OPENAI_API_KEY`).

### Configure OpenAI/OpenRouter Key via .env

1. Create local env file:
   - `cp .env.example .env`
2. Edit `.env` and set at least:
   - `OPENAI_BASE_URL=https://openrouter.ai/api/v1` (or your OpenAI-compatible endpoint)
   - `OPENAI_API_KEY=<your_real_api_key>`
3. Restart stack:
   - `npm run start`

Example `.env`:

```dotenv
POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=local_db_password
N8N_ENCRYPTION_KEY=local_n8n_encryption_key
LANGGRAPH_API_KEY=local_langgraph_api_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-or-v1-xxxxxxxx
LLM_MODEL=openrouter/openai/gpt-4o-mini
```

Provider/Key matching is mandatory:

- OpenRouter key (`sk-or-v1-...`) requires:
  - `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
- OpenAI key (`sk-...`) requires:
  - `OPENAI_BASE_URL=https://api.openai.com/v1`

If key and base URL do not match, model calls fail with `401` authentication errors.
After changing `.env`, restart the stack:

- `npm run stop`
- `npm run start`

### Command Line Example

    docker run -it --rm --name agent -p 8583:8000 mwaeckerlin/langgraph-agent

Browse to http://localhost:8583/ok. Returns `{"status": "ok"}` when healthy.

### Adding Graphs

Place `.py` files in `GRAPHS_DIR` (default `/app/graphs`). Each module must expose:

 - `graph` — compiled LangGraph `StateGraph`
 - `name` — unique graph identifier (str)
 - `description` — human-readable description (str)

Example: see [`graphs/echo.py`](graphs/echo.py).

## Minimal Setup: n8n Tests LangGraph

This repository contains a minimal local stack (`db`, `n8n`, `langgraph-agent`) and an importable n8n workflow template.

Start it with:

- `npm run start`

1. Open n8n:
   - `http://localhost:5678`
2. Import workflow:
   - `...` menu (top right) → `Import from file…` → select `n8n-sample-workflow.json`
3. Open workflow `LangGraph Agent Gateway` and click `Publish`.
4. The published workflow exposes three endpoints:
   - `POST /webhook/langgraph/create-thread`
   - `POST /webhook/langgraph/run`
   - `POST /webhook/langgraph/thread-run`
5. Execution mode:
   - Use `/webhook/...` endpoints for published operation.
   - `/webhook-test/...` endpoints are for editor test mode only.

### End-to-End Agent Calls Through n8n

1. Create thread:
   - `curl -i -X POST http://localhost:5678/webhook/langgraph/create-thread`
2. Stateless run:
   - `curl -i -X POST http://localhost:5678/webhook/langgraph/run -H 'Content-Type: application/json' -d '{"graph_name":"echo","input":{"message":"hello stateless"},"config":{}}'`
3. Threaded run:
   - `curl -i -X POST http://localhost:5678/webhook/langgraph/thread-run -H 'Content-Type: application/json' -d '{"thread_id":"<THREAD_ID>","graph_name":"echo","input":{"message":"hello thread"},"config":{}}'`
4. Optional host checks:
   - `curl -i http://localhost:8583/ok`
   - `curl -i -H 'Authorization: Bearer local_langgraph_api_key' http://localhost:8583/graphs`

LLM auth note:
- If `OPENAI_API_KEY` is missing, `echo` falls back to local response mode and returns `"[local-echo] <message>"`.
- For real model output, set a valid `OPENAI_API_KEY` for the configured `OPENAI_BASE_URL`.
----

[LangGraph]: https://github.com/langchain-ai/langgraph "LangGraph on GitHub"
[LiteLLM]: https://github.com/BerriAI/litellm "LiteLLM on GitHub"
[mwaeckerlin/langgraph-agent]: https://hub.docker.com/r/mwaeckerlin/langgraph-agent "get the image from docker hub"
[mwaeckerlin/python]: https://hub.docker.com/r/mwaeckerlin/python "minimalistic Python runtime image"
[mwaeckerlin/python-build]: https://hub.docker.com/r/mwaeckerlin/python-build "Python build image"
