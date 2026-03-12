"""MCP server for monitoring a Synology NAS media stack."""

import os
from typing import Literal

from mcp.server.fastmcp import FastMCP

TransportType = Literal["stdio", "sse", "streamable-http"]
TRANSPORT: TransportType = os.environ.get("MCP_TRANSPORT", "stdio")  # type: ignore[assignment]
MCP_PORT = int(os.environ.get("MCP_PORT", 8888))

mcp = FastMCP("mediastack", host="0.0.0.0", port=MCP_PORT)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NAS_HOST = os.environ.get("NAS_HOST", "192.168.1.100")

SERVICES = {
    "sonarr": {
        "port": int(os.environ.get("SONARR_PORT", 8989)),
        "api_key": os.environ.get("SONARR_API_KEY", ""),
    },
    "radarr": {
        "port": int(os.environ.get("RADARR_PORT", 7878)),
        "api_key": os.environ.get("RADARR_API_KEY", ""),
    },
    "prowlarr": {
        "port": int(os.environ.get("PROWLARR_PORT", 9696)),
        "api_key": os.environ.get("PROWLARR_API_KEY", ""),
        "api_version": "v1",
    },
    "readarr": {
        "port": int(os.environ.get("READARR_PORT", 8787)),
        "api_key": os.environ.get("READARR_API_KEY", ""),
        "api_version": "v1",
    },
    "bazarr": {
        "port": int(os.environ.get("BAZARR_PORT", 6767)),
        "api_key": os.environ.get("BAZARR_API_KEY", ""),
    },
}

SABNZBD_PORT = int(os.environ.get("SABNZBD_PORT", 8080))
SABNZBD_API_KEY = os.environ.get("SABNZBD_API_KEY", "")

QBITTORRENT_PORT = int(os.environ.get("QBITTORRENT_PORT", 8090))
QBITTORRENT_USER = os.environ.get("QBITTORRENT_USERNAME", "admin")
QBITTORRENT_PASS = os.environ.get("QBITTORRENT_PASSWORD", "adminadmin")

SEERR_PORT = int(os.environ.get("SEERR_PORT", 5055))
SEERR_API_KEY = os.environ.get("SEERR_API_KEY", "")

GLUETUN_PORT = int(os.environ.get("GLUETUN_PORT", 8005))

TIMEOUT = 10.0


def main():
    import mcp_mediastack.tools  # noqa: F401 – triggers @mcp.tool() registration

    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()
