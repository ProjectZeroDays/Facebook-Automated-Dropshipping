"""mcp_integration.py — wire MCP client into the chatbot and action system.

Registers MCP tools as callable actions and provides a bridge so the LLM
assistant can invoke MCP server capabilities (filesystem, github, sqlite, fetch).
"""
from __future__ import annotations
import json
from typing import Any
import fbm_core as C
import fbm.mcp_client as MCP
import actions as A

_mcp_client = None

def _client():
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCP.get_client()
        _mcp_client.connect_all()
    return _mcp_client

def list_mcp_tools() -> dict[str, list[str]]:
    """Return all MCP server -> tools mappings."""
    c = _client()
    return c.list_tools()

def call_mcp_tool(server: str, tool: str, args: dict | None = None) -> dict:
    """Call an MCP tool and return a structured result."""
    c = _client()
    return c.call_tool(server, tool, args or {})

def register_mcp_actions() -> int:
    """Register every discovered MCP tool as an action in the action registry."""
    count = 0
    tools = list_mcp_tools()
    for server, tool_list in tools.items():
        for tool in tool_list:
            name = f"mcp_{server}_{tool}"
            def make_fn(s=server, t=tool):
                def fn(**kwargs):
                    return call_mcp_tool(s, t, kwargs)
                return fn
            A.register(name, make_fn(), patterns=[name])
            count += 1
    return count

def mcp_context_for_prompt() -> str:
    """Build a context string describing available MCP capabilities for the LLM."""
    tools = list_mcp_tools()
    lines = ["## MCP Tools Available", ""]
    for server, tool_list in tools.items():
        lines.append(f"### {server}")
        for t in tool_list:
            lines.append(f"- `mcp_{server}_{t}`: call the `{t}` tool on the `{server}` MCP server")
        lines.append("")
    return "\n".join(lines)

def main():
    C.load_env()
    n = register_mcp_actions()
    print(f"Registered {n} MCP actions")
    print(mcp_context_for_prompt())
    print("mcp_integration ok")

if __name__ == "__main__":
    main()
