#!/usr/bin/env python3
"""Exit scenario for a token still on a pump.fun bonding curve (before migration).

Price comes from VIRTUAL reserves, but a seller can only be paid from REAL SOL reserves.
Aggregator "liquidity" is neither of them, so do not feed it here.

  gross SOL out = virtual_sol * n / (virtual_token + n)    (n = tokens sold)
  paid          = min(gross, real_sol) minus the fee
  fee           = 125 bps observed on a real sell on 2026-09-25; check the current global config

Checked against a real sell (tx 2DteD4eP...sbd, 2026-09-25 15:21:32 UTC): 8,736,256.39 tokens -> 0.403888573 SOL.
This script reproduces it to within 0.0001 SOL (see tests/test_pumpfun.py).

Live data (no dependencies, uses the public Solana RPC unless you pass --rpc):
  python tools/pumpfun_exit.py --curve 8t4tkjQkH3ArH2zmUVKmFbCUE1pHyCDq4Ac2ojbMh1wh
Manual:
  python tools/pumpfun_exit.py --virtual-sol 39.03 --virtual-token 824846527 --real-sol 9.03 --sell-tokens 8736256
"""
import argparse
import base64
import json
import math
import struct
import sys
import urllib.request
from datetime import datetime, timezone

LAMPORTS = 1_000_000_000
TOKEN_DECIMALS = 6  # pump.fun mints use 6 decimals


def decode_curve(data_b64: str) -> dict:
    """BondingCurve account: 8-byte discriminator, then u64 virtual_token, virtual_sol, real_token,
    real_sol, token_total_supply, then bool complete (pump-fun/pump-public-docs)."""
    raw = base64.b64decode(data_b64)
    if len(raw) < 49:
        raise ValueError("account too short to be a pump.fun bonding curve")
    vt, vs, rt, rs, supply = struct.unpack_from("<QQQQQ", raw, 8)
    return {
        "virtual_token": vt / 10**TOKEN_DECIMALS,
        "virtual_sol": vs / LAMPORTS,
        "real_token": rt / 10**TOKEN_DECIMALS,
        "real_sol": rs / LAMPORTS,
        "supply": supply / 10**TOKEN_DECIMALS,
        "complete": bool(raw[48]),
    }


def fetch_curve(address: str, rpc: str) -> tuple[dict, int]:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getAccountInfo",
                       "params": [address, {"encoding": "base64"}]}).encode()
    req = urllib.request.Request(rpc, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.load(r)["result"]
    if not res or not res["value"]:
        raise ValueError("account not found")
    return decode_curve(res["value"]["data"][0]), res["context"]["slot"]


def sell_on_curve(n_tokens: float, c: dict, fee_bps: float = 125) -> dict:
    vs, vt, rs = c["virtual_sol"], c["virtual_token"], c["real_sol"]
    spot = vs / vt
    gross = vs * n_tokens / (vt + n_tokens)
    capped = gross > rs
    paid_gross = min(gross, rs)
    net = paid_gross * (1 - fee_bps / 10_000)
    return {
        "spot_sol_per_token": spot,
        "gross_sol": gross,
        "net_sol": net,
        "capped_by_real_sol": capped,
        "avg_fill": net / (n_tokens * spot) - 1,
        "spot_move": ((vs - paid_gross) / (vt + n_tokens)) / spot - 1,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Sell scenario on a pump.fun bonding curve.")
    p.add_argument("--curve", help="bonding curve account address (reads live state over RPC)")
    p.add_argument("--rpc", default="https://api.mainnet-beta.solana.com")
    p.add_argument("--virtual-sol", type=float)
    p.add_argument("--virtual-token", type=float)
    p.add_argument("--real-sol", type=float)
    p.add_argument("--sell-tokens", type=float, nargs="*", help="token amounts to sell (UI units)")
    p.add_argument("--fee-bps", type=float, default=125)
    p.add_argument("--sol-usd", type=float, help="optional SOL price to show USD")
    a = p.parse_args()

    if a.curve:
        try:
            c, slot = fetch_curve(a.curve, a.rpc)
        except Exception as e:  # noqa: BLE001
            sys.exit(f"error: could not read curve over RPC: {e}. Status for exit: UNKNOWN")
        src = f"{a.curve} @ slot {slot}, {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC"
    else:
        vals = (a.virtual_sol, a.virtual_token, a.real_sol)
        if any(v is None or not math.isfinite(v) or v < 0 for v in vals) or not a.virtual_sol or not a.virtual_token:
            sys.exit("error: pass --curve, or all of --virtual-sol, --virtual-token, --real-sol (positive numbers)")
        c = {"virtual_sol": a.virtual_sol, "virtual_token": a.virtual_token, "real_sol": a.real_sol, "complete": False}
        src = "manual input"
    if not 0 <= a.fee_bps < 10_000:
        sys.exit("error: --fee-bps must be between 0 and 9999")

    print(f"model=pumpfun_bonding_curve | source: {src} | fee {a.fee_bps:g} bps")
    if c.get("complete"):
        print("curve is COMPLETE: the token migrated. this model no longer applies. get a PumpSwap / router quote.")
        return
    spot = c["virtual_sol"] / c["virtual_token"]
    usd = (lambda s: f" (${s * a.sol_usd:,.0f})") if a.sol_usd else (lambda s: "")
    print(f"spot {spot:.10f} SOL/token | virtual SOL {c['virtual_sol']:.4f} | REAL SOL {c['real_sol']:.6f}{usd(c['real_sol'])}")
    if c["real_sol"] < 0.01:
        print("real SOL is ~0: the price is only virtual. there is nothing to sell into.")

    sizes = a.sell_tokens or [s / spot for s in (0.1, 1, 10)]
    print(f"\n  {'tokens sold':>16} {'worth at spot':>14} {'you get':>12} {'avg fill':>9} {'spot after':>11}")
    for n in sizes:
        if not math.isfinite(n) or n <= 0:
            sys.exit(f"error: sell size must be positive, got {n}")
        r = sell_on_curve(n, c, a.fee_bps)
        flag = "  CAPPED by real SOL" if r["capped_by_real_sol"] else ""
        print(f"  {n:>16,.0f} {n * spot:>10.4f} SOL {r['net_sol']:>8.4f} SOL {r['avg_fill'] * 100:>8.1f}% {r['spot_move'] * 100:>10.1f}%{flag}")
    print("\n  model of the curve state at one moment. a live quote or simulation beats it.")


if __name__ == "__main__":
    main()
