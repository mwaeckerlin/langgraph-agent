import os
from pathlib import Path


def _read_secret(name: str) -> str:
    path = Path(f"/run/secrets/{name}")
    if path.exists():
        return path.read_text().strip()
    return os.environ.get(name.upper().replace("-", "_"), "")


def get_api_key() -> str:
    return _read_secret("langgraph_api_key")
