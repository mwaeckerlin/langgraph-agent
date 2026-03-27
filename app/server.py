import os
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, status
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

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
_db_pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _checkpointer, _db_pool

    db_uri = os.environ.get("DATABASE_URI", "")
    _db_pool = await psycopg.AsyncConnection.connect(db_uri, autocommit=True)
    _checkpointer = AsyncPostgresSaver(_db_pool)
    await _checkpointer.setup()

    graphs_dir = os.environ.get("GRAPHS_DIR", "/app/graphs")
    load_graphs(graphs_dir)

    yield

    if _db_pool is not None:
        await _db_pool.close()


app = FastAPI(lifespan=lifespan)


def _verify_token(authorization: Annotated[str | None, Header()] = None) -> None:
    api_key = get_api_key()
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
        raise HTTPException(status_code=503, detail="Checkpointer not ready")
    config = {"configurable": {"thread_id": thread_id}}
    state = await _checkpointer.aget(config)
    if state is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    return state.channel_values if hasattr(state, "channel_values") else {}
