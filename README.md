# mcp-mediastack

An [MCP](https://modelcontextprotocol.io/) server that provides 45 tools for monitoring and managing a Docker-based media stack. Built with [FastMCP](https://github.com/jlowin/fastmcp) and [httpx](https://www.python-httpx.org/).

## Supported Services

- **Sonarr** - TV series management
- **Radarr** - Movie management
- **SABnzbd** - Usenet downloader
- **qBittorrent** - Torrent client
- **Prowlarr** - Indexer management
- **Readarr** - Book management
- **Bazarr** - Subtitle management
- **Seerr** - Media requests
- **Gluetun** - VPN status monitoring

## Quick Start

### Docker Run

```bash
docker run -d \
  --name mediastack-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  -e NAS_HOST=192.168.1.100 \
  -e SONARR_API_KEY=your_key \
  -e RADARR_API_KEY=your_key \
  -e SABNZBD_API_KEY=your_key \
  ghcr.io/aderaaij/mcp-mediastack:latest
```

### Docker Compose

```yaml
services:
  mediastack-mcp:
    image: ghcr.io/aderaaij/mcp-mediastack:latest
    container_name: mediastack-mcp
    restart: unless-stopped
    ports:
      - 8888:8888
    environment:
      - MCP_TRANSPORT=sse
      - MCP_PORT=8888
      - NAS_HOST=192.168.1.100
      - SONARR_API_KEY=${SONARR_API_KEY}
      - RADARR_API_KEY=${RADARR_API_KEY}
      - SABNZBD_API_KEY=${SABNZBD_API_KEY}
      - PROWLARR_API_KEY=${PROWLARR_API_KEY}
      - READARR_API_KEY=${READARR_API_KEY}
      - BAZARR_API_KEY=${BAZARR_API_KEY}
      - SEERR_API_KEY=${SEERR_API_KEY}
      - QBITTORRENT_USERNAME=${QBITTORRENT_USERNAME}
      - QBITTORRENT_PASSWORD=${QBITTORRENT_PASSWORD}
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `sse` |
| `MCP_PORT` | `8888` | Port for SSE transport |
| `NAS_HOST` | `192.168.1.100` | IP/hostname of your server running the media stack |
| `SONARR_API_KEY` | | Sonarr API key (Settings > General) |
| `SONARR_PORT` | `8989` | Sonarr port |
| `RADARR_API_KEY` | | Radarr API key |
| `RADARR_PORT` | `7878` | Radarr port |
| `SABNZBD_API_KEY` | | SABnzbd API key |
| `SABNZBD_PORT` | `8080` | SABnzbd port |
| `QBITTORRENT_USERNAME` | `admin` | qBittorrent username |
| `QBITTORRENT_PASSWORD` | `adminadmin` | qBittorrent password |
| `QBITTORRENT_PORT` | `8090` | qBittorrent port |
| `PROWLARR_API_KEY` | | Prowlarr API key |
| `PROWLARR_PORT` | `9696` | Prowlarr port |
| `READARR_API_KEY` | | Readarr API key |
| `READARR_PORT` | `8787` | Readarr port |
| `BAZARR_API_KEY` | | Bazarr API key |
| `BAZARR_PORT` | `6767` | Bazarr port |
| `SEERR_API_KEY` | | Seerr API key |
| `SEERR_PORT` | `5055` | Seerr port |
| `GLUETUN_PORT` | `8005` | Gluetun control API port |

## Tools

### Monitoring (28 tools)

| Tool | Description |
|---|---|
| `get_system_overview` | Combined status of all services |
| `get_vpn_status` | Current VPN connection info via Gluetun |
| `check_vpn_health` | Verify VPN is working (IP leak check) |
| `get_sonarr_status` | Sonarr system status |
| `get_sonarr_queue` | Active download queue |
| `get_sonarr_calendar` | Upcoming episodes |
| `get_sonarr_activity` | Recent download history |
| `get_sonarr_missing` | Missing episodes |
| `search_sonarr_series` | Search existing library |
| `get_sonarr_library_stats` | Library statistics |
| `get_radarr_status` | Radarr system status |
| `get_radarr_queue` | Active download queue |
| `get_radarr_calendar` | Upcoming movies |
| `get_radarr_activity` | Recent download history |
| `get_radarr_missing` | Missing movies |
| `search_radarr_movies` | Search existing library |
| `get_radarr_library_stats` | Library statistics |
| `get_sabnzbd_status` | SABnzbd queue and status |
| `get_sabnzbd_history` | Download history |
| `get_qbittorrent_status` | qBittorrent transfer info |
| `get_qbittorrent_torrents` | List torrents with filters |
| `get_prowlarr_status` | Indexer status and stats |
| `get_readarr_status` | Readarr system status |
| `get_readarr_queue` | Readarr download queue |
| `get_bazarr_status` | Bazarr system status |
| `get_bazarr_wanted` | Missing subtitles |
| `get_seerr_status` | Pending requests and stats |

### Actions (17 tools)

| Tool | Description |
|---|---|
| `lookup_sonarr_series` | Search for new series to add |
| `add_sonarr_series` | Add series by TVDB ID |
| `sonarr_search_missing` | Trigger search for missing episodes |
| `sonarr_remove_from_queue` | Remove stuck queue items |
| `lookup_radarr_movies` | Search for new movies to add |
| `add_radarr_movie` | Add movie by TMDB ID |
| `radarr_search_missing` | Trigger search for missing movies |
| `radarr_remove_from_queue` | Remove stuck queue items |
| `send_arr_command` | Send a command to Sonarr/Radarr/Readarr (e.g. RefreshSeries, CheckHealth) |
| `sabnzbd_pause_resume` | Pause or resume SABnzbd |
| `sabnzbd_delete_job` | Delete a download job |
| `sabnzbd_retry_failed` | Retry a failed download |
| `qbittorrent_pause_torrents` | Pause torrents |
| `qbittorrent_resume_torrents` | Resume torrents |
| `qbittorrent_delete_torrents` | Delete torrents |
| `seerr_approve_request` | Approve a media request |
| `seerr_decline_request` | Decline a media request |

## Claude Desktop Integration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

### Direct (stdio, same machine)

```json
{
  "mcpServers": {
    "mediastack": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "NAS_HOST=192.168.1.100",
        "-e", "SONARR_API_KEY=your_key",
        "ghcr.io/aderaaij/mcp-mediastack:latest"
      ]
    }
  }
}
```

### Remote (SSE via mcp-remote)

If the server is running on a remote host with SSE transport:

```json
{
  "mcpServers": {
    "mediastack": {
      "command": "npx",
      "args": ["mcp-remote", "http://your-server:8888/sse"]
    }
  }
}
```

## Known Quirks

- **httpx params**: Never pass `params={}` (empty dict) to httpx — it strips query parameters from the URL. Only pass `params` when non-empty.
- **Seerr titles**: Seerr requests don't include titles directly. The server resolves them via TMDB lookups using the media's TMDB ID.
- **qBittorrent auth**: Uses session-based cookie auth, not API keys. The server handles login automatically.

## Development

```bash
# Install dependencies
uv sync

# Run locally (stdio mode)
python -m mcp_mediastack

# Run locally (SSE mode)
MCP_TRANSPORT=sse python -m mcp_mediastack
```

## License

MIT
