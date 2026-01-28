# MCP Remote Connection Guide

This guide explains how to run the MCP server so remote clients can connect, and how to test connectivity from another PC.

## Start MCP server on host PC (Windows)

Bind the server to all interfaces and use port 8000.

```powershell
# EXE variant
mcp_server.exe --host 0.0.0.0 --port 8000

# Python variant (venv)
$env:MCP_HOST = "0.0.0.0"
$env:MCP_PORT = "8000"
& "c:\BoschSoftwareDeveloper\Project_01\BSD_MCP_HSWPr\.venv\Scripts\python.exe" "c:\BoschSoftwareDeveloper\Project_01\BSD_MCP_HSWPr\BoschMCP_HSWPr\server.py"
```

Open Windows Firewall for port 8000 and allow ping.

```powershell
netsh advfirewall firewall add rule name="MCP 8000" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="Allow ICMPv4-In" dir=in action=allow protocol=icmpv4
```

Verify the server is listening.

```powershell
netstat -ano | findstr :8000
# Expect LISTENING on 0.0.0.0:8000
```

Local health checks on the host.

```powershell
Invoke-WebRequest http://127.0.0.1:8000/ -UseBasicParsing
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
```

## Remote client configuration

Use the host PC’s IPv4 address from `ipconfig`.

```json
{
  "servers": {
    "HSWPR_MCP": {
      "url": "http://<host-ip>:8000",
      "type": "http"
    }
  },
  "inputs": []
}
```

## Connectivity test script (remote PC)

Run this script to validate GET /, GET /health, and JSON-RPC calls.

File: `scripts/test_mcp_connection.py`

```python
#!/usr/bin/env python3
"""
Simple MCP server connectivity test.
- Checks HTTP GET / and /health
- Sends a JSON-RPC initialize to POST /
Usage:
  python test_mcp_connection.py http://<host>:<port>
Defaults to http://127.0.0.1:8000 if not provided.
"""
import json
import sys
import urllib.request
import urllib.error
from urllib.parse import urljoin


def http_get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
            return status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return -1, str(e)


def http_post_json(url: str, payload: dict) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
            return status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return -1, str(e)


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    root_url = urljoin(base_url, "/")
    health_url = urljoin(base_url, "/health")

    print(f"Testing MCP server at: {base_url}")

    # GET /
    status, body = http_get(root_url)
    print(f"GET / -> status={status}")
    print(body[:500] + ("..." if len(body) > 500 else ""))

    # GET /health
    status, body = http_get(health_url)
    print(f"GET /health -> status={status}")
    print(body[:500] + ("..." if len(body) > 500 else ""))

    # JSON-RPC initialize
    initialize_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    status, body = http_post_json(root_url, initialize_payload)
    print(f"POST / (initialize) -> status={status}")
    print(body[:500] + ("..." if len(body) > 500 else ""))

    # Tools list
    tools_list_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    status, body = http_post_json(root_url, tools_list_payload)
    print(f"POST / (tools/list) -> status={status}")
    print(body[:500] + ("..." if len(body) > 500 else ""))


if __name__ == "__main__":
    main()
```

### How to run the script on remote PC

```powershell
# Default to 127.0.0.1:8000
& python ".\scripts\test_mcp_connection.py"

# Specify host IP and port
& python ".\scripts\test_mcp_connection.py" "http://192.168.1.50:8000"
```

## Troubleshooting

If ping and TCP fail from remote:
- Verify both PCs are on the same subnet/VLAN.
- Disable VPN/split-tunnel or add a route to the host.
- Check host network profile and firewall:

```powershell
Get-NetConnectionProfile
```

If TCP fails but ping works:
- Ensure server is bound to 0.0.0.0 (not 127.0.0.1).
- Try a different port (e.g., 8001) and update client URL.
- Check for proxy on the remote PC; add exception for the host IP.
