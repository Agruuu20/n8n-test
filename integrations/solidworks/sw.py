#!/usr/bin/env python3
"""Run a guarded sequence of SolidWorks MCP tool calls in ONE server session.

Useful when the MCP server is not attached to the client (e.g. before the
project-scoped `.mcp.json` is approved) and for replayable build scripts.
Stops at the first call whose result is not `status: success`.

    sw.py steps.json                                  # local mock server (stdio)
    sw.py steps.json --url http://127.0.0.1:8765/mcp --token $TOKEN   # HTTP bridge
    sw.py --list                                      # list tools + argument names

steps.json is a list of {"tool": "<name>", "args": {...}} objects. Arguments are
wrapped in `input_data` automatically for tools that expect it.
Needs `fastmcp` (the vendored venv has it: .vendor/SolidworksMCP-python/.venv/bin/python).
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport

HERE = Path(__file__).resolve().parent


def transport(args):
    if args.url:
        headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
        return StreamableHttpTransport(args.url, headers=headers)
    return StdioTransport(command="bash", args=[str(HERE / "run-mock.sh")])


async def run(args):
    async with Client(transport(args), timeout=300) as c:
        tools = {t.name: t for t in await c.list_tools()}
        if args.list:
            for t in tools.values():
                props = (t.inputSchema or {}).get("properties", {})
                print(f"{t.name:40s} {'input_data{...}' if 'input_data' in props else '(no args)'}")
            return 0
        steps = json.loads(Path(args.steps).read_text())
        for i, step in enumerate(steps, 1):
            name, a = step["tool"], step.get("args", {})
            if name not in tools:
                print(f"[{i}] {name}: UNKNOWN TOOL"); return 2
            wrap = "input_data" in (tools[name].inputSchema or {}).get("properties", {})
            try:
                res = await c.call_tool(name, {"input_data": a} if wrap else a)
                data = res.data if res.data is not None else res.content[0].text
            except Exception as e:  # validation errors etc.
                print(f"[{i}] {name}: ERROR {str(e)[:300]}"); return 1
            ok = not isinstance(data, dict) or data.get("status") == "success"
            print(f"[{i}] {name}: {'ok' if ok else 'FAILED'} - {(data.get('message') if isinstance(data, dict) else data)}")
            if args.verbose:
                print("     " + json.dumps(data, default=str)[:600])
            if not ok:
                return 1
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("steps", nargs="?")
    p.add_argument("--url"); p.add_argument("--token")
    p.add_argument("--list", action="store_true"); p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args()
    if not a.steps and not a.list:
        p.error("steps file or --list required")
    sys.exit(asyncio.run(run(a)))
