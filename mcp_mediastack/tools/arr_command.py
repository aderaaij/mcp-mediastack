"""Generic command tool for Sonarr, Radarr, and Readarr."""

from typing import Literal

from mcp_mediastack.helpers import _arr_post, _fmt
from mcp_mediastack.server import mcp


@mcp.tool()
async def send_arr_command(
    app: Literal["sonarr", "radarr", "readarr"],
    command_name: str,
    command_args: dict | None = None,
) -> str:
    """Send a command to Sonarr, Radarr, or Readarr via their /command endpoint.

    Common commands:
      - Sonarr: RefreshSeries, RescanSeries, SeriesSearch, MissingEpisodeSearch, CheckHealth,
                RssSync, RenameFiles, Backup
      - Radarr: RefreshMovie, RescanMovie, MoviesSearch, MissingMoviesSearch, CheckHealth,
                RssSync, RenameFiles, Backup
      - Readarr: RefreshAuthor, RescanFolders, MissingBookSearch, CheckHealth, RssSync, Backup

    Some commands accept extra args, e.g. {"seriesId": 123} for RefreshSeries
    or {"movieIds": [1, 2]} for MoviesSearch.
    """
    body = {"name": command_name, **(command_args or {})}
    result = await _arr_post(app, "/command", json_data=body)
    return _fmt(result)
