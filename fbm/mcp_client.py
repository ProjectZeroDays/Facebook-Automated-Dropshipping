"""mcp_client.py — MCP client integration."""
from __future__ import annotations
import json, os
from pathlib import Path
import fbm_core as C

CONFIG = Path("mcp_servers.json")
DEFAULTS = {
    "filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]},
    "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
    "sqlite": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-sqlite", "fbm.sqlite"]},
    "fetch": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-fetch"]},
}

class MCPClient:
    def __init__(self):
        self.servers = {}
        self.tools = {}
        self._load_config()

    def _load_config(self):
        cfg = {}
        if CONFIG.exists():
            try:
                cfg = json.loads(CONFIG.read_text())
            except Exception:
                cfg = {}
        for name, spec in {**DEFAULTS, **cfg}.items():
            self.servers[name] = spec

    def list_servers(self):
        return list(self.servers.keys())

    def list_tools(self, server=None):
        if server:
            return self.tools.get(server, [])
        return {s: self.tools.get(s, []) for s in self.servers}

    def call_tool(self, server, tool, args=None):
        args = args or {}
        return {"server": server, "tool": tool, "args": args, "result": None, "status": "not_connected"}

    def connect(self, server):
        if server not in self.servers:
            return False
        self.tools[server] = []
        return True

    def connect_all(self):
        for s in self.servers:
            self.connect(s)
        return self.servers

_client = None

def get_client():
    global _client
    if _client is None:
        _client = MCPClient()
    return _client

def main():
    C.load_env()
    c = get_client()
    c.connect_all()
    print("MCP servers:", c.list_servers())
    print("mcp_client ok")

if __name__ == "__main__":
    main()
