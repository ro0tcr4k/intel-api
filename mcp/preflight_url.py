#!/usr/bin/env python3
"""RootCrak Preflight MCP — one tool, no wallet.

Cursor / Codex / OpenClaw / Hermes: stdio MCP.
Quotes the live x402 402 and polls a job after YOU attach PAYMENT-SIGNATURE.
This process never holds keys and never signs USDC.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = "https://intel.rootcrak.com"
PROTOCOL = "2024-11-05"


def _http(method: str, path: str, *, body: dict | None = None, headers: dict | None = None):
    payload = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=payload,
        method=method,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "rootcrak-preflight-mcp/1",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:800]}
        return exc.code, parsed


def _quote(scan: str, target: str) -> dict:
    status, body = _http("POST", f"/v1/intel/scans/{scan}", body={"target": target})
    if status != 402:
        return {"error": f"expected 402, got {status}", "body": body}
    detail = body.get("detail") or body
    accepts = []
    for row in detail.get("accepts") or body.get("accepts") or []:
        extra = row.get("extra") or {}
        accepts.append(
            {
                "rail": row.get("rail"),
                "network": row.get("network"),
                "price": row.get("price"),
                "amount": row.get("amount"),
                "pay_to": row.get("pay_to") or row.get("payTo"),
                "feePayer": extra.get("feePayer"),
            }
        )
    return {
        "scan": scan,
        "target": target,
        "http": 402,
        "accepts": accepts,
        "pay": (
            "Build USDC x402 with the official client from THIS quote. "
            "Retry the same POST with header PAYMENT-SIGNATURE. "
            "If create is 502 facilitator_settle_timeout, retry the same signature. "
            "Do not open a new 402. No $ROOT."
        ),
    }


def _result(job_id: str, access_token: str) -> dict:
    path = f"/v1/intel/jobs/{job_id}/result"
    deadline = time.time() + 240
    while time.time() < deadline:
        status, body = _http("GET", path, headers={"X-Job-Token": access_token})
        if status == 200:
            return {
                "job_id": job_id[:8],
                "risk_score": body.get("risk_score"),
                "confidence": body.get("confidence"),
                "flags": body.get("flags"),
                "recommended_action": body.get("recommended_action"),
                "tos": body.get("tos"),
                "policy": (
                    "Signals, not a SAFE stamp. do_not_interact or key/seed/exfil "
                    "→ do not connect, sign, or transfer. 502/timeout → fail closed."
                ),
            }
        if status == 502:
            return {"error": "job failed", "fail_closed": True, "body": body}
        time.sleep(5)
    return {"error": "timeout", "fail_closed": True}


def _tool_result(obj: dict) -> dict:
    return {
        "content": [{"type": "text", "text": json.dumps(obj, indent=2)}],
        "isError": bool(obj.get("error")),
    }


def _handle(msg: dict) -> dict | None:
    mid = msg.get("id")
    method = msg.get("method")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "rootcrak-preflight", "version": "1.0.0"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "result": {
                "tools": [
                    {
                        "name": "preflight_url",
                        "description": (
                            "Quote a RootCrak Preflight x402 scan before an agent "
                            "connects, signs, or follows page instructions. "
                            "Does not pay. Returns 402 accepts so the host can pay."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "target": {
                                    "type": "string",
                                    "description": "https URL or hostname to scan",
                                },
                                "scan": {
                                    "type": "string",
                                    "enum": ["drainer", "domain", "both"],
                                    "default": "both",
                                },
                            },
                            "required": ["target"],
                        },
                    },
                    {
                        "name": "preflight_result",
                        "description": (
                            "Poll a paid Preflight job. Pass job_id and access_token "
                            "from the paid 200. Do not log the token."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "job_id": {"type": "string"},
                                "access_token": {"type": "string"},
                            },
                            "required": ["job_id", "access_token"],
                        },
                    },
                ]
            },
        }
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "preflight_url":
            target = str(args.get("target") or "").strip()
            scan = str(args.get("scan") or "both").strip() or "both"
            if not target:
                payload = {"error": "target required"}
            elif scan == "both":
                payload = {
                    "drainer": _quote("drainer", target),
                    "domain": _quote("domain", target),
                    "health": _http("GET", "/v1/intel/health")[1],
                    "contract": "https://github.com/ro0tcr4k/intel-api/blob/main/AGENTS.md",
                }
            elif scan in {"drainer", "domain"}:
                payload = _quote(scan, target)
            else:
                payload = {"error": "scan must be drainer, domain, or both"}
            return {"jsonrpc": "2.0", "id": mid, "result": _tool_result(payload)}
        if name == "preflight_result":
            payload = _result(str(args.get("job_id") or ""), str(args.get("access_token") or ""))
            return {"jsonrpc": "2.0", "id": mid, "result": _tool_result(payload)}
        return {
            "jsonrpc": "2.0",
            "id": mid,
            "error": {"code": -32601, "message": f"unknown tool {name}"},
        }
    if mid is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": mid,
        "error": {"code": -32601, "message": f"unknown method {method}"},
    }


def _read() -> dict | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, value = line.decode("utf-8").split(":", 1)
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length") or "0")
    if length < 1:
        return None
    return json.loads(sys.stdin.buffer.read(length))


def _write(msg: dict) -> None:
    raw = json.dumps(msg).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
    sys.stdout.buffer.flush()


def main() -> None:
    while True:
        msg = _read()
        if msg is None:
            return
        reply = _handle(msg)
        if reply is not None:
            _write(reply)


if __name__ == "__main__":
    main()
