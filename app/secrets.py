import os
from pathlib import Path


def read_secret(name: str, env_fallback: str | None = None) -> str:
    """Read a Docker secret from /run/secrets/<name>, fall back to env var."""
    path = Path(f"/run/secrets/{name}")
    if path.exists():
        return path.read_text().strip()
    var = env_fallback or name.upper()
    value = os.environ.get(var, "")
    if not value:
        raise RuntimeError(f"Secret '{name}' not found at {path} and env '{var}' is empty")
    return value
