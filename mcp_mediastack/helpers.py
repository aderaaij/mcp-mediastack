"""Shared HTTP helpers and formatting utilities."""

import json
from typing import Any

import httpx

from mcp_mediastack.server import NAS_HOST, SERVICES, TIMEOUT


def _url(port: int, path: str) -> str:
    return f"http://{NAS_HOST}:{port}{path}"


async def _get(port: int, path: str, headers: dict | None = None, params: dict | None = None) -> dict | list | str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        kwargs: dict[str, Any] = {"headers": headers or {}}
        if params:
            kwargs["params"] = params
        resp = await client.get(_url(port, path), **kwargs)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


async def _post(
    port: int, path: str, headers: dict | None = None, json_data: Any = None, params: dict | None = None
) -> dict | list | str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        kwargs: dict[str, Any] = {"headers": headers or {}}
        if json_data is not None:
            kwargs["json"] = json_data
        if params:
            kwargs["params"] = params
        resp = await client.post(_url(port, path), **kwargs)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


async def _delete(port: int, path: str, headers: dict | None = None, params: dict | None = None) -> dict | list | str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        kwargs: dict[str, Any] = {"headers": headers or {}}
        if params:
            kwargs["params"] = params
        resp = await client.delete(_url(port, path), **kwargs)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


async def _put(port: int, path: str, headers: dict | None = None, json_data: Any = None) -> dict | list | str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.put(_url(port, path), headers=headers or {}, json=json_data)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return resp.text


async def _arr_get(service: str, path: str) -> dict | list | str:
    """GET request to an *arr service (Sonarr, Radarr, etc.)."""
    cfg = SERVICES[service]
    api_ver = cfg.get("api_version", "v3")
    return await _get(cfg["port"], f"/api/{api_ver}{path}", headers={"X-Api-Key": cfg["api_key"]})


async def _arr_post(service: str, path: str, json_data: Any = None) -> dict | list | str:
    """POST request to an *arr service."""
    cfg = SERVICES[service]
    api_ver = cfg.get("api_version", "v3")
    return await _post(cfg["port"], f"/api/{api_ver}{path}", headers={"X-Api-Key": cfg["api_key"]}, json_data=json_data)


async def _arr_delete(service: str, path: str, params: dict | None = None) -> dict | list | str:
    """DELETE request to an *arr service."""
    cfg = SERVICES[service]
    api_ver = cfg.get("api_version", "v3")
    return await _delete(cfg["port"], f"/api/{api_ver}{path}", headers={"X-Api-Key": cfg["api_key"]}, params=params)


async def _arr_put(service: str, path: str, json_data: Any = None) -> dict | list | str:
    """PUT request to an *arr service."""
    cfg = SERVICES[service]
    api_ver = cfg.get("api_version", "v3")
    return await _put(cfg["port"], f"/api/{api_ver}{path}", headers={"X-Api-Key": cfg["api_key"]}, json_data=json_data)


def _fmt(data: Any) -> str:
    """Format data for display."""
    if isinstance(data, dict | list):
        return json.dumps(data, indent=2, default=str)
    return str(data)


def _human_bytes(b: int | float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def _se(season: Any, episode: Any) -> str:
    """Format season/episode as S01E02."""
    try:
        return f"S{int(season):02d}E{int(episode):02d}"
    except (TypeError, ValueError):
        return f"S{season}E{episode}"
