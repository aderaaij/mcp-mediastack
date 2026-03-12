"""VPN / Gluetun tools."""

import httpx

from mcp_mediastack.helpers import _fmt, _get, _url
from mcp_mediastack.server import (
    GLUETUN_PORT,
    QBITTORRENT_PASS,
    QBITTORRENT_PORT,
    QBITTORRENT_USER,
    SABNZBD_API_KEY,
    SABNZBD_PORT,
    TIMEOUT,
    mcp,
)


@mcp.tool()
async def get_vpn_status() -> str:
    """Get VPN connection status from Gluetun – public IP, forwarded port, and connection details."""
    results = {}
    for endpoint in ["/v1/publicip/ip", "/v1/openvpn/status"]:
        try:
            results[endpoint] = await _get(GLUETUN_PORT, endpoint)
        except Exception as e:
            results[endpoint] = f"error: {e}"
    return _fmt(results)


@mcp.tool()
async def check_vpn_health() -> str:
    """Comprehensive VPN health check – verifies Gluetun is healthy, VPN IP is active, and that SABnzbd and qBittorrent are reachable through the VPN tunnel."""
    health = {"gluetun": {}, "sabnzbd": {}, "qbittorrent": {}, "overall": "healthy"}

    # Check Gluetun API and VPN IP
    try:
        ip_data = await _get(GLUETUN_PORT, "/v1/publicip/ip")
        health["gluetun"]["vpn_ip"] = ip_data
        health["gluetun"]["status"] = "connected"
    except Exception as e:
        health["gluetun"]["status"] = "unreachable"
        health["gluetun"]["error"] = str(e)
        health["overall"] = "unhealthy"

    try:
        status_data = await _get(GLUETUN_PORT, "/v1/openvpn/status")
        # Note: /v1/openvpn/status reports "stopped" when using WireGuard – this is
        # expected and not an error. The VPN IP check above is the reliable indicator.
        health["gluetun"]["tunnel_status"] = status_data
        if isinstance(status_data, dict) and status_data.get("status") == "stopped":
            health["gluetun"]["tunnel_note"] = (
                "Reports 'stopped' because WireGuard is in use (not OpenVPN) – this is normal"
            )
    except Exception:
        pass

    # Check SABnzbd reachability (routed through Gluetun)
    try:
        data = await _get(SABNZBD_PORT, "/api", params={"apikey": SABNZBD_API_KEY, "output": "json", "mode": "version"})
        health["sabnzbd"]["status"] = "reachable"
        health["sabnzbd"]["version"] = data
    except Exception as e:
        health["sabnzbd"]["status"] = "unreachable"
        health["sabnzbd"]["error"] = str(e)
        health["overall"] = "unhealthy"

    # Check qBittorrent reachability (routed through Gluetun)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                _url(QBITTORRENT_PORT, "/api/v2/auth/login"),
                data={"username": QBITTORRENT_USER, "password": QBITTORRENT_PASS},
            )
            if resp.status_code == 200:
                health["qbittorrent"]["status"] = "reachable"
            else:
                health["qbittorrent"]["status"] = "auth_failed"
                health["overall"] = "degraded"
    except Exception as e:
        health["qbittorrent"]["status"] = "unreachable"
        health["qbittorrent"]["error"] = str(e)
        health["overall"] = "unhealthy"

    # Summary
    if health["overall"] == "unhealthy":
        health["recommendation"] = (
            "Gluetun or dependent services are down. Try: docker-compose restart gluetun && docker restart qbittorrent sabnzbd"
        )
    elif health["overall"] == "degraded":
        health["recommendation"] = "Some services have issues. Check individual service errors above."

    return _fmt(health)
