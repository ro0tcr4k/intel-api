# Examples

- `unpaid.sh` — health + SDK pin + 402 quote. No USDC spent.
- `python_client.py` — quote, then `create_job` / `wait_result` after you attach an official x402 `PAYMENT-SIGNATURE`.

Sign payments with the [official x402 client](https://docs.x402.org). On Solana, copy `feePayer` from the 402 you just received.
