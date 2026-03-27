import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, status
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.auth import get_api_key
from app.graph_loader import get_graph_info, get_graphs, load_graphs
from app.models import (
    GraphInfo,
    HealthResponse,
    RunRequest,
    RunResponse,
    ThreadResponse,
)

_checkpointer: AsyncPostgresSaver | None = None
_pool: AsyncConnectionPool | None = None


def _read_secret(name: str, env_var: str | None = None) -> str:
    path = Path(f"/run/secrets/{name}")
    if path.exists():
        return path.read_text().strip()
    return os.environ.get(env_var or name.upper(), "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _checkpointer, _pool

    db_uri = os.environ.get("DATABASE_URI", "").strip()
    if not db_uri:
        db_password = _read_secret("langgraph_db_password")
        if db_password:
            db_uri = f"postgresql://langgraph:{db_password}@db:5432/langgraph"
    if not db_uri:
        raise RuntimeError(
            "DATABASE_URI is required (or provide secret langgraph_db_password)"
        )

    _pool = AsyncConnectionPool(
        conninfo=db_uri,
        open=False,
        kwargs={"autocommit": True},
    )
    await _pool.open()
    _checkpointer = AsyncPostgresSaver(_pool)
    await _checkpointer.setup()

    openai_key = _read_secret("litellm_master_key")
    if openai_key:
        os.environ.setdefault("OPENAI_API_KEY", openai_key)

    graphs_dir = os.environ.get("GRAPHS_DIR", "/app/graphs")
    load_graphs(graphs_dir)

    yield

    if _pool is not None:
        await _pool.close()


app = FastAPI(lifespan=lifespan)


def _verify_token(authorization: str | None = Header(default=None)) -> None:
    api_key = get_api_key()
    if not api_key:
        return
    if authorization != f"Bearer {api_key}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )


@app.get("/ok", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get(
    "/graphs",
    response_model=list[GraphInfo],
    dependencies=[Depends(_verify_token)],
)
async def list_graphs() -> list[GraphInfo]:
    return [GraphInfo(**info) for info in get_graph_info()]


@app.post(
    "/runs",
    response_model=RunResponse,
    dependencies=[Depends(_verify_token)],
)
async def stateless_run(request: RunRequest) -> RunResponse:
    graphs = get_graphs()
    if request.graph_name not in graphs:
        raise HTTPException(status_code=404, detail="Graph not found")
    graph = graphs[request.graph_name]
    result = await graph.ainvoke(request.input, config=request.config)
    return RunResponse(output=result)


@app.post(
    "/threads",
    response_model=ThreadResponse,
    dependencies=[Depends(_verify_token)],
)
async def create_thread() -> ThreadResponse:
    return ThreadResponse(thread_id=str(uuid.uuid4()))


@app.post(
    "/threads/{thread_id}/runs",
    response_model=RunResponse,
    dependencies=[Depends(_verify_token)],
)
async def thread_run(thread_id: str, request: RunRequest) -> RunResponse:
    graphs = get_graphs()
    if request.graph_name not in graphs:
        raise HTTPException(status_code=404, detail="Graph not found")
    if _checkpointer is None:
        raise HTTPException(status_code=503, detail="No database configured")
    graph = graphs[request.graph_name]
    config = {
        **request.config,
        "configurable": {
            **request.config.get("configurable", {}),
            "thread_id": thread_id,
        },
    }
    result = await graph.ainvoke(
        request.input,
        config=config,
        checkpointer=_checkpointer,
    )
    return RunResponse(output=result)


@app.get(
    "/threads/{thread_id}/state",
    dependencies=[Depends(_verify_token)],
)
async def get_thread_state(thread_id: str) -> dict:
    if _checkpointer is None:
        raise HTTPException(status_code=503, detail="No database configured")
    config = {"configurable": {"thread_id": thread_id}}
    state = await _checkpointer.aget(config)
    if state is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return state.channel_values if hasattr(state, "channel_values") else {}
