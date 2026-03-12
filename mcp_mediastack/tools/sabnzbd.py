"""SABnzbd tools – Usenet download management."""

from mcp_mediastack.helpers import _fmt, _get
from mcp_mediastack.server import SABNZBD_API_KEY, SABNZBD_PORT, mcp

# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_sabnzbd_status() -> str:
    """Get SABnzbd status – speed, queue size, disk space, paused state."""
    data = await _get(SABNZBD_PORT, "/api", params={"apikey": SABNZBD_API_KEY, "output": "json", "mode": "queue"})
    q = data.get("queue", {}) if isinstance(data, dict) else {}
    return _fmt(
        {
            "status": q.get("status"),
            "speed": q.get("speed"),
            "size": q.get("size"),
            "sizeLeft": q.get("sizeleft"),
            "timeLeft": q.get("timeleft"),
            "diskspace1": q.get("diskspace1"),
            "diskspace2": q.get("diskspace2"),
            "paused": q.get("paused"),
            "noofslots": q.get("noofslots"),
            "slots": [
                {
                    "nzo_id": s.get("nzo_id"),
                    "filename": s.get("filename"),
                    "size": s.get("size"),
                    "sizeleft": s.get("sizeleft"),
                    "status": s.get("status"),
                    "percentage": s.get("percentage"),
                    "timeleft": s.get("timeleft"),
                }
                for s in q.get("slots", [])[:20]
            ],
        }
    )


@mcp.tool()
async def get_sabnzbd_history(limit: int = 20) -> str:
    """Get SABnzbd download history."""
    data = await _get(
        SABNZBD_PORT,
        "/api",
        params={"apikey": SABNZBD_API_KEY, "output": "json", "mode": "history", "limit": str(limit)},
    )
    h = data.get("history", {}) if isinstance(data, dict) else {}
    slots = []
    for s in h.get("slots", [])[:limit]:
        slots.append(
            {
                "nzo_id": s.get("nzo_id"),
                "name": s.get("name"),
                "size": s.get("size"),
                "status": s.get("status"),
                "completed": s.get("completed"),
                "category": s.get("category"),
            }
        )
    return _fmt({"totalSize": h.get("total_size"), "items": slots})


# ---------------------------------------------------------------------------
# Action tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def sabnzbd_pause_resume(action: str = "pause") -> str:
    """Pause or resume the SABnzbd download queue. Action: 'pause' or 'resume'."""
    mode = "pause" if action == "pause" else "resume"
    data = await _get(SABNZBD_PORT, "/api", params={"apikey": SABNZBD_API_KEY, "output": "json", "mode": mode})
    return _fmt({"action": mode, "result": data})


@mcp.tool()
async def sabnzbd_delete_job(nzo_id: str) -> str:
    """Delete a job from SABnzbd queue by its nzo_id. Get IDs from get_sabnzbd_status."""
    data = await _get(
        SABNZBD_PORT,
        "/api",
        params={"apikey": SABNZBD_API_KEY, "output": "json", "mode": "queue", "name": "delete", "value": nzo_id},
    )
    return _fmt({"deleted": nzo_id, "result": data})


@mcp.tool()
async def sabnzbd_retry_failed(nzo_id: str) -> str:
    """Retry a failed SABnzbd download by its nzo_id. Get IDs from get_sabnzbd_history."""
    data = await _get(
        SABNZBD_PORT, "/api", params={"apikey": SABNZBD_API_KEY, "output": "json", "mode": "retry", "value": nzo_id}
    )
    return _fmt({"retried": nzo_id, "result": data})
