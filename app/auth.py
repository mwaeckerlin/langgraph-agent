from pathlib import Path
from fastapi import HTTPException, status


def _read_secret(name: str) -> str:
    path = Path(f"/run/secrets/{name}")
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Secret '{name}' not found at {path}",
        )
    return path.read_text().strip()


def get_api_key() -> str:
    return _read_secret("langgraph_api_key")
