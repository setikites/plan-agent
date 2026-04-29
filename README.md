# Anaplan MCP Server
Python MCP server for Anaplan APIs 

## Description
Demonstrate resources, tempates, and tools for AI agents working with Anaplan.  This code uses OAuth authentication and the anaplan-sdk Python library.

## Deployment
Using uv with the pyproject.toml, setup your directory with the required python libraries.

Create a .env file or set environment variables with OAuth parameters needed to login.

```
uv run python login.py
```
```
uv run python main.py
```

[Sample session with Claude Code](session_2026-04-28.md)

## Testing
```
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "manual-test", "version": "1.0.0"}}}
```
```
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
```
```
{"jsonrpc": "2.0", "id": 3, "method": "resources/list"}
```
```
{"jsonrpc": "2.0", "id": 4, "method": "resources/templates/list", "params": {"cursor": null}}
```
```
{"jsonrpc": "2.0", "id": 5, "method": "resources/read", "params": {"uri": "anaplan://me"}}
```
```
{"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "your_tool_name", "arguments": {"arg1": "value1"}}}
```