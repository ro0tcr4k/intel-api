# x402 handshake

Protocol: official [x402](https://docs.x402.org) (`GET https://intel.rootcrak.com/v1/intel/sdk` for the seller pin).

```
Agent                         intel.rootcrak.com                    Facilitator
  |                                    |                                 |
  | POST /v1/intel/scans/{type}        |                                 |
  | { target }                         |                                 |
  | -------------------------------→   |                                 |
  | 402 + accepts[]                    |                                 |
  | ←-------------------------------   |                                 |
  |                                    |                                 |
  | sign USDC exact payment            |                                 |
  | (use extra.feePayer on Solana)     |                                 |
  |                                    |                                 |
  | POST same path + PAYMENT-SIGNATURE |                                 |
  | -------------------------------→   |  verify + settle                |
  |                                    | ----------------------------→   |
  |                                    | ←----------------------------   |
  | 200 { job_id, access_token, poll } |                                 |
  | ←-------------------------------   |                                 |
  |                                    |                                 |
  | GET .../result  X-Job-Token        |                                 |
  | 202 … 200 Intel payload            |                                 |
```

## 402 accept (shape)

Each `accepts[]` row includes at least:

- `scheme` (exact)
- `network` (CAIP-2)
- `asset` (USDC mint / token)
- `amount` (atomic, 6 decimals)
- `pay_to`
- `price` (`$0.05` or `$0.25`)
- `rail` (`evm` | `spl`)
- `extra.feePayer` on Solana (current facilitator payer — do not reuse an old one)

## Headers

| Direction | Header | Role |
|---|---|---|
| Agent → API | `PAYMENT-SIGNATURE` | Signed x402 payload |
| Agent → API | `X-Job-Token` | Job result access |
| API → Agent | `Retry-After` | Seconds to wait on 202 / 429 |
| API → Agent | `PAYMENT-RESPONSE` | Server receipt after settle — **not** a client input |

## Poll

| scan | `poll_after_seconds` | `timeout_seconds` |
|---|---|---|
| drainer | 5 | 90 |
| domain | 12 | 480 |

Stop polling when you exceed `timeout_seconds` without a 200. Fail closed.

## Errors

| Status | Meaning |
|---|---|
| 402 | Need payment, or payment rejected (including facilitator mismatch) |
| 401 | Job token missing |
| 404 | Unknown job or wrong token |
| 429 | Rate limit — wait `Retry-After` |
| 502 | Paid job failed in the engine |
| 503 | Verifier / SDK unavailable |
