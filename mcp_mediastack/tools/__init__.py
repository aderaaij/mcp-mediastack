"""Import tool modules based on which services are configured."""

import importlib
import logging
import os

from mcp_mediastack.server import SABNZBD_API_KEY, SEERR_API_KEY, SERVICES

logger = logging.getLogger(__name__)

# All available tool modules and how to detect if they're configured.
# Services with API keys: enabled when key is non-empty.
# qBittorrent/VPN: enabled by default (no API key required), disable explicitly.
_TOOL_MODULES: dict[str, bool] = {
    "sonarr": bool(SERVICES["sonarr"]["api_key"]),
    "radarr": bool(SERVICES["radarr"]["api_key"]),
    "readarr": bool(SERVICES["readarr"]["api_key"]),
    "prowlarr": bool(SERVICES["prowlarr"]["api_key"]),
    "bazarr": bool(SERVICES["bazarr"]["api_key"]),
    "sabnzbd": bool(SABNZBD_API_KEY),
    "seerr": bool(SEERR_API_KEY),
    "qbittorrent": True,
    "vpn": True,
    # Cross-service tools, always loaded
    "arr_command": True,
    "overview": True,
}

# Allow explicit override: ENABLED_SERVICES=sonarr,radarr or DISABLED_SERVICES=vpn,qbittorrent
_enabled_override = os.environ.get("ENABLED_SERVICES", "").strip()
_disabled_override = os.environ.get("DISABLED_SERVICES", "").strip()

if _enabled_override:
    # Only load explicitly listed services (plus always-on tools)
    _always_on = {"arr_command", "overview"}
    _enabled_set = {s.strip() for s in _enabled_override.split(",")} | _always_on
    _TOOL_MODULES = {k: k in _enabled_set for k in _TOOL_MODULES}

if _disabled_override:
    # Disable explicitly listed services
    _disabled_set = {s.strip() for s in _disabled_override.split(",")}
    for name in _disabled_set:
        if name in _TOOL_MODULES:
            _TOOL_MODULES[name] = False

_loaded = []
_skipped = []

for module_name, enabled in _TOOL_MODULES.items():
    if enabled:
        importlib.import_module(f"mcp_mediastack.tools.{module_name}")
        _loaded.append(module_name)
    else:
        _skipped.append(module_name)

if _skipped:
    logger.info("Skipped tools (not configured): %s", ", ".join(_skipped))
if _loaded:
    logger.info("Loaded tools: %s", ", ".join(_loaded))
