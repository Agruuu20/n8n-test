#!/usr/bin/env python3
"""HTTP bridge for SolidworksMCP-python, with bearer-token auth.

Why this exists: upstream's documented remote mode
(`python -m solidworks_mcp.server --mode remote`) crashes at startup with
"Already running asyncio in this thread" because it calls the synchronous
`FastMCP.run()` from inside a running event loop. This script starts the same
server through `run_http_async` instead, and refuses every request that lacks
the bearer token (upstream's HTTP mode has no transport-level auth, and this
server can open/overwrite files and run VBA on the host).

Run it with the Python that has solidworks_mcp installed (on Windows, for real
SolidWorks: `.venv\\Scripts\\python.exe`), with SolidWorks already open:

    python http_bridge.py --real --year 2026 --port 8765

Then point an MCP client at http://127.0.0.1:8765/mcp with the header
`Authorization: Bearer <token>`. Keep the bind on 127.0.0.1 and reach it
through an SSH tunnel / private VPN; do not expose it on the open internet.
"""

from __future__ import annotations

import argparse
import asyncio
import hmac
import os
import secrets
import sys

from solidworks_mcp.config import (
    AdapterType,
    DeploymentMode,
    SecurityLevel,
    SolidWorksMCPConfig,
)
from solidworks_mcp.server import SolidWorksMCPServer
from starlette.middleware import Middleware


class BearerAuth:
    """Pure-ASGI middleware: 401 unless `Authorization: Bearer <token>` matches."""

    def __init__(self, app, token: str) -> None:
        self.app = app
        self._expected = f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            supplied = dict(scope["headers"]).get(b"authorization", b"")
            if not hmac.compare_digest(supplied, self._expected):
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [(b"content-type", b"text/plain")],
                    }
                )
                await send({"type": "http.response.body", "body": b"unauthorized"})
                return
        await self.app(scope, receive, send)


def build_config(args: argparse.Namespace) -> SolidWorksMCPConfig:
    mock = not args.real
    return SolidWorksMCPConfig(
        deployment_mode=DeploymentMode.REMOTE,
        security_level=SecurityLevel.MINIMAL,
        adapter_type=AdapterType.MOCK if mock else AdapterType.PYWIN32,
        mock_solidworks=mock,
        solidworks_path="mock://solidworks" if mock else "",
        solidworks_year=args.year,
        log_level=args.log_level,
        host=args.host,
        port=args.port,
        circuit_breaker_enabled=True,
    )


async def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--real", action="store_true", help="real COM adapter (Windows + SolidWorks open); default is mock")
    p.add_argument("--year", type=int, default=None, help="SolidWorks year hint, e.g. 2026")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--allowed-host", action="append", default=[], help="extra Host header value to accept (e.g. a tunnel hostname)")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = p.parse_args()

    token = os.environ.get("SOLIDWORKS_MCP_BRIDGE_TOKEN") or secrets.token_urlsafe(32)
    if "SOLIDWORKS_MCP_BRIDGE_TOKEN" not in os.environ:
        print(f"[bridge] generated token (set SOLIDWORKS_MCP_BRIDGE_TOKEN to pin it): {token}", file=sys.stderr)

    server = SolidWorksMCPServer(build_config(args))
    await server.setup()
    await server.adapter.connect()  # real mode: attaches to the running SLDWORKS.exe
    print(f"[bridge] {'REAL' if args.real else 'MOCK'} adapter, {server.state.tool_count} tools, listening on http://{args.host}:{args.port}/mcp", file=sys.stderr)
    try:
        await server.mcp.run_http_async(
            transport="http",
            host=args.host,
            port=args.port,
            show_banner=False,
            middleware=[Middleware(BearerAuth, token=token)],
            allowed_hosts=args.allowed_host or None,
        )
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
