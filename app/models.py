from typing import Any

from pydantic import BaseModel


class RunRequest(BaseModel):
    graph_name: str
    input: dict[str, Any]
    config: dict[str, Any] = {}


class RunResponse(BaseModel):
    output: dict[str, Any]


class ThreadResponse(BaseModel):
    thread_id: str


class GraphInfo(BaseModel):
    name: str
    description: str


class HealthResponse(BaseModel):
    status: str
