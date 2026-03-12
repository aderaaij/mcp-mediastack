# Contributing

## Adding a new tool to an existing service

1. Open the relevant file in `mcp_mediastack/tools/` (e.g. `sonarr.py`)
2. Add your tool function with the `@mcp.tool()` decorator:

```python
@mcp.tool()
async def get_sonarr_tags() -> str:
    """Get all tags configured in Sonarr."""
    data = await _arr_get("sonarr", "/tag")
    return _fmt(data)
```

3. That's it — the tool will be registered automatically on next startup.

## Adding a new service

### 1. Add configuration to `server.py`

If the service uses an API key, add it to the `SERVICES` dict or as standalone variables:

```python
# In SERVICES dict (for *arr-style services):
SERVICES = {
    ...
    "lidarr": {
        "port": int(os.environ.get("LIDARR_PORT", 8686)),
        "api_key": os.environ.get("LIDARR_API_KEY", ""),
    },
}

# Or as standalone variables (for non-arr services):
MYSERVICE_PORT = int(os.environ.get("MYSERVICE_PORT", 9999))
MYSERVICE_API_KEY = os.environ.get("MYSERVICE_API_KEY", "")
```

### 2. Create a tool module

Create `mcp_mediastack/tools/myservice.py`:

```python
"""MyService tools – short description."""

from mcp_mediastack.helpers import _fmt, _get
from mcp_mediastack.server import MYSERVICE_API_KEY, MYSERVICE_PORT, mcp

# For *arr services, use the _arr_* helpers instead:
# from mcp_mediastack.helpers import _arr_get, _fmt
# from mcp_mediastack.server import mcp


@mcp.tool()
async def get_myservice_status() -> str:
    """Get MyService status and health."""
    data = await _get(MYSERVICE_PORT, "/api/status", headers={"X-Api-Key": MYSERVICE_API_KEY})
    return _fmt(data)
```

**Key points:**
- Import `mcp` from `mcp_mediastack.server` and use `@mcp.tool()` to register tools
- Import helpers from `mcp_mediastack.helpers` — use `_arr_get`/`_arr_post` for \*arr services, or `_get`/`_post` for everything else
- Import config (ports, API keys) from `mcp_mediastack.server`
- Return `_fmt(data)` to format responses as JSON strings
- Keep tool docstrings descriptive — they're shown to the LLM

### 3. Register it in `tools/__init__.py`

Add an entry to `_TOOL_MODULES` with the auto-detect condition:

```python
_TOOL_MODULES: dict[str, bool] = {
    ...
    "myservice": bool(MYSERVICE_API_KEY),  # API key services
    # or for services without API keys:
    "myservice": True,  # enabled by default, disable via DISABLED_SERVICES
}
```

Don't forget to import the config variable at the top of `__init__.py`:

```python
from mcp_mediastack.server import ..., MYSERVICE_API_KEY
```

### 4. Update documentation

- Add the service to the **Supported Services** list in `README.md`
- Add environment variables to the **Environment Variables** table
- Add tools to the **Tools** table (Monitoring or Actions section)
- Add the env var to `.env.example`

## Available helpers

| Helper | Use for |
|---|---|
| `_arr_get(service, path)` | GET to an \*arr service (Sonarr, Radarr, etc.) — handles API key and versioned URL |
| `_arr_post(service, path, json_data)` | POST to an \*arr service |
| `_arr_delete(service, path, params)` | DELETE to an \*arr service |
| `_arr_put(service, path, json_data)` | PUT to an \*arr service |
| `_get(port, path, headers, params)` | Raw GET to any service |
| `_post(port, path, headers, json_data)` | Raw POST to any service |
| `_delete(port, path, headers, params)` | Raw DELETE to any service |
| `_put(port, path, headers, json_data)` | Raw PUT to any service |
| `_fmt(data)` | Format response as indented JSON string |
| `_human_bytes(b)` | Format bytes as human-readable (e.g. `1.5 GB`) |
| `_se(season, episode)` | Format as `S01E02` |
| `_url(port, path)` | Build full URL from NAS_HOST + port + path |

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Linting

Ruff handles both linting and formatting. Pre-commit runs it automatically, or manually:

```bash
ruff check mcp_mediastack/        # lint
ruff format mcp_mediastack/       # format
```
