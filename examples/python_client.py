"""Minimal Intel API client: health, unpaid 402, poll after you attach payment.

Does not hold keys. Sign USDC with the official x402 SDK, then pass the
PAYMENT-SIGNATURE header into create_job().
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE = "https://intel.rootcrak.com"


def http(method: str, path: str, *, body: dict | None = None, headers: dict | None = None):
    payload = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=payload,
        method=method,
        headers={"Content-Type": "application/json", "User-Agent": "rootcrak-intel-example/1", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw[:800]}
        return exc.code, parsed, dict(exc.headers)


def quote(scan_type: str, target: str) -> dict:
    status, body, _ = http("POST", f"/v1/intel/scans/{scan_type}", body={"target": target})
    if status != 402:
        raise RuntimeError(f"expected 402, got {status}")
    detail = body.get("detail") or body
    return detail


def create_job(scan_type: str, target: str, payment_signature: str) -> dict:
    status, body, _ = http(
        "POST",
        f"/v1/intel/scans/{scan_type}",
        body={"target": target},
        headers={"PAYMENT-SIGNATURE": payment_signature},
    )
    if status != 200 or not body.get("job_id"):
        raise RuntimeError(f"settle failed: {status} {body}")
    return body


def wait_result(job: dict) -> dict:
    token = job["access_token"]
    path = job["result"]
    deadline = time.time() + int(job.get("timeout_seconds") or 90)
    sleep_for = float(job.get("poll_after_seconds") or 5)
    while time.time() < deadline:
        status, body, headers = http("GET", path, headers={"X-Job-Token": token})
        if status == 200:
            return body
        if status == 502:
            raise RuntimeError(f"job failed: {body}")
        retry = headers.get("Retry-After") or headers.get("retry-after")
        time.sleep(float(retry) if retry else sleep_for)
    raise TimeoutError("job did not finish in timeout_seconds")


if __name__ == "__main__":
    health = http("GET", "/v1/intel/health")[1]
    print("health", {k: health.get(k) for k in ("status", "environment", "payments_enabled")})
    quoted = quote("domain", "https://example.com")
    accepts = quoted.get("accepts") or []
    print("402 rails", [(a.get("rail"), a.get("price"), a.get("amount")) for a in accepts])
    print("sign a USDC x402 payment for one accept, then call create_job() + wait_result()")
