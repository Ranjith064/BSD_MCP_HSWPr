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
