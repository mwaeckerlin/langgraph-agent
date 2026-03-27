import importlib.util
import os
from pathlib import Path
from typing import Any


_graphs: dict[str, Any] = {}
_graph_info: dict[str, dict] = {}


def load_graphs(graphs_dir: str) -> None:
    _graphs.clear()
    _graph_info.clear()
    for path in Path(graphs_dir).glob("*.py"):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        graph = getattr(module, "graph", None)
        if graph is None:
            continue
        name = getattr(module, "name", path.stem)
        description = getattr(module, "description", "")
        _graphs[name] = graph
        _graph_info[name] = {"name": name, "description": description}


def get_graphs() -> dict[str, Any]:
    return _graphs


def get_graph_info() -> list[dict]:
    return list(_graph_info.values())
