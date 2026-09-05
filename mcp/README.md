# RootCrak Preflight MCP

One MCP server for Cursor, Codex, OpenClaw, Hermes, and anything else that speaks stdio MCP.

Tool: `preflight_url` — quotes the live x402 402.  
Tool: `preflight_result` — polls a job **after** you paid.

This process **does not hold keys** and **does not sign USDC**. The host pays with the official x402 client, then retries `POST` with `PAYMENT-SIGNATURE`.

## Cursor

```json
{
  "mcpServers": {
    "rootcrak-preflight": {
      "command": "python3",
      "args": ["/absolute/path/to/intel-api/mcp/preflight_url.py"]
    }
  }
}
```

Same block works in Claude Desktop / OpenClaw / Hermes MCP config. Codex: point the MCP stdio command at this file.

## Flow

1. Agent calls `preflight_url` with a target (`scan`: `drainer`, `domain`, or `both`).
2. You get `accepts[]` (price, pay_to, Solana `feePayer`).
3. Pay that quote. Retry the same create POST with `PAYMENT-SIGNATURE`.
4. Call `preflight_result` with `job_id` + `access_token` from the paid 200.

Contract: [AGENTS.md](../AGENTS.md)  
Live: https://intel.rootcrak.com/
