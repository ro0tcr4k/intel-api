# Why agents should scan before they act

## The shift

Humans pause on a connect-wallet modal. Agents do not, unless you program a pause. The same two crimes that hit people now hit autonomous signers:

1. **Wallet drainers** — malicious dapps, cloned frontends, approval phishing. One `approve` or malicious transaction and the wallet is empty.
2. **Prompt injection** — instructions hidden in a page, tweet, image, or CSS (`opacity:0`, off-screen text, encoded blobs). The model treats them as tasks. Documented cases include Morse-code injection on Base (~$200K) and a hidden tweet instruction (~$175K).

The agent economy makes this global: high frequency, no second pair of eyes, keys sitting in the same process that fetches untrusted HTML.

## What RootCrak Intel is

A **paid, machine-readable pre-flight**. You give a URL. You pay USDC over HTTP 402 (x402). You get risk signals — score, confidence, flags, evidence, a recommended action. You decide whether to proceed.

It is **not** a warranty, an audit badge, or a SAFE/DANGEROUS oracle. A wrong “all clear” is how brands die. We refuse that shape on purpose.

## What we actually run (v1)

- **Drainer ($0.05)** — static heuristics for known drain kits and hostile approval flows. No headless browser in this paid path.
- **Domain ($0.25)** — transport/security headers, DNS email auth gaps, sensitive file exposure, plus a **static LLM-injection** pass on the HTML we already fetched (hidden text, instruction override, encoded payloads, wallet/key exfil, jailbreak phrasing).

Novel wording can evade regex. That is why the output is advice plus evidence, and why `do_not_interact` / exfil flags should fail closed.

## Why pay per call

Agents are not the human free tier. The free scanner on rootcrak.com is a funnel for people. This API is the agent paywall: settle first, then compute. USDC on Base and Solana so EVM and SVM agents use the rail they already hold.

## Fail-closed default

If the API is unreachable, the job fails, or you are unsure: **do not sign**. Scanning is cheaper than a drained agent wallet.
